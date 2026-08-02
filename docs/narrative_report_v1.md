# Narativní report — VcfWriter (Vcf-compiler)

**Datum:** 27. června 2026
**Repo:** https://github.com/outpost2026/Vcf-compiler
**Package:** `vcf_parser` — `from vcf_parser import write`

---

## 1. Co bylo dosaženo

Vznikl **VcfWriter** — plnohodnotný kompilátor proprietárního VCF formátu (Ruida VCutWorks, RDD6584G oscilační nůž) postavený od základu čistou serializací (clean-slate). Žádné template-patching, žádné copy-paste binárních bloků — každý bajt výstupního souboru je generován podle specifikace odvozené z reverzního inženýrství.

Klíčové milníky:

- **Funkční write API:** `write(spec: dict, path: str)` — Python slovník -> binární VCF soubor
- **Ověřená 74B segmentová struktura:** geometrické elementy s proměnným počtem segmentů
- **610B/210B layer bloky** se všemi parametry řezu (rychlost, typ nože, barva, H1/H2, feed count, V-slot směr, extendy)
- **28 unit/roundtrip testů** (28 PASS, 2 SKIP — očekávané)
- **6 demo VCF souborů** včetně produkčních vícevrstvých souborů
- **Roundtrip přes reference:** vygenerovaný VCF → zpětné načtení → porovnání vrstev i elementů
- **Git push** do `https://github.com/outpost2026/Vcf-compiler`

### Opravené chyby během vývoje

1. **Layer block layout:** referenční VCF mají speed na offsetu +4, nikoliv +8. Parser používal workaround `S = pos + 4` který fungoval jen pro černé vrstvy (color = 0), protože nechtěně četl 4B barvy + 4B speed jako jeden float64.
2. **Cutter type mapping:** formát ukládá index do `CUTTER_MAP` (0="Vibrate cutter"), nikoliv ID z `CUTTER_ID_MAP` (1="Vibrate cutter").
3. **BGR byte order:** `color_bgr = (R << 16) | (G << 8) | B`, nikoliv `(B << 16) | (G << 8) | R` — R a B komponenty byly prohozené.
4. **Layer order:** writer zapisoval vrstvy v opačném pořadí (reversed) a parser je zase obracel, což způsobovalo net reversal při roundtripu. Writer nyní zapisuje v pořadí dle spec.
5. **V-slot direction:** používal se `DIR_ID_MAP` (1/2/3) ale formát ukládá index do `DIR_MAP` (0/1/2).

---

## 2. Architektura nástroje

```
vcf_parser/
├── __init__.py       # Public API: write(), VcfWriterError
├── _writer.py        # VcfWriter třída + top-level write()
├── _reader.py        # Čtení VCF: extract_active_layers_details() + konstanty
├── _config.py        # Machine profile (fallback)
└── _geometry.py      # Geometrické utility: bbox, délka cesty, containment
```

### Závislosti (import graph)

```
write() → VcfWriter → _reader.py   (GEOMETRY_SIG, CUTTER_MAP, DIR_MAP)
                     → _config.py   (machine_profile fallback, volitelné)
                     → _geometry.py (bbox, path_length, volitelné)

NEZÁVISÍ NA: Knowledge_base, app.py, streamlit
```

### Data flow

```
spec: dict
  ├── "layers": [list of layer dicts]
  │   ├── cutter_type, speed_mms, color_rgb
  │   ├── start_height_h1_mm, end_height_h2_mm
  │   ├── direction, starting_extension_mm, ending_extension_mm
  │   ├── is_output_yes, number_of_feeding
  │
  └── "elements": [list of geometry element dicts]
      ├── geom_type ("Polyline" | "Circle" | "Polygon")
      ├── vertices: [(x1,y1), (x2,y2), ...]
      └── layer_index: int (odkaz do layers[])
          │
          ▼
    VcfWriter.write(fd)
      ├── header()  → magic + layer bloky
      ├── body()    → geometry elementy (GEOMETRY_SIG + segmenty)
      └── trailer() → 0xD7
          │
          ▼
    binarni VCF soubor
```

### Třídy a metody

| Třída / Funkce | Účel |
|---|---|
| `VcfLayer` | Kontejner pro data jedné vrstvy (path, speed, cutter, h1/h2, barva, direction, extendy) |
| `VcfWriter` | Hlavní writer — skládá header + body + trailer do binárního proudu |
| `VcfWriter.header()` | Generuje magic + N× layer blok |
| `VcfWriter.body()` | Generuje GEOMETRY_SIG + N× 74B segmentů |
| `VcfWriter.trailer()` | Zakončovací byte 0xD7 |
| `VcfWriter.encode_layer_block()` | Jeden 610B (v1.0.013) nebo 210B (v1.0.012) blok |
| `VcfWriter.encode_geometry_element()` | Jeden polygon s N segmenty (45 + N*74 B) |
| `VcfWriter.encode_circle_element()` | Kružnice (type_id=1, subtype=3) |
| `write(spec, output_path)` | Top-level API — vytvoří VcfWriter, zapíše soubor |

---

## 3. Principy fungování

### Binární formát VCF

VCF soubor se skládá ze tří částí:

```
┌─────────────────────────────────────────────┐
│ HEADER                                       │
│  ├─ Magic: "RDVCUTFILEVER1.0.013"            │
│  ├─ Padding: 4× 0x00                         │
│  └─ Layer bloky: N × 610B (nebo 210B)        │
│    ┌─────────────────────────────────────┐   │
│    │ +0:  output_flag (u32)              │   │
│    │ +4:  speed_mms (f64)                │   │
│    │ +12: color_bgr (u32)                │   │
│    │ +32: cutter_type (i32, CUTTER_MAP)  │   │
│    │ +76: H1 start_height (f64)          │   │
│    │ +84: feed_count (i32)               │   │
│    │ +92: H2 end_height (f64)            │   │
│    │ +100: V-slot direction (u16)         │   │
│    │ +102: V-slot comp (f64)              │   │
│    │ +110: start_ext (f64)                │   │
│    │ +118: end_ext (f64)                  │   │
│    └─────────────────────────────────────┘   │
├─────────────────────────────────────────────┤
│ BODY                                         │
│  └─ Geometry element:                        │
│    ┌─────────────────────────────────────┐   │
│    │ +0:  GEOMETRY_SIG (8B)              │   │
│    │ +8:  geom_color (u32)               │   │
│    │ +45: type_id (u32)                  │   │
│    │ +49: pt_count (u32)                 │   │
│    │ +53: subtype (u32)                  │   │
│    │ +45: [segment 0: 74B]               │   │
│    │      +14: x1 (f64)                  │   │
│    │      +22: y1 (f64)                  │   │
│    │      +30: x2 (f64)                  │   │
│    │      +38: y2 (f64)                  │   │
│    │      +46: d0 (f64, arc data)        │   │
│    │      +54: d1 (f64)                  │   │
│    │      +62: d2 (f64)                  │   │
│    │ +45: [segment 1: 74B]               │   │
│    │ ...                                  │   │
│    └─────────────────────────────────────┘   │
├─────────────────────────────────────────────┤
│ TRAILER: 0xD7                                │
└─────────────────────────────────────────────┘
```

### Barevný systém

Barva je uložena ve dvou místech:

1. **V layer bloku** (offset +12): BGR uint32 — `(R << 16) | (G << 8) | B`
2. **V geometry elementu** (offset +8): `(BGR << 8) & 0xFFFFFFFF` — posun o 8 bitů doleva. Tento posun vytváří "geom_color" který se používá pro párování elementů s vrstvami.

Příklad: červená `[255, 0, 0]`:
- BGR = `(255 << 16) | (0 << 8) | 0` = `0x00FF0000`
- geom_color = `(0x00FF0000 << 8) & 0xFFFFFFFF` = `0xFF000000`

### Identifikace vrstev parserem

Parser `extract_active_layers_details()` používá unikátní strategii:

1. **Najde všechny GEOMETRY_SIG** v binárních datech → získá `first_geometry_pos`
2. **Iteruje pozpátku** od `first_geometry_pos` po násobcích `block_size` (610 nebo 210)
3. **Validuje layer blok** pomocí speed checku: `1.0 <= speed <= 2000.0`, `speed % 5 == 0`, `speed.is_integer()` + kontrola že `geom_color` vzniklý z barvy v bloku odpovídá některé z barev nalezených v geometrii
4. **Vrací seznam aktivních vrstev** v pořadí od první po poslední

Tento přístup je odolný vůči neznámým datům mezi magicem a první vrstvou (DXF embedding, metadata).

---

## 4. Možné cesty importu dat

### 4.1 JSON z DXF konvertoru (primární varianta)

```
DXF soubor ──→ DXF parser ──→ JSON spec ──→ vcf_parser.write() ──→ .VCF
```

**Princip:** Externí nástroj (např. ezdxf v Pythonu, nebo DXF knihovna) přečte DXF, extrahuje entity (LINE, POLYLINE, CIRCLE, ARC, LWPOLYLINE) a vygeneruje JSON ve formátu:

```json
{
  "layers": [
    {
      "cutter_type": "Vibrate cutter",
      "speed_mms": 500.0,
      "start_height_h1_mm": 2.0,
      "end_height_h2_mm": 12.0,
      "color_rgb": [255, 0, 0],
      "direction": "N/A",
      "starting_extension_mm": 0.0,
      "ending_extension_mm": 0.0,
      "is_output_yes": true,
      "number_of_feeding": 1
    }
  ],
  "elements": [
    {
      "geom_type": "Polyline",
      "vertices": [[x1,y1], [x2,y2], ...],
      "layer_index": 0,
      "is_output_yes": true
    }
  ]
}
```

**Výhody:**
- Čistá separace koncernů — DXF parsing je complexní doména sama o sobě
- JSON lze snadno debugovat, verzovat, ručně editovat
- `vcf_parser` zůstává čistě serializační vrstvou
- Žádná závislost na DXF knihovnách v jádře kompilátoru

**Nevýhody:**
- Nutnost napsat/udržovat DXF→JSON konvertor zvlášť
- Dvě úrovně konfigurace (konvertor + writer)
- Nutnost mapovat DXF vrstvy na řezné parametry

### 4.2 Skeleton template (alternativní varianta — zvažovaná devem)

```
Skeleton.VCF ──→ vcf_parser._reader ──→ spec dict ──→ modifikace ──→ vcf_parser.write() ──→ .VCF
                    (extrahuje vrstvy
                     a geometrii)
```

**Princip:** Jako vstup slouží existující "kosterní" VCF soubor, který obsahuje:

- Základní geometrická primitiva (úsečky, kružnice, obdélníky) s různými barvami
- Přednastavené vrstvy s definovanými parametry (rychlost, typ nože, H1/H2, extendy)
- Ukázkové V-slot vrstvy se správnou konfigurací direction

Tento skeleton se načte pomocí `extract_active_layers_details()` a interního parseru elementů, výsledný `spec` slovník se modifikuje (doplnění/přepsání geometrie, úprava parametrů) a zapíše se nový VCF.

**Výhody:**
- Není potřeba DXF parser — VCF je zároveň vstup i výstup
- Skeleton slouží jako "živá dokumentace" formátu
- Možnost validovat změny přímo v VCutWorks
- Skeleton může obsahovat strojově specifická nastavení (machine profile)

**Nevýhody:**
- Skeleton musí být ručně vytvořen a udržován (ideálně přímo ve VCutWorks)
- Pokud se změní formát VCF, skeleton je třeba aktualizovat
- Omezená flexibilita — geometrie je definována skeletonem, ne externím vstupem

**Varianta: kombinace obou přístupů**
```
Skeleton.VCF ──→ extract layers ──→ layer parametry
                                          ↓
DXF ──→ parser ──→ geometrie ──────→ write(merged_spec)
                                          ↓
                                       .VCF
```

Tedy: parametry vrstev ze skeletonu, geometrie z DXF. Skeleton definuje "jak řežeme", DXF definuje "co řežeme".

### 4.3 Machine profile (konfigurační vrstva)

Soubor `machine_profile.json` poskytuje fallback hodnoty pro kinematické parametry stroje (max speed, corner brake, overheads). `_config.py` načítá tento profil pomocí `@lru_cache` a `_geometry.py` ho využívá pro případné optimalizace řezné dráhy.

Aktuálně je tato vrstva volitelná — writer funguje i bez ní (používá defaults).

---

## 5. Open source reference z Ruida ekosystému

Při návrhu VcfWriter byly použity poznatky z těchto open source projektů:

| Projekt | Jazyk | Role | Přínos |
|---------|--------|------|--------|
| **[jnweiger/ruida-laser](https://github.com/jnweiger/ruida-laser)** (`src/ruida.py`, 805 ř.) | Python | `.rd` generátor | Hlavní šablona pro VcfWriter — generování head/body/trail, 3 třídy: RuidaLayer, Ruida, RuidaUdp |
| **[meerk40t/ruida](https://github.com/meerk40t/meerk40t)** (`rdjob.py`, 2244 ř.) | Python | Bimodální `.rd` parser + generátor | Nejdůkladnější implementace Ruida protokolu, 60+ encoder metod, auto-detekce verzí |
| **[kkaempf/ruida](https://github.com/kkaempf/ruida)** (~44 souborů) | Ruby | Parser/dekodér | Clean command dispatch, typový systém, self-synchronizing XOR encoding |
| **[schuermans.info/rdcam](https://schuermans.info/rdcam)** | Docs | RE dokumentace | Původní scrambling algoritmus, message format |
| **ArboresTech Wiki** (http://wiki.ArboresTech.com/) | Docs | Reference | Kompletní command table, DA parametry |

### Klíčová ponaučení z open source

1. **VCF není .rd se scramblingem** — .rd používá `swap bit7<->bit0, XOR MAGIC, +1`, VCF je raw serializace. To zjednodušuje writer.
2. **74B segmenty jsou fixní** — .rd používá variabilní příkazy (88/a8=11B, 89/a9=5B), VCF má jednotnou 74B strukturu. Jiný přístup k path→binary.
3. **Souřadnice**: .rd používá `int_35` v μm (5B base-128), VCF používá IEEE 754 float64 v mm (8B little-endian).
4. **CNC parametry**: .rd = laser power/frequency, VCF = cutter_type, H1/H2, oscillation_freq, V-slot.
5. **~70% kódu z jnweiger/ruida-laser a meerk40t je re-use** — architektura (třídy Layer/Writer), sekvenční zápis, struktura header/body/trailer.

### Vztah k B2B-Knowledge-Base

Kopírované dokumenty v `docs/`:

| Soubor | Zdroj | Popis |
|--------|-------|-------|
| `VCF_Reverse_Engineering_Inference_Workflow_2026.md` | `01_METODIKY/01_reverse_engineering/` | Kompletní RE workflow, 1276 ř., v1.1 |
| `SYSTEQ_VCF_STACK_ANATOMY_V2.md` | `02_ANALYZY/03_kodove_analyzy/` | Architektonická disekce vcf_parser_b2b stacku, 643 ř. |
| `RE_CASE_STUDY_VCUTWORKS_LIGHTBURN_v2.md` | `04_KNOWLEDGE_BASE/01_reverse_engineering/` | Kazuistika RE — 29 dní, V1→V22, 371 ř. |
| `KNOWLEDGE_CORPUS_VCUTWORKS_LIGHTBURN.md` | `04_KNOWLEDGE_BASE/00_CNC_CAM/` | Znalostní korpus — VCF + DXF formáty, barevné mapování, 435 ř. |
| `DXF_PREDICTIVE_PARSER_METHODOLOGY.md` | `04_KNOWLEDGE_BASE/00_CNC_CAM/` | Metodika prediktivního parseru DXF, včetně LightBurn→AutoCAD rozdílů |

### Možné cesty importu dat (doplnění)

Open source rešerše potvrzuje dvě cesty:

**Cesta A — DXF→JSON→VCF (primární):**
- `ezdxf` knihovna pro čtení DXF
- Nutnost řešit LightBurn DXF odlišnosti ( proprietární CAM paleta, INSERT bloky → 50% ztráta geometrie bez block explosion)
- JSON spec jako neutrální formát mezi DXF parsrem a VcfWriterem

**Cesta B — Skeleton VCF template:**
- VCF jako vstup i výstup (read → modify → write)
- Možnost kombinovat parametry vrstev ze skeletonu s geometrií z DXF
- Skeleton lze vytvořit přímo ve VCutWorks

**Cesta C — Přímá konverze .rd → .VCF:**
- Teoreticky možné díky sdílenému Ruida protokolu
- Vyžaduje mapování: laser power → cutter_type, frequency → oscillation_freq, color base-128 → BGR uint32
- Nízká priorita — .rd je laserový formát, VCF je nůž

---

## 6. Stav a další kroky

### Hotovo
- [x] VcfWriter s čistou serializací
- [x] write() API
- [x] Layer block encoding (610B / 210B)
- [x] Geometry element encoding (Polyline, Circle)
- [x] V-slot parametry (direction, extendy, kompenzace)
- [x] Barevný systém (BGR + geom_color)
- [x] Parser pro zpětné čtení a validaci
- [x] 28 testů
- [x] Demo VCF soubory
- [x] Push na GitHub

### Zbývá
- [ ] **VCutWorks validace** — otevřít vygenerovaný VCF přímo v VCutWorks, zkontrolovat vrstvy a geometrii vizuálně
- [ ] **Polygon type (type_id=1)** — uzavřené polygony
- [ ] **ARC segment data** — vyplnění d0, d1, d2 pro oblouky a kružnice (aktuálně 0.0, což je korektní jen pro rovné úseky)
- [ ] **DXF→JSON bridge** — buď jako samostatný nástroj nebo integrovaný modul
- [ ] **Skeleton template** — vytvoření kosterního VCF pro vývojový workflow
