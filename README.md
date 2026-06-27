# Vcf-compiler

**Clean-slate serialization of Ruida VCF (VCutWorks) binary format for RDD6584G oscillating knife.**

`from vcf_parser import write; write(spec, "output.VCF")`

---

## Quick start

```python
from vcf_parser import write

spec = {
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
            "is_output_yes": True,
            "number_of_feeding": 1,
        }
    ],
    "elements": [
        {
            "geom_type": "Polyline",
            "vertices": [(100.0, 100.0), (500.0, 100.0)],
            "layer_index": 0,
            "is_output_yes": True,
        }
    ],
}

write(spec, "output.VCF")
```

---

## Package structure

```
vcf_parser/
├── __init__.py       # write(), VcfWriterError
├── _writer.py        # VcfWriter — header/body/trailer serialization
├── _reader.py        # Layer extraction + constants (CUTTER_MAP, DIR_MAP, GEOMETRY_SIG)
├── _config.py        # Machine profile fallback
└── _geometry.py      # Bbox, path length, containment utilities
```

**Import graph:** `write()` → `VcfWriter` → `_reader` (encoding, maps), `_config` (optional), `_geometry` (optional).  
**Does NOT depend on:** `Knowledge_base`, `app.py`, `streamlit`.

---

## VCF binary format

```
┌─────────────────────────────────────────────┐
│ HEADER                                       │
│  ├─ Magic: "RDVCUTFILEVER1.0.013" (20 B)     │
│  └─ Layer blocks: N × 610 B (v1.0.013)       │
│       +0: output_flag (u32)                  │
│       +4: speed_mms (f64)                    │
│      +12: color_bgr (u32)                    │
│      +32: cutter_type (i32, CUTTER_MAP idx)  │
│      +76: H1 start height (f64)              │
│      +84: feed_count (i32)                   │
│      +92: H2 end height (f64)                │
│     +100: V-slot direction (u16)             │
│     +102: V-slot comp (f64)                  │
│     +110: start_ext (f64)                    │
│     +118: end_ext (f64)                      │
├─────────────────────────────────────────────┤
│ BODY                                         │
│  └─ Elements: GEOMETRY_SIG + N × 74 B segs  │
│       +0: GEOMETRY_SIG (8 B)                 │
│       +8: geom_color (u32)                   │
│      +45: type_id / pt_count / subtype       │
│      +45: [segment 0: x1,y1,x2,y2, d0,d1,d2]│
├─────────────────────────────────────────────┤
│ TRAILER: 0xD7                                │
└─────────────────────────────────────────────┘
```

---

## Tests

```bash
pytest tests/ -v
```

- 28 unit + roundtrip tests (28 PASS, 2 SKIP)
- 6 demo VCF files in `demo_data/`
- Roundtrip: parse reference VCF → write → reparse → compare

---

## Open source references

This project builds on RE insights from the Ruida protocol ecosystem:

| Project | Language | Role |
|---------|----------|------|
| [jnweiger/ruida-laser](https://github.com/jnweiger/ruida-laser) | Python | `.rd` generator — template for VcfWriter |
| [meerk40t/ruida](https://github.com/meerk40t/meerk40t) | Python | Bimodal `.rd` parser + generator, 60+ encoder methods |
| [kkaempf/ruida](https://github.com/kkaempf/ruida) | Ruby | Clean `.rd` command dispatch and decoding |
| [schuermans.info/rdcam](https://schuermans.info/rdcam) | Docs | Original scrambling algorithm, message format RE |
| [ArboresTech Wiki](http://wiki.ArboresTech.com/) | Docs | Complete Ruida command table |

Full methodology and VCF format specification: `docs/narrative_report_v1.md`

### Documentation

| Document | Description |
|----------|-------------|
| `docs/narrative_report_v1.md` | Architecture, format spec, import paths, open source references |
| `docs/VCF_Reverse_Engineering_Inference_Workflow_2026.md` | Full RE methodology (v1.1, 1276 lines) |
| `docs/RE_CASE_STUDY_VCUTWORKS_LIGHTBURN_v2.md` | 29-day RE case study: V1→V22 parser evolution |
| `docs/SYSTEQ_VCF_STACK_ANATOMY_V2.md` | Architectural analysis of the vcf_parser_b2b stack |
| `docs/KNOWLEDGE_CORPUS_VCUTWORKS_LIGHTBURN.md` | VCF + DXF format knowledge corpus |
| `docs/DXF_PREDICTIVE_PARSER_METHODOLOGY.md` | DXF predictive parser methodology (LightBurn vs AutoCAD) |

---

## Author

**Ondřej Soušek** — [outpost2026](https://github.com/outpost2026)  
Reverse engineering & clean-slate implementation of Ruida VCutWorks binary format for B2B CNC automation.

License: MIT
