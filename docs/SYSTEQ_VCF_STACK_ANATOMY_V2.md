# SYSTEQ VCF Stack — V2: Architektonická disekce & oponentura

**Verze dokumentu:** 2.0 | **Datum:** 2026-06-25 | **Autor:** outpost2026
**Účel:** Samostatná (de novo) architektonická analýza celého vyvinutého stacku. Nenavazuje na V1 — jedná se o nezávislou oponenturu na stejném zdrojovém kódu. Výstup pro autorovu vlastní inferenci a rozhodnutí o dalším postupu.

---

## ČÁST A: Architektonická disekce

### A.1 Rozsah repozitáře

| Soubor | Rozsah | Role v architektuře |
|---|---|---|
| `vcf_binary_reader.py` | 155 ř. | L0 — binární extrakce VCF vrstev |
| `vcf_geometry.py` | 1197 ř. | L1 — parsování geometrie + 6 detekčních funkcí + 9 pomocných funkcí |
| `vcf_time_predictor.py` | 71 ř. | L2 — kinematický model predikce času |
| `vcf_parser_v20.py` | 810 ř. | L3 — engine orchestrace (RuidaVcfEngineV20) |
| `vcf_config.py` | 149 ř. | Konfigurační vrstva (JSON loadery, fallback defaulty) |
| `Knowledge_base/engine.py` | 564 ř. | L4 — sémantický audit (6 rule kategorií) |
| `Knowledge_base/models.py` | 103 ř. | Datové modely (RuleClass, Severity, EpistemicMetadata) |
| `Knowledge_base/rules.json` | 101 ř. | Pravidla s epistemickou metadatovou vrstvou |
| `app_config.json` | 77 ř. | Obchodní + GCP konfigurace |
| `machine_profile.json` | 74 ř. | Kinematický profil stroje |
| `app.py` (Streamlit) | 1082 ř. | L5 — Web UI |
| **Celkem** | **~3400 ř.** | **6 vrstev, 11 souborů** |

Test infrastructure: 10 test souborů, 7 golden master baselines, 23 demo VCF souborů.

### A.2 Vrstvená architektura

```
app.py (1082 ř.)                          ← L5: Prezentační
  └─ vcf_parser_v20.py (810 ř.)            ← L3: Orchestrační
       ├─ vcf_binary_reader.py (155 ř.)    ← L0: Binární RE
       ├─ vcf_geometry.py (1197 ř.)        ← L1: Geometrie + detekce
       ├─ vcf_time_predictor.py (71 ř.)    ← L2: Čas
       ├─ vcf_config.py (149 ř.)           ← Konfigurace
       └─ Knowledge_base/engine.py (564 ř.)← L4: Sémantický audit
            ├─ models.py (103 ř.)
            └─ rules.json (101 ř.)
```

### A.3 Data flow

```
VCF binary
  │
  ▼
L0 extract_active_layers_details()        → 32 pokusných čtení bloků, filtrace speed ∈ [100, 2000] ∩ %5=0 → []layer
  │
  ▼
L1 parse_geometry_v18_2()                 → sekvenční skenování GEOMETRY_SIG → []element s bbox, centroid, vertices, complexity
  │  group_elements()                     → shape_groups s instancí
  │  detect_panel_format()                → mapování dimenzí na standardy
  │  compute_density_grid()               → 8×8 histogram
  │  detect_symmetry()                    → 12-intervalová histogramová symetrie
  │  classify_layout()                    → variance-based classification
  │
  ▼
L3 parse_bytes() — monolitická orchestrace (ř. 72–752):
  │  → canvas bbox z aktivních elementů
  │  → tloušťka inference (V-slot H2 → 12/24mm)
  │  → layer-level sequence validation
  │  → element_id assignment #1 (ř. 271)
  │  → element-level nested cut sequence (ř. 277–376)
  │  → BFS sub-jobs clustering (ř. 400–444)
  │  → parents_map (ř. 472–491) + element_id assignment #2 (ř. 494)
  │  → topology_tree (ř. 510–518) + proximity_matrix (ř. 520–534)
  │  → ml_features (ř. 544–579: 55+ feats, 5 first layers)
  │  → L2 predict_cut_time() ← machine_profile.json
  │
  ▼
L3 (pozhůstatek)                          → complexity_index klasifikace
  │
  ▼
L4 KnowledgeBaseEngine.validate_all()    → 8 validačních kroků:
  │   validate_h2() per layer
  │   validate_sequence() layer-level + nesting-offset
  │   validate_fixation() canvas-level
  │   validate_edge_merge() via vcf_geometry.detect_open_paths_in_parents()
  │   validate_micro_segments() via vcf_geometry.detect_micro_segments()
  │   validate_unclosed_loops() via vcf_geometry.detect_unclosed_loops()
  │   validate_orphans() via vcf_geometry.detect_orphan_elements()
  │   validate_unconnected_internal_decor() via vcf_geometry.detect_unconnected_internal_decor()
  │
  ▼
L3 assembly → parsed_data dict (60+ top-level klíčů)
  │
  ▼
L5 app.py → [HUD → 2D Viz → Rizika → Layer Card → Metadata → Pricing → Download]
```

### A.4 Import graf a závislosti

```
app.py
  ├─ import vcf_parser_v20.RuidaVcfEngineV20   ← pevná závislost
  ├─ import vcf_binary_reader.get_color_name     ← vizualizační
  └─ import vcf_config.{get_pricing, get_panel_formats, ...}

vcf_parser_v20.py
  ├─ import vcf_binary_reader.{...}              ← pevná závislost
  ├─ import vcf_geometry.{parse, groups, ...}    ← pevná závislost
  ├─ import vcf_time_predictor.{...}             ← pevná závislost
  ├─ import vcf_config.{...}                     ← pevná závislost
  └─ import Knowledge_base.engine (volitelný)    ← conditional import

vcf_geometry.py
  ├─ import vcf_binary_reader.GEOMETRY_SIG
  └─ import vcf_config.get_panel_format_tuples

vcf_time_predictor.py
  └─ import vcf_config.get_kinematic_params

Knowledge_base/engine.py
  └─ import vcf_geometry.{detect_* funkce}       ← pevná závislost na L1!

vcf_config.py
  └─ (bez importů mimo standardní knihovnu)
```

**Kritická zjištění o závislostech:**
1. `Knowledge_base/engine.py` pevně importuje 6 funkcí z `vcf_geometry.py`. KB modul tak závisí na geometrickém parseru (L1). Při oddělení KB do samostatného balíčku je nutné detekční funkce vyjmout z geometry a vložit do KB — nebo KB modul přebalit i s kopií geometry.
2. `machine_profile.json` je čten přes `vcf_config.get_kinematic_params()`, který ho hledá vedle `__file__` v `src/`. Při refactoringu se cesta rozbije.

---

## ČÁST B: Katalog nálezů

### B.1 KRITICKÉ (blokující smlouvu nebo bezpečnostní incident)

#### ISSUE-CRIT-01 — Chybějící public API `parse()`

**Lokalizace:** Celý repozitář — žádný `vcf_parser/__init__.py` neexistuje.

**Popis:** Technické zadání Modulu A explicitně požaduje:
```python
from vcf_parser import parse
result = parse("/cesta/k/souboru.vcf")
```
Realita: Engine je dostupný pouze jako `RuidaVcfEngineV20(file_bytes, filename)`. Chybí:
- `__init__.py` modulu `vcf_parser`
- Funkce `parse(filepath: str) -> dict` wrapper
- `pyproject.toml` definuje balíček, ale `where = ["src"]` hledá `vcf_parser_v20*` (soubor) ne `vcf_parser/` (adresář)

**Dopad:** Při předávce klient nedostane specifikovaný deliverable. Spor o nesplnění smlouvy.

**Řešení:** Vytvořit `src/vcf_parser/` adresář s `__init__.py`:
```python
from pathlib import Path
from .engine import RuidaVcfEngineV20

def parse(filepath: str) -> dict:
    path = Path(filepath)
    engine = RuidaVcfEngineV20(path.read_bytes(), filename=path.name)
    return engine.parsed_data
```
Upravit `pyproject.toml`: `where = ["src"]`, `include = ["vcf_parser*", "vcf_parser_v20*"]`.

**Odhad:** 30 min.

---

#### ISSUE-CRIT-02 — GCP credentials v app_config.json

**Lokalizace:** `app_config.json` ř. 70–76. JSON obsahuje `project_id`, `project_number`, `region`, `service_name`, `image` (docker image path).

**Popis:** Tento soubor je v `src/` — tj. v kontextu pip instalace. Při `pip install vcf-parser-b2b` bude zahrnut do distribuce.

**Dopad:** Klient obdrží přístupové údaje k GCP infrastruktuře autora. Incident úrovně "credential leak".

**Řešení:**
1. Vytvořit `deploy.json` (gitignored) obsahující celý blok `gcp`.
2. V `app_config.json` ponechat pouze: `pricing`, `panel_formats`, `analysis`, `auth`, `kb_overrides`.
3. Reader v `vcf_config.py` `load_app_config()` nebude potřebovat změnu — GCP klíč nebude v JSON, výchozí hodnoty se použijí.

**Odhad:** 15 min.

---

#### ISSUE-CRIT-03 — machine_profile.json: hypotetický základ bez jediné kalibrace

**Lokalizace:** `machine_profile.json` celý. `epistemic_confidence_index: 0.0`.

**Popis:**
- 6 konstant má `"validation_status": "empirical"` — **ale žádné měření neproběhlo**. Hodnoty jsou odhadnuté z dokumentace nebo intuice.
- 5 konstant má `"validation_status": "hypothesis"` — přiznaná neověřenost.
- `epistemic_confidence_index` má poznámku `"_note": "Tento blok je automaticky prepisovan parserem."` — ale parser ho nikde neaktualizuje! 0.0 je statická hodnota.

Dále `vcf_time_predictor.py` má další skryté slabiny:
- **Ř. 26:** Detekce organické dráhy je založena na **názvu souboru** (`is_organic = any(kw in filename.lower() for kw in ["deska", "botanic", "circle", "fluenz", "curve", "pcb"])`). Přesun souboru nebo přejmenování změní predikci. Mělo by se detekovat z geometrie (curvature_index elementů).
- **Ř. 38–50:** V-slot má pro "both side" hardcodovaný `mult = 2.0` bez rozlišení direction vs oboustranný.
- **Celý model** je postaven na 13 timestampovaných VCF souborech. Korelace predikce vs realita nebyla nikdy změřena.

**Dopad:** Claim "95–99 % accuracy" v nabídce je neobhajitelný. Skutečná chyba je neznámá. Systematická odchylka (např. +15 % na každém souboru) by znamenala, že klient systematicky podhodnocuje náklady.

**Řešení:**
1. V `machine_profile.json` nahradit `"validation_status"` z `"empirical"` → `"hypothesis"` všude, kde chybí protokol o měření.
2. Implementovat `scripts/calibrate.py` — interaktivní průvodce měřením na reálném stroji (4 kroky: max_speed, t_corner, t_lift, setup_overhead).
3. Upravit `time_predictor.py` — detekce organic z geometrie, ne z filename.
4. Přidat do `machine_profile.json` field `"_calibration_warning": "Bez kalibrace na konkrétním stroji je chyba predikce neznámá (±20–30 %)."`

**Odhad:** 3 h (calibrate.py) + 2–4 h (měření na stroji).

---

### B.2 VYSOKÉ (IP ochrana, licencování, integrita výstupu)

#### ISSUE-HIGH-01 — KB invocation pevně provázána s enginem

**Lokalizace:** `vcf_parser_v20.py` — import ř. 34–39, invoke ř. 622–681, assembly ř. 683–727.

**Popis:** Přestože import `Knowledge_base` je volitelný (`KB_AVAILABLE` flag), parsed_data dict je strukturou provázán s KB výstupem:

```python
# Ř. 686–691: KB výstup je integrován do manufacturing_intelligence
"manufacturing_intelligence": {
    "enabled": kb_enabled,           # False bez KB
    "semantic_warnings": [...],       # Prázdné bez KB
    "risk_score": 0.0,               # Nulové bez KB
    "material_thickness_confidence": thickness_confidence  # CHYBA: viz ISSUE-HIGH-02
}
```

**Problém:** Engine vrací odlišný JSON output v závislosti na přítomnosti KB. Volající kód (app.py) kontroluje `mi.get("semantic_warnings", [])`, ale nemá garantovanou strukturu — v jednom režimu vrací dicty s `.to_dict()`, ve druhém prázdné pole.

**Dopad:** Nelze engine dodat bez KB modulu — API výstup by degradoval. Klient, který si nekoupí QC Suite, dostane ořezaný výstup, což vyvolá otázky.

**Řešení:** KB výsledky přesunout do samostatného klíče `parsed_data["systeq_kb"]` a `manufacturing_intelligence` ponechat s fixní strukturou, která nezávisí na KB přítomnosti. Engine vrací konzistentní `manufacturing_intelligence` vždy (sequence check, thickness confidence z vlastní inference).

**Odhad:** 2 h (separace klíčů) + 1 h (úprava app.py).

---

#### ISSUE-HIGH-02 — `ThicknessConfidence` enum leak do fail-safe větve

**Lokalizace:** `vcf_parser_v20.py` ř. 690.

**Popis:** Assembly dict obsahuje:
```python
"material_thickness_confidence": thickness_confidence.value if kb_enabled and hasattr(thickness_confidence, "value") else (thickness_confidence if kb_enabled else "LOW")
```

Tento řádek má tři problémy:
1. Syntax error: `thickness_confidence` je použito jako enum (`.value`) i jako string ("LOW"), podle podmínky. Ve fail-safe větvi (ř. 582–602) je `thickness_confidence` **nedefinováno** — fail-safe nastavuje `material_thickness` ale ne `thickness_confidence`.
2. Podmínka `kb_enabled and hasattr(...)` znamená, že když KB není k dispozici, použije se `thickness_confidence` (enum) jako hodnota. Enums se sice serializují, ale vrací "ThicknessConfidence.LOW" místo "LOW".
3. `hasattr(thickness_confidence, "value")` je vždy True pro enum — podmínka je redundantní, ale maskuje problém, že když `thickness_confidence` není definováno, spadne na `NameError`.

**Dopad:** Při selhání parsování a `kb_enabled=False` tato assembly řádka vyhodí `NameError: name 'thickness_confidence' is not defined` — což spadne do vnějšího `except Exception` (ř. 731) a vrátí generický fail-safe dict bez diagnostiky.

**Řešení:**
1. V fail-safe větvi (ř. 582–602) přidat `thickness_confidence = ThicknessConfidence.LOW` (pokud je KB k dispozici) nebo string `"LOW"`.
2. Sjednotit reprezentaci: vždy string, nebo vždy enum. Doporučuji string — jednodušší JSON serializace.

**Odhad:** 15 min.

---

#### ISSUE-HIGH-03 — Neúplný `ThicknessConfidence.LOW` fallback v fail-safe

**Lokalizace:** `vcf_parser_v20.py` ř. 582–602 (fail-safe větev).

**Popis:** Fail-safe větev nastavuje defaultní hodnoty pro situaci, kdy parsing selže. Ale proměnná `thickness_confidence` není v tomto bloku definována — zatímco v hlavní větvi (ř. 163–183) je definována před použitím. Při přístupu na ř. 690 (assembly) s `kb_enabled=False` dostaneme `NameError`.

Toto je subtilní bug — projevuje se pouze když (a) parsing selže a (b) KB není k dispozici. V současnosti obě podmínky nejsou splněny současně (KB je ve vývojovém prostředí vždy k dispozici), ale v produkci klienta bez QC Suite by nastal.

**Dopad:** Crash při sestavování výstupu → generický fail-safe dict → klient neví proč.

**Řešení:** Viz ISSUE-HIGH-02 — přidat definici `thickness_confidence` do fail-safe větve.

**Odhad:** Součást ISSUE-HIGH-02.

---

#### ISSUE-HIGH-04 — Monolit `vcf_geometry.py`: parsovací a detekční kód ve stejném souboru

**Lokalizace:** `vcf_geometry.py` — struktura:

| Řádky | Obsah | Kategorie |
|---|---|---|
| 16–193 | `parse_geometry_v18_2()` | **Parser — dodáváno** |
| 196–238 | `group_elements()` | **Parser — dodáváno** |
| 241–247 | `detect_panel_format()` | **Parser — dodáváno** |
| 250–272 | `compute_density_grid()` | **Parser — dodáváno** |
| 275–312 | `detect_symmetry()` | **Parser — dodáváno** |
| 315–343 | `classify_layout()` | **Parser — dodáváno** |
| 346–370 | `bbox_distance()`, `analyze_sub_jobs_relation()` | **Parser — dodáváno** |
| 373–408 | `_catmull_rom_centripetal()` | Pomocná |
| 411–418 | `_linear_subdivide()` | Pomocná |
| 421–437 | `_angle_between()`, `_max_collinear_deviation()` | Pomocná |
| 442–524 | `_fit_circle_through_three_points()`, `_arc_signed_angle()`, `_generate_arc_points_segment()` | Pomocná |
| 527–629 | `_merge_consecutive_arcs()`, `reconstruct_element_vertices()` | Pomocná |
| **659–725** | `_bbox_contains()`, **`detect_open_paths_in_parents()`** | **Detekce — NENÍ dodáváno** |
| **728–750** | **`detect_micro_segments()`** | **Detekce — NENÍ dodáváno** |
| **753–781** | **`detect_unclosed_loops()`** | **Detekce — NENÍ dodáváno** |
| **784–816** | **`detect_orphan_elements()`** | **Detekce — NENÍ dodáváno** |
| **819–889** | **`filter_micro_segment_clusters()`** | **Detekce — NENÍ dodáváno** |
| **892–908** | `_min_distance_to_segments()` | Pomocná |
| **911–1081** | **`detect_unconnected_internal_decor()`** | **Detekce — NENÍ dodáváno** |
| 1084–1197 | `_is_endpoint_on_bbox_edge()`, `_build_endpoint_kdtree()`, `_find_nearest_endpoint()`, `_compute_global_canvas_bbox()`, `filter_unclosed_decor_loops()` | Pomocná + Detekce |

**Dopad:** `vcf_geometry.py` je importován enginem (L3) jako celek. Klient obdrží všech 6 detekčních funkcí, i když si nekoupil QC Suite. Ztráta upsell potenciálu 12 000 Kč.

**Řešení:**
1. Vytvořit `vcf_parser/geometry.py` — parsovací funkce + pomocné (ř. 16–629).
2. Vytvořit `systeq_kb/geometry_detection.py` — detekční funkce + jejich pomocné (ř. 659–1197).
3. Upravit `Knowledge_base/engine.py` importy — `from systeq_kb.geometry_detection import ...`
4. Upravit `vcf_parser_v20.py` importy — `from .geometry import ...` (pouze parse funkce)

**Odhad:** 2 h.

---

#### ISSUE-HIGH-05 — Duplicitní implementace nesting detekce

**Lokalizace:**
- Engine nesting: `vcf_parser_v20.py` ř. 289–376 — `_bbox_contains()` + area-sorted groups se sdíleným centroidem.
- KB nesting: `Knowledge_base/engine.py` ř. 215–242 — offset-based comparison.

**Popis:** Obě detekce hledají "vnitřní prvek řezaný po vnějším", ale jinou metodou:

| Metoda | Co detekuje | Kritérium |
|---|---|---|
| Engine (L3) | Skupiny elementů se stejným centroidem (±2mm), porovnání area sorted order vs cut order | Bbox containment + centroid proximity |
| KB (L4) | Individuální parent/child páry, porovnání hex offsetů | Parent_id + offset comparison |

Výsledky se mohou lišit — engine detekuje skupiny se sdíleným centroidem (typické pro vnořené tvary ze stejného DXF), KB detekuje libovolné parent-child páry podle offsetu v souboru.

**Dopad:**
1. Inkonzistentní varování — engine zahlásí 1 warning na celou skupinu, KB zahlásí N warningů na jednotlivé páry.
2. Duplicitní kód — `_bbox_contains()` existuje v engine (`vcf_parser_v20.py` ř. 289) i v `vcf_geometry.py` (ř. 659). Sémanticky identická funkce, dvě kopie.
3. Matoucí pro klienta — dvě různé sady "nesting errors" s různým rozsahem.

**Řešení:** Odstranit engine-level nesting detekci (ř. 289–376) a ponechat pouze KB verzi. Engine only provádí layer-level sequence check (ř. 234–268). KB detekce se aktivuje po zakoupení QC Suite.

**Odhad:** 1 h.

---

#### ISSUE-HIGH-06 — Redundantní double assignment `element_id`

**Lokalizace:** `vcf_parser_v20.py` ř. 270–275 a ř. 493–498.

**Popis:** Element ID je přiřazeno dvakrát ve stejném bloku `if not fail_safe_flag:`:
- Ř. 271–273: `el["element_id"] = f"Element_{idx + 1}"` — před nesting detekcí (protože nesting detekce na ř. 277 používá element_id)
- Ř. 494: `el["element_id"] = f"Element_{idx + 1}"` — po parents_map, před topology_tree

První assignment (ř. 271) je funkčně nutný pro nesting detekci. Druhý (ř. 494) je redundantní — element_id je již nastaveno na stejné hodnoty.

Dále `parent_id` a `children_ids` jsou inicializovány na ř. 274–275 a pak znovu přepsány/vyčištěny na ř. 496–499.

**Dopad:** Žádná chyba za běhu, ale zvyšuje kognitivní zátěž a riziko nekonzistence při úpravách.

**Řešení:** Odstranit ř. 494 (druhá assignment element_id). Ponechat pouze první assignment (ř. 271–275) pro pole, která nesting detekce potřebuje. parents_map logiku aplikovat na již existující element_id bez přepisu.

**Odhad:** 15 min.

---

### B.3 STŘEDNÍ (strukturální, datové, design)

#### ISSUE-MED-01 — Fail-safe dict maskuje chybu — chybí `_error` indikátor

**Lokalizace:** `vcf_parser_v20.py` ř. 733–752 (exception handler).

**Popis:** Když celé `parse_bytes()` selže, vrací se dict s:
```python
"fail_safe_flag": True,
"erp_time_prediction": {"predicted_time_seconds": 0, ...}
```

Tento dict je **strukturou identický** s úspěšným výstupem (stejné klíče). Volající kód (vč. `app.py`) nemá spolehlivou detekci selhání:
- `app.py` ř. 1047: `except Exception` — ale to chytá pouze chyby vizualizace, ne fail-safe režim.
- `app.py` ř. 343: `engine = RuidaVcfEngineV20(...)` — engine **nikdy neraise**; selhání je vždy vráceno jako fail-safe dict.
- Jediný indikátor selhání je `item.get("fail_safe_flag")` — ale `app.py` tuto hodnotu nikde nekontroluje explicitně. Kontroluje ji jen nepřímo přes `item["elements_parsed"] > 0` (prázdná vizualizace).

**Dopad:** Klient nahraje poškozený VCF → engine vrátí fail-safe dict → dashboard zobrazí prázdnou stránku bez vysvětlení. Klient neví, že šlo o chybu VS "žádná data".

**Řešení:**
1. Přidat do fail-safe dict: `"_error": True, "_error_message": str(e)`.
2. V `app.py` explicitně kontrolovat `item.get("_error")` a zobrazit chybovou hlášku.
3. Alternativně: engine by měl v `__init__` raisovat výjimku při fatální chybě — volající kód ji ošetří. Fail-safe ať zůstane jen pro non-fatální warningy.

**Odhad:** 30 min.

---

#### ISSUE-MED-02 — `epistemic_confidence_index` není automaticky přepisován

**Lokalizace:** `machine_profile.json` ř. 67–73.

**Popis:** `_note` tvrdí: "Tento blok je automaticky prepisovan parserem. Nemanualne upravovat." Ale grep repozitáře pro `epistemic_confidence_index` vrací pouze výskyty v `machine_profile.json` a `vcf_config.py` (kde se čte). **Nikde se nezapisuje.** Hodnota je staticky 0.0.

**Dopad:** Dokumentace neodpovídá realitě. Pokud by nějaká budoucí logika spoléhala na tuto hodnotu (např. "pokud index > 0.5, zobraz accuracy"), dostane vždy 0.0.

**Řešení:** Buď implementovat automatický výpočet (poměr empiricky ověřených konstant / všech), nebo odstranit zavádějící `_note`. Druhá varianta je jednodušší a nevyžaduje údržbu.

**Odhad:** 5 min (oprava dokumentace) nebo 1 h (implementace výpočtu).

---

#### ISSUE-MED-03 — `machine_profile.json` cesta závisí na `__file__` — rozbije se při refactoringu

**Lokalizace:** `vcf_config.py` ř. 8: `_CONFIG_DIR = Path(__file__).resolve().parent`.

**Popis:** `load_machine_profile()` hledá `machine_profile.json` v adresáři vedle `vcf_config.py`. Při refactoringu do `vcf_parser/config.py` zůstane cesta v `vcf_parser/`. Při pip instalaci to bude `site-packages/vcf_parser/machine_profile.json` — **což je config, který má být per-instalace, ne per-package.**

**Dopad:** Při pip instalaci nelze machine_profile.json změnit bez přepsání package souborů. Klient nemůže kalibrovat stroj.

**Řešení:**
1. `machine_profile.json` číst z pracovního adresáře (`Path.cwd()`) nebo z environmentální proměnné (`SYSTEQ_MACHINE_PROFILE`).
2. Nebo ho číst z `~/.systeq/machine_profile.json`.
3. Defaultní kopii ponechat v package pro fallback.

**Odhad:** 30 min.

---

#### ISSUE-MED-04 — Time predictor: organic detekce z filename, ne z geometrie

**Lokalizace:** `vcf_time_predictor.py` ř. 26.

**Popis:**
```python
is_organic = any(kw in filename.lower() for kw in ["deska", "botanic", "circle", "fluenz", "curve", "pcb"])
```

Tato heuristika určuje, zda použít `t_corner` (rovné rohy) nebo `t_corner_organic` (organické křivky). Ale:
- Keyword "circle" — kruh v DXF je běžný tvar, ne organický.
- Keyword "pcb" — irrelevatní pro PET felt panely.
- Soubor `1ks.VCF` nemá žádný z těchto keywordů, ale může obsahovat organické křivky.
- Přejmenování souboru změní predikci.

**Dopad:** Predikce času se liší podle názvu souboru — nedeterministické vzhledem k obsahu.

**Řešení:** Detekovat organické dráhy z geometrických vlastností elementů (curvature_index, sharp_corners_count) — data jsou již k dispozici v `layers_details[x]["complexity"]`.

**Odhad:** 30 min.

---

#### ISSUE-MED-05 — Streamlit app je monolit (1082 ř.) s embedovaným CSS

**Lokalizace:** `app.py`.

**Popis:**
- 260 ř. CSS v `st.markdown()` (ř. 23–258) — inline styly, žádná separace
- ~40 ř. HTML (header, footer)
- ~700 ř. aplikační logiky: parsování, vizualizace, kalkulátor, download, error handling
- Duální role (Obchodní / CNC) inline, ne pluginy
- Footer (ř. 1038–1043) obsahuje reálné telefonní číslo `+420 735 045 256` a email `sousek@systeq.cz` — **hardcodované**. Při sdílení dashboard linku (Streamlit Cloud) jsou veřejně viditelné.

**Dopad:**
1. C2 (DXF Web UI) bude vyžadovat Streamlit — nelze znovupoužít kód bez extrakce.
2. Osobní kontaktní údaje autora v produkčním kódu.

**Řešení:**
1. Extrahovat CSS do samostatného souboru nebo modulu.
2. Extrahovat 2D vizualizaci do `dashboard/viz.py`.
3. Telefon/email přesunout do konfigurace nebo environmentálních proměnných.
4. Vytvořit `dashboard/__init__.py` s tovární funkcí `create_dashboard(role, engine)`.

**Odhad:** 2–3 h.

---

#### ISSUE-MED-06 — `_build_endpoint_kdtree()` importuje scipy (volitelná závislost)

**Lokalizace:** `vcf_geometry.py` ř. 1113 — `from scipy.spatial import cKDTree`.

**Popis:** Toto je jediné místo v celém repozitáři, které vyžaduje scipy. Ale `pyproject.toml` scipy neuvádí v dependencies. Funkce `_build_endpoint_kdtree()` při chybějícím scipy vrací `None`, a `_find_nearest_endpoint()` fallbackuje na O(n) brute-force. Ale funkce `_build_endpoint_kdtree()` **není nikde volána** — je mrtvý kód.

**Dopad:** Nízký — kód běží i bez scipy. Ale mrtvý kód matoucí při analýze.

**Řešení:** Odstranit nebo označit `# TODO: unused, remove or integrate`. Při extrakci detekcí do `systeq_kb/` tuto funkci vynechat.

**Odhad:** 5 min.

---

### B.4 NÍZKÉ (kosmetické, dokumentace)

#### ISSUE-LOW-01 — Hardware verze VCF detekována dvěma metodami

**Lokalizace:**
- `vcf_binary_reader.py` ř. 64–68: kontroluje `b"RDVCUTFILEVER1.0.012"` a `b"VER1.0.012"` — pro volbu block_size (610 vs 210).
- `vcf_parser_v20.py` ř. 87: kontroluje `b"RDVCUT"`, `b"VER"` — pro detekci neznámé verze.

**Popis:** Dvě verze detekce, různé signatury, různé dopady. Není zdokumentováno, proč se liší.

**Řešení:** Sjednotit verzi detekce do jedné funkce v `vcf_binary_reader.py`, vracet enum nebo tuple (block_size, is_known_version). Engine pak jen kontroluje `is_known_version`.

**Odhad:** 30 min.

---

#### ISSUE-LOW-02 — Duplicitní definice PANEL_FORMATS

**Lokalizace:**
- `vcf_config.py` ř. 124–136: `_default_app_config()["panel_formats"]`
- `app_config.json` ř. 17–24: `panel_formats`

**Popis:** JSON překrývá default. Pokud JSON chybí, použije se default. Konzistentní fallback pattern, ale při editaci se musí měnit obě místa.

**Řešení:** Odstranit default z kódu. Nechat jen JSON. Při chybějícím JSON vrátit prázdný seznam (nebo error) místo duplicitního defaultu.

**Odhad:** 15 min.

---

#### ISSUE-LOW-03 — Memory/Speed warning: 8×8 kDTree se staví pro každý element

**Lokalizace:** `vcf_geometry.py` ř. 1095–1117.

**Popis:** `_build_endpoint_kdtree()` pokud by byl volán, staví kDTree z endpointů všech elementů ve vrstvě. Pro velké soubory s mnoha elementy je to O(n log n) operace. Ale — viz ISSUE-MED-06 — funkce je aktuálně mrtvý kód.

**Řešení:** Viz ISSUE-MED-06.

---

## ČÁST C: Refaktoringový plán

### C.1 Cílová architektura

```
vcf_parser/                         ← pip install vcf-parser-b2b
├── __init__.py                     ← from vcf_parser import parse
├── engine.py                       ← RuidaVcfEngineV20 (rozdělené metody)
├── binary_reader.py                ← (beze změny)
├── geometry.py                     ← parse + groups + panel + sym + density + layout
├── time_predictor.py               ← (opravený: organic z geometrie)
├── config.py                       ← (beze změny, opravená cesta k machine_profile)
├── app_config.json                 ← (bez GCP, bez KB overrides)
└── machine_profile.json            ← (označeno "hypothesis", s varováním)

systeq_kb/                          ← pip install systeq-kb (volitelný)
├── __init__.py
├── engine.py                       ← KnowledgeBaseEngine (beze změny)
├── models.py                       ← (beze změny)
├── rules.json                      ← (beze změny)
├── geometry_detection.py           ← detect_* funkce + pomocné extrahované z geometry
└── (plus kdtree integrace volitelně)

dashboard/                          ← SYSTEQ Dashboard (samostatný balíček)
├── __init__.py
├── styles.py                       ← extrahované CSS
├── viz.py                          ← 2D Matplotlib vizualizace
├── vcf_app.py                      ← VCF dashboard entry point
└── dxf_app.py                      ← DXF dashboard (C2, bude implementováno)

scripts/
├── calibrate.py                    ← interaktivní kalibrace machine_profile
└── migrate.py                      ← migrace dat mezi verzemi (budoucí)

tests/                              ← (beze změny, rozšířené o unit testy izolovaných metod)
```

### C.2 Fáze refaktoringu

#### Fáze 0 — Před podpisem smlouvy (nyní, ~2 h)

| Krok | Akce | Čas | Návaznost na issues |
|---|---|---|---|
| F0.1 | Odstranit GCP credentials z `app_config.json` → `deploy.json` (gitignored) | 15 min | CRIT-02 |
| F0.2 | Vytvořit `src/vcf_parser/__init__.py` s `parse()` wrapperem | 30 min | CRIT-01 |
| F0.3 | Opravit `machine_profile.json`: validation_status → hypothesis, přidat `_calibration_warning` | 10 min | CRIT-03 |
| F0.4 | Opravit ISSUE-HIGH-02/03: `thickness_confidence` do fail-safe větve + fix assembly ř. 690 | 15 min | HIGH-02, HIGH-03 |
| F0.5 | Commit + push checkpoint | 5 min | — |

#### Fáze 1 — Při podpisu smlouvy (1. týden, ~10 h)

| Krok | Akce | Čas | Návaznost |
|---|---|---|---|
| F1.1 | Extrahovat detekční funkce z `vcf_geometry.py` → `systeq_kb/geometry_detection.py` | 2 h | HIGH-04 |
| F1.2 | Vytvořit `systeq_kb/` balíček s `__init__.py`, kopií engine, models, rules | 30 min | HIGH-04 |
| F1.3 | Rozdělit `parse_bytes()` na metody: `_binary()`, `_geometry()`, `_predict()`, `_audit()`, `_assemble()` | 3 h | HIGH-01 |
| F1.4 | Separovat KB výsledky do `parsed_data["systeq_kb"]` — engine výstup nezávislý na KB | 1 h | HIGH-01 |
| F1.5 | Odstranit duplicitní engine-level nesting (ř. 289–376) — ponechat pouze layer-level check | 1 h | HIGH-05 |
| F1.6 | Opravit time predictor — organic detekce z geometrie, ne z filename | 30 min | MED-04 |
| F1.7 | Přidat `_error` indikátor do fail-safe dict + kontrolu v app.py | 30 min | MED-01 |
| F1.8 | Opravit cestu k `machine_profile.json` — čtení z `cwd()` s fallbackem | 30 min | MED-03 |

#### Fáze 2 — Po akceptaci (2.–3. týden, ~30–50 h)

| Krok | Akce | Čas |
|---|---|---|
| F2.1 | Implementovat `scripts/calibrate.py` — interaktivní průvodce | 3 h |
| F2.2 | Kalibrovat na Moodpasta stroji | 2–4 h |
| F2.3 | Refaktorovat `app.py` → `dashboard/vcf_app.py` + `dashboard/styles.py` + `dashboard/viz.py` | 2–3 h |
| F2.4 | Odstranit hardcodované telefonní číslo/email z `app.py` | 15 min |
| F2.5 | Implementovat file watcher + GSheets ETL (Modul B-A) | 14–24 h |
| F2.6 | Implementovat DXF Web UI (Modul C2) | 16–27 h |

### C.3 Anti-patterns — co NEDĚLAT

1. **Nerefaktorovat celý engine naráz.** Iterativně, po commit-ověných krocích. Každý refaktoring ověřit proti golden master testům.
2. **Nedávat KB engine do stejného balíčku jako vcf_parser.** Oddělení umožní nezávislé licencování a verzování.
3. **Neponechávat hardcodované cesty k JSONům.** Při pip instalaci se rozbijí.
4. **Neslibovat přesnost bez kalibrace.** `machine_profile.json` s `index = 0.0` je důkaz, že přesnost nebyla měřena.

---

## ČÁST D: Upsell & IP ochrana

### D.1 Hotové komponenty mimo scope technického zadání

| Komponenta | Kde | Hodnota | Zdůvodnění ceny |
|---|---|---|---|
| **QC Suite** — 6 detekčních pravidel | `vcf_geometry.py` + `Knowledge_base/` | 12 000 Kč | 22 iterací vývoje, CLASS_A-D epistemika, 6 nezávislých validačních kroků |
| **2D Vizualizace** — severity overlay | `app.py` (Matplotlib) | 8 000 Kč | 8 vizuálních vrstev (severity, nesting BBOX, merge, orphan, micro, unclosed, decor, annotations) |
| **Layer Card** — nástroje per vrstva | `app.py` + `vcf_parser_v20.py` | 4 000 Kč | Tabulka per vrstva: cutter, H1/H2, extensions, speed |
| **Risk Score** — 0-15 | `vcf_parser_v20.py` | 3 000 Kč | CRITICAL×3 + WARNING×1 |
| **Golden Master Suite** | `tests/` + `golden_master/` | 5 000 Kč | Deterministické ověření 7 baseline souborů |
| **KB Override Panel** | `app.py` sidebar | 4 000 Kč | Live toggling 6 detekčních pravidel |
| **CNC Knowledge Corpus** | `docs/` (40 souborů) | 15 000 Kč | DEFECT_CATALOG, RE case study, ontologie |
| **ML Feature vektor** | `vcf_parser_v20.py` | 0 Kč | Základ pro C1 — zdarma jako strategický asset |
| **Odoo CSV export** | `app.py` | 3 000 Kč | Ready-to-import formát pro ERP |
| **Kalkulátor marží** | `app.py` + `app_config.json` | 4 000 Kč | Strojní čas × materiál × marže |

**Celkový upsell potenciál bez dalšího vývoje: ~58 000 Kč**

### D.2 Oddělení pro licencování

| Komponenta | Mechanismus oddělení | Blokováno čím |
|---|---|---|
| QC Suite | `pip install systeq-kb` — volitelná dependence | ISSUE-HIGH-04 (monolit geometry) |
| 2D Vizualizace | Extrakt do `dashboard/viz.py` — pip install dashboard | ISSUE-MED-05 (monolit app.py) |
| Risk Score | Automaticky součástí QC Suite (KB počítá risk) | — |
| Layer Card | Součást dashboard balíčku | — |
| Golden Master | Samostatný repozitář — nepipový asset | — |

---

## Metadata

| Atribut | Hodnota |
|---|---|
| **Verze dokumentu** | 2.0 |
| **Datum** | 2026-06-25 |
| **Autor** | outpost2026 |
| **Klasifikace** | Interní — není určeno pro klienta |
| **Vstupní data** | Kompletní read-through 11 zdrojových souborů repozitáře `vcf_parser_b2b/src/` |
| **Metoda** | De novo analýza — nenavazuje na V1, nezávislá oponentura |
