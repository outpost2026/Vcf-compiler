# DXF Predictive Parser — Metodologie kodifikace tacitních znalostí operátora CNC

**Verze:** 1.0
**Datum:** 12. 6. 2026
**Status:** Architectural blueprint — vyžaduje dostatečný vzorek VCF pro aktivaci
**Autor:** Reasoning analysis (outpost2026 + OpenCode agent)
**Cíl:** Kodifikovat metodická pravidla pro převedení tacitních znalostí CNC operátora (manifestovaných v řezných parametrech historických VCF souborů) do light-ML nástrojů, jež umožní **prediktivní pre-processing DXF** — předpověď řezných parametrů přímo z geometrie výkresu.

---

## 1. Problém — epistemologická dekonstrukce

### 1.1 Co operátor dělá (implicitní inference)

```
GEOMETRIE (vidí na obrazovce)
    ↓ percepce tvarů, velikostí, křivostí, drobnosti prvků
MENTÁLNÍ MODEL (zkušenost + intuice + znalost stroje)
    ↓ rozhodnutí
PARAMETRY ŘEZU (zapsány do vrstev ve VCutWorks → uloženo ve VCF)
```

Operátor nepočítá parametry — **rozhoduje se**. Jeho rozhodnutí nejsou náhodná — jsou to deterministické reakce na geometrii, ověřené stovkami zakázek. Parametry nejsou arbitrární, jsou **podmíněny geometrickými vlastnostmi** — operátor jen neumí tuto vazbu formalizovat.

### 1.2 Co VCF parser aktuálně umí

Aktuální parser (`vcf_parser_v20.py`) z VCF extrahuje:
- **Geometrii na úrovni elementů:** souřadnice, typ (Line/Polyline/Polygon/Circle), plochu, perimeter, bbox, aspect ratio, centroid
- **Parametry vrstev:** cutter_type_id, speed, power, passes, frequency, direction, width_comp, overshoot
- **Sémantický audit:** risk_score, sequence violations, H2 warnings, vakuový přítlak — **tvrdá fyzikální pravidla** (Knowledge Base engine)

**Co chybí:** Schopnost **předpovědět**, jaké parametry by měla vrstva obdržet, známe-li pouze geometrii jejích elementů. Tedy: "Když dám parseru surové DXF, jaké řezné parametry navrhne?"

### 1.3 Proč je to B2B primární objektiv

1. **DXF je vstupem od designérů** — neobsahuje CNC parametry (ty přidává až operátor ve VCutWorks)
2. **Firmy bez operátora** (např. outsourcing výroby, nový závod) nemají historická data — chtějí defaultní parametry odvozené z geometrie
3. **Nacenění ve fázi návrhu** — grafik vytvoří DXF a hned vidí orientační dobu a náklady řezu
4. **Škálování výroby** — eliminuje bus-factor jednoho technologa

---

## 2. Klíčový insight: jednotka analýzy není element, ale vrstva

Elementy v jedné vrstvě **sdílejí identické parametry**. Operátor nepřiřazuje parametry elementům — přiřazuje je **skupinám geometricky podobných elementů** (to jest vrstvám).

Statistická velikost vzorku = **počet vrstev**, nikoliv počet elementů. 33 výrobních VCF souborů × průměrně 4 vrstvy = ~132 nezávislých vzorků. To je **dostatečné pro extrakci jednoduchých pravidel** (decision tree max_depth=3), ale nedostatečné pro hluboké neuronové sítě.

**Deskriptor vrstvy** = statistická distribuce geometrických vlastností jejích elementů:

| Feature | Popis | Typ | Význam |
|---------|-------|-----|--------|
| `geom_type_freq` | Frekvence typů elementů (Circle/Line/Polyline/Polygon) | `Dict[str,float]` | Operátor segmentuje podle tvarů |
| `mean_radius` | Průměrný poloměr kružnic | `float` | Vibrate nůž má minimální rádius |
| `median_area` | Medián plochy elementů | `float` | Vakuový přítlak, riziko posunu |
| `total_perimeter` | Celková délka dráhy ve vrstvě | `float` | Dominantní prediktor času |
| `mean_aspect_ratio` | Průměrný poměr width/height | `float` | Protáhlé tvary = riziko torze |
| `mean_curvature` | Průměrná křivost (zakřivenost drah) | `float` | Akcelerace stroje v zatáčkách |
| `count_small_elements` | Počet elementů s plochou pod threshold | `int` | Drobné díly = riziko vytržení |
| `convex_hull_density` | Poměr plochy elementů / plocha convex hullu | `float` | Nesting hustota |

---

## 3. Pět cest k prediktivnímu parseru

### Cesta 1: Physics Baseline — tvrdá fyzikální pravidla

**Princip:** Některé parametry jsou **fyzikálně vynuceny** — nezávisí na preferenci operátora, ale na omezeních stroje a materiálu. Tyto vazby lze formalizovat jako `if-then` pravidla zapsaná v `rules.json`.

**Tyto pravidla již zachytávají:**
```
geometrie → fyzikální omezení → nutný parametr
```

Příklady:
```
IF min_radius < 2.0 mm → tool = Vibrate cutter
  (V-slot nůž neprojede otáčkou, fyzicky nemožné)

IF element.area < 200 mm² → RISK_CRITICAL: posun dílu
  (vakuový přítlak < gravitace + řezná síla)

IF element.bbox_max_dim > 1200 mm AND panel = 1200 → FATAL
  (element větší než panel — nelze vyřezat)

IF H2 > H_total * 0.8 → WARNING: nulový průřez
  (zbytková tloušťka je větší než 80% materiálu)
```

**Implementace:**
- Rozšířit `Knowledge_base/models.py` o `GeometryRule`, `ToolMappingRule`
- Rozšířit `Knowledge_base/rules.json` o geometrická pravidla
- Integrovat do `vcf_parser_v20.py` jako *pre-inference* (před voláním ML)

**Výhoda:** Žádná data — pravidla jsou odvoditelná z fyziky stroje. 100% traceovatelnost.
**Výstup:** `layer_params = physics_minimum(geometry)` — dolní mez, od které se může ML odrazit.

---

### Cesta 2: Decision Boundary Mining — extrakce pravidel z historických VCF

**Princip:** Pro každý cílový parametr (tool_type, speed, passes) najít **kombinaci 1—3 geometrických featureů vrstvy**, která ho nejlépe separuje.

**Algoritmus:**
```python
from sklearn.tree import DecisionTreeClassifier, export_text

# X = deskriptory vrstev z historických VCF
# y = cílový parametr (např. cutter_type_id: 0=V-slot, 1=Vibrate)
#      nebo: speed_binned (nízká/střední/vysoká)

clf = DecisionTreeClassifier(max_depth=3, min_samples_leaf=5)
clf.fit(X, y)
rules = export_text(clf, feature_names=X.columns)

# P-hodnota z bootstrapu (1000 iterací s náhodně přeskupenými y)
p_value = (sum(null_accuracy >= observed_accuracy) + 1) / (1000 + 1)
```

**Očekávaný výstup:**
```
|--- mean_radius <= 4.50
|   |--- fraction_circles <= 0.80
|   |   |--- class: V-slot       (P=0.87, N=12)
|   |--- fraction_circles > 0.80
|   |   |--- mean_area <= 350.00
|   |   |   |--- class: Vibrate  (P=0.94, N=18)
```

**Klíčová omezení:**
- `max_depth=3` zabraňuje overfittingu na malém vzorku (132 vrstev)
- `min_samples_leaf=5` vynucuje minimální podporu pravidla
- Bootstrap P-hodnota testuje, zda pravidlo není náhodné
- Pravidla generovaná z vrstev (nikoliv elementů) eliminují pseudoreplikaci

**Klasifikátory — co extrahovat pro jaký parametr:**

| Cílový parametr | Typ | Klasifikátor | Vysvětlení |
|-----------------|-----|-------------|------------|
| `cutter_type_id` | nominální (1=V-slot, 2=Vibrate) | DecisionTreeClassifier | Který nástroj pro jakou geometrii |
| `speed_binned` | ordinální (low/medium/high) | DecisionTreeClassifier | Rychlostní kategorie per geometrie |
| `passes` | ordinální (1, 2, 3) | DecisionTreeClassifier | Počet průjezdů |
| `direction` | binární (CW/CCW) | DecisionTreeClassifier | Směr řezu |
| `width_comp` | binární (On/Off) | DecisionTreeClassifier | Kompenzace šířky nástroje |

**Prah minimální jistoty:**
- P > 0.80: pravidlo je aktivní (aplikováno)
- P ∈ 0.60—0.80: pravidlo je navrženo s flag `CONDITINAL`
- P < 0.60: pravidlo není extrahováno → fallback na Cestu 3

---

### Cesta 3: Case-Based Reasoning — vyhledávání nejpodobnější zakázky

**Princip:** Místo generalizace pravidel použít **paměť** — najít v archivu historických VCF nejpodobnější výkres a převzít jeho parametry.

Toto je nejbližší simulaci toho, jak operátor reálně přemýšlí: "Tohle je jako ta zakázka z minulého týdne."

**Algoritmus:**
```python
from sklearn.metrics.pairwise import cosine_similarity

def find_closest_layer(new_layer_features, archive_layers, top_k=3):
    similarities = cosine_similarity(
        new_layer_features.reshape(1, -1),
        archive_layers
    )
    top_indices = np.argsort(similarities[0])[-top_k:][::-1]
    return top_indices, similarities[0][top_indices]

# Pro každou vrstvu nového DXF:
#   1. Vypočíst feature vector
#   2. Najít top-3 nejpodobnější vrstvy v historickém archivu
#   3. Hlasováním (majority vote) určit parametry
#   4. Confidence = průměrná similarita × shoda parametrů
```

**Deskriptor výkresu** (pro celkovou podobnost):
- Počet vrstev
- Celkový počet elementů
- Distribuce typů geometrie napříč celým výkresem
- Celková plocha a perimeter
- Bounding box celého výkresu

**Výhoda:** Žádný trénink — pouze indexace. Funguje okamžitě po nashromáždění archivu.
**Omezení:** Selhává graceful — "žádná podobná zakázka" → flag pro manuální vstup.

---

### Cesta 4: Operator Signature Extraction — delta od fyzikální baseline

**Princip:** Každý operátor má **osobní signaturu** — systematické odchylky od fyzikálně optimálních parametrů. Zachytit tuto signaturu jako offset:

```
predikovaný_parametr = physics_baseline(geometrie) + operator_delta(geometrie)
```

**Hypotetické příklady:**
- "Karel vždy dává o 15 % nižší speed na polygony s area > 2000 mm²"
- "Karel nikdy nepoužívá Passes > 1 pro 12mm materiál"
- "Karel řadí kruhy pod 10 mm do Vibrate, i když by fyzikálně stačil V-slot"

**Implementace:**
```python
# Operator delta pro speed:
delta_speed = observed_speed - physics_recommended_speed
# Fit regression on geometry features:
delta_speed(geom_features) = f(mean_radius, mean_area, fraction_circles, ...)
# Např. linear regression: beta coefficients = "operator signature"
```

**Omezení:** Vyžaduje identifikaci operátora. VCF formát neukládá operator_id — nutná aproximace (časové okno, pracovní stanice, konvence pojmenování).

---

### Cesta 5: Inverse Conditional Analysis — frekventistický pohled

**Princip:** Obrátit perspektivu: **"Když operátor použil parametr X, co měla geometrie společného?"**

Místo predikce P(parametr | geometrie) analyzovat P(geometrie | parametr):

```
P(mean_radius < 5mm | tool=Vibrate) = 0.94
P(fraction_polygons > 0.5 | tool=V-slot) = 0.89
P(count_small_elements > 20 | passes=2) = 0.73
```

**Výstup:** Pro každou hodnotu parametru → profil "typické" geometrie:
```
Vibrate cutter: typicky min_radius < 4.5 mm, fraction_circles > 0.8, count > 10
V-slot:         typicky min_radius > 5 mm, fraction_polygons > 0.5, total_area > 5000 mm²
```

Tato cesta je **statisticky robustnější** než klasifikace, protože podmiňuje na diskrétním parametru (který je pevnou hodnotou z vrstvy). Lze ji použít jako validační křížovou kontrolu pro Cestu 2 — pravidla z obou cest se musí shodovat.

---

## 4. Doporučená hybridní architektura (1 + 2 + 3)

```
┌──────────────────────────────────────────────────────────────────┐
│                    DXF PRE-PROCESSOR PIPELINE                      │
│                                                                    │
│  ┌─────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │ 1. PHYSICS  │    │ 2. RULE MINING   │    │ 3. CASE FALLBACK │  │
│  │  BASELINE   │    │ (z histor. VCF)  │    │ (cosine similarity│  │
│  │  (rules)    │───▶│ (decision tree)  │───▶│  na archivním     │  │
│  │             │    │                  │    │  poolu VCF)       │  │
│  └──────┬──────┘    └───────┬──────────┘    └───────┬──────────┘  │
│         │                   │                       │             │
│         ▼                   ▼                       ▼             │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │         OUTCOME: layer_params + confidence_flag                │ │
│  │         ├── HIGH (P>90%)   → automaticky aplikováno           │ │
│  │         ├── MEDIUM (P>80%) → navrženo, technolog schvaluje    │ │
│  │         └── LOW (P<80%)   → FLAG: manuální vstup              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  4. OPERATOR SIGNATURE (volitelně, pro personalizaci)         │ │
│  │     delta_speed = f(geometry) per operator_id                 │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  5. INVERSE CHECK (validace)                                  │ │
│  │     Shoduje se navržený parametr s frekventistickým profilem? │ │
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### 4.1 Tok dat

1. **DXF na vstupu** → parser extrahuje geometrii (stejná pipeline jako VCF, jen bez parametrů vrstev)
2. **Geometrie elementů** → agregace do deskriptoru vrstev (feature vector)
3. **Feature vector** → Cesta 1: aplikace tvrdých fyzikálních pravidel → `params_min`
4. **Feature vector** → Cesta 2: klasifikace do parametrů → `params_ml` + `confidence`
5. **Pokud confidence < 0.80** → Cesta 3: vyhledání nejpodobnější vrstvy v archivu → `params_case`
6. **Merge:** `params_ml` kde confidence >= 0.80, `params_case` kde confidence < 0.80
7. **Validace (Cesta 5):** navržené parametry vs. inverzní frekventistický profil

### 4.2 Výstup — DXF pre-processor

```json
{
  "dxf_file": "zakazka_abc.dxf",
  "predicted_layers": [
    {
      "layer_index": 0,
      "elements": 42,
      "geometry_profile": {
        "mean_radius": 3.2,
        "fraction_circles": 0.95,
        "total_area_mm2": 4520.0
      },
      "predicted_params": {
        "cutter_type": "Vibrate",
        "cutter_type_id": 2,
        "speed_mm_s": 10,
        "passes": 1,
        "direction": "CCW",
        "width_comp": false
      },
      "confidence": 0.94,
      "confidence_flag": "HIGH",
      "source": "decision_tree",
      "rule": "IF mean_radius<4.5 AND fraction_circles>0.8 THEN Vibrate",
      "support_n": 18
    }
  ],
  "manual_review_required": false,
  "timestamp": "2026-06-12T15:00:00+02:00",
  "engine_version": "dxf_preprocessor_v1.0"
}
```

---

## 5. Technický implementační plán

### 5.1 Nové soubory

```
src/
  analysis/
    __init__.py
    layer_descriptor.py          # Výpočet feature vektoru vrstvy
    pattern_miner.py             # Cesta 2: decision tree rule extraction
    case_retriever.py            # Cesta 3: cosine similarity search
    inverse_analyzer.py          # Cesta 5: inverzní frekventistická analýza
  dxf_preprocessor.py            # Hlavní pipeline (orchestrátor)

tests/
  test_layer_descriptor.py
  test_pattern_miner.py
  test_case_retriever.py

data/
  element_dataset/               # Fáze 0: flat dataset
    build_dataset.py              # Skript pro extrakci z historických VCF
    layers.parquet                # Deskriptory vrstev + parametry

docs/analysis/                    # Výstupy analýz
    parameter_correlations.md
```

### 5.2 Knihovny (přidat do `requirements.txt`)

```
scikit-learn>=1.3.0
numpy>=1.24.0
pandas>=2.2.0     # již máme
scipy>=1.11.0
```

Žádné deep learning frameworky — pouze `scikit-learn` pro interpretovatelné modely.

### 5.3 Fáze implementace

| Fáze | Název | Co obsahuje | Odhad |
|------|-------|-------------|-------|
| **0** | Dataset Builder | Skript, který projde všechny parsované VCF, pro každou vrstvu vypočítá deskriptor a uloží flat dataset `layers.parquet` | 0.5 dne |
| **1** | Physics Baseline | Rozšířit `Knowledge_base/rules.json` o geometrická pravidla (tool mapping z poloměru, vakuum z plochy, bbox z panelu) | 0.5 dne |
| **2** | Pattern Miner | `pattern_miner.py` — decision tree pro tool_type, speed_binned, passes, direction, width_comp. Bootstrap P-hodnoty. Export pravidel do JSON. | 1.0 dne |
| **3** | Case Retriever | `case_retriever.py` — cosine similarity indexace archivu vrstev. Vyhledávání top-k a majority vote | 0.5 dne |
| **4** | Pipeline Integration | `dxf_preprocessor.py` — orchestrátor Cest 1→2→3→5. Confidence calculation. Výstupní JSON. Integrace do `app.py` jako nový expander v dashboardu. | 1.0 dne |
| **5** | Evaluace | Porovnání predikovaných vs. reálných parametrů na hold-out VCF (např. fluenz_l). Report přesnosti. | 0.5 dne |

---

## 6. Vstupní požadavky na data — minimální vzorek

| Požadavek | Minimum | Ideální | Proč |
|-----------|---------|---------|------|
| Počet unikátních VCF | 30 | 100+ | Každý VCF přispívá ~4 vrstvami → 120 vs. 400 vzorků |
| Počet různých materiálů | 1 | 3+ | Mix napříč materiály rozbíjí signál (confounder) |
| Od jednoho operátora | ideálně 1 | 1-2 s identifikací | Různí operátoři = různé signatury = šum |
| Různorodost geometrie | min. 5 VCF s kruhy < 5 mm | pokrýt celé spektrum | Bez variance v trénovacích datech není co fitovat |
| Hold-out set (evaluace) | 20 % dat (min. 6 VCF) | 30 % | Nezávislé ověření přesnosti |

**Signál bude detekovatelný již při 30—50 VCF od jednoho operátora**, za předpokladu, že:
- Operátor je konzistentní (nemění styl ze dne na den)
- Geometrie je dostatečně variabilní (malé kruhy, velké polygony, smíšené vrstvy)
- Materiálová třída je homogenní (např. všechny 12mm PET plsť)

---

## 7. Validace úspěšnosti — finální metriky

| Kritérium | Měřítko | Threshold |
|-----------|---------|-----------|
| **Tool type accuracy** | F1-score (Cesta 2) na hold-out setu | > 0.85 |
| **Speed bin accuracy** | Weighted F1 (low/medium/high) | > 0.75 |
| **Passes accuracy** | Exact match na hold-out setu | > 0.80 |
| **Case-based recall** | Úlohy kde Cesta 3 správně nahrazuje selhávající Cestu 2 | Změřit |
| **Fyzikální false-positive rate** | Cesta 1 navrhne tool_type, který není fyzikálně možný | = 0 (blokováno rules engine) |
| **Interpretovatelnost** | Každé pravidlo z Cesty 2 je vyjádřeno jako `if X then Y` | 100 % |

---

## 8. Vazba na existující kódovou bázi

| Existující modul | Jak bude rozšířen |
|------------------|-------------------|
| `vcf_parser_v20.py` | Volání `dxf_preprocessor.py` po parsování geometrie. Nový výstup `predicted_params` v `parsed_data`. |
| `Knowledge_base/engine.py` | Nová pravidla v `rules.json`: tool mapping z geometrie, vakuový přítlak, panel overflow |
| `Knowledge_base/models.py` | Nové třídy: `GeometryRule`, `ToolMappingRule`, `LayerDescriptor` |
| `app.py` | Nový dashboard expander: "Predikce parametrů z geometrie (DXF pre-processing)" |
| `tests/test_golden_master.py` | Nový test: `test_dxf_prediction_match` — porovnání predikovaných a reálných parametrů na hold-out datech |

---

## 9. Metadata dokumentu

```json
{
  "document_id": "DXF_PREDICTIVE_PARSER_METHODOLOGY_V1.0",
  "author": "outpost2026 + OpenCode reasoning agent",
  "date": "2026-06-12",
  "status": "BLUEPRINT",
  "activation_prerequisite": "Dostupnost archivu 30+ VCF souborů od jednoho operátora",
  "next_document": "IMPLEMENTATION PLAN — fáze 0–5 s odhadem pracnosti",
  "related": [
    "docs/RE_CASE_STUDY_VCUTWORKS_LIGHTBURN_v2.md",
    "docs/KNOWLEDGE_CORPUS_VCUTWORKS_LIGHTBURN.md",
    "docs/HANDOFF_SESSION_2026-06-11.md",
    "src/Knowledge_base/engine.py"
  ]
}
```
