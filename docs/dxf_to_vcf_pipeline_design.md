# DXF → VCF Pipeline Design

**Version:** 1.0  
**Date:** 27 June 2026  
**Author:** dev (LLM-augmented design review)  
**Status:** Draft / Pre-implementation

---

## Table of Contents

1. [Pipeline Overview](#1-pipeline-overview)
2. [Data Flow Architecture](#2-data-flow-architecture)
3. [Component Specification](#3-component-specification)
4. [Mapping Config Specification](#4-mapping-config-specification)
5. [Entity Conversion Matrix](#5-entity-conversion-matrix)
6. [Implementation Steps](#6-implementation-steps)
7. [Test Strategy](#7-test-strategy)
8. [Risk Register](#8-risk-register)

---

## 1. Pipeline Overview

```
                    ┌──────────────────┐
                    │   LightBurn UI   │
                    │  (kreslení DXF)  │
                    └────────┬─────────┘
                             │ export DXF
                             ▼
                    ┌──────────────────┐
                    │   DXF soubor     │
                    │  (.dxf ASCII)    │
                    └────────┬─────────┘
                             │
                             ▼
               ┌──────────────────────────┐
               │  dxf_geometry_indexer    │
               │  (dxf_integrace repo)    │
               │  - ezdxf reader          │
               │  - entity extraction     │
               │  - layer card            │
               └────────┬─────────────────┘
                        │ index_dxf()
                        ▼
               ┌──────────────────────────┐
               │   Pipeline adaptér       │
               │   (nový modul)           │
               │                          │
               │   1. Získat entities     │
               │   2. Mapovat ACI→VCF     │
               │      parametry           │
               │   3. Sestavit VCF spec   │
               └────────┬─────────────────┘
                        │ write(spec)
                        ▼
               ┌──────────────────────────┐
               │  vcf_parser._writer      │
               │  (Vcf-compiler repo)     │
               │  - serializace na VCF    │
               └────────┬─────────────────┘
                        │
                        ▼
               ┌──────────────────────────┐
               │   Výstupní .VCF soubor   │
               │   (připraveno k řezu)    │
               └──────────────────────────┘
```

### Principle

Two existing, independently tested libraries are connected by a thin adaptér layer:

| Layer | Repository | Technology | Status |
|---|---|---|---|
| DXF parser | `dxf_integrace` | `ezdxf`, pure Python | ✅ v2.3.0, 2072 ř., 5 test files |
| VCF writer | `Vcf-compiler` | Pure Python, struct | ✅ v1.0.0, 28 testů |
| **Adaptér** | `Vcf-compiler` (nový) | ~150 ř. | ❌ Neexistuje |

---

## 2. Data Flow Architecture

### 2.1 Raw data from DXF parser

`index_dxf(dxf_path, tool_config, keep_vertices=True)` returns:

```python
{
    "entities": [
        {
            "id": "E_0000",
            "type": "LWPOLYLINE",          # LINE, CIRCLE, ARC, SPLINE, ELLIPSE, POLYLINE
            "layer": "mainlayer",
            "color_index": 1,               # ACI 1-255
            "length_mm": 8240.0,
            "point_count": 8,
            "vertices": [(x1,y1), (x2,y2), ...],  # ONLY when keep_vertices=True
            "is_closed_loop": True,
            "bbox_mm": [...],
            "has_arcs": False,
            # ...
        },
        # ...
    ],
    "layer_card": {
        "colors": {
            "1": {
                "color_index": 1,
                "color_name": "Red",
                "entity_count": 1,
                "total_length_mm": 8240.0,
                "tool_config": {
                    "cutter_type": "Vibrate cutter",
                    "base_speed_mms": 150,
                    "direction": "N/A",
                    "h2_mm": -0.3,
                    "validation_status": "hypothesis",
                    "is_output": True,
                    "note": "Červená — vnější obrysy"
                },
                "is_mapped": True
            },
            "4": { ... }  # Cyan - 182 entities
        }
    },
    "layers": [   # DXF layer grouping (not ACI)
        {
            "name": "mainlayer",
            "color_index": 1,
            "entity_ids": ["E_0000", "E_0001", ...],
            # ...
        }
    ]
}
```

### 2.2 Target VCF spec format

```python
spec = {
    "layers": [
        {
            "cutter_type": "Vibrate cutter",    # z tool_config
            "speed_mms": 150.0,                  # z tool_config
            "start_height_h1_mm": 2.0,           # fallback / z config
            "end_height_h2_mm": -0.3,            # z tool_config (h2_mm)
            "color_rgb": [255, 0, 0],            # ACI → RGB lookup
            "direction": "N/A",                   # z tool_config
            "starting_extension_mm": 0.0,         # z tool_config
            "ending_extension_mm": 0.0,           # z tool_config
            "is_output_yes": True,                # z tool_config
            "number_of_feeding": 1,               # default 1
        }
    ],
    "elements": [
        {
            "geom_type": "Polyline",             # inferovaný z DXF type
            "vertices": [(x1,y1), (x2,y2), ...], # z DXF entity
            "layer_index": 0,                     # index do layers[] podle ACI
            "is_output_yes": True,
        }
    ]
}
```

### 2.3 ACI-to-VCF-layer mapping logic

The critical design decision: **grouping entities by ACI color index, not by DXF layer name.**

Reasoning:
- VCF writer matches elements to layers via `geom_color` (derived from `color_rgb`)
- ACI color is the only shared key between DXF entity attributes and VCF layer parameters
- `dxf_tool_config.json` already maps ACI → CNC tool params
- DXF layer names are often generic ("mainlayer", "0", "Layer_1") and carry no CNC meaning

**Edge case:** One DXF layer can contain multiple ACI colors. Solution: one VCF layer per unique ACI color present in the DXF, not per DXF layer name.

---

## 3. Component Specification

### 3.1 Pipeline adaptér — `vcf_parser._dxf_adapter.py`

**Interface:**

```python
def dxf_to_spec(
    dxf_path: str | Path,
    tool_config_path: str | Path | None = None,
    h1_default: float = 2.0,
    feed_count_default: int = 1,
) -> dict:
    """
    Parse DXF → apply tool mapping → return VCF-compatible spec dict.

    Args:
        dxf_path: Path to input DXF file
        tool_config_path: Path to vcf_compiler_map_config.json
        h1_default: Fallback H1 value if not in tool config
        feed_count_default: Fallback feed count

    Returns:
        spec dict ready for vcf_parser.write(spec, output_path)
    """
```

**Internal steps:**

```
1. Validate file exists, is .dxf
2. Import dxf_geometry_indexer_v2.index_dxf (or lazy import)
3. Call index_dxf(path, tool_config=loaded_config, keep_vertices=True)
4. If tool_config_path given: load JSON, pass as tool_config
5. Group entities by color_index (ACI)
6. For each ACI group:
   a. Look up tool_config mapping (fallback to heuristic)
   b. Resolve ACI → RGB color (static lookup table)
   c. Build VcfLayer-compatible dict
7. For each entity:
   a. Map DXF type → geom_type ("Polyline" for most)
   b. ARC/CIRCLE → decide: approximation vs. native
   c. Assign layer_index by ACI match
8. Build and return spec dict
```

### 3.2 ACI → RGB color mapping

```python
# Standard AutoCAD Color Index (ACI) to RGB
# Only ACI 1-9 cover 80%+ of real-world DXF files
ACI_TO_RGB = {
    0: (0, 0, 0),          # ByBlock
    1: (255, 0, 0),        # Red
    2: (255, 255, 0),      # Yellow
    3: (0, 255, 0),        # Green
    4: (0, 255, 255),      # Cyan
    5: (0, 0, 255),        # Blue
    6: (255, 0, 255),      # Magenta
    7: (255, 255, 255),    # White
    8: (128, 128, 128),    # Dark Gray
    9: (192, 192, 192),    # Light Gray
    30: (255, 165, 0),     # Orange
    52: (191, 255, 0),     # Lime
    92: (8, 145, 178),     # Azure
}
```

### 3.3 Geometry type mapping

| DXF type | VCF geom_type | Action |
|---|---|---|
| `LINE` | `Polyline` | 2 vertices: start→end |
| `LWPOLYLINE` | `Polyline` | Direct pass (already vertices) |
| `POLYLINE` | `Polyline` | Direct pass |
| `CIRCLE` | `Circle` nebo `Polyline` | Use VcfWriter.encode_circle_element() if circle, else 36-segment polyline |
| `ARC` | `Polyline` | Resample to N segments via bulge math |
| `SPLINE` | `Polyline` | Pass resampled vertices |
| `ELLIPSE` | `Polyline` | Pass resampled vertices |

**Circle decision:** The DXF indexer already approximates circles as 36-segment polylines. For VCF output, prefer the native `VcfWriter.encode_circle_element()` when the entity is a true `CIRCLE` type. The adaptér should detect this and call the appropriate encoder.

---

## 4. Mapping Config Specification

The mapping config defines how ACI colors translate to CNC cutting parameters.

**Location:** `vcf_compiler_map_config.json` (in project root or `vcf_parser/`)

### 4.1 Schema

```jsonc
{
  "_schema": "vcf_compiler_map_config_v1.0",
  "_description": "Mapování ACI barev z DXF na VCF parametry pro RDD6584G oscilační nůž",

  "aci_color_mapping": {
    "<ACI_index>": {
      "cutter_type": "Vibrate cutter | V-slot | Wheel | Milling cutter | Vibrate cut",
      "speed_mms": <float>,
      "direction": "Left | Right | Cut both side | N/A",
      "h1_mm": <float>,            // start_height_h1_mm (startovní výška)
      "h2_mm": <float>,            // end_height_h2_mm (negativní = pod úroveň materiálu)
      "vs_comp_mm": <float>,       // V-slot width compensation (jen pro V-slot)
      "start_extension_mm": <float>,
      "end_extension_mm": <float>,
      "is_output": <bool>,
      "number_of_feeding": <int>,

      "validation_status": "empirical | calibrated | hypothesis",
      "_note": "Popis účelu barvy v produkci"
    }
  },

  "defaults": {
    "h1_mm": 2.0,
    "number_of_feeding": 1,
    "fallback_cutter": "Vibrate cutter",
    "fallback_speed_mms": 200.0,
    "fallback_h2_mm": -0.3
  }
}
```

### 4.2 Initial seed values (from production VCF analysis)

These values were empirically derived from reverse-engineering production VCF files and cross-referencing with `dxf_tool_config.json` in the `dxf_integrace` repository.

| ACI | Color | Cutter | Speed (mm/s) | H2 (mm) | Direction | Extensions | Status |
|---|---|---|---|---|---|---|---|
| 1 | Red | Vibrate cutter | 150 | -0.3 | N/A | 0/0 | hypothesis |
| 2 | Yellow | V-slot | 300 | 6.0 | Left | 0/0 | empirical |
| 3 | Green | V-slot | 200 | 6.0 | Cut both side | 2.0/2.0 | empirical |
| 4 | Cyan | ambiguous* | 200 | varies | Cut both side | 2.0/2.0 | hypothesis |
| 5 | Blue | Vibrate cutter | 100 | -0.3 | N/A | 0/0 | empirical |
| 6 | Magenta | Vibrate cutter | 300 | -0.3 | N/A | 0/0 | calibrated |
| 7 | White/Black | Vibrate cutter | 200 | -0.3 | N/A | 0/0 | empirical |
| 30 | Orange | V-slot | 100 | 6.0 | Cut both side | 2.0/2.0 | calibrated |
| 52 | Lime | V-slot | 200 | 6.0 | Cut both side | 3.0/3.0 | hypothesis |
| 92 | Azure | V-slot | 300 | 6.0 | Cut both side | 10.0/10.0 | hypothesis |

*\*ACI 4 (Cyan) is ambiguous — resolved by point density heuristic: density >30 pts/m → Vibrate 50 mm/s, else V-slot 200 mm/s*

---

## 5. Entity Conversion Matrix

### 5.1 ARC handling

ARC entities in DXF have `radius`, `start_angle`, `end_angle`. The DXF indexer resamples them to N straight segments. For VCF, we can either:
- Pass the resampled polyline (lossy but simple)
- Store arc data in the 74B segment `d0, d1, d2` fields (requires RE of those fields)

**Recommendation for MVP:** Pass resampled polylines. The 74B arc fields are not yet understood.

### 5.2 Closed loops

Closed DXF entities (`is_closed_loop=True`) should NOT repeat the first vertex at the end. The VcfWriter `encode_geometry_element()` creates `pt_count = len(path) - 1` segments from `N` vertices, using `(path[i], path[i+1])` pairs. A closed loop of 4 vertices is naturally encoded as 3 segments from `[v0, v1, v2, v3]` — the closing segment `(v3, v0)` is MISSING.

**Fix for closed loops:** Append the first vertex to the end of the vertex list:
```python
if is_closed and vertices[0] != vertices[-1]:
    vertices = vertices + [vertices[0]]
```

This is the same pattern used in the DXF indexer's `_lw_length()` and `_poly_length()` functions.

### 5.3 Multiple ACI colors in one DXF layer

Common in LightBurn exports: all geometry in "mainlayer" but with different ACI colors. The adaptér creates one VCF layer per unique ACI color and assigns elements accordingly.

### 5.4 Zero-length / degenerate entities

Filter out entities with `length_mm <= 0` or `point_count < 2` (LINE with identical start/end). The DXF indexer already does this, but the adaptér should double-check.

---

## 6. Implementation Steps

### Phase 1: Core adaptér (~3-4 hours)

| Step | Task | Files | Depends on |
|---|---|---|---|
| 1.1 | Create `vcf_compiler_map_config.json` with ACI→VCF mapping | `vcf_compiler_map_config.json` | — |
| 1.2 | Create `vcf_parser/_dxf_adapter.py` with `dxf_to_spec()` | `vcf_parser/_dxf_adapter.py` | 1.1 |
| 1.3 | Implement ACI→RGB lookup table | `vcf_parser/_dxf_adapter.py` | — |
| 1.4 | Implement entity grouping by `color_index` | `vcf_parser/_dxf_adapter.py` | — |
| 1.5 | Implement closed-loop vertex fix | `vcf_parser/_dxf_adapter.py` | — |
| 1.6 | Implement geometry type mapping (LINE→Polyline, CIRCLE→Circle, etc.) | `vcf_parser/_dxf_adapter.py` | — |
| 1.7 | Wire into `vcf_parser/__init__.py` (export `compile_dxf`) | `vcf_parser/__init__.py` | 1.2 |

### Phase 2: Integration test (~2 hours)

| Step | Task | Files |
|---|---|---|
| 2.1 | Create test DXF files (primitive geometries) | `tests/test_data/` |
| 2.2 | Write `test_dxf_adapter.py`: verify spec dict structure | `tests/test_dxf_adapter.py` |
| 2.3 | Write roundtrip: create DXF→adaptér→VCF→re-parse→compare | `tests/test_dxf_to_vcf_roundtrip.py` |
| 2.4 | Test with real DXF files from `demo_data/` | integration |

### Phase 3: CLI pipeline script (~1 hour)

| Step | Task | Files |
|---|---|---|
| 3.1 | Create `scripts/vcf_compile.py` CLI | `scripts/vcf_compile.py` |
| 3.2 | CLI flags: `-i input.dxf`, `-o output.VCF`, `--config`, `--h1`, `--feed` | `scripts/vcf_compile.py` |
| 3.3 | Install as console_scripts entry point in `pyproject.toml` | `pyproject.toml` |

### Phase 4: Polish (~2 hours)

| Step | Task |
|---|---|
| 4.1 | Handle edge cases: entities with no mapping, unmapped ACI colors |
| 4.2 | Add logging for unmapped colors (warn but continue with fallback) |
| 4.3 | Determinism test: same DXF → same VCF (byte-for-byte) |
| 4.4 | Golden master tests for known DXFs |
| 4.5 | Update README with DXF→VCF instructions |

---

## 7. Test Strategy

### 7.1 Unit tests

| Test | What it verifies |
|---|---|
| `test_aci_to_rgb_known` | ACI 1→[255,0,0], ACI 7→[255,255,255] |
| `test_aci_to_rgb_unknown` | ACI 200→white fallback |
| `test_group_entities_by_aci` | 3 entities with ACI 1, 2 entities with ACI 2 → 2 groups |
| `test_closed_loop_vertex_fix` | [v0,v1,v2] closed → [v0,v1,v2,v0] |
| `test_entity_type_mapping` | LINE→Polyline, CIRCLE→Circle, ARC→Polyline |
| `test_spec_structure` | Output has "layers" + "elements", correct types |
| `test_layer_params_mapped` | ACI 3 → V-slot, 200 mm/s, Cut both side |

### 7.2 Integration tests

| Test | What it verifies |
|---|---|
| `test_dxf_to_vcf_roundtrip` | Parse DXF → write VCF → read VCF → compare layers + elements |
| `test_vcf_loads_in_reader` | Written VCF can be parsed by `extract_active_layers_details()` |
| `test_determinism_same_dxf` | Same DXF → byte-identical VCF |
| `test_multicolor_layer` | DXF with 3 ACI colors in 1 layer → 3 VCF layers |

### 7.3 Golden master tests

Store canonical VCF outputs for known DXF files. Regression check.

### 7.4 Manual validation

| Test | Setup |
|---|---|
| VCutWorks open | Otevřít výstupní VCF v RDCAM / VCutWorks, zkontrolovat vrstvy |
| LightBurn→DXF→VCF loop | Nakreslit primitiva v LightBurn, export DXF, zkompilovat, otevřít v RDCAM |

---

## 8. Risk Register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| **LightBurn DXF nekonzistence** — LightBurn exportuje DXF s proprietárními odchylkami (INSERT bloky, ACI paleta, chybějící entity) | Medium | High | Otestovat s minimálně 5 různými LightBurn DXF exporty; `ezdxf` handle INSERT přes `explode()` |
| **ARC segment data neznámá** — 74B segment má d0/d1/d2 pro oblouky, ale jejich formát není zRE | High | Medium | MVP používá resampled polylines; arc data jsou future work |
| **V-slot direction mismatch** — DXF nemá koncept "Left/Right/Cut both side"; mapování je čistě konvenční | Medium | Medium | Jasně dokumentovat konvence; validation_status = hypothesis pro nové ACI |
| **Chybějící H1 v DXF** — VCF potřebuje H1 (start_height), DXF ji neposkytuje | Low (known) | Low | Pevný default 2.0 mm (empiricky ověřený) |
| **Velké DXF soubory (>1000 entit)** — index_dxf počítá TAC, graph features, bool analýzu, což může být pomalé | Low | Low | keep_vertices=True vypíná ML features, nezpomaluje |
| **Změny v dxf_geometry_indexer API** — pokud se změní rozhraní `index_dxf()`, adaptér přestane fungovat | Low | High | Pin version dependency; testovat proti golden master |

---

## Appendix A: Mapping config seed values

```json
{
  "_schema": "vcf_compiler_map_config_v1.0",
  "aci_color_mapping": {
    "1":  { "cutter_type": "Vibrate cutter", "speed_mms": 150, "direction": "N/A",         "h1_mm": 2.0, "h2_mm": -0.3, "vs_comp_mm": 0.0, "start_extension_mm": 0.0, "end_extension_mm": 0.0, "is_output": true, "number_of_feeding": 1, "validation_status": "hypothesis", "_note": "Red — outer contours" },
    "2":  { "cutter_type": "V-slot",         "speed_mms": 300, "direction": "Left",         "h1_mm": 2.0, "h2_mm": 6.0,  "vs_comp_mm": 0.1, "start_extension_mm": 0.0, "end_extension_mm": 0.0, "is_output": true, "number_of_feeding": 1, "validation_status": "empirical",  "_note": "Yellow — chamfers, one-sided V-slot" },
    "3":  { "cutter_type": "V-slot",         "speed_mms": 200, "direction": "Cut both side","h1_mm": 2.0, "h2_mm": 6.0,  "vs_comp_mm": 0.0, "start_extension_mm": 2.0, "end_extension_mm": 2.0, "is_output": true, "number_of_feeding": 1, "validation_status": "empirical",  "_note": "Green — standard V-slot pattern" },
    "5":  { "cutter_type": "Vibrate cutter", "speed_mms": 100, "direction": "N/A",         "h1_mm": 2.0, "h2_mm": -0.3, "vs_comp_mm": 0.0, "start_extension_mm": 0.0, "end_extension_mm": 0.0, "is_output": true, "number_of_feeding": 1, "validation_status": "empirical",  "_note": "Blue — small holes/circles" },
    "6":  { "cutter_type": "Vibrate cutter", "speed_mms": 300, "direction": "N/A",         "h1_mm": 2.0, "h2_mm": -0.3, "vs_comp_mm": 0.0, "start_extension_mm": 0.0, "end_extension_mm": 0.0, "is_output": true, "number_of_feeding": 1, "validation_status": "calibrated", "_note": "Magenta — high-speed chop" },
    "7":  { "cutter_type": "Vibrate cutter", "speed_mms": 200, "direction": "N/A",         "h1_mm": 2.0, "h2_mm": -0.3, "vs_comp_mm": 0.0, "start_extension_mm": 0.0, "end_extension_mm": 0.0, "is_output": true, "number_of_feeding": 1, "validation_status": "empirical",  "_note": "White — main contours" },
    "30": { "cutter_type": "V-slot",         "speed_mms": 100, "direction": "Cut both side","h1_mm": 2.0, "h2_mm": 6.0,  "vs_comp_mm": 0.0, "start_extension_mm": 2.0, "end_extension_mm": 2.0, "is_output": true, "number_of_feeding": 1, "validation_status": "calibrated", "_note": "Orange — special V-slot, slow, complex patterns" }
  }
}
```

## Appendix B: Installation & dependency

The adaptér requires `dxf_integrace` to be importable. Options:

1. **Subtree/copy** — Copy `dxf_geometry_indexer_v2.py` into `vcf_parser/` as `_dxf_indexer.py`
2. **Pip install** — Install `dxf_integrace` as editable package (`pip install -e ../dxf_integrace`)
3. **Separate microservice** — DXF→JSON as CLI, VCF compiler reads JSON

**Recommendation for MVP:** Option 1 (copy + strip) — copy only the `index_dxf()` function and its dependencies from `dxf_geometry_indexer_v2.py`, removing ML/semantic/visualization code. Target: ~500 lines instead of 2072.
