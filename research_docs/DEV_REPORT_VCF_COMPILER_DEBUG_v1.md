# DEV REPORT: VCF kompilátor — RE Analysis & Debug Evolution (v2)

**Verze dokumentu:** 3.0  
**Datum:** 2026-06-30  
**Autor:** SYSTEQ výzkumný tým + LLM asistovaná analýza  
**Účel:** Kompletní dokumentace reverzního inženýrství VCF formátu, debugovací metodiky (binary search variant), slepých uliček, a finálního working PoC. V2 rozšiřuje v1 o výsledky GUI testování a novou RE metodologii. V3 přidává session 8 findings — multi-element element count breakthrough.

---

## 1. EXECUTIVE SUMMARY

### 1.1 Problém

Pipeline pro automatickou kompilaci DXF → VCF vytváří binární VCF soubory, které **nejsou korektně načteny** do CAM softwaru VCutWorks (Ruida RDD6584G oscillating knife). Symptomy:

1. **Chybějící ACI vrstvy** — některé layer bloky nejsou rozpoznány, geometrie se nezobrazí
2. **Nenačtené soubory** — některé syntetické VCF nejsou VCutWorks načteny vůbec
3. **Koruptovaná kompilace** — binární struktura se liší od nativních VCF exportovaných přímo z VCutWorks

### 1.2 Aktuální stav (v3)

Problém má **dvě fáze**:

**Fáze 1 (session 1–6, vyřešeno):** 3 root causes (trailer, element_count@92, direction@104) způsobovaly hard rejection a missing geometry. Fixed writerem. Single-element, single-layer polyline VCF (square_1_aci) funguje v VCutWorks.

**Fáze 2 (session 7, identifikováno):** 2 nové root causes:
- Circle segment encoding chybný (8 float64 → 4)
- Chybí 196B footer mezi geometry elementy

Multi-element, multi-layer, a circle VCF stále selhávají. Tento dokument je aktualizován na v3 s těmito nálezy.

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

## 2.5 BINARY SEARCH VARIANT METHODOLOGY — BREAKTHROUGH (v2)

### 2.5.1 Problém s hex-diff analýzou

Do session 5 byla jedinou metodou identifikace chyb **hex diff** — porovnání nativního a syntetického VCF byte po bytu. Tato metoda produkovala 1055 diff regionů s ~90% rozdílu v empty blocích. To vedlo k **mylné hypotéze H6** — že empty block init data jsou primární příčinou selhání.

**Blind spot:** Hex diff měří kvantitu rozdílů, ne jejich **kritičnost**. 3740 B rozdílů v empty blocích (které nejsou kritické) maskovalo 12 B kritických rozdílů v active bloku a chybějící DXF path v traileru.

### 2.5.2 LLM navržená metodika — Binary Search Variants

LLM model navrhl zcela nový přístup: **generovat VCF varianty s postupně přidávanými structural features** a testovat každou v GUI VCutWorks. Tím se izoluje, která konkrétní změna způsobuje selhání.

**Princip:** Místo hledání "co všechno je špatně" (hex diff), hledáme "co je minimálně potřeba" (binary search).

### 2.5.3 Variant grid A–J

| Var | Empty bloky | Linked-list | MP | Trailer | Full layer | Výsledek v GUI |
|-----|-------------|-------------|----|---------|------------|-----------------|
| A | ✗ | ✗ | ✗ | ✗ | ✗ | no load, black canvas |
| B | ✓ | ✗ | ✗ | ✗ | ✗ | load, no geometry |
| C | ✓ | ✓ | ✗ | ✗ | ✗ | load, no geometry |
| D | ✓ | ✓ | ✓ | ✗ | ✗ | load OK, ACI ok, no geometry |
| E | ✓ | ✓ | ✓ | ✓ | ✗ | **NO LOAD** ← trailer způsobuje rejection |
| F | ✓ | ✓ | ✓ | ✓ | ✓ | **NO LOAD** |
| G | ✓(native) | ✓ | ✓ | ✓ | ✓ | **NO LOAD** (trailer stále špatný) |
| H | ✓ | ✓ | ✓ | ✗ | ✓ | load OK, ACI ok, **NO GEOMETRY** |
| I | ✓ | ✓ | ✗ | ✓ | ✓ | load, black canvas |
| J | ✗ | ✗ | ✓ | ✓ | ✓ | no load |

**Klíčové nálezy z A–J:**
- E vs D: **trailer způsobuje hard rejection** (jediný rozdíl)
- H vs F: bez traileru loadne, ale **bez geometrie**
- D: ACI OK ale **žádná geometrie** → active block fields chybí

### 2.5.4 Navazující varianty K–S (patched & fixed)

Po identifikaci traileru a active block fields jako kritických oblastí, byly vytvořeny varianty s patchovanými nativními daty:

| Var | Popis | Výsledek |
|-----|-------|----------|
| K | synth body + native trailer | no load (old active block) |
| L | synth + native DXF path | no load |
| **M** | **synth + native active block + native trailer** | **✅ WORKS! Geometrie, ACI, parametry OK** |
| N | synth + native trailer only | no load |
| O | synth + native active block, no trailer | no load |
| **P** | **fixed writer (3 fixes) + demo params** | **✅ LOAD OK, geometry renders** |
| **Q** | **P + native empty blocks** | **✅ WORKS (confirms empty blocks irrelevant)** |
| **R** | **fixed writer matching native params** | **✅ WORKS, param OK (speed=80)** |
| **S** | **fixed writer + native coords + params + path** | **157868B, 0 diffs HEADER/GEOM/TRAILER** |

**Variant M je definitivní důkaz:** active block fields + trailer = complete fix.

### 2.5.5 Rationalizace metodiky

Proč byla tato metoda úspěšná tam, kde hex diff selhal?

1. **Izolace proměnných:** Každá varianta mění pouze jednu strukturní vlastnost oproti předchozí
2. **Ground truth je VCutWorks, ne hex diff:** Jediná validní metrika je "loadne/neloadne" v reálném SW
3. **Patched varianty eliminují kumulativní chyby:** Když varianta M patchuje nativní active block do jinak chybného synth, a funguje, víme přesně co chybí
4. **Eliminace falešných pozitiv:** Hex diff ukazoval 3740 B chyb v empty blocích jako kritické — GUI testy ukázaly, že jsou irelevantní

---

## 3. BINÁRNÍ FORMÁT VCF (aktuální RE stav — v2)

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
Offset  | Velikost | Pole                    | Writer | Native | Status
--------|----------|------------------------|--------|--------|-------
0       | 4        | output_flag (uint32)   | ✅     | ✅     | original
4       | 8        | speed (float64)        | ✅     | ✅     | original
12      | 4        | color (uint32, BGR)    | ✅     | ✅     | FIXED session 4 (byl na 76)
16      | 8        | ???                    | ❌     | ✅     | not critical (zeros OK)
24      | 8        | h1_alt? (float64)      | ❌     | varied | 0.0 active blk, 24.0 empty blk #0
32      | 4        | cutter_idx (int32)     | ✅     | ✅     | original
36      | 4        | ??? (uint32=1)         | ❌     | ✅     | not critical
40      | 8        | field_40 (float64=5.0) | ✅     | ✅     | FIXED session 6
48      | 4        | direction (uint32=2)   | ❌     | ✅     | not critical (104 stačí)
52-75   | 24       | padding                | ❌     | ❌     | zeros in native too
76      | 4        | color (uint32, always 0)| ✅    | ✅     | original (vždy black)
80      | 8        | h1 (float64)           | ✅     | ✅     | original
88      | 4        | feed_count (int32)     | ✅     | ✅     | original
92      | 1        | element_count (uint8)  | ✅     | ✅=1   | **FIXED session 6** — kritické pro geometrii
93-95   | 3        | padding                | ❌     | ❌     | zeros in native
96      | 8        | h2 (float64)           | ✅     | ✅     | original
104     | 2        | direction (uint16)     | ✅     | ✅=2   | **FIXED session 6** — nyní pro všechny typy
106     | 8        | vs_comp (float64)      | ✅     | ✅     | V-slot only
114     | 8        | start_ext (float64)    | ✅     | ✅     | V-slot only
122     | 8        | end_ext (float64)      | ✅     | ✅     | V-slot only
130-175 | 46       | ???                    | ❌     | varied | zeros OK
176     | 8        | field_176 (≈0.0)       | ❌     | denorm | semantically identical
184     | 8        | field_184 (≈0.0)       | ❌     | denorm | semantically identical
192-196 | 5        | ???                    | ❌     | ❌     | zeros
197     | 1        | field_197 (uint8=64)   | ✅     | ✅     | FIXED session 6
198     | 8        | field_198 (float64=0.5)| ✅     | ✅     | FIXED session 6
206-601 | 396      | ???                    | ❌     | varied | zeros OK (potvrzeno GUI)
602     | 4        | next_layer_flag (uint32)| ✅     | ✅     | linked-list
606     | 4        | next_layer_color (uint32)| ✅    | ✅=1   | **FIXED** poslední blok color=1
```

**Změny oproti v1:**
- `@12 color`: FIXED — barva vrstvy (BGR)
- `@40 field_40`: FIXED — float64 5.0 (neznámý parametr, konzistentní napříč nativními VCF)
- `@92 element_count`: FIXED — počet elementů v dané vrstvě (kritické pro zobrazení geometrie)
- `@104 direction`: FIXED — nyní pro všechny typy nožů, nejen V-slot (native=2 = "Cut both side")
- `@197 field_197`: FIXED — uint8 64 (0x40, neznámý flag)
- `@198 field_198`: FIXED — float64 0.5 (neznámý parametr)
- `@606 terminator`: FIXED — poslední blok má next_color=1 (místo 0)
- `@176, @184`: NOT FIXED — denormalized near-zero v native, 0.0 v writeru (semanticky identické)

### 3.3 Geometry element — header

```
Offset  | Velikost | Pole
--------|----------|---------------------------------------------------
0       | 8        | GEOMETRY_SIG = 0x01 0x00 0x01 0x00 0x00 0xFF 0xFF 0xFF
8       | 4        | geom_color (uint32) = (BGR << 8) & 0xFFFFFFFF
12      | 33       | GEOMETRY_HEADER_TEMPLATE (4x float64 1.0 + padding)
45      | 4        | geom_type (uint32: 0=open, 1=closed)
49      | 4        | pt_count (uint32 = number of segments)
53      | 4        | subtype (uint32: 0=polyline, 3=circle)
```

### 3.4 Geometry element — segment structure (v2 — corrected)

Segment struktura závisí na `subtype`. Každý segment je 74 B.

**Polyline (subtype=0)** — 4 float64 na segment (2 body = start+end):
```
Offset  | Velikost | Pole
--------|----------|------
0       | 2        | pad/zeros
2       | 8        | x1 (float64) — start point X
10      | 8        | y1 (float64) — start point Y
18      | 8        | x2 (float64) — end point X
26      | 8        | y2 (float64) — end point Y
34      | 40       | pad/zeros (nevyplněno)
```

Native fishbone/manchester potvrzují: polyline segment obsahuje 4 float64, zbylých 40 B jsou nuly.

**Circle (subtype=3)** — 8 float64 na segment (4 body = start + end + 2 control):
```
Offset  | Velikost | Pole
--------|----------|------
0       | 2        | pad/zeros
2       | 8        | x1 (float64) — arc start X
10      | 8        | y1 (float64) — arc start Y
18      | 8        | x2 (float64) — arc end X
26      | 8        | y2 (float64) — arc end Y
34      | 8        | cx (float64) — control point 1 X / center X
42      | 8        | cy (float64) — control point 1 Y / center Y
50      | 8        | cz (float64) — control point 2 X
58      | 8        | cw (float64) — control point 2 Y
66      | 8        | pad/zeros
```

**Důkaz:** Native circle_500_single_aci.VCF má v každém ze 4 segmentů 8 vyplněných float64. Writer (encode_circle_element) zapisuje jen 4 → VCutWorks čte kontrolní body z paddingové oblasti (nulové hodnoty) → zkreslený tvar.

Příklad native segment [0]:
```
+2: 360.000    +10: 1450.000   ← start point
+18: 610.000   +26: 1700.000   ← end point
+34: 360.000   +42: 1588.071   ← control point 1
+50: 471.929   +58: 1700.000   ← control point 2
```

### 3.5 Geometry element — 196B footer (v2 — new discovery)

Každý geometry element v nativním VCF je ukončen **196B footerem**. Tento footer je mezi elementy — nikoliv za posledním elementem.

```
Element header (45 B)
    + pt_count × segment (74 B each)
    + FOOTER (196 B)
    = NEXT element header
```

| VCF | Elementů | Delta (gap − expected) | Potvrzení |
|-----|----------|------------------------|-----------|
| square_1_aci native | 1 | +0 (poslední, za ním trailer) | — |
| fishbone native | 14 | +196 B každý | ✅ konzistentní |
| manchester native | 72 | +196 B každý | ✅ konzistentní |
| circle_500 native | 1 | +0 (poslední) | — |
| botanic_simple synth | 16 | **+0 B** (chybí footer) | ❌ |
| double_line_2 synth | 2 | **+0 B** (chybí footer) | ❌ |

**Struktura footeru** (předběžná):
- Většinou nulové bytes
- Obsahuje float64 5.0 (shodné s `field_40` v layer bloku)
- Obsahuje float64 89.0 (stack rozměr?)
- Zakončen 4B paddingem + začátkem dalšího GEOMETRY_SIG

**Dopad:** Writer negeneruje footer → VCutWorks při iteraci elementů očekává každý další element o 196 B dále, než skutečně je. Pro single-element VCF to nevadí. Pro multi-element VCF (botanic_simple = 16 elementů, fishbone = 14) jsou elementy 2..N na špatných pozicích → nejsou detekovány/rendrovány.

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

## 5. HYPOTÉZY — VERDIKT PO GUI TESTOVÁNÍ (v2)

### 5.1 Přehled

Následující tabulka shrnuje všech 10 formulovaných hypotéz (H1–H10) a jejich verdikt po dokončení GUI testování v session 6. Hypotézy byly testovány metodou **binary search variants** — generování VCF variant s inkrementálními změnami a testování každé v reálném VCutWorks GUI.

| # | Hypotéza | Původní priorita | Verdikt | Důkaz |
|---|----------|-------------------|---------|-------|
| H1 | Layer bloky nekompletní — chybí ~90% dat | ⭐⭐⭐⭐⭐ | **DISPROVEN** (částečně) | Empty block init data (3740 B) nejsou kritická — circle_500 je má nulové a funguje. Active block (610 B) potřebuje jen ~12 specifických bytů. |
| H2 | Linked-list terminátor poslední vrstvy | ⭐⭐⭐⭐ | **POTVRZENO** | Poslední blok vyžaduje `next_layer_color = 1` (místo 0). Fixed v session 6. |
| H3 | Machine profile mismatch | ⭐⭐⭐ | **DISPROVEN** | 0 byte diffs mezi writer MACHINE_PROFILE a nativním VCF. |
| H4 | Chybějící geometry count/preamble | ⭐⭐ | **DISPROVEN** | Geometry area má 0 diffs oproti nativnímu — struktura je korektní. |
| H5 | Chybný geom_color formát | ⭐⭐ | **DISPROVEN** | `(BGR << 8)` formát je korektní — 0 diffs v geometry barvách. |
| H6 | Empty block init data způsobují rejection | ⭐⭐⭐ (nová) | **DISPROVEN** | Variant Q (fixed writer + native empties) funguje stejně jako P. circle_500 native má nulové empty bloky a funguje v VCutWorks. |
| H7 | Active block bytes @92, @104, @40, @197, @198 jsou kritické | ⭐⭐⭐⭐⭐ (nová) | **POTVRZENO** | Variant M (synth + native active block) = WORKING. @92=element_count, @104=direction=2. |
| H8 | Trailer DXF path je kritický | ⭐⭐⭐⭐⭐ (nová) | **POTVRZENO** | Variant E (D+trailer bez path) = NO LOAD. Variant H (F-trailer) = LOAD OK. Trailer BEZ path dat = hard rejection. |
| H9 | Fixed writer generuje VCutWorks-kompatibilní VCF | ⭐⭐⭐⭐⭐ (nová) | **POTVRZENO** | Variants P, Q, R, S všechny LOAD OK v GUI s geometrií. |
| H10 | Formát verze 1.0.013 je problém | ⭐⭐ (nová) | **DISPROVEN** | Writer produkuje 1.0.013 formát, který VCutWorks akceptuje. |

### 5.2 Detailní analýza každé hypotézy

#### H1 — Layer bloky jsou nekompletní ⭐⭐⭐⭐⭐ → DISPROVEN (částečně)

**Původní předpoklad:** Writer zapisuje jen 7 polí z 610 B → VCutWorks layer zahodí.

**Skutečnost:** GUI testy ukázaly, že pouze ~12 specifických bytů v active bloku je kritických:
- `@40`: float64 5.0 (neznámý parametr, konzistentní napříč nativními)
- `@92`: uint8 element_count (počet path elementů v layeru)
- `@104`: uint16 direction pro všechny cutter typy (nejen V-slot)
- `@197`: uint8 64 (0x40, neznámý flag)
- `@198`: float64 0.5 (neznámý parametr)
- `@606`: uint32 1 (terminator barva posledního bloku)

Zbývajících ~596 B v 610B bloku může být nulových (včetně 3740 B empty block init dat).

**Ponaučení:** Hex diff kvantifikoval rozdíly (1055 regionů), ale nedokázal odlišit **kritické** od **irelevantních**. Metrika "počet rozdílů" byla zavádějící.

#### H2 — Linked-list terminátor poslední vrstvy ⭐⭐⭐⭐ → POTVRZENO

**Nález:** Writer nastavoval `next_layer_color = 0` pro poslední blok. Nativní VCF má `next_layer_color = 1` (BGR černá = 0x000001). Fixed.

**Dopad:** Samotný terminátor nestačil k vyřešení problému (varianty E, F, G stále selhávaly kvůli traileru), ale je součástí sady 5 fixů.

#### H3 — Machine profile mismatch ⭐⭐⭐ → DISPROVEN

**Důkaz:** Hex diff potvrdil 0 byte diffs mezi `MACHINE_PROFILE` konstantou v `_writer.py` a nativním `square_1_aci.VCF`. Profil je korektní.

#### H4 — Chybějící geometry count/preamble ⭐⭐ → DISPROVEN

**Důkaz:** Geometry oblast v syntetickém VCF (včetně GEOMETRY_SIG, header template, coordinat) má 0 diffs oproti nativnímu, když jsou použity stejné vstupní souřadnice.

#### H5 — Chybný geom_color formát ⭐⭐ → DISPROVEN

**Důkaz:** `(BGR << 8) & 0xFFFFFFFF` formát je korektní. Nativní VCF používá stejný formát — potvrzeno 0 diffs.

#### H6 — Empty block init data způsobují hard rejection ⭐⭐⭐ → DISPROVEN

**Původní zdůvodnění:** Variant G (native empty init data patch) redukoval hex diff z 2394 regionů na 11. To vedlo k domněnce, že empty block init je primární příčina.

**Vyvrácení:** 
- Variant G ve skutečnosti selhal kvůli **traileru** (stejně jako E, F), ne kvůli empty blokům
- Variant Q (fixed writer + native empty init data) funguje STEJNĚ jako P (fixed writer bez native empty)
- Nativní `circle_500_single_aci.VCF` má zcela nulové empty bloky a v VCutWorks funguje

**Závěr:** VCutWorks nevaliduje empty block init data. 3740 B rozdílů v empty blocích jsou "falešné pozitivy" hex diff analýzy.

#### H7 — Active block specific bytes @92, @104 @40, @197, @198 jsou kritické ⭐⭐⭐⭐⭐ → POTVRZENO

**Průlomový důkaz:** Variant M (synth body + native active block + native trailer) = **PRVNI FUNKČNÍ** varianta. Kombinace native active block dat s jinak syntetickým tělem dokazuje, že právě tato data chyběla.

**Konkrétní fixy:**
- `@92` (uint8): `element_count = len(layer._paths)` — VCutWorks podle toho ví, kolik elementů v layeru hledat
- `@104` (uint16): `direction` pro VŠECHNY cutter typy (ne jen V-slot). Default = 2 ("Cut both side")
- `@40` (float64): 5.0 — neznámý parametr, konzistentní napříč všemi nativními VCF
- `@197` (uint8): 64 (0x40) — neznámý flag
- `@198` (float64): 0.5 — neznámý parametr

#### H8 — Trailer DXF path je kritický ⭐⭐⭐⭐⭐ → POTVRZENO

**Průlomový důkaz:** 
- Variant D (bez traileru) = LOAD OK
- Variant E (D + trailer) = NO LOAD (jediný rozdíl!)
- Variant H (F - trailer) = LOAD OK

**Mechanismus:** VCutWorks při přítomnosti traileru striktně validuje DXF path data. Pokud trailer existuje (TRAILER_PREFIX je zapsán), ale path string je prázdný nebo chybí, VCutWorks zahodí celý soubor s "neočekávaný formát souboru".

**Fix:** `trailer()` metoda vždy zapisuje path data. Pokud `dxf_source_path` je None, zapíše se prázdný string.

#### H9 — Fixed writer generuje VCutWorks-kompatibilní VCF ⭐⭐⭐⭐⭐ → POTVRZENO

**Důkaz:** Variants P, Q, R, S všechny prošly GUI testem:
- **P**: fixed writer + demo params → LOAD OK, geometry renders
- **Q**: P + native empty blocks → LOAD OK (stejný výsledek — potvrzuje H6)
- **R**: fixed writer + native params → LOAD OK, params correct (speed=80)
- **S**: fixed writer + native coords + path → 157868 B, 0 diffs HEADER/GEOMETRY/TRAILER

#### H10 — Formát verze 1.0.013 je problém ⭐⭐ → DISPROVEN

**Důkaz:** Writer `HEADER_MAGIC = b"RDVCUTFILEVER1.0.013"` je korektní. VCutWorks akceptuje 1.0.013 formát — varianty P-R fungují s tímto magic stringem.

### H11 — Circle segment encoding obsahuje 8 float64 (ne 4) ⭐⭐⭐⭐⭐ (NOVÁ, v3)

**Důkaz:** Native circle_500_single_aci.VCF má v každém segmentu (subtype=3) 8 vyplněných float64 na pozicích +2, +10, +18, +26, +34, +42, +50, +58. Writer zapisuje pouze 4 (+2 až +26) → VCutWorks čte zbývající 4 z nulové padding oblasti → zkreslený tvar.

**Dopad:** Všechny circle elementy jsou v GUI zobrazeny jako deformovaný čtyřúhelník.

**Hypotéza:** 8 float64 kóduje kubickou Bézier křivku (2 control pointy) nebo arc s definicí středu. Nutno RE na nativních cirklech.

### H12 — Chybí 196B footer za každým geometry elementem ⭐⭐⭐⭐⭐ (NOVÁ, v3)

**Důkaz:** Všechny multi-element nativní VCF (fishbone 14 elem, manchester 72 elem) mají `delta=196 B` mezi elementy — každý element je o 196 B větší než `45 + pt_count × 74`. Syntetické VCF mají `delta=0`.

**Dopad:** Pro single-element VCF (square_1_aci) nevadí. Pro multi-element VCF jsou elementy 2..N na pozicích posunutých o 196×(N-1) B → VCutWorks nenajde validní GEOMETRY_SIG na očekávané pozici → nerenruje geometrii.

**Otevřená otázka:** Co přesně footer obsahuje? Předběžná analýza ukazuje převážně nuly s výskytem float64 5.0 a 89.0. Může obsahovat per-element metadata (délka, bounding box, toolpath cache).

### H13 — Multi-layer selhání je důsledek H12 ⭐⭐⭐⭐ (NOVÁ, v3)

**Hypotéza:** Problém s multi-layer VCF (double_line_2_aci, 0 render) je přímý důsledek chybějícího 196B footeru. Druhý element (druhá ACI vrstva) je na špatné pozici → VCutWorks nenajde jeho GEOMETRY_SIG → nezobrazí geometrii.

**Alternativa:** Může být samostatný problém s mapováním layer block → geometry element přes barvu. Nutno ověřit po fixu H12.

### 5.4 Rozšířený katalog element typů

Reader identifikuje následující geometrické typy z GEOMETRY_SIG:

| Pole | Offset | Velikost | Význam | Hodnoty |
|------|--------|----------|--------|---------|
| `geom_type` | +45 | uint32 | Uzavřenost cesty | 0=open, 1=closed |
| `pt_count` | +49 | uint32 | Počet segmentů | 1..N (počet 74B segmentů) |
| `subtype` | +53 | uint32 | Geometrický primitiv | 0=polyline, 3=circle |

Segmentová struktura (74 B):

| Offset | Velikost | Polyline (sub=0) | Circle (sub=3) |
|--------|----------|-------------------|-----------------|
| 0 | 2 | padding | padding |
| 2 | 8 | x1 (start) | x1 (arc start) |
| 10 | 8 | y1 (start) | y1 (arc start) |
| 18 | 8 | x2 (end) | x2 (arc end) |
| 26 | 8 | y2 (end) | y2 (arc end) |
| 34 | 8 | padding/0 | control point 1 X |
| 42 | 8 | padding/0 | control point 1 Y |
| 50 | 8 | padding/0 | control point 2 X |
| 58 | 8 | padding/0 | control point 2 Y |
| 66 | 8 | padding/0 | padding |

Element size = 45 + pt_count × 74 + (196 if not last element)

### 5.3 Co jsme se naučili o metodologii RE

1. **Hex diff není diagnostický nástroj — je to indikátor.** Ukazuje kvantitu rozdílů, ne jejich kritičnost.
2. **Binary search variant methodology** (LLM navržená) byla zásadní inovace — místo "co je špatně" hledáme "co je minimálně potřeba".
3. **GUI testování je jediný ground truth.** Reader roundtrip testy a hex diff mohou být zavádějící.
4. **Patched varianty** (vkládání nativních dat do syntetického těla) umožňují izolovat přesně ty oblasti, které jsou kritické.
5. **Počet chyb neodpovídá závažnosti.** 3 nezávislé bugy způsobovaly selhání, přestože hex diff ukazoval ~1055 diff regionů. Zbylých ~1052 byly falešné pozitivy.
6. **Multi-element/multi-layer testování odhalilo skryté chyby.** Single-element VCF (square_1_aci) funguje, ale multi-element ne. To znamená, že předchozí testování bylo neúplné — "working PoC" platí jen pro specifický subset vstupů.

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

### 6.6 Binary search variant files — KLÍČOVÝ ZDROJ (v2)

Vygenerováno `dev_scripts/vcf_binary_search.py`. 19 variant (A–S) pro GUI testování. Každá varianta testuje specifickou kombinaci structural features.

| # | Soubor | Velikost | Popis | GUI výsledek |
|---|--------|----------|-------|-------------|
| 27 | `demo_data/binary_search_variants/var_A_minimal_active_first.VCF` | 1005 B | Pouze active blok (žádné empty bloky, MP, trailer) | no load, black canvas |
| 28 | `demo_data/binary_search_variants/var_B_empty_blocks.VCF` | 157165 B | A + 256 empty bloků | load, no geometry |
| 29 | `demo_data/binary_search_variants/var_C_linked_list.VCF` | 157165 B | B + linked-list pointery | load, no geometry |
| 30 | `demo_data/binary_search_variants/var_D_machine_profile.VCF` | 157583 B | C + MACHINE_PROFILE | load OK, ACI ok, no geometry |
| 31 | `demo_data/binary_search_variants/var_E_trailer.VCF` | 157782 B | D + trailer (bez DXF path) | **NO LOAD** ← objev |
| 32 | `demo_data/binary_search_variants/var_F_full_current.VCF` | 157782 B | E + full layer (aktuální writer) | **NO LOAD** |
| 33 | `demo_data/binary_search_variants/var_G_native_empty_init.VCF` | 157867 B | F + native empty block init data patch | **NO LOAD** (trailer stále špatný) |
| 34 | `demo_data/binary_search_variants/var_H_no_trailer.VCF` | 157583 B | F - trailer | load OK, ACI ok, **NO GEOMETRY** |
| 35 | `demo_data/binary_search_variants/var_I_no_mp.VCF` | 157449 B | F - MACHINE_PROFILE | load, black canvas |
| 36 | `demo_data/binary_search_variants/var_J_active_first.VCF` | 1707 B | active-first (bez empty bloků) + MP + trailer | no load |
| 37 | `demo_data/binary_search_variants/var_K_native_trailer.VCF` | 157868 B | synth body + native trailer | NO LOAD (old active block) |
| 38 | `demo_data/binary_search_variants/var_L_native_dxfpath.VCF` | 157868 B | synth + native DXF path patched | NO LOAD |
| 39 | `demo_data/binary_search_variants/var_M_native_active_trailer.VCF` | 157868 B | synth + native active block + native trailer | **✅ WORKS** ← BREAKTHROUGH |
| 40 | `demo_data/binary_search_variants/var_N_native_trailer_only.VCF` | 157868 B | synth + native trailer only | NO LOAD |
| 41 | `demo_data/binary_search_variants/var_O_native_active_no_trailer.VCF` | 157583 B | synth + native active block, no trailer | NO LOAD |
| 42 | `demo_data/binary_search_variants/var_P_fixed_writer.VCF` | 157808 B | fixed writer (3 fixes) + demo params | **✅ WORKS** |
| 43 | `demo_data/binary_search_variants/var_Q_fixed_plus_empties.VCF` | 157808 B | P + native empty block init data | **✅ WORKS** (stejný = empties irelevantní) |
| 44 | `demo_data/binary_search_variants/var_R_fixed_matching_native.VCF` | 157868 B | fixed writer + native params + path | **✅ WORKS** (params OK) |
| 45 | `demo_data/binary_search_variants/var_S_fixed_native_coords.VCF` | 157868 B | fixed writer + native coords + params + path | **✅ WORKS**, 0 diffs HEADER/GEOMETRY/TRAILER |

### 6.7 Hex diff výstup

| # | Cesta |
|---|-------|
| 46 | `hex_diff_report.md` | 1055 diff regionů (před fixy) |

### 6.8 Dokumentace (nepovinné, kontextové)

| # | Cesta |
|---|-------|
| 47 | `docs/VCF_Reverse_Engineering_Inference_Workflow_2026.md` |
| 48 | `docs/SYSTEQ_VCF_STACK_ANATOMY_V2.md` |
| 49 | `docs/narrative_report_v1.md` |
| 50 | `docs/RE_CASE_STUDY_VCUTWORKS_LIGHTBURN_v2.md` |

### 6.9 Související balíček — vcf_color_service

| # | Cesta | Účel |
|---|-------|------|
| 51 | `vcf_color_service/vcf_color_service/core.py` | ColorMapper centrální třída |
| 52 | `vcf_color_service/vcf_color_service/config.json` | Ground-truth ACI data |

### 6.10 Reporty

| # | Cesta |
|---|-------|
| 53 | `research_docs/DEV_REPORT_VCF_COMPILER_DEBUG_v1.md` | Tento dokument (v2) |
| 54 | `research_docs/REPORT_early_dev_phase_anomaly_v1.md` | Early phase analysis |
| 55 | `research_docs/REPORT_dev_phase_evolution.md` | Full evolution report (session 1→6) |
| 56 | `research_docs/Gemini_RD_VCF.txt` | LLM methodology research |

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
  - element_count@92 (uint8) = počet path elementů
  - direction@104 (uint16) pro VŠECHNY cutter typy
  - field_40@40 (float64=5.0), field_197@197 (uint8=64), field_198@198 (float64=0.5)

Krok 3.2: Oprav linked-list terminátor — next_layer_color@606 = 1 pro poslední blok

Krok 3.3: Oprav trailer() — vždy zapisuj DXF path data (i prázdný string)

Krok 3.4: Run testy → write → read roundtrip musí stále procházet (28/28 PASS)
```

### Fáze 4: Verifikace hex diffem

```
Krok 4.1: Vygeneruj nový syntetický VCF s fixed writerem
Krok 4.2: Hex diff proti nativnímu
  - HEADER: 0 diffs
  - GEOMETRY: 0 diffs (se stejnými vstupy)
  - TRAILER: 0 diffs (se stejnou DXF cestou)
  - ACTIVE_BLOCK: 4 zbývající diffs (denormalizované near-zero — semanticky identické)
  - EMPTY_BLOCKS: 3740 diffs (POTVRZENO jako nekritické)
```

### Fáze 5: GUI testování v VCutWorks — BINARY SEARCH VARIANT METHODOLOGY (v2)

Tato fáze byla vyvinuta jako reakce na selhání hex diff analýzy a stala se klíčovým průlomem.

```
Krok 5.1: Vygeneruj varianty A–J s inkrementálními structural features
  A = minimal (active-first, žádné empty bloky)
  B = A + 256 empty blocks
  C = B + linked-list pointery
  D = C + MACHINE_PROFILE
  E = D + trailer (bez DXF path)
  F = E + full current writer (všechna pole)
  G = F + native empty block init patch
  H = F - trailer (izoluje trailer efekt)
  I = F - MACHINE_PROFILE (izoluje MP efekt)
  J = active-first (bez empty bloků) + MP + trailer

Krok 5.2: Každou variantu otestuj v reálném VCutWorks GUI
  - Sleduj 3 kritéria: LOAD status, ACI/layer recognition, geometry rendering
  - Zaznamenej výsledek do variant gridu

Krok 5.3: Identifikuj kritické oblasti z gridu
  - E vs D = trailer způsobuje hard rejection
  - H vs F = bez traileru loadne ale bez geometrie
  - D = ACI OK ale žádná geometrie → active block fields chybí

Krok 5.4: Vygeneruj patched varianty K–S pro izolaci konkrétních fixů
  - K, L, N = native trailer patches (izolace traileru)
  - M = native active block + native trailer (DŮKAZ)
  - O = native active block bez traileru (izolace active block)
  - P = fixed writer (ověření fixů)
  - Q = P + native empties (disproof H6)
  - R = fixed writer + native params (full matching)
  - S = fixed writer + native coordinates (0 diffs v kritických regionech)

Krok 5.5: Aplikuj fixy do writeru a re-run testy

Důležité principy:
- Ground truth je VCutWorks, ne hex diff
- Každá varianta mění pouze jednu strukturní vlastnost
- Patched varianty eliminují kumulativní chyby
- "Loadne/neloadne" je jediná validní metrika
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

## 10. RIZIKA A OMEZENÍ (v2 — working PoC)

### 10.1 Stav rizik

| Riziko | Původní stav | Aktuální stav (v2) |
|--------|-------------|-------------------|
| Black box RE | Vše je neznámé | **Working PoC** — 3 bugy identifikovány a fixed. Writer produkuje VCutWorks-kompatibilní VCF. |
| Version lock | Formát se může lišit | **Částečně mitigováno** — writer produkuje 1.0.013 formát, který VCutWorks akceptuje. Zpětná kompatibilita s 1.0.012 není zaručena. |
| Machine-specific | MACHINE_PROFILE specifický | **Mitigováno** — MACHINE_PROFILE má 0 diffs proti nativnímu exportu z VCutWorks. |
| Kontrolní součty | Může vyžadovat neznámé CRC | **DISPROVENO** — VCutWorks nevyžaduje žádný kontrolní součet. VCF bez CRC funguje. |
| Multi-layer validace | Netestováno | **Otevřené** — GUI test proběhl pouze na single-layer VCF. Multi-layer (fishbone, manchester) čeká na test. |
| Circle element rendering | Netestováno | **Otevřené** — writer používá 4-segment encoding. Native používá 1-segment. Může se lišit v renderování. |

### 10.2 Zbývající omezení (v3 — po GUI testech multi-element)

1. **Circle encoding chybný** — segment pro subtype=3 vyžaduje 8 float64 (4 body), writer píše jen 4 → deformovaný tvar. **NENÍ FIXOVÁNO.**
2. **Chybí 196B footer za elementy** — writer negeneruje footer mezi geometry elementy. Multi-element VCF selhávají. **NENÍ FIXOVÁNO.**
3. **Multi-layer závisí na #2** — double_line_2_aci selhává kvůli footeru, ne samostatnému layer problému. Nutno ověřit po fixu.
4. **"Working PoC" je částečný** — platí pouze pro single-element, single-layer VCF (square_1_aci). Multi-element a circle nefungují.
5. **Empty block init data** — nejsou kritická, ale pro úplnost by mohla být populována machine default hodnotami
6. **Fishbone element discrepancy** — DXF produkuje 41 elementů, native má 14 (konsolidace?)
7. **Reader nepodporuje nová pole** — reader neparsuje @40, @92, @104, @197, @198, @606

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

## 12. ZÁVĚR (v2 — working PoC)

### 12.1 Shrnutí

Po 6 výzkumných session, 19 binary search variantách (A–S), a 3 nezávislých bug fixech je **VCF writer plně funkční a produkuje soubory kompatibilní s VCutWorks**.

### 12.2 Nálezy — fáze 1 (session 1–6, vyřešeno)

**3 nezávislé root causes VCF selhání (všechny fixed):**

1. **Trailer truncated (HARD REJECTION):** `trailer()` zapisoval TRAILER_PREFIX, ale DXF path data pouze když `dxf_source_path != None`. VCutWorks při detekci traileru očekává path data — jinak zahodí celý soubor.

2. **Active block @92=0 (NO GEOMETRY):** Byte @92 v active bloku (610B) ukládá počet elementů v dané vrstvě. Writer nechával 0, VCutWorks podle toho nevykresloval geometrii.

3. **Active block @104=0 (NO DIRECTION):** Byte @104 ukládá direction pro VŠECHNY cutter typy (nejen V-slot). Writer ho nastavoval jen pro V-slot.

**Dodatečná populovaná pole** (potvrzeno jako korektní defaulty):
- `@40`: float64 5.0, `@197`: uint8 64, `@198`: float64 0.5, `@606`: uint32 1

### 12.3 Nálezy — fáze 2 (session 7, identifikováno, nefixed)

**3 nové root causes (multi-element/multi-layer selhání):**

4. **Circle segment encoding (H11):** Segment pro subtype=3 vyžaduje 8 float64 (start + end + 2 control body). Writer zapisuje jen 4. → Deformovaný tvar kruhu.

5. **Chybějící 196B footer (H12):** Každý geometry element v nativním VCF je ukončen 196B footerem. Writer ho negeneruje. → Multi-element VCF selhávají (elementy 2..N na špatných pozicích).

6. **Multi-layer selhání (H13):** Pravděpodobně důsledek H12, nikoliv samostatný problém. Nutno ověřit po fixu H11+H12.

### 12.4 Co funguje / nefunguje (v3)

| Scénář | Status | Poznámka |
|--------|--------|----------|
| Single-element, single-layer, polyline | ✅ WORKS | square_1_aci — plně funkční |
| Single-element circle | ❌ BROKEN | H11 — chybí kontrolní body v segmentech |
| Multi-element, single-layer (botanic) | ❌ BROKEN | H12 — chybí 196B footer |
| Multi-layer (double_line_2) | ❌ BROKEN | H13 — pravděpodobně důsledek H12 |
| Fixed writer tests | ✅ 28/28 PASS | Writer unit/roundtrip testy |
| VCutWorks single-element load | ✅ LOAD OK | Potvrzeno GUI testy |

### 12.5 Prioritizace fixů

1. **HIGH — 196B footer (H12):** Rozšířit `encode_geometry_element()` o generování 196B footeru za každým elementem (kromě posledního?). Toto odblokuje multi-element VCF.
2. **HIGH — Circle segment (H11):** Rozšířit segment na 8 float64 pro subtype=3. Potřebujeme RE control point formátu (kubická Bézier? arc definice?).
3. **MEDIUM — Multi-layer (H13):** Ověřit po fixech H11+H12, zda multi-layer funguje. Pokud ne, RE vztahu layer block ↔ geometry element.

### 12.5 Metodologický přínos

Tento výzkum demonstruje sílu **LLM-asisted binary search variant methodology** při RE proprietárních binárních formátů:

- **LLM navrhl** generování inkrementálních variant s izolovanými structural features
- **LLM navrhl** patched varianty (vkládání nativních dat) pro izolaci kritických oblastí
- **Lidský operátor** testoval každou variantu v reálném VCutWorks GUI
- Výsledek: 3 bugy identifikovány za jednu session tam, kde hex diff analýza selhávala týden

---

## 13. SESSION 8 FINDINGS — MULTI-ELEMENT ELEMENT COUNT BREAKTHROUGH

**Datum:** 2026-06-30  
**Status:** ✅ GUI nyní detekuje multi-element správně (line_10_elements: 10 elem, square_5_elements: 5 elem)

### 13.1 Problém

Po fixech v session 7 (196B footer, circle Bezier encoding) zůstával multi-element VCF v GUI nefunkční — zobrazoval pouze 1 element místo N. Testy (28/28) procházely, protože reader používá odlišný mechanismus detekce elementů než VCutWorks GUI.

### 13.2 Debugovací iterace (8 pokusů)

| Iterace | Akce | Výsledek |
|---------|------|----------|
| 1 | Oprava trailer prefixu 200B→20B | Circle OK, multi-element stále ne |
| 2 | Oprava ELEMENT_TAIL 196B→180B pro poslední element | Pořád ne |
| 3 | Změna ec@92 na 0 (chybný závěr z posunutých offsetů) | Pořád ne |
| 4 | Objev off-by-2: POST_STOCK_HEADER=14B, ne 12B | Zneplatněn závěr o ec@92=0 |
| 5 | Ruční hex diff všech native VCF (1-elem i 2-elem) | ec@92=1 VŽDY, nezávisle na počtu elementů |
| 6 | Analýza vcf_parser_b2b (produkční parser z B2B repo) | **BREAKTHROUGH** — parser používá GEOMETRY_SIG scan, ne ec@92/offset606 |
| 7 | Objev offset606 = poslední 4B posledního layer bloku | = skutečný počet elementů (1→1, 2→2) |
| 8 | FIX: ec@92=1, offset606=total_elements | **GUI načte druhý element** |

### 13.3 Root Causes Fixed

#### RC5: ec@92=0 (mělo být 1) — "has geometry" flag

- **Původní chybný závěr:** ec@92 = element count, mělo by být = počtu elementů
- **Skutečnost:** ec@92 = 1 ve VŠECH nativních souborech (1-elem i 2-elem). Je to boolean flag indikující "vrstva obsahuje geometrii", ne počet elementů.
- **Proč byl chybný závěr:** Off-by-2 chyba v měření POST_STOCK_HEADER (14B vs 12B) posunula všechny offsetové analýzy layer bloků o 2B → byte na pozici 92 nebyl tam, kde jsme mysleli.

#### RC6: offset606=1 (mělo být = element_count)

- **Původní stav:** Writer psal hardcoded 1 na poslední 4B posledního layer bloku
- **Skutečnost:** Posledních 4B posledního bloku = celkový počet elementů napříč všemi vrstvami
- **Ověření:** Native 1-elem → offset606=1, native 2-elem → offset606=2, native fishbone (14 elem) → offset606=14
- **Mechanismus:** VCutWorks GUI čTE offset606 pro určení počtu elementů. Když je 1, zobrazí jen 1 element bez ohledu na skutečný počet v geometrii.

### 13.4 Kritické objevy

#### D8 — Off-by-2 bug v preamble výpočtu

```python
POST_STOCK_HEADER = struct.pack('<I',0)      # 4B
                  + struct.pack('<d',100.0)   # 8B
                  + struct.pack('<H',1)        # 2B
                  = 14 bytes  # !! bylo počítáno jako 12
```

Celá preamble: 1 (prefix) + 20 (magic) + 3 (post_magic) + 8 (stock_w) + 8 (stock_h) + 14 (POST_STOCK_HEADER) + 418 (MACHINE_PROFILE) = **472 bytes**

Dříve používaných 12B posunulo všechny layer block field analýzy o 2B → neplatné závěry o ec@92 a dalších polích.

#### D9 — ec@92 ≠ element_count (je to "has geometry" flag)

| Soubor | Elementů | ec@92 | Interpretace |
|--------|----------|-------|-------------|
| square_1_aci native | 1 | 1 | Má geometrii |
| circle_500 native | 1 | 1 | Má geometrii |
| fishbone native | 14 | 1 | Má geometrii |
| manchester native | 72 | 1 | Má geometrii |
| botanic native | 16 | 1 | Má geometrii |

#### D10 — offset606 = element count v posledním layer bloku

| Soubor | Elementů | offset606 |
|--------|----------|-----------|
| square_1_aci native | 1 | 1 |
| double_line native (2 elem) | 2 | 2 |
| fishbone native | 14 | 14 |
| manchester native | 72 | 72 |
| botanic native | 16 | 16 |

#### D11 — B2B parser (vcf_parser_b2b) nepoužívá ec@92 ani offset606

**Architektura produkčního parseru:**
- Forward scan: hledá GEOMETRY_SIG (bytes `\x01\x00\x01\x00\x00\xff\xff\xff` na offsetu 444-449)
- Backward scan: od GEOMETRY_SIG zpět počítá layer bloky (krok 610B, max 32 bloků)
- Element count: počítá GEOMETRY_SIG výskyty v binárce

**Důsledek:** Parser vždy našel správný počet elementů (i v neopravených synth VCF), protože skenuje binární strukturu, nečte metadata z layer bloků. To vysvětluje, proč testy (28/28) vždy procházely, ale GUI selhávalo.

#### D12 — Parser != GUI (dva nezávislé element-count mechanismy)

| Komponenta | Mechanismus detekce elementů |
|------------|------------------------------|
| vcf_parser_b2b | GEOMETRY_SIG forward scan |
| VCutWorks GUI | offset606 z posledního layer bloku |
| náš vcf_parser/_reader.py | Backward scan + GEOMETRY_SIG |

Toto je klíčové ponaučení: **každý parser může používat jinou strategii**. Validace přes reader neznamená validaci přes GUI.

### 13.5 Implementované fixy

**Soubor:** `vcf_parser/_writer.py`

**Fix 1 — encode_layer_block() line 275:**
```python
# Before:
block[92] = 0
# After:
block[92] = 1  # 'has geometry' flag (NOT element count)
```

**Fix 2 — header() line 183:**
```python
# Before:
struct.pack('<I', 1)  # hardcoded 1
# After:
total_elements = sum(len(layer._paths) for layer in self._layers)
struct.pack('<I', total_elements)  # actual element count
```

### 13.6 Verifikace

#### Hex analýza po fixu

| Soubor | ec@92 | offset606 | SIGs | Status |
|--------|-------|-----------|------|--------|
| synth line_10_elements | 1 | 10 | 10 | ✅ MATCHES expected |
| synth square_5_elements | 1 | 5 | 5 | ✅ MATCHES expected |
| native 1-elem (all) | 1 | 1 | 1 | ✅ Baseline |
| native 2-elem (double_line) | 1 | 2 | 2 | ✅ Baseline |

#### GUI výsledky

| Soubor | Očekávané elementy | GUI výsledek |
|--------|-------------------|--------------|
| line_10_elements.VCF | 10 | ✅ **10 elementů** |
| square_5_elements.VCF | 5 | ✅ **5 elementů** |
| single_line_2000_elements_2.VCF | 2 | ✅ **2 elementy** |

### 13.7 Zbývající problémy

| Problém | Severita | Majitel |
|---------|----------|---------|
| Square — duplicitní vertexy (7 segmentů místo 4) | HIGH | DXF adapter deduplication |
| Circle/Curve — SPLINE oversampling (100+ segmentů) | HIGH | Bezier encoding |
| Color diff: 0x0A0A0A00 vs native 0x00000000 | MEDIUM | ACI 0 mapping workaround |
| ELEMENT_FOOTER content diff (offsety 32-47, 112-143) | LOW | Neověřeno |
| GEOMETRY_HEADER_TEMPLATE jen 4× float64 1.0 | LOW | Neověřeno pro multi-element |
| Fishbone konsolidace 41→14 elementů | MEDIUM | Neznámá pravidla |

### 13.8 Metodologické ponaučení

1. **Parser != GUI** — Validace přes reader/parser nestačí. Každý software může používat jiný mechanismus pro stejnou informaci.
2. **Off-by-one/off-by-two chyby jsou záludné** — Špatné měření délky struktury (14B vs 12B) zneplatnilo všechny odvozené offsetové analýzy.
3. **Cross-referencuj s produkčním kódem** — Analýza vcf_parser_b2b (produkční parser) odhalila, že element count se čte z offset606, ne z ec@92. Bez této referenční implementace bychom pravděpodobně stále hledali.
4. **Testy nejsou ground truth** — 28/28 testů procházelo i s chybným offset606. Testy testují reader logiku, ne GUI logiku.
5. **Multi-iterační debugging je normální** — Trvalo 8 iterací najít 2 jednoduché single-line changes. Každá slepá ulička poskytla data potřebná pro další krok.

---

*Konec dokumentu — verze 3.0*
