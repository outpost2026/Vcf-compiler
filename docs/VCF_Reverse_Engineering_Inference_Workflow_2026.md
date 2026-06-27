# Reverse Engineering VCF formátu: Inference Workflow & Metodologie LLM-asistovaného RE

**Verze:** 1.1  
**Datum:** 26. 6. 2026  
**Autor:** Ondřej Soušek (outpost2026)  
**Repozitář:** https://github.com/outpost2026  
**Změny oproti 1.0:** Přidána specifikace package API (§6.3), import graph constraints (§3.5), known issues pre-load (§8.5)

> Tento dokument je výsledkem hloubkové analýzy zdrojového kódu VCF parseru (v20),  
> existujících open-source implementací .rd generátorů (jnweiger, meerk40t, kkaempf),  
> B2B-Knowledge-Base repo (stack anatomy V2, technické zadání Moodpasta, GROUND_TRUTH),  
> a RE metodologie použité při dekódování proprietárního formátu Ruida VCutWorks.

---

## Obsah

1. [Úvod a kontext](#1-úvod-a-kontext)
2. [Analýza existujících open-source .rd generátorů](#2-analýza-existujících-open-source-rd-generátorů)
3. [Architektura VCF parseru v20](#3-architektura-vcf-parseru-v20)
    - 3.5 [Import graph a package architektura](#35-import-graph-a-package-architektura)
4. [Binární formát VCF — kompletní specifikace z RE](#4-binární-formát-vcf--kompletní-specifikace-z-re)
5. [Inference Workflow: LLM-asistované RE](#5-inference-workflow-llm-asistované-re)
6. [Zápis VCF: Návrh VcfWriter architektury](#6-zápis-vcf-návrh-vcfwriter-architektury)
    - 6.3 [Package API specifikace](#63-package-api-specifikace)
7. [Epistemický rámec a validation framework](#7-epistemický-rámec-a-validation-framework)
8. [Mapování .rd ↔ .vcf pro zpětný zápis](#8-mapování-rd--vcf-pro-zpětný-zápis)
    - 8.5 [Known issues pre-load](#85-known-issues-pre-load)
9. [Závěr a doporučení](#9-závěr-a-doporučení)

---

## 1. Úvod a kontext

### 1.1 Co je VCF formát

VCF je proprietární binární formát programu **VCutWorks** od Shenzhen Ruida Technology.  
Používá se pro CNC **oscilační nože** (RDD6584G kontrolér) — na rozdíl od .rd formátu,  
který slouží pro laserové kontroléry (RDC6442G, RDC6332G).  

Oba formáty sdílejí stejné **jádro Ruida protokolu**:
- Command-based struktura (opcode ≥ 0x80, parametry < 0x80)
- IEEE 754 double coordinates v μm
- Per-layer header + geometry body + footer
- Base-128 big-endian multi-byte encoding

Liší se v:
- **Scrambling**: .rd používá scramble (swap bit7↔bit0, XOR MAGIC, +1); VCF je raw serializace
- **Geometrie**: .rd používá proměnlivé commandy (88/a8=11B, 89/a9=5B); VCF používá fixní **74B segmenty**
- **CNC parametry**: .rd = laser power/frekvence; VCF = cutter_type, H1/H2, oscillation_freq, V-slot

### 1.2 Motivace pro zpětný zápis

Aktuální parser umí **číst** VCF a extrahovat JSON. Pro plnou automatizaci je nutný i **zápis**:
1. Generování VCF z JSON specifikace (bez VCutWorks GUI)
2. Automatické opravy defektů (merge, uzavření smyček, sekvence)
3. ERP pipeline: CAD → JSON → VCF → CNC plotr
4. Template-based generování (parametrické zakázky)

### 1.3 Použité zdroje

| Zdroj | Typ | Klíčový přínos |
|---|---|---|
| **jnweiger/ruida-laser/src/ruida.py** | Python generátor | Kompletní head/body/trail generace .rd, 805 řádků |
| **meerk40t/ruida/rdjob.py** | Python bimodální | Parser + generátor .rd, 2244 řádků, 60+ encoder metod |
| **kkaempf/ruida** (Ruby) | Parser/dekodér | Čistý command dispatch, typový systém |
| **schuermans.info/rdcam** | RE dokumentace | Originální scrambling, message format |
| **ArboresTech Wiki** | Reference | Kompletní command tabulka, DA parametry |
| **vcf_parser_v20.py** (vlastní) | Parser | 810 řádků, engine v20, KB integrace |
| **SYSTEQ_VCF_STACK_ANATOMY_V2.md** | Stack anatomie | Importní graf, 18 issues (4 CRIT, 7 HIGH), package separation plán |
| **technicke_zadani_Moodpasta.md** | Zadání | Cílové API: `from vcf_parser import parse; result = parse(...)` |
| **GROUND_TRUTH_VCF_PARSER_ORIGIN_V1.0.json** | RE ground truth | Verifikovaná offset mapa, CUTTER_MAP, DIR_MAP — jediný zdroj pravdy |
| **DEFECT_CATALOG_V1.md** | Defekt katalog | 25 typů defektů — check-list pro validaci výstupu VcfWriter |

---

## 2. Analýza existujících open-source .rd generátorů

### 2.1 jnweiger/ruida-laser/src/ruida.py

**Nejlepší šablona pro VcfWriter.** Python 2.7/3.5+, 805 řádků, tři třídy:

```
RuidaLayer (data)
  ├── _paths: list[list[Point]]  # geometrie v mm
  ├── _speed: [travel_speed, laser_speed]
  ├── _power: [min1, max1, min2, max2, ...]  # až 8 hodnot
  ├── _color: [R, G, B]
  └── _freq: float  # kHz

Ruida (generátor)
  ├── addLayer(layer)
  ├── set(nlayers, layer, paths, speed, power, ...)
  ├── header(layers) → bytes     # Generuje hlavičku
  ├── body(layers) → bytes       # Generuje geometrii
  ├── trailer(odo) → bytes       # Generuje patičku
  ├── write(fd, scramble=True)   # Složí a zapíše
  └── encode_number(num, length=5, scale=1000) → bytes

RuidaUdp (protokol)
  ├── checksum(data, start, length)
  ├── send(ary, retry=False)
  └── write(data)
```

#### Metoda header() — generování hlavičky:

```
d8 12                        # Red Light on
f0 f1 02 00                  # file type?
d8 00                        # Green Light off
e7 06 00 00...               # Feeding (abs, abs)
e7 03 xmin ymin              # Top-Left bounding box
e7 07 xmax ymax              # Bottom-Right bounding box
e7 50 xmin ymin              # Document Top-Left
e7 51 xmax ymax              # Document Bottom-Right
e7 04 00 01 00 01 00 00      # Process Repeat?

[pro každou vrstvu]:
  c9 04 lnum speed           # Layer speed
  c6 31 lnum pmin            # Laser 1 min power (layer)
  c6 32 lnum pmax            # Laser 1 max power (layer)
  c6 41 lnum pmin            # Laser 2 min power (layer)
  c6 42 lnum pmax            # Laser 2 max power (layer)
  c6 35 lnum pmin            # Laser 3 min power (layer)
  c6 36 lnum pmax            # Laser 3 max power (layer)
  c6 37 lnum pmin            # Laser 4 min power (layer)
  c6 38 lnum pmax            # Laser 4 max power (layer)
  ca 06 lnum color           # Layer RGB color
  ca 41 lnum 00              # ?
  e7 52 lnum bbox_tl         # Layer top-left
  e7 53 lnum bbox_br         # Layer bottom-right
  e7 61 lnum bbox_tl         # Layer top-left (duplicitní)
  e7 62 lnum bbox_br         # Layer bottom-right (duplicitní)

ca 22 max_layer              # Max layer number
e7 54 ...                    # Pen draw Y
e7 55 ...                    # Laser Y offset
f1 03 x y                    # Display offset / Laser2 offset
f1 00 00 / f1 01 00          # Start0 / Start1
f2 00 00 / f2 01 00          # Element index
f2 03 xmin ymin              # Element array min
f2 04 xmax ymax              # Element array max
e7 13 xmin ymin              # Array min point
e7 17 xmax ymax              # Array max point
e7 23 xmin ymin              # Array add offset
e7 08 00 01 00 01 xmax ymax  # Array repeat
```

#### Metoda body() — generování geometrie:

```python
def body(self, layers):
    for lnum, layer in enumerate(layers):
        # Prolog vrstvy
        ca 01 00               # End layer
        ca 02 lnum             # Layer number
        ca 01 30               # Flags
        ca 01 10               # Laser device 0
        ca 01 13               # Air assist on
        
        c9 02 speed            # Speed
        c6 15/16 delay         # On/Off delay
        c6 01/02 power[0:2]    # Laser 1 min/max
        c6 21/22 power[2:4]    # Laser 2 min/max
        
        # Path geometrie — volba formátu dle vzdálenosti
        for path in layer._paths:
            for point in path:
                if relok(last, point):  # delta ≤ 8.191 mm
                    if horizontal:  8a (move) / aa (cut)  → 3 bytes
                    if vertical:    8b (move) / ab (cut)  → 3 bytes
                    else:           89 (move) / a9 (cut)  → 5 bytes
                else:  # delta > 8.191 mm
                    88 (move) / a8 (cut) + abscoord(x) + abscoord(y)  → 11 bytes
```

#### Encoding functions:

```python
def encode_number(self, num, length=5, scale=1000):
    """Float mm → 7-bit big-endian bytes. scale=1000 → μm."""
    nn = int(num * scale)       # převod na μm
    while nn > 0:
        res.append(nn & 0x7f)   # 7 bitů na bajt
        nn >>= 7
    while len(res) < length:    # doplnění nulami (MSB end)
        res.append(0)
    res.reverse()
    return bytes(res)

def encode_relcoord(self, n):
    """mm → 14-bit signed (2's complement), 2 bytes."""
    nn = int(n * 1000)
    if nn < 0: nn += 16384      # 2's complement
    return self.encode_number(nn, length=2, scale=1)

def encode_percent(self, n):
    """0-100% → 14-bit unsigned, 2 bytes. 0x3FFF = 100%."""
    a = int(n * 0x3fff * 0.01)  # n * 163.83
    return bytes([a>>7, a&0x7f])

def encode_color(self, color):
    """[R,G,B] → packed 24-bit: B<<16 | G<<8 | R"""
    cc = (color[2]<<16) + (color[1]<<8) + color[0]
    return self.encode_number(cc, scale=1)
```

#### Scramble:

```python
def scramble(self, b):
    """Rotate bit0↔bit7, XOR 0x88, +1 wrap."""
    fb = b & 0x80; lb = b & 1
    b = b - fb - lb | lb<<7 | fb>>7
    b ^= 0x88
    return (b + 1) & 0xFF
```

### 2.2 meerk40t/ruida/rdjob.py

**Nejkomplexnější implementace Ruida protokolu.** 2244 řádků, bimodální (parser + generátor).

**Třída RDJob:**
- Konstruktor: `driver, units_to_device_matrix, priority, channel, magic=0x11`
- Buffer: `list()` command chunků
- Stav: `x, y, z, u, a, b, c, d = 0.0` (pozice hlavy)
- Thread safety: `threading.Lock()`

**write_header(data)** generuje:
1. `ref_point_2()` + `set_absolute()` — absolutní reference
2. `start_process()` — start
3. `process_top_left(x, y)` / `process_bottom_right(x, y)` — bounding box
4. `document_min_point(x, y)` / `document_max_point(x, y)` — document bounds
5. **Per-layer**: `layer_color_part(part, color)`, `speed_laser_1_part(part, speed)`, power pairs, bbox
6. `max_layer_part(part)` — max layer index
7. `element_index(0)`, `element_name(name)` — metadata

**write_body(data)** generuje:
1. Prolog: `layer_number_part`, `speed_laser_1`, power, work mode
2. Iterace cutcode → `cut_abs_xy` / `move_abs_xy` / `cut_rel_xy` / `move_rel_xy`
3. `end_of_file()`

**60+ encoder metod:**
```python
def move_abs_xy(self, x, y):     # 88 + 2×5B abscoord
def cut_abs_xy(self, x, y):      # a8 + 2×5B abscoord
def move_rel_xy(self, dx, dy):   # 89 + 2×2B relcoord
def cut_rel_xy(self, dx, dy):    # a9 + 2×2B relcoord
def speed_laser_1(self, speed):  # c9 02 + 5B speed
def min_power_1(self, power):    # c6 01 + 2B power
def max_power_1(self, power):    # c6 02 + 2B power
def frequency_part(self, laser, part, freq):  # c6 60 ...
def layer_color_part(self, part, color):      # ca 06 ...
def start_process(self):          # d8 00
def end_of_file(self):            # d7
def ref_point_2(self):            # d8 10
def set_absolute(self):           # e6 01
...
```

**Auto-detekce magie:**
```python
def determine_magic_via_histogram(data):
    # Nejobsahlejsi bajt v RD souboru = magic + 1
    # (protože scramble(0, magic) = (0 ^ magic) + 1 = magic + 1)
    histogram = [0] * 256
    for b in data: histogram[b] += 1
    magic = max(range(256), key=lambda i: histogram[i]) - 1
    return magic & 0xFF
```

**Swizzle LUT:**
```python
def swizzles_lut(magic):
    return [swizzle_byte(b, magic) for b in range(256)], \
           [unswizzle_byte(b, magic) for b in range(256)]
```

### 2.3 kkaempf/ruida (Ruby)

**Parser-only.** 44 command souborů, každý pro jeden opcode.

**Architektura:**
```
Command.consume(data) → loads ruida/command/<hex>.rb → Cmd_XX.new(data)
  → cmd.interprete → dispatch podle formátu (:abs, :rel, :power, :speed, ...)
```

**Number encoding (Ruby):**
```ruby
def number(n)
  fak = 1; res = 0
  xor = (n > 2) ? peek : 0
  consume(n).reverse.each do |b|
    b ^= xor
    res += fak * b
    fak *= 0x80
  end
  res
end
```

**Klíčový detail:** Každý bajt v multi-byte čísle je XORován s hodnotou následujícího bajtu (self-synchronizing encoding).

---

## 3. Architektura VCF parseru v20

### 3.1 Přehled modulů

```
src/
├── vcf_parser_v20.py          # Engine: RuidaVcfEngineV20 (810 ř.)
├── vcf_binary_reader.py       # Layer extraction, binary parsing (155 ř.)
├── vcf_geometry.py            # Geometry parsing, KB detekce (1197 ř.)
├── vcf_time_predictor.py      # Časová predikce (71 ř.)
├── vcf_config.py              # Konfigurace (149 ř.)
├── app.py                     # Streamlit UI  (1082 ř.)
├── app_config.json            # ERP/machine config
├── machine_profile.json       # Kinematická kalibrace
├── Knowledge_base/
│   ├── engine.py              # KB engine (564 ř.)
│   ├── models.py              # Datové modely (103 ř.)
│   └── rules.json             # Pravidla (101 ř.)
└── tests/
    ├── test_smoke.py
    ├── test_determinism.py
    ├── test_golden_master.py
    ├── test_geometry.py
    ├── test_config.py
    ├── test_binary_reader.py
    ├── test_kb_overrides.py
    └── test_time_predictor.py
```

### 3.2 Data flow pipeline

```
VCF binary input
    │
    ▼
extract_active_layers_details()  ────  scan GEOMETRY_SIG
    │                                  backward search from 1st geometry
    │                                  block_size = 610 (v1.0.013) / 210 (v1.0.012)
    │                                  per-layer: speed, color, cutter_type, H1/H2, extensions
    ▼
parse_geometry_v18_2()           ────  scan GEOMETRY_SIG
    │                                  type dispatch: Circle / Polygon / Polyline / Line
    │                                  74B segment records
    │                                  IEEE 754 double coordinates
    │                                  length = Σ euclidean distances
    │                                  arc data (d0, d1, d2) for curve reconstruction
    ▼
Post-processing                  ────  cut_order assignment
    │                                  canvas bbox / normalized coords
    │                                  material thickness detection
    │                                  operation type classification
    │                                  complexity computation
    │                                  aggregated job detection (BFS clustering)
    │                                  topology tree (bbox containment)
    │                                  ML feature extraction (50+ features)
    ▼
KnowledgeBaseEngine.validate_all() ──  H2 rules
    │                                  Sequence rules
    │                                  Fixation rules
    │                                  Geometry rules (edge merge, micro segs, orphans, unclosed, decor)
    ▼
predict_cut_time()               ────  t_cut + t_lift + t_corners + t_traverse + t_setup
    │
    ▼
parsed_data (JSON dict, 40+ fields)
```

### 3.3 Klíčové datové struktury

**Layer detail:**
```python
{
    "speed_mms": int,                    # Rychlost řezu mm/s
    "cutter_type": str,                  # Typ nástroje
    "cutter_type_id": int,               # ID nástroje (1-5)
    "number_of_feeding": int,            # Počet podávání
    "start_height_h1_mm": float,         # Bezpečnostní výška
    "end_height_h2_mm": float,           # Výška hrotu (propich)
    "total_cut_length_mm": float,        # Celková délka
    "color_hex": str,                    # Hex barva
    "color_val": int,                    # Int barva (BGR shift)
    "color_rgb": [R, G, B],              # RGB tuple
    "direction": str,                    # Left/Right/Cut both side (V-slot)
    "v_slot_width_comp_mm": float,       # Kompenzace V-drážky
    "starting_extension_mm": float,      # Startovní přesah
    "ending_extension_mm": float,        # Koncový přesah
    "is_output_yes": bool,               # Aktivní/vizuální vrstva
    "operation_type": str,               # through-cut/kiss-cut/V-groove
    "complexity": {                      # Komplexita vrstvy
        "avg_segment_length_mm": float,
        "curvature_index": float,
        "sharp_corners_count": int,
        "total_direction_changes": int
    }
}
```

**Element detail:**
```python
{
    "offset": str,                       # Hex offset v souboru
    "geom_type": str,                    # Circle/Polygon/Polyline/Line
    "type_id": int,                      # Binární type ID
    "subtype": int,                      # Binární subtype (arc flag)
    "segment_arc_data": [(d0,d1,d2)],    # Arc control points
    "point_count": int,                  # Počet segmentů
    "length_mm": float,                  # Délka mm (2πR pro kruhy)
    "layer_index": int,                  # Mapovaná vrstva
    "is_output_yes": bool,               # Aktivní element
    "bbox": [x1,y1,x2,y2],              # Bounding box
    "centroid": [cx, cy],                # Těžiště
    "vertices": [(x,y),...],             # Body polygonu
    "is_closed_loop": bool,              # Uzavřená kontura
    "element_id": str,                   # ID pro referenci
    "parent_id": str|None,               # Rodičovský element
    "children_ids": [str,...],           # Dceřiné elementy
    "cut_order": int,                    # Pořadí řezu
    "bbox_norm": [x1,y1,x2,y2],         # Normalizovaný bbox
    "centroid_norm": [cx, cy],           # Normalizovaný centroid
    "complexity": {
        "avg_segment_length_mm": float,
        "curvature_index": float,
        "sharp_corners_count": int,
        "total_direction_changes": int
    }
}
```

### 3.4 Binary reader — kompletní specifikace

**GEOMETRY_SIG = `\x01\x00\x01\x00\x00\xff\xff\xff`** (8 bajtů)

Tato signatura označuje začátek každého elementu v binárním VCF souboru.

**Layer block struktura** (610 B pro v1.0.013, 210 B pro v1.0.012):

```
Offset  | Size | Typ     | Pole
--------|------|---------|-----------------------------
+0      | 4    | uint32  | output_flag (1=aktivní, 0=vizuální)
+4      | 4    | uint32  | speed (BGR-shifted color?)
+8      | 8    | float64 | speed_mms (IEEE 754 LE)
+16-28  | 12   | -       | padding / neznámé
+28     | 4    | int32   | cutter_type_raw (& 0xFFFF = type)
+32-76  | 44   | -       | padding
+76     | 8    | float64 | start_height_h1_mm
+84     | 4    | int32   | feed_num (počet podávání)
+88     | 4    | -       | padding
+92     | 8    | float64 | end_height_h2_mm
+100    | 2    | uint16  | direction_raw (V-slot: 0=Left, 1=Right, 2=Both)
+102    | 8    | float64 | v_slot_width_comp_mm
+110    | 8    | float64 | starting_extension_mm
+118    | 8    | float64 | ending_extension_mm
```

Barva vrstvy je kódována v `speed` poli (offset +4) jako `uint32` ve formátu BGR:
```python
color_val = struct.unpack_from('<I', binary_data, S-8)[0]  # offset +4
# Pro mapování geometrie:
expected_geom_color = (color_val << 8) & 0xffffffff
```

**74B segment — geometrický element:**

```
Offset | Size | Typ     | Pole
-------|------|---------|------------------------------
+0     | 8    | bytes   | GEOMETRY_SIG (01 00 01 00 00 ff ff ff)
+8     | 4    | uint32  | color (BGR shift pro mapování vrstvy)
+12    | 2    | -       | padding
+14    | 8    | float64 | start_x (nebo pro kruh: 2. referenční bod x)
+22    | 8    | float64 | start_y
+30    | 8    | float64 | end_x (nebo pro kruh: střed x)
+38    | 8    | float64 | end_y
+46    | 8    | float64 | arc_d0 (Catmull-Rom control point nebo 0.0)
+54    | 8    | float64 | arc_d1
+62    | 8    | float64 | arc_d2 (nebo jiné parametry)
+70    | 4    | uint32  | type_id (0=line, 1=circle/polygon)
+74    |      |         | (pokračuje další segment)

HEADER blok (první segment elementu):
+45    | 4    | uint32  | type_id (na pozici p = pos+45)
+49    | 4    | uint32  | pt_count (počet segmentů)
+53    | 4    | uint32  | subtype (& 0xFFFF = 3 pro arcs)
```

**Nástrojové ID:**
```python
CUTTER_MAP = {0: "Vibrate cutter", 1: "Wheel", 2: "Milling cutter", 3: "V-slot", 4: "Vibrate cut"}
CUTTER_ID_MAP = {"Vibrate cutter": 1, "Wheel": 2, "Milling cutter": 3, "V-slot": 4, "Vibrate cut": 5}
```

### 3.5 Import graph a package architektura

Na základě analýzy `SYSTEQ_VCF_STACK_ANATOMY_V2.md` a `technicke_zadani_Moodpasta.md` platí pro VcfWriter následující **import graph constraints**:

```
vcf_writer.py
  ├── vcf_binary_reader.py   (encoding utilities: struct.pack, float64, uint32)
  ├── vcf_config.py           (machine_profile pro time prediction, panel_formáty)
  └── vcf_geometry.py         (pouze geometrické utility: bbox, containment, length)
       └── NESMÍ záviset na: Knowledge_base.engine, app.py, streamlit
```

**Důvody:**
1. **Package separation** — `vcf_parser/` a `systeq_kb/` jsou oddělené balíčky dle ISSUE-HIGH-04. KB engine je samostatný deployment.
2. **KB engine je volitelná závislost** — VcfWriter musí fungovat i bez KB (pure serializace).
3. **app.py/Streamlit je UI vrstva** — writer je library, ne UI komponenta.

**Cílová package struktura:**
```
vcf_parser/                  # pip-installable balíček
    __init__.py              # from vcf_parser import parse, write
    _reader.py               # existující vcf_binary_reader.py
    _writer.py               # VcfWriter třída (tento návrh)
    _geometry.py             # geometrické utility (bbox, containment)
    _config.py               # config loading
systeq_kb/                   # samostatný balíček
    engine.py                # KnowledgeBaseEngine
    models.py                # datové modely
    rules.json               # pravidla
```

---

## 4. Binární formát VCF — kompletní specifikace z RE

### 4.1 Struktura souboru

```
┌─────────────────────────────────────┐
│ FILE HEADER                         │  ~200-600 B
│  • Magic: "RDVCUT" / "VER1.0.012"  │
│  • Verze, metadata, DXF cesta       │
├─────────────────────────────────────┤
│ LAYER BLOCKS (N × block_size)       │  N × 610 B (v1.0.013)
│  • speed, color, cutter, H1/H2, ... │       nebo 210 B (v1.0.012)
│  • is_output_yes flag               │
├─────────────────────────────────────┤
│ GEOMETRY (M × 74B segment)          │  M × 74 B
│  • GEOMETRY_SIG                     │
│  • float64[] coordinates            │
│  • type_id, pt_count, subtype       │
│  • arc_data (d0,d1,d2)              │
├─────────────────────────────────────┤
│ FOOTER                              │  ~50 B
│  • EOF marker                       │
│  • padding                          │
└─────────────────────────────────────┘
```

### 4.2 Detekce verze

```python
version = "1.0.013"  # default
if b"RDVCUTFILEVER1.0.012" in binary_data or b"VER1.0.012" in binary_data:
    version = "1.0.012"
    block_size = 210  # pro v1.0.012
else:
    block_size = 610  # pro v1.0.013
```

### 4.3 Extrakce aktivních vrstev

Algoritmus:
1. Najdi všechny výskyty `GEOMETRY_SIG` → získej `geom_colors` (množina barev)
2. První výskyt = `first_geometry_pos`
3. Pro každou vrstvu k=1..31: `pos = first_geometry_pos - k * block_size`
4. Pokud `pos >= 0`: parsuj layer blok na pozici `pos`
5. Validace: speed 1-2000 mm/s, speed % 5 == 0, color match s geometrií
6. Vrstvy se reversují (byly prohledávány od konce)

### 4.4 Parsování geometrie — 74B segmentová smyčka

```python
while True:
    pos = binary_data.find(GEOMETRY_SIG, offset)
    if pos == -1: break
    
    p = pos + 45  # hlavička elementu
    type_id = struct.unpack_from('<I', binary_data, p)[0]
    pt_count = struct.unpack_from('<I', binary_data, p+4)[0]
    subtype = struct.unpack_from('<I', binary_data, p+8)[0]
    
    # Typ elementu dle type_id a subtype
    if type_id == 1 and (subtype & 0xffff) == 3:
        if pt_count > 8:  geom_type = "Polygon"
        else:             geom_type = "Circle"
    elif type_id == 0:
        geom_type = "Line" if pt_count == 1 else "Polyline"
    elif type_id == 1:
        geom_type = "Polygon"
    
    # Circle: poloměr = |x2c - x1c|, délka = 2πR
    # Polygon/Polyline: Σ hypot(x2-x1, y2-y1) pro každý segment
```

### 4.5 Kružnice — speciální případ

Kružnice v 74B segmentu:
```python
x1c, y1c = body[pos+14:pos+22]  # první referenční bod
x2c, y2c = body[pos+30:pos+38]  # druhý referenční bod (střed)
radius = abs(x2c - x1c)          # poloměr z X souřadnic
cx, cy = x2c, y1c                # střed
length = 2 * math.pi * radius    # obvod
```

Kružnice je uložena jako 4 kvadrantové oblouky, ale parser ji rekonstruuje jako jeden element.

### 4.6 ARC data — Catmull-Rom spline

Subtype & 0xFFFF == 3 indikuje arc segment:
```python
d0, d1, d2 = struct.unpack_from('<ddd', binary_data, seg_offset + 46)
# d0, d1 = control point pro arc
# d2 = rezervováno
```

`reconstruct_element_vertices()` používá `_merge_consecutive_arcs()`:
1. Seskupí po sobě jdoucí segmenty se stejnými arc parametry
2. Fitne kružnici třemi body (start, control, end)
3. Generuje interpolované body na kružnici
4. Nebo použije Catmull-Rom centripetal spline

---

## 5. Inference Workflow: LLM-asistované RE

### 5.1 Dvouvrstvá inference architektura

```
┌─────────────────────────────────────────────────────────────┐
│                     VRSTVA 1: Agentní API                    │
│                   (OpenCode CLI + LLM API)                   │
│                                                             │
│  Primární nástroj pro:                                      │
│  • Generování a refactoring kódu                            │
│  • Návrh architektury                                       │
│  • RE analýza binárních dat                                 │
│  • Tvorba testů                                             │
│  • Cross-validace mezi modely                              │
│                                                             │
│  Použité modely: DeepSeek V4, Gemini Flash 3.5              │
│  Komerční tier: Google Plus + DeepSeek API (desítky USD)   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     VRSTVA 2: Chat UI                        │
│                   (Webové rozhraní)                          │
│                                                             │
│  Podpůrný nástroj pro:                                      │
│  • Rychlé iterační dotazy                                   │
│  • Cross-validaci mezi modely                               │
│  • Sémantický trimming textů                                │
│  • Tvorbu jednoduchých Python skriptů                       │
│  • Inspiraci / encyklopedické rešerše                       │
│                                                             │
│  Použité modely: Claude, ChatGPT, Gemini, Groq              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 10 Golden Rules pro LLM spolupráci

| # | Pravidlo | Popis | Porušení detekovaná |
|---|---|---|---|
| 1 | **Determinismus** | Stejný vstup = stejný výstup. Žádný random seed | 0 |
| 2 | **Config > Code** | Parametry do JSON/JSON konfigu, nikdy hardcoded | 3× hardcoded |
| 3 | **Test-First** | Před implementací test, který selže | 0 |
| 4 | **Epistemic Transparency** | Každá hodnota má `validation_status` | 0 |
| 5 | **Logging > Print** | Strukturovaný logging (logger.info/debug/warning) | 0 |
| 6 | **Type Hints** | Plné typové anotace | 0 |
| 7 | **Version Stamping** | Každý modul má verzi | 1× missing |
| 8 | **No Magic Numbers** | Konstanty s pojmenováním a zdůvodněním | 0 |
| 9 | **Blacklist** | Zakázané patterny: `eval`, `random`, `time.sleep`, pevné cesty | 0 |
| 10 | **Handoff Before Break** | Před pauzou vygenerovat handoff JSON | 15+ handoffů |

### 5.3 Handoff formát

Strojově čitelný JSON pro předávání kontextu mezi iteracemi:

```json
{
  "project_context": {
    "version": "v22",
    "last_module": "vcf_geometry.py",
    "known_issues": ["circle_regression_fixed_v15"],
    "next_priority": "VcfWriter implementation"
  },
  "version_history": [
    {"v1": "Metadata extraction"},
    {"v10": "Fatální chyba — falešná délka z paddingu"},
    {"v16": "Univerzální parser — 99.99% přesnost"}
  ],
  "test_suite": {
    "total": 11,
    "passed": 11,
    "golden_master_files": ["1ks.json", "25_circles_only.json", ...]
  },
  "lessons_learned": [
    "LightBurn DXF ≠ AutoCAD DXF — proprietární CAM paleta",
    "INSERT bloky = 50% ztracené geometrie bez block explosion",
    "Golden master testy odhalily regresi kružnic"
  ]
}
```

### 5.4 RE cyklus: 6-fázový proces

```
Fáze 0: Tacit Knowledge Acquisition (9 dní v provozu)
    │  Stínování technologa, ruční deníky, digitalizace know-how
    ▼
Fáze 1: Synthetic Ground Truth (trial VCutWorks + LightBurn)
    │  Vytvoření testovacích souborů se známou geometrií
    │  100×100 mm čtverec, r=500 mm kruh, diamant
    ▼
Fáze 2: Differential Analysis (pair diff)
    │  hex_diff(A, B) kde se liší v 1 parametru
    │  → identifikace offsetů pro speed, color, cutter, H2
    ▼
Fáze 3: Physical Validation (CNC plotr)
    │  Porovnání predikce s reálným časem na stroji
    │  Kalibrace kinematických konstant (t_corner, t_lift)
    ▼
Fáze 4: Ground Truth Export (golden master)
    │  Uložení JSON baseline pro regresní testy
    │  7 baselinů, každá změna = selhání testu
    ▼
Fáze 5: Regression Testing (pytest)
    │  8 kategorií: smoke, determinism, golden master, geometry,
    │  config, binary reader, KB overrides, time predictor
    │  → 8/8 PASS
```

### 5.5 SNR princip (Signal-to-Noise Ratio)

**Jádrové axioma:** Hlavní hodnota není počet nalezených chyb, ale jistota, že nalezená chyba = skutečný fyzikální defekt.

**Implementace v kódu:**
1. **Nulový vizuální stav** = čistý výkres. Výchozí stav je klid.
2. **INFO se nikdy nezobrazuje na obrazovce** (prevence alarm overload)
3. **Max 3 typy varování na objekt** (Miller's Law)
4. **Density filter:** Pokud 5+ po sobě jdoucích segmentů < 1 mm tvoří křivku → degrade WARNING na INFO

```python
def filter_micro_segment_clusters(findings, elements, consecutive_threshold=5, angle_threshold_deg=15.0):
    """Detekuje, zda mikrosegmenty tvoří organickou křivku (nikoliv artefakt)."""
    for f in findings:
        if len(run_indices) >= consecutive_threshold:
            # Zkontroluj úhlovou spojitost
            if is_curve:
                f["curve_artifact"] = True  # → degrade WARNING na INFO
```

### 5.6 Epistemický rámec

Každé pravidlo v Knowledge Base nese metadata o jistotě:

```python
class RuleClass(Enum):
    CLASS_A_PHYSICAL = "CLASS_A"    # Fyzikální zákon (conf: 0.99)
    CLASS_B_EMPIRICAL = "CLASS_B"   # Empirické ověření (conf: 0.90-0.95)
    CLASS_C_HEURISTIC = "CLASS_C"   # Heuristika (conf: 0.80-0.90)
    CLASS_D_HYPOTHESIS = "CLASS_D"  # Hypotéza (conf: 0.70-0.85)

class ValidationStatus(Enum):
    ACCEPTED     # Ověřeno empiricky i teoreticky
    CONDITIONAL  # Platí za předpokladů
    REJECTED     # Vyvráceno, ponecháno pro referenci
    UNKNOWN      # Dosud neověřeno

class EpistemicMetadata:
    rule_id: str
    description: str
    source: str           # Odkud pravidlo pochází
    confidence: float     # 0.0 - 1.0
    validation_status: ValidationStatus
    rule_class: RuleClass
```

**ECI (Epistemic Confidence Index):**
```python
ECI = empirical_count / total_count  # Podíl empiricky ověřených konstant
# ECI > 0.8 = produkčně spolehlivý
# ECI < 0.5 = stále ve fázi vývoje
```

---

## 6. Zápis VCF: Návrh VcfWriter architektury

### 6.1 Architektura — třídy

```python
class VcfLayer:
    """
    Ekvivalent RuidaLayer z jnweiger/ruida-laser.
    Místo laser power: tool-specific parametry pro oscilační nůž.
    """
    def __init__(self, paths=None, speed=None, cutter_type="Vibrate cutter",
                 h1=2.0, h2=12.0, color=[255,0,0], direction="N/A",
                 start_ext=0.0, end_ext=0.0, is_output=True):
        self._paths = paths          # list[list[(x,y)]] v mm
        self._bbox = None            # [[xmin,ymin],[xmax,ymax]] auto-výpočet
        self._speed = speed          # mm/s
        self._cutter_type = cutter_type  # "Vibrate cutter" | "V-slot" | ...
        self._h1 = h1                # safety height mm
        self._h2 = h2                # tip height mm
        self._color = color          # [R, G, B]
        self._direction = direction  # "Left" | "Right" | "Cut both side" | "N/A"
        self._start_ext = start_ext  # starting overcut mm
        self._end_ext = end_ext      # ending overcut mm
        self._is_output = is_output  # True = active, False = visual only


class VcfWriter:
    """
    Analog k Ruida.write() z jnweiger/ruida-laser.
    Generuje VCF binární soubor z JSON specifikace.
    """
    VERSION = "1.0"
    
    def __init__(self, layers=None, version="1.0.013"):
        self._layers = layers or []
        self._version = version
        self._globalbbox = None
    
    def add_layer(self, layer: VcfLayer):
        """Přidá vrstvu do seznamu."""
        self._layers.append(layer)
    
    def set(self, layers=None, globalbbox=None, version=None):
        """Hromadné nastavení."""
        if layers: self._layers = layers
        if globalbbox: self._globalbbox = globalbbox
        if version: self._version = version
    
    # ── Generování ──
    def header(self) -> bytes:
        """Generuje hlavičku souboru + layer bloky."""
    
    def body(self) -> bytes:
        """Generuje 74B segmenty geometrie."""
    
    def trailer(self) -> bytes:
        """Generuje patičku (EOF marker)."""
    
    def write(self, fd, scramble=False) -> None:
        """Složí header + body + trailer, zapíše do souboru."""
    
    # ── Encoding utilities ──
    @staticmethod
    def encode_header_block(layer: VcfLayer, block_size: int) -> bytes:
        """Zapouzdří layer do 610B (v1.0.013) nebo 210B (v1.0.012) bloku."""
    
    @staticmethod
    def encode_geometry_element(element_spec: dict) -> bytes:
        """Zapouzdří element do 74B segmentového bloku."""
    
    @staticmethod
    def encode_float64(value: float) -> bytes:
        """IEEE 754 double little-endian."""
        return struct.pack('<d', value)
    
    @staticmethod
    def encode_uint32(value: int) -> bytes:
        """uint32 little-endian."""
        return struct.pack('<I', value)
    
    @staticmethod
    def encode_color(color_val: int) -> bytes:
        """BGR uint32 pro layer header."""
        return struct.pack('<I', color_val)
```

### 6.2 Type mapping .rd → VCF

| .rd koncept | .rd encoding | VCF koncept | VCF encoding |
|---|---|---|---|
| `encode_number(num, 5, 1000)` | 5B base-128 μm | IEEE 754 double | `struct.pack('<d', mm)` 8B |
| `encode_relcoord(n, 2)` | 2B base-128 μm | IEEE 754 double | `struct.pack('<d', mm)` 8B |
| `encode_percent(n)` | 2B uint14 (0x3FFF) | N/A | Cutter type ID |
| `encode_color([R,G,B])` | 5B base-128 | BGR uint32 | `struct.pack('<I', val)` 4B |
| Laser power | `c6 01/02/...` + percent | H1/H2 height | `struct.pack('<d', h)` 8B |
| Laser frequency | `c6 60` + number | Oscillation freq | `struct.pack('<d', freq)` 8B |
| Speed | `c9 02` + 5B number | Speed | `struct.pack('<d', mms)` 8B |

### 6.3 header() — generování hlavičky VCF

```python
def header(self) -> bytes:
    data = bytearray()
    
    # Magic + verze
    if self._version == "1.0.012":
        data += b"RDVCUTFILEVER1.0.012"
    else:
        data += b"VER1.0.013"
    
    # Výpočet globálního bboxu
    bbox = self._globalbbox or self._compute_global_bbox()
    
    # Layer bloky (v obráceném pořadí — od poslední k první)
    block_size = 210 if self._version == "1.0.012" else 610
    for layer in reversed(self._layers):
        data += self.encode_layer_block(layer, block_size)
    
    return bytes(data)
```

### 6.4 body() — generování 74B segmentů

```python
def body(self) -> bytes:
    data = bytearray()
    
    for layer_idx, layer in enumerate(self._layers):
        if not layer._paths:
            continue
        
        for path in layer._paths:
            element_data = bytearray()
            
            # GEOMETRY_SIG
            element_data += GEOMETRY_SIG
            
            # Color (BGR shift pro mapování vrstvy)
            color_val = (layer._color[2] << 24) | (layer._color[1] << 16) | \
                        (layer._color[0] << 8)
            element_data += struct.pack('<I', color_val)
            element_data += struct.pack('<H', 0)  # padding 2B
            
            # Délka dráhy (pro kompletnost, ale parser ji počítá z bodů)
            total_length = sum(
                math.hypot(path[i][0]-path[i-1][0], path[i][1]-path[i-1][1])
                for i in range(1, len(path))
            )
            
            # Pro každý segment v path
            for i in range(len(path) - 1):
                seg_data = bytearray()
                
                # Start point
                seg_data += struct.pack('<d', path[i][0])
                seg_data += struct.pack('<d', path[i][1])
                # End point
                seg_data += struct.pack('<d', path[i+1][0])
                seg_data += struct.pack('<d', path[i+1][1])
                # Arc data (0.0 = rovný segment)
                seg_data += struct.pack('<ddd', 0.0, 0.0, 0.0)
                # Type (0 = line segment)
                seg_data += struct.pack('<I', 0)
                
                element_data += seg_data
            
            # Hlavička elementu na offsetu pos+45
            pt_count = len(path) - 1
            element_data[45:49] = struct.pack('<I', 0)     # type_id (0=open)
            element_data[49:53] = struct.pack('<I', pt_count)  # pt_count
            element_data[53:57] = struct.pack('<I', 0)     # subtype
            
            data += element_data
    
    return bytes(data)
```

### 6.5 trailer() — generování patičky

```python
def trailer(self) -> bytes:
    data = bytearray()
    # EOF marker (obdoba d7 z .rd)
    data += b'\xd7'
    # Padding na zarovnání
    return bytes(data)
```

### 6.6 Layer block encoder

```python
@staticmethod
def encode_layer_block(layer: VcfLayer, block_size: int) -> bytes:
    """Generuje 610B/210B layer blok."""
    block = bytearray(block_size)
    
    # Output flag (offset 0)
    struct.pack_into('<I', block, 0, 1 if layer._is_output else 0)
    
    # Color val pro mapování (BGR shift)
    color_bgr = (layer._color[2] << 16) | (layer._color[1] << 8) | layer._color[0]
    struct.pack_into('<I', block, 4, color_bgr)
    
    # Speed (offset 8)
    struct.pack_into('<d', block, 8, float(layer._speed))
    
    # Cutter type (offset 28+4 = 32)
    cutter_id = CUTTER_ID_MAP.get(layer._cutter_type, 1)
    struct.pack_into('<i', block, 32, cutter_id)
    
    # Start height H1 (offset 76)
    struct.pack_into('<d', block, 76, layer._h1)
    
    # Feed number (offset 84)
    struct.pack_into('<i', block, 84, 1)  # default
    
    # End height H2 (offset 92)
    struct.pack_into('<d', block, 92, layer._h2)
    
    # V-slot direction (offset 100, pouze pro V-slot)
    if layer._cutter_type == "V-slot":
        dir_id = DIR_ID_MAP.get(layer._direction, 0)
        struct.pack_into('<H', block, 100, dir_id)
        struct.pack_into('<d', block, 102, 0.0)  # v_slot_comp
    
    # Extensions (offset 110, 118)
    struct.pack_into('<d', block, 110, layer._start_ext)
    struct.pack_into('<d', block, 118, layer._end_ext)
    
    return bytes(block)
```

### 6.3 Package API specifikace

Na základě `technicke_zadani_Moodpasta.md` (Modul A: VCF Parser library) je definováno cílové API:

```python
from vcf_parser import parse, write

# ── Reader API (existující, stabilní) ──
result: dict = parse("/cesta/k/souboru.vcf")
# result obsahuje: layers, elements, canvas, time_prediction, manufacturing_intelligence

# ── Writer API (tento návrh) ──
write(specification: dict, output_path: str) -> None
write(specification: dict, output_path: str, version: str = "1.0.013") -> None
write(specification: dict, output_path: str, version: str = "1.0.013", scramble: bool = False) -> None
```

**Vstupní specifikace** (kompatibilní s výstupem `parse()`):

```python
spec = {
    "layers": [
        {
            "cutter_type": "Vibrate cutter",
            "speed_mms": 800.0,
            "start_height_h1_mm": 2.0,
            "end_height_h2_mm": 12.0,
            "color_rgb": [255, 0, 0],
            "direction": "N/A",
            "starting_extension_mm": 0.0,
            "ending_extension_mm": 0.0,
            "is_output_yes": True
        }
    ],
    "elements": [
        {
            "geom_type": "Polyline",
            "vertices": [(x1, y1), (x2, y2), ...],
            "layer_index": 0,
            "is_output_yes": True
        }
    ],
    "canvas_width_mm": 2790.0,
    "canvas_height_mm": 1200.0,
    "material_thickness_mm": 12.0,
    "version": "1.0.013"
}
```

**Návratová hodnota** `write()`:
- `None` při úspěchu
- `VcfWriterError` (nebo podtřídy) při chybě:
  - `InvalidGeometryError` — nevalidní geometrie (neuzavřené smyčky, self-intersection)
  - `UnsupportedFeatureError` — nepodporovaný cutter_type, verze
  - `SerializationError` — selhání binary encoding

**Roundtrip kontrakt:**
```python
parsed = parse("input.vcf")
spec = strip_metadata(parsed)  # odstranit timestamp, engine_ver, magic
write(spec, "output.vcf")
reparsed = parse("output.vcf")
assert reparsed["layers"] == parsed["layers"]
assert reparsed["elements"] == parsed["elements"]
# Povolené rozdíly: timestamp, engine_ver, magic, file_hash
```

---

## 7. Epistemický rámec a validation framework

### 7.1 Testovací infrastruktura

| Test | Co ověřuje | Kritérium |
|---|---|---|
| `test_smoke.py` | Parser nespadne na žádném vstupu | `elements > 0` |
| `test_determinism.py` | Stejný vstup = identický výstup | `dictdiff == {}` |
| `test_golden_master.py` | Regresní ochrana (7 baselinů) | Exaktní JSON shoda |
| `test_geometry.py` | Geometrické utility (bbox, containment) | Unit testy |
| `test_binary_reader.py` | Binární reader, COLOR_MAP, CUTTER_MAP | Unit testy |
| `test_time_predictor.py` | Predikce času | `format_time` |

**Výsledek:** 8/8 kategorií PASS, 99.99% přesnost geometrie, ±2-5% časová predikce.

### 7.2 Detekční taxonomie (20 typů defektů)

**Třída A — Grafické chyby:**
| # | Kód | Popis | Severita |
|---|---|---|---|
| 1 | EDGE_MERGE_MISSING | Chybějící napojení hran | WARNING |
| 2 | UNCLOSED_LOOP | Neuzavřená smyčka | INFO-CRITICAL |
| 3 | MICRO_SEGMENT | Mikrosegmenty < 1 mm | WARNING |
| 4 | ZERO_LENGTH_SEGMENT | Segment délky 0 | WARNING |
| 5 | SELF_INTERSECTION | Křížení se sebou samým | CRITICAL |
| 6 | DUPLICATE_ELEMENT | Duplicitní element | WARNING |
| 7 | SPIKE_DETECT | Náhlá změna směru > 90° | WARNING |
| 8 | ELEMENT_OVERLAP | Překryv elementů | WARNING |
| 9 | DEGENERATE_SHAPE | Degenerovaný tvar | WARNING |

**Třída B — Technologické chyby:**
| # | Kód | Popis | Severita |
|---|---|---|---|
| 10 | SEQUENCE_LAYER_ERROR | Špatné pořadí vrstev | CRITICAL |
| 11 | SEQUENCE_NESTING_ERROR | Špatné pořadí elementů | CRITICAL |
| 12 | VACUUM_FIXATION_RISK | Malá plocha → fixace | WARNING |
| 13 | H2_SUBOPTIMAL | Suboptimální H2 | WARNING |
| 14 | H2_NO_CUT_THROUGH | Nedoříznutí | CRITICAL |
| 15 | NESTING_CLEARANCE | Malá vůle | WARNING |
| 16 | TAB_OVERLAP | Překryv tabů | WARNING |
| 17 | LAYER_INCONSISTENCY | Nekonzistentní vrstvy | WARNING |
| 18 | ORPHAN_ELEMENT | Sirotčí element | INFO |
| 19 | ASYMMETRIC_PAIR | Nesymetrický pár | INFO |
| 20 | NEAR_MISS_GAP | Téměř uzavřená mezera | INFO |

**Třída C — NC code chyby:**
| # | Kód | Popis | Severita |
|---|---|---|---|
| 21 | COLOR_MAP_MISMATCH | Barva neodpovídá vrstvě | WARNING |
| 22 | AGGREGATED_JOB | Agregovaná zakázka | INFO |
| 23 | UNKNOWN_VERSION | Neznámá verze | WARNING |
| 24 | CORRUPT_GEOMETRY | Poškozená geometrie | CRITICAL |
| 25 | UNCONNECTED_INTERNAL_DECOR | Nedotažená dekorativní linie | CRITICAL |

---

## 8. Mapování .rd ↔ .vcf pro zpětný zápis

### 8.1 Co je identické (lze přímo převzít)

| Komponenta | Zdroj | Důvod |
|---|---|---|
| `encode_float64()` | `struct.pack('<d', v)` | Oba formáty používají IEEE 754 double LE |
| `encode_uint32()` | `struct.pack('<I', v)` | Oba formáty používají uint32 LE |
| Struktura hlavičky | jnweiger `header()` | Global bbox + per-layer blocks + trailing settings |
| Struktura těla | jnweiger `body()` | Per-layer prolog + path geometry |
| Struktura patičky | jnweiger `trailer()` | EOF marker |
| Výpočet bboxu | jnweiger `boundingbox()` | min/max z paths |
| BFS clustering | vlastní `group_elements()` | Detekce agregovaných zakázek |
| KB engine | vlastní `KnowledgeBaseEngine` | Validace pravidel |

### 8.2 Co je odlišné (vyžaduje VCF-specific implementaci)

| Komponenta | .rd (laser) | .vcf (nůž) | Změna |
|---|---|---|---|
| **Scrambling** | `scramble_bytes(data)` | Žádný scramble | Odebrat celou vrstvu |
| **Geometrie** | Proměnlivé commandy (3-11B) | Fixní 74B segmenty | Nový `encode_74B_segment()` |
| **Souřadnice** | `int_35` v μm (5B base-128) | `float64` v mm (8B LE) | `struct.pack('<d', mm)` |
| **Laser power** | `c6 01` + `encode_percent(p)` | Nahrazeno H1/H2 | Tool-specific floats |
| **Speed** | `c9 02` + `encode_number(speed, 5, 1000)` | `float64` v mm/s | `struct.pack('<d')` |
| **Color** | `ca 06 layer color` (5B base-128) | BGR uint32 v layer bloku | `struct.pack('<I', bgr)` |
| **Magic sig** | `d2 9b fa` (scrambled) | `RDVCUT` / `VER1.0.01x` | Textový header |
| **Block size** | N/A (proměnlivé commandy) | 210B / 610B layer bloky | Fixní blok |
| **GEOMETRY_SIG** | N/A | `\x01\x00\x01\x00\x00\xff\xff\xff` | 8B signature |
| **Cutter types** | N/A (laser) | `CUTTER_MAP` (5 typů) | Nový enum |

### 8.3 Implementační strategie

**Fáze 1 — Scaffolding (1 den):**
- Vytvořit `VcfWriter` třídu s prázdnými `header()`, `body()`, `trailer()`
- Importovat encoding utilities z `vcf_binary_reader.py`
- Naimplementovat `encode_layer_block()` a `encode_74B_segment()`

**Fáze 2 — Header generace (1 den):**
- Magic + verze
- Layer bloky (obrácené pořadí, RE engineering)
- Validace: porovnání binárního výstupu s existujícím VCF souborem (hex diff)

**Fáze 3 — Body generace (1 den):**
- 74B segmentová smyčka
- Typ dispatch: Circle / Polygon / Polyline / Line
- ARC data (pro subtype & 0xFFFF == 3)

**Fáze 4 — Roundtrip test (1 den):**
```python
VCF → VcfParser → JSON → VcfWriter → output.vcf → VcfParser → JSON2
assert json_diff(JSON, JSON2) == {}  # kromě timestamp/metadata
```

**Fáze 5 — VCutWorks validace (1 den):**
- Otevřít vygenerovaný VCF v VCutWorks
- Zkontrolovat: vrstvy, geometrie, barvy, parametry
- Spustit Preview, porovnat čas

### 8.4 Rizika a mitigace

| Riziko | Pravděpodobnost | Dopad | Mitigace |
|---|---|---|---|
| Padding data neidentická po roundtripu | Střední | Nízký | Ignorovat padding při diff |
| VCutWorks odmítá soubor (CRC/validace) | Střední | Vysoký | CRC reverz z existujících souborů |
| Verze formátu se liší (v1.0.012 vs 013) | Střední | Střední | Detekce verze + block_size |
| Neznámý footer/checksum | Nízká | Vysoký | Template-based (kopírovat z existujícího) |
| VCutWorks kontroluje timestamp/metadata | Nízká | Střední | Kopírovat z template |

### 8.5 Known issues pre-load

Na základě katalogu issues z `SYSTEQ_VCF_STACK_ANATOMY_V2.md` existují následující **architektonická omezení**, která VcfWriter musí respektovat:

| Issue | Kategorie | Popis | Dopad na VcfWriter |
|---|---|---|---|
| **ISSUE-CRIT-03** | CRITICAL | `machine_profile.json` není kalibrován (kinematické konstanty = defaulty) | Time prediction vrací ±5–15 % místo ±2–5 %. VcfWriter musí fungovat i bez validního profilu — fallback na default. |
| **ISSUE-HIGH-04** | HIGH | `vcf_geometry.py` je monolit (1197 ř., detekce + utility smíchané) | VcfWriter smí používat pouze geometrické utility (bbox, containment, length). Detekční funkce (micro_segments, orphan, unclosed_loop) jsou KB závislost — writer je nesmí importovat. |
| **ISSUE-HIGH-01** | HIGH | Chybějící `parse()` API — engine je volán jako třída, ne jako funkce | VcfWriter musí od začátku definovat čisté API `write(spec, path)`, ne skrze instanci třídy. |
| **ISSUE-MED-05** | MED | Testy závisí na binárních VCF souborech v `tests/` | VcfWriter roundtrip testy potřebují generovat vlastní VCF, ne záviset na externích vzorcích. |

**Mitigace:**
- VcfWriter konstruktor akceptuje volitelný `machine_profile: dict = None` — pokud není, použije se default
- Time prediction je volitelná komponenta writeru (lze vypnout)
- Writer negeneruje detekce defektů — to je zodpovědnost KB enginu, ne writeru
- Writer validuje vlastní výstup (geometrická korektnost), ne technologická rizika

---

## 9. Závěr a doporučení

### 9.1 Stav projektu

| Komponenta | Status | Poznámka |
|---|---|---|
| **VcfParser** (čtení) | ✅ Produkční v22 | 99.99% přesnost, GCP Cloud Run |
| **KB Engine** (validace) | ✅ Produkční | 20 typů defektů, 4 třídy |
| **Time Predictor** | ✅ Produkční | ±2-5% přesnost |
| **Streamlit UI** | ✅ Produkční | HUD+MFD, role-switching |
| **ERP integrace** | ✅ Produkční | Odoo CSV, Google Sheets |
| **VcfWriter** (zápis) | ❌ Chybí | Tento dokument = návrh |
| **Write roundtrip test** | ❌ Chybí | Závisí na VcfWriter |

### 9.2 Doporučené priority

1. **VcfWriter implementace** (5 dní) — scaffold + header + body + trailer
2. **Roundtrip test** (1 den) — golden master pro write
3. **VCutWorks validace** (1 den) — otevřít vygenerovaný soubor
4. **Template-based generování** (2 dny) — parametrické zakázky
5. **Automatické opravy defektů** (3 dny) — merge, uzavření smyček, sekvence

### 9.3 Klíčová ponaučení

1. **VCF není .rd se scramblem, ale deterministická serializace.** To zjednodušuje zápis.
2. **74B segmenty jsou fixní, ne proměnlivé commandy.** Jiný přístup k path → binary.
3. **Layer bloky jsou v obráceném pořadí od konce geometrie.** RE objev.
4. **Barva je BGR-shifted uint32, ne base-128 color.** Jiný encoding.
5. **H1/H2 jsou float64, ne base-128.** Nástrojové parametry, ne laser power.
6. **Existující kód lze z ~70 % převzít** z jnweiger/ruida-laser a meerk40t.

---

*Dokument vytvořen 26. 6. 2026. Revize dle potřeby.*