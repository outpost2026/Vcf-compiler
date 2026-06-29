# Návrh nových disekčních a statistických nástrojů pro RE analýzu VCF/DXF

**Verze:** 1.0  
**Datum:** 2026-06-30  
**Autor:** RE session 8 — syntéza existujících nástrojů a identifikace slepých míst

---

## 1. Současný stav — inventář existujících nástrojů

Před návrhem nových nástrojů je nutné zmapovat, co již existuje a jaké RE mezery zůstávají.

### 1.1 Diagnostické skripty v `dev_scripts/`

| Nástroj | Účel | Silné stránky | Slepá místa |
|---------|------|---------------|-------------|
| `diagnose_multi_element.py` | Detekce verze VCF, počítání elementů (GEOMETRY_SIG vs offset606), detekce anomálií footerů | křížová kontrola ec@92/offset606, detekce 1.0.012 vs 1.0.013 | nečte pole footerů, neanalyzuje vrstvové bloky na úrovni polí |
| `build_element_types_catalog.py` | Katalogizace typů elementů (type_id, subtype, pt_count) přes 51 souborů + footer analýza + gap analýza | ground-truth katalog, footer detection, gap matrix native vs writer | nepočítá distribuce hodnot polí, nerozkládá footery na jednotlivá pole |
| `vcf_binary_search.py` | Generování VCF variant s vypnutými/zapnutými features (A-J) | systematické testování validity formátu | není scanner — generuje, neanalyzuje |
| `vcf_dxf_re_correlator_v1.1.py` | Korelace DXF↔VCF geometrie, odvození transformační matice, mapování barev | hlasovací mechanismus, master agregace | pouze jeden pár souborů, není dávkový režim |
| `hex_diff_v2.py` | Binární diff native vs synthetic | detailní hex dump s kontextem | žádné sémantické značení diffs |
| `VcfWrappingAnalyzer.py` | Legacy RE geometrie (překonán v1.1) | — | — |

### 1.2 Externí nástroje v `vcf_color_service/`

| Nástroj | Účel |
|---------|------|
| `vcf_color_extractor.py` | Statistická extrakce ACI mapování z VCF layer bloků |
| `vcf_validate_layers.py` | Validační brána pro pipeline (CI) |

### 1.3 Production parser `vcf_parser_b2b/src/`

Poskytuje tyto capabilities, které nové nástroje mohou využít:

| Modul | Klíčová funkce | Výstup |
|-------|---------------|--------|
| `vcf_binary_reader.py` | `extract_active_layers_details()` | seznam layer dictů (speed, cutter, H1, H2, color, extensions, direction) |
| `vcf_geometry.py` | `parse_geometry_v18_2()` | elementy s bbox, centroid, délka, curvature, sharp corners, vertices, arc data |
| `vcf_parser_v20.py` | `RuidaVcfEngineV20.parse_bytes()` | kompletní parsed_data: elementy, layers, shape_groups, topology_tree, ml_features |
| `vcf_time_predictor.py` | `predict_cut_time()` | časová predikce |

---

## 2. Návrh nových nástrojů

### 2.1 P0 — kritické RE mezery (doporučeno jako první)

---

#### Nástroj #1: `dissect_footers.py` — Footer Field Dissector

**Cíl:** Systematicky rozpitvat všech 196/245/253 B footer struktury na jednotlivá pole a statisticky určit jejich význam.

**Motivace:** Současné nástroje detekují footer jako "196 B blob" a umí říct, zda je konstantní nebo proměnný. Nikdo ale systematicky neextrahoval všech ~196 B do pole po poli, nezkoumal korelaci napříč elementy v rámci jednoho souboru ani napříč celou training DB. Přitom víme, že footery obsahují DXF group code data, bounding box hodnoty a per-element metadata.

**Co by měl nástroj dělat:**

1. Pro každý element v multi-element VCF najít footer offset (pomocí `GEOMETRY_SIG` + `_compute_expected_element_size()` + detekce 196/245/253 B)
2. Extrahovat všech ~196 B jako sekvenci uint16, uint32, float64 a raw bytů
3. Pro každý offset spočítat statistiku napříč elementy:
   - konstantní napříč všemi elementy → pravděpodobně default/hodnota
   - měnící se → pravděpodobně per-element data
   - nulový/bazén → pravděpodobně nepoužitý
4. Z detekovaných proměnných polí extrahovat:
   - IEEE 754 hodnoty → bounding box, pozice
   - ASCII řetězce → DXF group code data
   - uint32 inkrementující → čítač/ID elementu
5. Identifikovat, co se mění mezi 196 B a 245 B footery (rozdíl = 49 B, ofsety 196-244)
6. Cross-file korelace stejných offsetů — hledání vzorů

**Vstupy:**
- `cesta k VCF` nebo `--dir` pro dávkové zpracování training DB
- volitelně `--element-range` pro detail na konkrétním elementu

**Výstupy:**
- `footer_matrix_{file}.json` — pole elementů × extrahovaná pole (s typovou anotací: uint32/float64/ascii/unknown)
- `footer_field_hypotheses.md` — pro každý offset: statistika (min, max, mean, const?), hypotéza o významu
- `footer_dxf_extracts_{file}.txt` — všechny ASCII řetězce extrahované z footerů
- Při `--dir`: `footer_crossfile_report.md` — agregace napříč training DB

**RE přínos:** Odhalí zbývající strukturu footer formátu, identifikuje per-element metadata pole, extrahuje DXF fragmenty, zodpoví otázku "k čemu slouží druhých 128 B footerů".

**Technická implementace:**
- Využít `vcf_parser_b2b.vcf_binary_reader.GEOMETRY_SIG` pro detekci elementů
- Vlastní `dissect_footer(data, sig_offset, pt_count)` funkce:
  1. Spočítat `expected_end = sig_offset + 45 + pt_count * 74`
  2. Zkusit 196, 245, 253 B — první, kde `data[expected_end + size : expected_end + size + 4]` není platný GEOMETRY_SIG
  3. Extrahovat blok po 4/8 bytech s typovou detekcí (float64 test pomocí NaN/Inf detekce)
- Pro ASCII detekci: skenovat footer pro `b'[A-Za-z0-9_ \\-\\.]{4,}'`

---

#### Nástroj #2: `dissect_layer_blocks.py` — Layer Block Forensics

**Cíl:** Kompletně zmapovat všech 610 B layer bloku (1.0.013) — aktivních i prázdných — a vytvořit definitivní field map.

**Motivace:** Současné nástroje a writer používají jen ~15 polí z 610 B (speed@4, color@12, cutter@36, H1@80, H2@96, extensions@114/122, ec@92, offset602/606, linked-list@608/604). Zbývá ~590 B, které jsou buď nepoužité, nebo obsahují důležitá metadata (next_layer_color, machine profile reference, atd.). Prázdných 256 bloků nebylo nikdy systematicky zkoumáno — obsahují init data, která mohou být důležitá pro validitu formátu.

**Co by měl nástroj dělat:**

1. Lokalizovat všechny 610 B bloky v souboru (nejprve 256 prázdných, pak aktivní)
2. Pro každý blok extrahovat všechna pole:
   - Známá (speed@4, block_index@10, color@12, cutter@36, H1@80, ec@92, atd.)
   - Neznámá (každých 4/8 B od offsetu 0-610)
3. Statistika napříč aktivními bloky v souboru:
   - Které offsety jsou konstantní → default/hardware config
   - Které offsety jsou vždy 0 → nepoužité
   - Které offsety korelují s layer parametry → objevení nových polí
4. Statistika napříč prázdnými bloky:
   - Jsou všechny stejné? Liší se index?
   - Je init data závislá na verzi?
   - Obsahují časová razítka?
5. Cross-file statistika: která pole jsou konzistentní napříč soubory?

**Vstupy:**
- `--dir` pro training DB, volitelně `--file` pro jednotlivý soubor

**Výstupy:**
- `layer_block_field_map_{version}.md` — kompletní mapa s popisem každého offsetu
- `layer_block_statistics.json` — per-offset statistika: min/max/mean/const/always_zero
- `empty_block_catalog.json` — init data vzory napříč soubory

**RE přínos:** Odhalí všechna dosud neznámá pole v layer bloku, umožní writeru generovat kompletnější bloky, potvrdí nebo vyvrátí hypotézy o linked-list pointerech a next_layer_color.

**Technická implementace:**
- Detekce hlavičky: najít první 610 B blok (hledáním sekvence speed+délky)
- Pro každý blok: `struct.unpack_from('<I', block, offset)` v krocích po 4, s dodatečným float64 testem
- Porovnání prázdných bloků: `hash(block)`, hledání jedinečných vzorů
- Využít `vcf_color_extractor.py` vzor pro cross-file agregaci

---

#### Nástroj #3: `decode_subtype_bits.py` — Subtype Upper-Bit Correlator

**Cíl:** Statisticky určit, co kóduje horních 16 bitů subtype hodnoty, která se liší soubor od souboru.

**Motivace:** Z element_types_catalog víme, že horních 16 bitů subtype není náhodných — klastruje se podle souborů (0x7299→nesting files, 0x72B9→PCB, 0x736F→stripe sixty, 0x71F7→Arbyd, 0x0019/0x3FF0/0x40A7→FLUENZ varianty). Nikdo ale systematicky nezkoumal korelaci s konkrétními parametry (cutter type, speed, material, datum, název souboru). Může jít o hash souboru, ID cutter configu, material ID, nebo dokonce bit field s více významy.

**Co by měl nástroj dělat:**

1. Extrahovat pro každý element: raw subtype, type_id, pt_count, geom_color, layer_index
2. Extrahovat pro každý soubor: verzi, velikost, datum (z FS), názvy (počet částí, material, rozměry), cutter typy, rychlosti, H2 hodnoty
3. Pro horních 16 bitů subtype:
   - Je hodnota konstantní v rámci souboru? → file-level metadata (hash/checksum)
   - Liší se per-layer nebo per-cutter? → layer-level metadata
   - Koreluje s rychlostí? → speed range encoding
   - Koreluje s názvem souboru? → material/job ID
4. Pokusit se dekódovat jako bit field:
   - Testovat jednotlivé bity proti binárním vlastnostem (has_circle, has_arc, output_flag, atd.)
5. Shluková analýza: které soubory sdílejí stejný upper-bit pattern?

**Vstupy:**
- `--dir` pro training DB

**Výstupy:**
- `subtype_upper_bit_hypotheses.md`:
  - Per-file tabulka: název, upper_bits, cutter_type, speed_range, material, layer_count, canvas_size
  - Hypotéza: "upper bits encode cutter configuration profile ID"
  - Bit field test results
- `subtype_correlation_matrix.json` — korelační koeficienty upper_bits vs všechny parametry

**RE přínos:** Definitivně zodpoví otázku "co znamenají horní 2 B subtype", což je jedna z nejdéle otevřených otázek v RE. Odhalí, zda writer musí nastavovat upper bits pro kompatibilitu.

**Technická implementace:**
- Využít `vcf_binary_reader.extract_active_layers_details()` pro layer parametry
- Vlastní `extract_subtypes(data)` — skenování GEOMETRY_SIG, čtení subtype z offsetu p+8
- Korelace: groupovat soubory podle upper_bits, porovnávat jejich parametry
- Pokud upper_bits koreluje s (cutter_type + speed), pravděpodobně "cutter profile ID"
- Pokud koreluje s MD5 prvních N bytů souboru, pravděpodobně "file checksum"

---

### 2.2 P1 — statistické a kvalitativní nástroje

---

#### Nástroj #4: `analyze_writer_gaps.py` — Writer Coverage Gap Analyzer

**Cíl:** Pro každý native VCF v training DB vygenerovat syntetický ekvivalent, hex-diffnout a klasifikovat každý diff region podle feature. Výstupem je procentuální "pokrytí" writeru vůči native formátu.

**Motivace:** Současný gap analysis v `build_element_types_catalog.py` je omezený na type_id/subtype/pt_count. Neexistuje nástroj, který by změřil, jak přesně writer reprodukuje native formát byte po bytu pro všechny produkční soubory. Potřebujeme vědět nejen "jaké typy elementů chybí", ale "o kolik bytů se liší header, layer bloky, geometry encoding, footers".

**Co by měl nástroj dělat:**

1. Pro každý native VCF v training DB:
   a. Přeparsovat pomocí `vcf_parser_b2b` (extrahovat vrstvy, elementy, barvy)
   b. Sestavit `VcfLayer[]` z extrahovaných dat
   c. Spustit writer: `VcfWriter(layers, version, dxf_source_path).header() + .body() + .trailer()`
   d. Hex-diff native vs synthetic
2. Každý diff region klasifikovat:
   - `HEADER_MAGIC` — magic bytes
   - `HEADER_SIZE` — canvas width/height
   - `HEADER_MP` — machine profile
   - `HEADER_UNKNOWN` — neznámá pole v hlavičce
   - `EMPTY_BLOCKS` — init data prázdných bloků
   - `ACTIVE_BLOCK_SPEED` — speed field
   - `ACTIVE_BLOCK_COLOR` — color field
   - `ACTIVE_BLOCK_UNKNOWN` — neznámá pole v layer bloku
   - `GEOM_TYPE` — type_id/subtype encoding
   - `GEOM_SEGMENT` — segment data (float64 formát)
   - `GEOM_ARC` — arc data (7. a 8. float64)
   - `FOOTER` — footer blob
   - `TRAILER` — trailer blob
3. Agregovat přes training DB: kolik souborů má shodu v jaké kategorii
4. Identifikovat "nejbližší" a "nejvzdálenější" soubor od writeru

**Vstupy:**
- `--dir` training DB, volitelně `--file` pro jednotlivý soubor

**Výstupy:**
- `writer_coverage_report.md`:
  - Per-feature tabulka: feature, pokrytí %, počet souborů se shodou, poznámka
  - Per-file tabulka: název, celková shoda %, největší diff region
  - "Top 5 nejvíce se lišících souborů" s analýzou proč
- `writer_gap_matrix.json` — strojově čitelná matice

**RE přínos:** Poskytne přesné měření, jak daleko je writer od "bitově identické reprodukce". Identifikuje, které featury writeru jsou priorita pro opravu (např. "footer chybí v 100 % souborů, arc data ve 40 %").

**Technická implementace:**
- Kritické: writer musí umět přijmout `VcfLayer` z externího parseru (tedy vytvořit `VcfWriter.from_parsed_data(parsed_data)`)
- Pokud writer aktuálně neumožňuje importovat vrstvy z parseru, nástroj musí mapovat: `parser output → VcfLayer` konstrukce

---

#### Nástroj #5: `segment_geometry_stats.py` — Segment Geometry Statistics

**Cíl:** Spočítat distribuce geometrických vlastností segmentů (délky, úhly, křivosti, arc parametry) napříč training DB pro definici "normální produkční geometrie".

**Motivace:** Katalog `element_types_catalog.md` sleduje pouze pt_count rozsahy. Nevíme:
- Jaká je typická délka segmentu? (krátké = 10-50 mm? dlouhé = 200-500 mm?)
- Jaké arc parametry používají native kružnice? (d0, d1, d2 = π? celý kruh?)
- Jaká je distribuce ostrých rohů?
- Které elementy jsou statistické odlehlé hodnoty?

Tyto znalosti jsou klíčové pro:
- Optimalizaci writer outputu (např. "99 % segmentů je kratších než 300 mm")
- Detekci anomálií v produkčních datech
- Rozhodnutí o arc aproximaci

**Co by měl nástroj dělat:**

1. Pro každý element v training DB extrahovat pomocí `vcf_geometry.parse_geometry_v18_2()`:
   - Pro každý segment: délka, dx, dy, úhel, arc (d0, d1, d2)
   - Pro každý element: celková délka, počet segmentů, curvature_index, sharp_corners_count
2. Spočítat histogramy (5, 10, 20, 50 binů) pro:
   - Délky segmentů (mm) — per geom_type
   - Úhly segmentů (deg)
   - Křivost (mm⁻¹)
   - Arc d0, d1, d2 hodnoty
   - Poměr arc/line segmentů
   - Ostré rohy na element
3. Identifikovat statistické odlehlosti (mean ± 3σ, IQR)
4. Per-soubor statistika pro srovnání

**Vstupy:**
- `--dir` training DB, volitelně `--by-file` pro per-soubor statistiku

**Výstupy:**
- `segment_geometry_histograms.json` — všechna histogram data
- `segment_geometry_report.md`:
  - Tabulka per-geom_type: medián délky, průměr, 95. percentil, max
  - Arc parametr distribuce (klíčové pro writer rozhodnutí: "arc = 0 vždy" vs "arc = π u kružnic")
  - Odlehlé elementy s vyznačením souboru a offsetu
  - "Typický element" profil

**RE přínos:** Poskytne data-driven podklady pro writer implementaci arc segmentů, odhalí skutečnou geometrickou komplexitu produkčních dat, umožní detekci anomálií.

**Technická implementace:**
- Využít `vcf_parser_v20.RuidaVcfEngineV20` pro parsování
- numpy pro histogramy (volitelně, fallback na collections.Counter)
- Pro arc analýzu: extrahovat d0, d1, d2 z raw segment dat a testovat:
  - Jsou vždy 0.0? (writer current)
  - Jsou π/2π pro kružnice?
  - Jsou lineárně závislé na délce/úhlu?

---

#### Nástroj #6: `batch_correlate_dxf_vcf.py` — Dávkový DXF↔VCF Korelátor

**Cíl:** Najít DXF zdroje v metadatech VCF, spustit korelátor dávkově a agregovat transformační matice a mapování barev s confidence score.

**Motivace:** Korelátor `vcf_dxf_re_correlator_v1.1.py` existuje, ale musí se spouštět ručně pár po páru. Training DB obsahuje DXF soubory embedded v metadatech (detekováno pomocí `extract_strings()`). Potřebujeme dávkově zpracovat všechny VCF-DXF páry a získat:
- Stabilní transformační matici (offset + Y-inverze) s měřením variance
- Confidence-weighted mapování ACI→geom_color napříč všemi páry
- Statistiku úspěšnosti korelace (kolik elementů se spáruje)

**Co by měl nástroj dělat:**

1. Pro každý VCF v training DB:
   a. Extrahovat metadata stringy (`vcf_binary_reader.extract_strings`)
   b. Najít `.dxf` reference
   c. Lokalizovat DXF soubor (relativní cesta, absolutní cesta, nebo v `demo_data/`)
2. Pro každý nalezený pár (DXF, VCF):
   a. Spustit `VcfDxfReCorrelator(dxf_path, vcf_path, tolerance)`
   b. Uložit report
3. Agregovat:
   - Průměrná transformace: medián offset_x, offset_y, % Y-inverze
   - Mapování barev: pro každý ACI index, vážený průměr geom_color (váha = confidence = matched/total)
   - Statistika: kolik párů bylo nalezeno, průměrný match rate, distribuční grafy

**Vstupy:**
- `--dir` training DB
- `--dxf-dir` cesta k DXF souborům (fallback)
- `--output-dir` pro reporty

**Výstupy:**
- `correlation_master.json` — agregovaná data napříč všemi páry
- `correlation_master.md` — lidsky čitelný report:
  - Tabulka párů: DXF, VCF, matched/total, offset_x, offset_y, y_inverted
  - Agregovaná transformace s intervaly spolehlivosti
  - Mapování barev s confidence
  - Seznam nespárovaných entit napříč všemi páry

**RE přínos:** Definitivní transformační matice mezi DXF a VCF koordináty. Statisticky robustní mapování ACI→geom_color pro writer.

**Technická implementace:**
- Využít `vcf_dxf_re_correlator_v1_1.VcfDxfReCorrelator` jako knihovnu
- Přidat `--batch` mód do correlatoru nebo vytvořit samostatný wrapper
- Důležité: ošetřit, že stejný DXF může být zdrojem více VCF (nesting)

---

### 2.3 P2 — exploratorní nástroje

---

#### Nástroj #7: `decode_color_fields.py` — Dekodér barevných polí

**Cíl:** Systematicky analyzovat všechna barevná pole v celém VCF formátu a určit jejich vzájemný vztah a kódování.

**Motivace:** Víme o 3 barevných polích — `color_val@12` (BGR 24-bit v layer bloku), `geom_color@+8` (uint32 v geometry headeru, vztah `geom_color = color_val << 8`), a `next_layer_color@606` (poslední 4 B layer bloku, hodnoty od 0 po 16,777,960). next_layer_color hodnoty zahrnují jak ACI indexy (0-255), tak přímé BGR barvy (0xFF0000 = červená, 0xFFFF00 = žlutá). Potřebujeme dekódovat:
- Kdy je next_layer_color ACI a kdy BGR?
- Je to skutečně next_layer_color nebo něco jiného (crc? timestamp?)
- Existují další barevná pole v neznámých oblastech?

**Co by měl nástroj dělat:**

1. Extrahovat všechna barevná pole z každého VCF:
   - `color_val` z layer bloku (BGR)
   - `geom_color` z geometry headeru
   - `next_layer_color` z offset 606 layer bloku
   - Prozkoumat i offset 602 (aktuálně linked-list pointer)
2. Pro každé pole:
   - Histogram hodnot
   - Korelace s ostatními poli
   - Korelace s layer parametry (cutter, speed)
3. Pro next_layer_color:
   - Klasifikovat hodnoty: low (<256) = ACI index, high (>0x100000) = BGR
   - Je vztah deterministický? `next_layer_color = ACI_TO_BGR[aci]`?
   - Mění se per-layer nebo per-element?
4. Ověřit geom_color = color_val << 8 napříč všemi soubory

**Výstupy:**
- `color_field_decoding.md` — hypotézy o kódování každého pole
- `color_field_correlations.json` — korelační matice

---

#### Nástroj #8: `analysis_header_variability.py` — Katalog variabilit hlaviček

**Cíl:** Systematicky změřit všechny velikosti a obsahy hlaviček napříč training DB.

**Motivace:** Víme, že 1.0.012 má hlavičku ~40 B, 1.0.013 má variabilní hlavičky (469, 472, 500+ B). Potřebujeme katalogizovat:
- Jaké jsou všechny velikosti hlaviček?
- Které části jsou povinné?
- Kdy chybí MACHINE_PROFILE?
- Existují hlavičky s custom daty?

**Co by měl nástroj dělat:**

1. Najít hranici hlavičky (první 610/210 B blok nebo GEOMETRY_SIG)
2. Extrahovat všech prvních N bytů jako "hlavičku"
3. Klasifikovat:
   - Magic bytes (RDVCUTFILEVER...)
   - Canvas width/height
   - POST_STOCK_HEADER (14 B?)
   - MACHINE_PROFILE (418 B?)
   - Neznámé oblasti
4. Cross-file srovnání velikostí a obsahu

---

#### Nástroj #9: `panel_statistics.py` — Statistika plátna a layoutu

**Cíl:** Spočítat distribuci velikostí pláten, počtů elementů, vrstev a density napříč training DB.

---

#### Nástroj #10: `sequence_patterns.py` — Analyzátor sekvencí řezu

**Cíl:** Analyzovat typické patterny v pořadí řezání elementů napříč vrstvami.

---

## 3. Matice priorit

| # | Nástroj | P | RE přínos | Náročnost | Závislosti |
|---|---------|---|-----------|-----------|------------|
| 1 | `dissect_footers.py` | P0 | 🔴🔴🔴 Odhalí strukturu footerů, DXF fragmenty, per-element metadata | Střední | `vcf_parser_b2b`, training DB |
| 2 | `dissect_layer_blocks.py` | P0 | 🔴🔴🔴 Kompletní field mapa 610 B bloku, prázdné bloky | Střední | training DB |
| 3 | `decode_subtype_bits.py` | P0 | 🔴🔴🔴 Definitivní význam upper 16 bit subtype | Nízká | `vcf_parser_b2b`, training DB |
| 4 | `analyze_writer_gaps.py` | P1 | 🟡🟡 Měření kvality writeru, prioritizace oprav | Vysoká | `vcf_parser_b2b` + `VcfWriter` |
| 5 | `segment_geometry_stats.py` | P1 | 🟡🟡 Distribuce geometrie, arc parametry, anomálie | Nízká | `vcf_parser_b2b`, numpy |
| 6 | `batch_correlate_dxf_vcf.py` | P1 | 🟡🟡 Agregovaná transformace, color mapping | Střední | correlator v1.1, DXF files |
| 7 | `decode_color_fields.py` | P2 | 🟢 Dekódování barevných polí | Nízká | training DB |
| 8 | `analysis_header_variability.py` | P2 | 🟢 Katalog hlaviček | Nízká | training DB |
| 9 | `panel_statistics.py` | P2 | 🟢 Layout distribuce | Nízká | `vcf_parser_b2b` |
| 10 | `sequence_patterns.py` | P2 | 🟢 Sekvenční patterny | Střední | `vcf_parser_b2b` |

## 4. Technické principy pro implementaci

### 4.1 Společné konvence

- Všechny nástroje ukládat do `dev_scripts/`
- Všechny výstupy ukládat do `research_docs/` (MD pro člověka, JSON pro stroj)
- Všechny nástroje podporují `--dir` pro dávkové zpracování training DB (`C:\Users\PC\Documents\Repozitar_Dev\_github\VCF_files_moodpasta\`)
- Všechny nástroje importují z `vcf_parser_b2b` přes `sys.path.insert`
- Výstupní MD soubory začínají `RESULT_` prefixem pro snadnou identifikaci

### 4.2 Detekce verze

```python
def detect_format(data: bytes) -> str:
    if b"RDVCUTFILEVER1.0.013" in data or b"VER1.0.013" in data:
        return "1.0.013"
    if b"RDVCUTFILEVER1.0.012" in data or b"VER1.0.012" in data:
        return "1.0.012"
    return "unknown"
```

### 4.3 Cross-file agregace

Vzor použitý v `vcf_color_extractor.py` (agregace do dictů, ukládání jako JSON + MD) je doporučený standard pro všechny nové nástroje.

---

## 5. Rozhodovací strom pro další RE vektor

Před příští session si dev přečte tento dokument a zváží:

```
1. Je priorita pochopit footer strukturu? → dissect_footers.py (P0)
2. Je priorita pochopit layer block field map? → dissect_layer_blocks.py (P0)
3. Je priorita pochopit subtype upper bits? → decode_subtype_bits.py (P0)
4. Je priorita změřit writer kvalitu? → analyze_writer_gaps.py (P1)
5. Je priorita statistika geometrie? → segment_geometry_stats.py (P1)
6. Je priorita dávková DXF↔VCF korelace? → batch_correlate_dxf_vcf.py (P1)
7. Něco jiného? → exploratorní nástroje (P2)
```

Doporučení: začít P0 sadou v pořadí (3 → 1 → 2), protože `decode_subtype_bits.py` má nejnižší náročnost a nejvyšší pravděpodobnost průlomového objevu. `dissect_footers.py` a `dissect_layer_blocks.py` jsou středně náročné ale přinesou kompletní field mapy, které jsou zásadní pro dokončení writeru.
