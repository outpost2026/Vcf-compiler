# DEV REPORT: VCF kompilátor — persistentní bug v syntetických VCF

**Verze dokumentu:** 1.0  
**Datum:** 2026-06-29  
**Autor:** SYSTEQ výzkumný tým  
**Účel:** Vstupní detailní injekt pro cross-validaci s jinými LLM model — podklad pro výzkum příčiny chyby v pipeline DXF → syntetické VCF → load do CAM softwaru VCutWorks

---

## 1. EXECUTIVE SUMMARY

### 1.1 Problém

Pipeline pro automatickou kompilaci DXF → VCF vytváří binární VCF soubory, které **nejsou korektně načteny** do CAM softwaru VCutWorks (Ruida RDD6584G oscillating knife). Symptomy:

1. **Chybějící ACI vrstvy** — některé layer bloky nejsou rozpoznány, geometrie se nezobrazí
2. **Nenačtené soubory** — některé syntetické VCF nejsou VCutWorks načteny vůbec
3. **Koruptovaná kompilace** — binární struktura se liší od nativních VCF exportovaných přímo z VCutWorks

### 1.2 Dopad na byznys proces

Cílem je automatizace tvorby VCF souborů bez nutnosti kompilace přes GUI VCutWorks:
- Operátor CNC by pouze **kontroloval** VCF soubory (autorita lidského operátora)
- Následně odesílal do CNC plotru
- Výsledek: výrazné zrychlení workflow & otevření procesu komukoliv z firmy

**Současný stav:** Pipeline je neprůchodná — blokuje celý automatizační proces.

---

## 2. ARCHITEKTURA PIPELINE

### 2.1 Data flow

```
DXF (LightBurn) 
    │
    ▼
dxf_geometry_indexer_v2 (externí balíček)
    │  ─── index_dxf() → entities s ACI color_index
    ▼
_vcf_parser/_dxf_adapter.py
    │  ─── _build_vcf_spec() → spec dict {layers, elements}
    ▼
_vcf_parser/_writer.py
    │  ─── VcfWriter.write() → binární VCF soubor
    ▼
VCutWorks CAM GUI  ←── ZDE SELHÁVÁ
    │
    ▼
CNC plotr RDD6584G
```

### 2.2 Komponenty pipeline

| Komponenta | Soubor | Zodpovědnost |
|---|---|---|
| DXF indexer | `dxf_geometry_indexer_v2` (externí) | Parsování DXF, extrakce entit s ACI barvami |
| DXF adaptér | `vcf_parser/_dxf_adapter.py` | Mapping ACI → VCF parametry, building spec dict |
| VCF writer | `vcf_parser/_writer.py` | Serializace spec dict → binární VCF |
| VCF reader | `vcf_parser/_reader.py` | Zpětné parsování VCF (pouze pro testy/RE) |
| Reader tests | `tests/test_roundtrip.py` | Ověřuje: write → read → porovnání |
| Unit tests | `tests/test_writer_unit.py` | Testuje jednotlivá pole layer bloku |

### 2.3 ACI → VCF mapping config

`soubor: vcf_compiler_map_config.json`

Mapuje ACI (AutoCAD Color Index) čísla z DXF na VCF cutter parametry:
- cutter_type: "Vibrate cutter" | "V-slot" | "Wheel" | "Milling cutter" | "Vibrate cut"
- speed_mms: řezná rychlost
- direction: "Left" | "Right" | "Cut both side" | "N/A"
- h1_mm / h2_mm: výškové parametry nože
- extensions, is_output, number_of_feeding

Pro ACI 4 (Cyan) existuje density-based resolver: >30 bodů/m → Vibrate cutter 50mm/s, else V-slot 200mm/s.

---

## 3. BINÁRNÍ FORMÁT VCF (aktuální RE stav)

### 3.1 Hlavička

```
Offset  | Pole
--------|---------------------------------------------------------------
0       | 0x13 (VCF_PREFIX, 1 byte)
1-19    | "RDVCUTFILEVER1.0.013" (HEADER_MAGIC, 19 bytes)
20-22   | 0x20 0x0A 0x00 (VCF_POST_MAGIC, 3 bytes)
23-31   | STOCK_WIDTH (float64 = 1220.0)
31-39   | STOCK_HEIGHT (float64 = 2900.0)
39-49   | POST_STOCK_HEADER (10 bytes: pad + float64 100.0 + uint16 1)
49-473  | MACHINE_PROFILE (~424 bytes, hardcoded)
473-end | Layer blocks (256 prázdných + N realných, each 610 bytes)
```

### 3.2 Layer block (610 bytes, v1.0.013)

```
Offset  | Velikost | Pole                    | Writer | Native
--------|----------|------------------------|--------|-------
0       | 4        | output_flag (uint32)   | ✅     | ✅
4       | 8        | speed (float64)        | ✅     | ✅
12      | 20       | ???                    | ❌     | ✅ (data present)
32      | 4        | cutter_idx (int32)     | ✅     | ✅
36      | 40       | ???                    | ❌     | ✅ (data present)
76      | 4        | color (uint32, always 0)| ✅    | ✅ (ale 0xFF?)
80      | 8        | h1 (float64)           | ✅     | ✅
88      | 4        | feed_count (int32)     | ✅     | ✅
92      | 4        | ???                    | ❌     | ✅ (data present)
96      | 8        | h2 (float64)           | ✅     | ✅
104     | 2        | direction (uint16, V-slot)| ✅  | ✅
106     | 8        | vs_comp (float64, V-slot)| ✅   | ✅
114     | 8        | start_ext (float64, V-slot)| ✅ | ✅
122     | 8        | end_ext (float64, V-slot)| ✅   | ✅
130     | 472      | ??? (rezerva/stringy/data)| ❌    | ✅ (data present)
602     | 4        | next_layer_flag (uint32)| ✅ *  | ✅
606     | 4        | next_layer_color (uint32)| ✅ * | ✅
```

`*` — Writer nastavuje only pro N-1 bloků (poslední blok má nuly)

### 3.3 Geometry element

```
Offset  | Velikost | Pole
--------|----------|---------------------------------------------------
0       | 8        | GEOMETRY_SIG = 0x01 0x00 0x01 0x00 0x00 0xFF 0xFF 0xFF
8       | 4        | geom_color (uint32) = (BGR << 8) & 0xFFFFFFFF
12      | 33       | GEOMETRY_HEADER_TEMPLATE (4x float64 1.0 + padding)
45      | 4        | geom_type (uint32: 0=open, 1=closed)
49      | 4        | pt_count (uint32 = path_len - 1)
53      | 4        | subtype (uint32: 0=polyline, 3=circle)
57+     | pt*74    | segment data (x1,y1,x2,y2 as float64 pairs)
```

Každý segment:
```
Offset  | Velikost | Pole
--------|----------|------
0-12    | 12       | pad/zeros
12      | 8        | x1 (float64)
20      | 8        | y1 (float64)
28      | 8        | x2 (float64)
36      | 8        | y2 (float64)
44      | 30       | pad/zeros
```

---

## 4. DŮKAZ CHYBY — HEX DIFF ANALÝZA

### 4.1 Metodika

Srovnání: `square_1_aci.VCF` (nativní, export z VCutWorks) vs `square_from_dxf.VCF` (syntetický, náš writer)

Nástroj: `dev_scripts/hex_diff_v2.py`

### 4.2 Statistika

| Metrika | Hodnota |
|---------|---------|
| Velikost nativního | 157 868 B |
| Velikost syntetického | 157 165 B |
| Rozdíl velikostí | 703 B (syntetický je menší) |
| Počet diff regionů | 1 055 |
| Charakter diffů | Nativní obsahuje data → syntetický má nuly |

### 4.3 Klíčové patterny z hex diff reportu

**Pattern A — Machine profile area (offset 0x40-0x1F0)**
- Nativní: 0x49 0x40 = float64 50.0 (rychlost?)
- Syntetický: 0x69 0x40 = float64 100.0
- Nativní obsahuje textové řetězce: "Fs.SHX", "opravit", "Arial Black", "0000", "9999"
- Syntetický: nuly

**Pattern B — Layer block area (offsety v krocích ~610)**
- Nativní: výplň v blocích na offsetech 12-31, 36-75, 92-95, 130-601
- Syntetický: nuly (writer nezapisuje)

**Pattern C — Linked-list pointers**
- Writer nastavuje next pointer na poslední 4B empty bloku #255 a realných bloků 0..N-2
- Poslední realný blok (N-1): next pointer = 0 (nastaveno? ne!)

### 4.4 Interpretace

Writer zapisuje ~10% dat layer bloku. Zbylých ~90% jsou nuly. VCutWorks pravděpodobně validuje více polí a při detekci nul layer ignoruje nebo zahodí celý soubor.

---

## 5. HYPOTÉZY (řazeno od nejpravděpodobnější)

### H1 — Layer bloky jsou nekompletní ⭐⭐⭐⭐⭐

**Důkaz:** `encode_layer_block()` (_writer.py:244-269) zapisuje jen 7 polí z 610 bytů. Nativní bloky mají data v celém rozsahu.

**Podezřelé oblasti:**
- Offsety 12-31 (20 B): Pravděpodobně akcelerační/brzdné parametry
- Offsety 36-75 (40 B): Charakteristiky nástroje (cutter-specific)
- Offsety 92-95 (4 B): Neznámé, ale v nativních vyplněno
- Offsety 130-601 (472 B): Rozsáhlá oblast — možná zpracované path cache nebo "render preview" data

**Výzkumná otázka:** Jaká data VCutWorks v těchto oblastech očekává? Jsou všechna povinná, nebo jen některá?

### H2 — Linked-list terminátor poslední vrstvy ⭐⭐⭐⭐

**Důkaz:** Writer nastavuje `next_layer_flag = 1` a `next_layer_color = color_of_next_layer` pro bloky 0..N-2. Pro poslední blok (N-1) jsou obě pole 0.

**Otázka:** Očekává VCutWorks v posledním bloku terminační hodnotu? Např.:
- next_layer_flag = 0 (současný stav — možná OK)
- next_layer_flag = 0xFF nebo self-reference offset
- next_layer_color = 0x00000000 nebo 0xFFFFFFFF

### H3 — Machine profile mismatch ⭐⭐⭐

**Důkaz:** Nativní VCF containuje specifická čísla a textové řetězce (název fontu, "Fs.SHX", "opravit") v MACHINE_PROFILE oblasti.

**Otázka:** Jsou hardcoded MACHINE_PROFILE bytes (_writer.py:42-69) kompatibilní s RDD6584G? Liší se od profilu, který VCutWorks očekává pro konkrétní stroj?

### H4 — Chybějící geometry count/preamble ⭐⭐

**Důkaz:** Mezi body a trailerem chybí potenciálně počet elementů nebo index.

**Otázka:** Má VCutWorks očekávat v těle souboru count geometrických elementů nebo jiný index?

### H5 — Chybný geom_color formát ⭐⭐

**Důkaz:** `expected_geom_color = (color_bgr << 8) & 0xffffffff` — BGR je posunut o 8 bitů doleva, takže low byte je vždy 0. Nativní VCF by mohl používat jiný formát.

**Otázka:** Je formát geom_color skutečně (BGR << 8) nebo je to přímo BGR, RGB, nebo jiný formát?

---

## 6. CROSS-VALIDAČNÍ SOUBORY — LLM INPUT MANIFEST

Pro účely výzkumu jsou identifikovány následující soubory, které LLM model **nutně potřebuje** pro analýzu:

### 6.1 Zdrojový kód pipeline (povinné)

| # | Cesta | Účel | Proč to LLM potřebuje |
|---|-------|------|----------------------|
| 1 | `vcf_parser/_writer.py` | Hlavní writer — generuje binární VCF | Analyzovat co a jak se zapisuje do bloků |
| 2 | `vcf_parser/_reader.py` | Reader/parser — zpětné čtení VCF | Pochopit RE formátu, validační logiku |
| 3 | `vcf_parser/_dxf_adapter.py` | DXF→VCF bridge | Jak vzniká spec dict z DXF |
| 4 | `vcf_parser/__init__.py` | Public API | Vstupní body pipeline |
| 5 | `vcf_parser/_geometry.py` | Geometrické utility | Výpočty bbox, verze |
| 6 | `vcf_parser/_config.py` | Konfigurace stroje | Machine profile loader |
| 7 | `vcf_compiler_map_config.json` | ACI→VCF mapping | Jak se mapují barvy na parametry |

### 6.2 Testy (povinné)

| # | Cesta | Účel |
|---|-------|------|
| 8 | `tests/test_writer_unit.py` | Unit testy writeru — 28 testů |
| 9 | `tests/test_roundtrip.py` | Integrační testy — write→read→compare |
| 10 | `tests/conftest.py` | Test fixtures |

### 6.3 Nativní VCF (zlato — referenční)

| # | Cesta | Charakteristika |
|---|-------|-----------------|
| 11 | `demo_data/square_1_aci.VCF` | 1 vrstva, ACI 7 (černá), 157 868 B — **PRIMÁRNÍ REFERENCE** |
| 12 | `demo_data/circle_500_single_aci.VCF` | 1 vrstva, single ACI |
| 13 | `demo_data/circle_diameter_600_native.VCF` | 1 vrstva, nativní export |
| 14 | `demo_data/fishbone_2790x1200_native.VCF` | Multi-vrstva, produkční VCF |
| 15 | `demo_data/manchester_3_subjobs_native.VCF` | 3 subjobs, multi-layer |
| 16 | `demo_data/square_1_aci.dxf` | Zdrojový DXF pro square_1_aci |
| 17 | `demo_data/square_1_aci.lbrn2` | LightBurn projekt |

### 6.4 Syntetické VCF (broken — testovací)

| # | Cesta | Poznámka |
|---|-------|----------|
| 18 | `demo_data/synthethic_vcf/square_from_dxf.VCF` | Syntetický ekvivalent square_1_aci |
| 19 | `demo_data/synthethic_vcf/circle_diameter_600_from_dxf.VCF` | Syntetický kruh z DXF |
| 20 | `demo_data/synthethic_vcf/fishbone_2790x1200_from_dxf.VCF` | Syntetický multi-layer |
| 21 | `demo_data/synthethic_vcf/manchester_3_subjobs_from_dxf.VCF` | Syntetický multi-subjob |
| 22 | `demo_data/synthethic_vcf/fresh_synthetic.VCF` | Čerstvý syntetický |
| 23 | `demo_data/synthethic_vcf/fresh_synthetic_no_dxf.VCF` | Syntetický bez DXF source |

### 6.5 Dev skripty (nepovinné, doporučené)

| # | Cesta | Účel |
|---|-------|------|
| 24 | `dev_scripts/hex_diff_v2.py` | Binary hex diff → MD report |
| 25 | `dev_scripts/vcf_dxf_re_correlator_v1.1.py` | DXF↔VCF korelace, transformace |
| 26 | `dev_scripts/VcfWrappingAnalyzer.py` | Layer/geometrie analyzátor |

### 6.6 Hex diff výstup

| # | Cesta |
|---|-------|
| 27 | `hex_diff_report.md` | 1055 diff regionů |

### 6.7 Dokumentace (nepovinné, kontextové)

| # | Cesta |
|---|-------|
| 28 | `docs/VCF_Reverse_Engineering_Inference_Workflow_2026.md` |
| 29 | `docs/SYSTEQ_VCF_STACK_ANATOMY_V2.md` |
| 30 | `docs/narrative_report_v1.md` |
| 31 | `docs/RE_CASE_STUDY_VCUTWORKS_LIGHTBURN_v2.md` |

### 6.8 Související balíček — vcf_color_service

| # | Cesta | Účel |
|---|-------|------|
| 32 | `vcf_color_service/vcf_color_service/core.py` | ColorMapper centrální třída |
| 33 | `vcf_color_service/vcf_color_service/config.json` | Ground-truth ACI data |

---

## 7. FORMULACE VÝZKUMNÝCH OTÁZEK PRO LLM

### 7.1 Primární otázky

**Q1 — Layer block fields:** Analyzuj hex dump nativního `square_1_aci.VCF` a identifikuj, která pole v layer bloku (610 B) jsou vyplněna oproti writerovým nulám. Kategorizuj:
- Povinná (bez nich VCutWorks layer zahodí)
- Volitelná (default values OK)
- Neznámá (další RE needed)

**Q2 — Linked-list terminátor:** Jaká hodnota je v nativním VCF na posledních 8 bytech posledního layer bloku (offsety 602-609)? Je to 0, nebo nějaká terminační hodnota?

**Q3 — Machine profile:** Porovnej hardcoded MACHINE_PROFILE z `_writer.py:42-69` s MACHINE_PROFILE oblastí v nativním `square_1_aci.VCF`. Jsou tam kritické rozdíly?

**Q4 — Geom_color formát:** Porovnej geometrické barvy v nativním VCF (první GEOMETRY_SIG výskyt) s barvou v layer bloku. Je formát skutečně (BGR << 8)?

### 7.2 Sekundární otázky

**Q5 — Body struktura:** Je mezi posledním layer blokem a prvním GEOMETRY_SIG v nativním VCF něco navíc (preamble, count)?

**Q6 — Trailer struktura:** Jaká data jsou v traileru nativního VCF? Liší se od TRAILER_PREFIX v `_writer.py:72-85`?

**Q7 — Empty blocks:** Mají empty bloky (0-254) v nativním VCF kromě indexu na offsetu 10 ještě nějaká data?

**Q8 — Subjob struktura:** V `manchester_3_subjobs_native.VCF` je více subjobů. Jak je tato informace reprezentována v binárce?

### 7.3 Validační otázky

**Q9 — Roundtrip konzistence:** Projde syntetický VCF naším readerem se stejnými parametry jako nativní? (odpověď: měl by — testy píšou že jo, ale ověř)

**Q10 — Mezivrstevní konzistence:** Mají všechny vrstvy v multi-layer nativním VCF stejnou strukturu nevyplněných oblastí?

---

## 8. POSTUP LADĚNÍ (doporučený workflow pro LLM)

### Fáze 1: Reverzní inženýrství nativního VCF

```
Krok 1.1: Analyzuj hlavičku (offset 0-473)
  - Porovnej magic bytes, stock rozměry, machine profile
  - Identifikuj textové řetězce (fonty, cesty)

Krok 1.2: Dekóduj layer bloky
  - Najdi pozici prvního GEOMETRY_SIG
  - Spočítej pozice layer bloků (backward search)
  - Extrahuj full 610B každého bloku
  - Identifikuj každé pole: význam, datový typ, hodnota

Krok 1.3: Analyzuj geometrii
  - Extrahuj GEOMETRY_SIG, barvy, souřadnice
  - Ověř formát geom_color (otázka Q4)

Krok 1.4: Analyzuj trailer
  - Identifikuj TRAILER_PREFIX
  - Najdi DXF source path string
```

### Fáze 2: Identifikace gapů v writeru

```
Krok 2.1: Mapuj writer.encode_layer_block() proti nativnímu bloku
  - Která pole chybí?
  - Která pole mají jiné hodnoty?
  - Která pole jsou kritická?

Krok 2.2: Ověř linked-list řetězec
  - Je last-layer terminátor správný?
  - Jsou next_color hodnoty konzistentní s geometry colors?

Krok 2.3: Ověř MACHINE_PROFILE
  - Porovnej byte-to-byte
  - Oprav pokud se liší
```

### Fáze 3: Implementace fixů

```
Krok 3.1: Rozšiř encode_layer_block()
  - Přidej chybějící pole s nativními default hodnotami
  - Zachovej V-slot specific fields

Krok 3.2: Oprav linked-list terminátor

Krok 3.3: Oprav MACHINE_PROFILE

Krok 3.4: Run testy → write → read roundtrip musí stále procházet
```

### Fáze 4: Verifikace

```
Krok 4.1: Vygeneruj nový syntetický VCF
Krok 4.2: Hex diff proti nativnímu — diff regionů by mělo dramaticky ubýt
Krok 4.3: Manuální test v VCutWorks GUI
Krok 4.4: Iteruj pokud stále nefunguje
```

---

## 9. TECHNICKÉ SPECIFIKACE

### 9.1 Vývojové prostředí

- **OS:** Windows 11 (x64)
- **Python:** >= 3.11
- **Test framework:** pytest >= 8.0
- **Žádné externí runtime dependencie** — pouze `struct`, `math`, `json`, `logging` ze stdlib
- **DXF dependencie:** `dxf_geometry_indexer_v2` (samostatný balíček, lazy import)

### 9.2 Cílová platforma

- **CAM software:** VCutWorks (Ruida)
- **CNC stroj:** RDD6584G oscillating knife
- **VCF formát:** v1.0.013 (610B layer blocks)

### 9.3 Současný stav testů

```
test_writer_unit.py → 28/28 PASS
test_roundtrip.py → 3 PASS + 2 SKIP (chybí demo soubory)
```

---

## 10. RIZIKA A OMEZENÍ

1. **Black box RE:** VCutWorks je proprietární software — vše je reverzní inženýrství
2. **Version lock:** Formát se může lišit mezi verzemi VCutWorks/VCF
3. **Machine-specific:** MACHINE_PROFILE může být specifický pro konkrétní stroj
4. **Bez záruky:** I po vyplnění všech polí může VCutWorks vyžadovat specifické kontrolní součty nebo signatury, které neznáme

---

## 11. PŘÍLOHY

### A. Klíčové konstanty z `_writer.py`

```python
HEADER_MAGIC      = b"RDVCUTFILEVER1.0.013"
VCF_PREFIX        = b"\x13"
VCF_POST_MAGIC    = b"\x20\x0a\x00"
EMPTY_BLOCK_COUNT = 256
LAYER_BLOCK_SIZE  = 610
STOCK_WIDTH       = 1220.0
STOCK_HEIGHT      = 2900.0
GEOMETRY_SIG      = b'\x01\x00\x01\x00\x00\xff\xff\xff'

CUTTER_MAP = {0: "Vibrate cutter", 1: "Wheel", 2: "Milling cutter", 3: "V-slot", 4: "Vibrate cut"}
DIR_MAP    = {0: "Left", 1: "Right", 2: "Cut both side"}
```

### B. Klíčové konstanty z `_reader.py`

```python
# Validace layer bloku:
# - speed musí být float v rozsahu 1.0-2000.0, celočíselný, dělitelný 5
# - color_val se čte z pos - 4 (next_color pointer předchozího bloku)
# - expected_geom_color = (color_val << 8) & 0xffffffff
# - kontrola: expected_geom_color ∈ geom_colors (z geometrie)
```

### C. Vztah layer color ↔ geom color

```
Layer block (next_color pointer): 
    color_val = (R << 16) | (G << 8) | B   (BGR v uint32)

Geometry element:
    geom_color = (color_val << 8) & 0xFFFFFFFF

Reader check:
    if (color_val << 8) & 0xFFFFFFFF == geom_color → layer patří k této geometrii
```

---

## 12. ZÁVĚR

Hlavní příčina chyby je s vysokou pravděpodobností **nekompletní layer block encoding** — writer zapisuje minimum polí, VCutWorks vyžaduje víc. Sekundární příčiny mohou zahrnovat chybný machine profile, linked-list terminátor, nebo chybějící body/trailer struktury.

Doporučený postup: **Phase 1 → Fáze reverzního inženýrství** — důkladně analyzovat nativní VCF layer bloky, identifikovat všechna pole, poté iterativně doplňovat do writeru a testovat v VCutWorks.

---

*Konec dokumentu*
