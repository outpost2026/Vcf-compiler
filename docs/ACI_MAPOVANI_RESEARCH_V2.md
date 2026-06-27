# Výzkumná zpráva: ACI mapování barev a parametrů vrstev DXF → VCF

**Verze:** 2.0  
**Datum:** 27. 6. 2026  
**Kontext:** DXF→VCF kompilátor (Vcf-compiler repo) — debugging "black canvas" v VCutWorks GUI  

---

## 1. Problémová situace

Při konverzi DXF souboru (`square_1_aci.dxf`) do VCF pomocí `compile_dxf()` a následném otevření v VCutWorks se zobrazí **prázdné plátno** — žádné vrstvy (layer cards), žádná vizualizace geometrie.

Přitom:
- **Nativní VCF** (vygenerovaný přímo VCutWorks ze stejného DXF) se zobrazuje správně
- **B2B Python reader** (Příloha: vcf_binary_reader.py, vcf_parser_v20.py) přečte oba soubory korektně
- **Roundtrip testy** (Vcf-compiler reader → writer → reader) procházejí

---

## 2. Diferenční analýza JSON výstupů (v20 parser)

### 2.1 Metodika

Oba VCF soubory zpracovány parserem `RuidaVcfEngineV20.parse_bytes()` → JSON export.
Porovnány strukturovaným deep-diffem.

### 2.2 Zásadní rozdíly

| Pole | Native (ground truth) | Synthetic (náš) | Δ | Dopad |
|------|----------------------|-----------------|---|-------|
| **color_hex** | `0x00000000` (černá) | `0x00ffffff` (bílá) | OPAK | **KRITICKÝ** — viz §3 |
| **color_rgb** | `[0, 0, 0]` | `[255, 255, 255]` | Inverze | |
| **speed_mms** | `80` | `200` | 2.5× | Méně kritický — ovlivňuje čas |
| **start_height_h1_mm** | `24.0` | `2.0` | 12× | **KRITICKÝ** — viz §3.3 |
| **end_height_h2_mm** | `-0.5` | `-0.3` | 0.2 mm | Minor |
| **number_of_feeding** | `1` | `1` | ✓ | OK |
| **cutter_type** | Vibrate cutter | Vibrate cutter | ✓ | OK |
| **is_output_yes** | true | true | ✓ | OK |
| **file_size_bytes** | 157868 | 157165 | -703 B | Odlišná velikost hlavičky |
| **extracted_metadata** | 12 položek (cesta, fonty) | 1 položka (pouze magic) | Metadata | Viz §4 |
| **operation_type** | through-cut | N/A | Klasifikace | Pouze parserová anotace |

### 2.3 Shodné prvky (v pořádku)

| Prvek | Status | Důkaz |
|-------|--------|-------|
| Geometrie (vertices) | ✓ Identická | 4 vrcholy, 1000×1000 mm čtverec |
| Počet elementů | ✓ 1 | 1 polygon, 4 segmenty |
| Počet vrstev | ✓ 1 | 1× Vibrate cutter |
| Layer mapping | ✓ Element → Layer 0 | layer_index = 0 |
| Bbox | ✓ [110, 950, 1110, 1950] | Shodný |
| Typ geometrie | ✓ Polygon (type_id=1) | Shodný |

---

## 3. ACI Color Mapping — ROOT CAUSE ANALYSIS

### 3.1 LightBurn ACI divergence (známý problém z RE Case Study)

Dle kazuistiky `RE_CASE_STUDY_VCUTWORKS_LIGHTBURN_v2.md` (kap. 5.5):

> **LightBurn DXF ≠ AutoCAD DXF.** LightBurn při exportu DXF nepoužívá standardní AutoCAD ACI→RGB mapování. Např. ACI 4 (standardně cyan) je v LightBurn mapován jinak.

Naše `ACI_TO_RGB` mapa v `_dxf_adapter.py` používá standardní AutoCAD mapování:
```python
ACI_TO_RGB = { ... 7: (255, 255, 255) ... }
```

ALE nativní VCF (vygenerovaný VCutWorks) ukládá ACI 7 jako **černou (0, 0, 0)**.

### 3.2 Hypotéza: VCutWorks inverzní paleta

VCutWorks pravděpodobně používá **inverzní barevnou paletu**:
- ACI 7 (AutoCAD: bílá) → VCutWorks: černá (index 0)
- Světlé ACI barvy → tmavé VCutWorks barvy (kvůli kontrastu na světlém plátně)

**Důsledek:** Naše mapování ACI 7 → bílá (255,255,255) ukládá do VCF barvu, kterou VCutWorks neočekává. Pokud VCutWorks:
1. **Používá barvu jako ID vrstvy** — bílá není v jeho interní paletě → vrstva ignorována
2. **Renderuje barvu na plátno** — bílá na bílém = neviditelné → "black canvas" efekt

### 3.3 Parametrická odchylka H1 (start_height)

Nativní VCF: `h1 = 24.0 mm`  
Náš VCF: `h1 = 2.0 mm`

Tato hodnota reprezentuje **bezpečnostní výšku** (safety height) — výška, do které se nástroj zvedne při přesunu mezi elementy.

**Hypotéza:** VCutWorks může mít **minimální bezpečnostní výšku** (např. 10 mm), pod kterou považuje VCF za nevalidní. H1 = 2.0 mm je extrémně nízká hodnota, která by způsobila kolizi nástroje s materiálem při přesunu.

Analýza: v nativním VCF je H1 = 24.0 mm → to je ~2× materiál (12 mm PET plsť) + rezerva. To dává smysl jako bezpečnostní výška.

### 3.4 Rychlost (speed)

Nativní VCF: speed = 80 mm/s  
Náš config: speed = 200 mm/s

Tato odchylka je způsobena ACI mapping konfigurací v `vcf_compiler_map_config.json`, kde ACI 7 má speed=200. Tato hodnota byla kalibrována z jiných vzorků, ale neodpovídá tomuto konkrétnímu nativnímu VCF.

---

## 4. Binární struktura — Hlavička (Header)

### 4.1 Zjištěný rozdíl

| Vlastnost | Native | Synthetic |
|-----------|--------|-----------|
| Velikost hlavičky | **472 bajtů** | **54 bajtů** |
| Blok 0 začíná na | offset 472 | offset 54 |
| Prvních 54 B | Identické s naším | Identické |

### 4.2 Co obsahuje extra hlavička (54-472)

Nativní hlavička obsahuje:
- **Metadata DXF cesty**: `square_1_aci.dxf`, `opravit`, `demo_data`, atd.
- **Názvy fontů**: `FS.SHX`, `Arial Black`, `Fs.SHX`
- **Neznámá binární data** (pravděpodobně default konfigurace stroje)

### 4.3 Hypotéza: VCutWorks validuje hlavičku

Pokud VCutWorks očekává v hlavičce specifická metadata (např. odkaz na zdrojový DXF soubor) a nenajde je, může:
- Považovat soubor za nekompletní → zobrazit prázdné plátno
- Selhat při parsování bloků (protože neví, kde bloky začínají)

---

## 5. Epistemická klasifikace zjištění

| Nález | Confidence | Třída | Status | Zdůvodnění |
|-------|-----------|-------|--------|------------|
| **Barva vrstvy je špatně** | 0.90 | CLASS_B (empirické) | ACCEPTED | Nativní VCF dokazuje černou, my dáváme bílou |
| **H1 = 2.0 mm je podezřelá** | 0.75 | CLASS_C (heuristika) | HYPOTHESIS | Nativní má 24.0 mm — bezpečnostní výška |
| **Hlavička je příliš krátká** | 0.70 | CLASS_D (hypotéza) | HYPOTHESIS | VCutWorks může validovat velikost hlavičky |
| **B2B reader najde layer** | 0.99 | CLASS_A (fyzikální) | ACCEPTED | Backward scan funguje — layer je na k=1 |
| **Geometrie je korektní** | 0.99 | CLASS_A (fyzikální) | ACCEPTED | Stejné vertexy, stejná délka |

---

## 6. Doporučení pro opravu

### 6.1 Priorita 1: Barva vrstvy

VCutWorks používá **vlastní barevnou paletu** nezávislou na AutoCAD ACI. Je třeba:
1. Zrevidovat ACI→RGB mapping pro VCutWorks (nikoliv AutoCAD)
2. Upravit `ACI_TO_RGB` v `_dxf_adapter.py` podle nativních VCF vzorků
3. Případně použít **inverzní mapování** (světlá ACI → tmavá VCF barva)

**Nejjednodušší test:** Nastavit ACI 7 → RGB (0, 0, 0) místo (255, 255, 255) a ověřit v VCutWorks.

### 6.2 Priorita 2: H1 (safety height)

Změnit H1 z 2.0 mm na hodnotu blízkou nativní:
- Z nativního VCF: H1 = 24.0 mm
- Navrhovaná hodnota: min. 10-15 mm (bezpečnostní rezerva)
- Ideálně: materiálová tloušťka + 10 mm

### 6.3 Priorita 3: Hlavička (rozšíření)

Prozkoumat možnost:
- Přidat metadata o zdrojovém DXF do hlavičky
- Zkopírovat hlavičku z template/nativního VCF a nahradit pouze bloky + geometrii
- Identifikovat klíčová pole v extra hlavičce (mezi offset 54-472)

### 6.4 Priorita 4: Rychlost (ACI kalibrace)

Aktualizovat `vcf_compiler_map_config.json`:
- ACI 7 speed: 200 → 80 (dle nativního VCF)
- Provést cross-validaci na více nativních VCF vzorcích

---

## 7. Závěr

Pipeline DXF → VCF je **binárně korektní** (b2b reader přečte oba soubory správně → stejné JSON výstupy pro vrstvy i geometrii). Problém je v **hodnotách parametrů**, které se liší od nativního VCF:

1. **Barva** (černá vs bílá) — nejpravděpodobnější příčina "black canvas"
2. **H1** (24.0 vs 2.0 mm) — potenciální bezpečnostní validace
3. **Hlavička** (472 vs 54 B) — možné formální odmítnutí souboru
4. **Speed** (80 vs 200) — méně kritické pro vizualizaci

**Doporučený postup:** Opravit barvu a H1, regenerovat VCF, otestovat v VCutWorks. Pokud stále nefunguje, řešit hlavičku.
