<div align="left">
  <a href="https://github.com/outpost2026/Vcf-compiler/blob/main/readme_cs.md">
    <img src="https://flagcdn.com/24x18/cz.png" alt="CS" height="18"> Česky
  </a>
</div>

# Vcf-compiler

[![CI](https://github.com/outpost2026/Vcf-compiler/actions/workflows/ci.yml/badge.svg)](https://github.com/outpost2026/Vcf-compiler/actions/workflows/ci.yml)

**Clean-slate VCF writer for Ruida VCutWorks (RDD6584G oscillating knife).**

Generates binary `.VCF` files from DXF input or Python spec — compatible with VCutWorks CAM software, confirmed by GUI testing.

```python
from vcf_parser import write

spec = {
    "layers": [{"cutter_type": "Vibrate cutter", "speed_mms": 500.0, "color_rgb": [255, 0, 0]}],
    "elements": [{"geom_type": "Polyline", "vertices": [(100,100), (500,100)], "layer_index": 0}],
}
write(spec, "output.VCF")
```

---

## Status: Working Proof of Concept ✅

After 6 research sessions and 19 binary search variants (A–S), **3 independent root causes** were identified and fixed. The writer now produces VCF files that load correctly in VCutWorks with geometry rendering, ACI layer recognition, and correct cutting parameters.

| Metric | Value |
|--------|-------|
| Writer tests | 30 tests (28 PASS, 2 SKIP) |
| VCutWorks compatibility | ✅ LOAD OK, geometry renders |
| Critical diffs vs native | 0 in HEADER, GEOMETRY, TRAILER |
| Remaining diffs | 4 denormalized bytes (semantically identical) |
| LOC | 1092 (6 modules) |
| CI | ✅ matrix (3.11-3.12), nightly, CodeQL, Dependabot |
| AI session tracking | `.ai_state.json` — versioned, 14+ sessions documented |

### Root causes (all fixed)

1. **Trailer truncated** → Hard rejection. Writer wrote TRAILER_PREFIX but skipped DXF path data when source path was None. Fixed: always write path data.
2. **Element count @92 = 0** → No geometry rendered. Writer left the element count byte at 0 in the active layer block. Fixed: `struct.pack_into('<B', block, 92, len(layer._paths))`.
3. **Direction @104 = 0** → Missing cut direction. Writer only set direction for V-slot cutters. Fixed: direction for ALL cutter types, default = 2 ("Cut both side").

---

## Architecture

```
                       ┌──────────────────┐
  DXF                  │  _dxf_adapter.py  │
  (LightBurn export) ──▶  compile_dxf()   │
                       └────────┬─────────┘
                                │ spec dict
                       ┌────────▼─────────┐
                       │    _writer.py     │
  Python spec ─────────▶  VcfWriter.write() │
                       └────────┬─────────┘
                                │ .VCF binary
                       ┌────────▼─────────┐
                       │    VCutWorks      │ ✅
                       └──────────────────┘
```

### Package layout

```
vcf_parser/
├── __init__.py       # write(), compile_dxf(), VcfWriterError
├── _writer.py        # VcfWriter — header/body/trailer serialization (441 LOC)
├── _reader.py        # VCF reader — RE constants, color/cutter/direction maps, string extraction
├── _dxf_adapter.py   # DXF→VCF bridge, ACI→VCF parameter mapping, batch compile
├── _geometry.py      # Bbox, path length, circle fit utilities
└── _config.py        # Machine profile fallback, version constants
```

### VCF binary format (v1.0.013)

```
┌──────────────────────────────────────────────────┐
│ HEADER (472 B)                                    │
│  ├─ Magic: "RDVCUTFILEVER1.0.013" (20 B)          │
│  ├─ Stock: 1220×2900 mm                           │
│  └─ MACHINE_PROFILE (418 B, verified 0 diffs)     │
├──────────────────────────────────────────────────┤
│ LAYER BLOCKS (N × 610 B)                          │
│  ├─ 256 empty blocks (padding)                    │
│  └─ Active block(s) — linked-list chained          │
│       @0: output_flag, @4: speed, @12: color_bgr   │
│       @32: cutter, @40: 5.0, @80: h1, @88: feed    │
│       @92: element_count ← CRITICAL                 │
│       @96: h2, @104: direction ← CRITICAL           │
│       @197: 64, @198: 0.5, @606: terminator         │
├──────────────────────────────────────────────────┤
│ GEOMETRY                                         │
│  └─ Elements: GEOMETRY_SIG + color + coords       │
├──────────────────────────────────────────────────┤
│ TRAILER: 0xD7 prefix + DXF source path string     │
└──────────────────────────────────────────────────┘
```

---

## RE Analysis Toolkit (dev_scripts/)

14 reverse engineering tools for batch VCF analysis, automated via orchestrator:

| Tool | Purpose |
|------|---------|
| `decode_subtype_bits.py` | Decodes geometry subtype bit fields |
| `dissect_footers.py` | Disassembles element footer structures |
| `dissect_layer_blocks.py` | Parses layer block byte layout |
| `segment_geometry_stats.py` | Statistical analysis of geometry segments |
| `batch_correlate_dxf_vcf.py` | Cross-correlates DXF→VCF pairs |
| `vcf_dxf_re_correlator_v1.1.py` | RE correlation with DXF reference |
| `vcf_binary_search.py` | Binary search variant generator |
| `build_element_types_catalog.py` | Element type taxonomy from corpus |
| `diagnose_multi_element.py` | Multi-element structure diagnosis |
| `analyze_hex_diffs.py` | Hex diff region analysis |
| `hex_diff_v2.py` | Enhanced hex diff with context |
| `batch_compile_dxf.py` | Batch DXF→VCF compilation |
| `VcfWrappingAnalyzer.py` | Wrapping pattern analysis |
| `run_all_re_tools.py` | **Orchestrator** — runs all tools on a VCF, aggregates results |

### Research outputs (10 files from 62-file batch analysis)

Available in `research_docs/`:

| Output | Content |
|--------|---------|
| `RESULT_correlation_master.md` | Master correlation matrix across all VCF/DXF pairs |
| `RESULT_footer_field_hypotheses.md` | Hypotheses for unknown footer fields |
| `RESULT_layer_block_field_map.json` | Annotated layer block field mapping |
| `RESULT_segment_geometry_report.md` | Statistical segment geometry profile |
| `RESULT_subtype_correlation_matrix.json` | Subtype bit→geometry type correlation |
| `RESULT_subtype_upper_bit_hypotheses.md` | Upper byte semantic hypotheses |
| `element_types_catalog.md` | Complete element type taxonomy |

---

## Breakthrough: Binary Search Variant Methodology

The root causes were found by a novel **binary search variant** approach — generating VCF files with incrementally added structural features and testing each in real VCutWorks GUI.

| Phase | Variants | Key Discovery |
|-------|----------|---------------|
| A–D | Incremental features | MP + empty blocks + linked-list = load OK, no geometry |
| E–G | Trailer variants | **Trailer without path data = hard rejection** |
| H–J | Feature isolation | Active block fields cause missing geometry |
| **K–O** | **Patched variants** | **M (native active+trait) = WORKS** — definitive proof |
| P–S | Fixed writer variants | **All 3 fixes confirmed by GUI** |

**Why this worked where hex diff failed:** Hex diff showed 1055 diff regions but could not distinguish critical (12 B) from irrelevant (3740 B empty block padding). GUI testing in real VCutWorks was the only reliable oracle.

---

## Tests

```bash
pytest tests/ -v
```

- 28 unit + roundtrip tests (28 PASS, 2 SKIP for missing demo files)
- 19 binary search variant files in `demo_data/binary_search_variants/` (A–S)
- 7 native VCF references in `demo_data/`
- Roundtrip: parse native → write → reparse → compare

---

## Documentation

### Research (research_docs/)

| Document | Description |
|----------|-------------|
| `DEV_REPORT_VCF_COMPILER_DEBUG_v2.md` | Full RE report — hypotheses, binary search methodology, layer block format |
| `REPORT_dev_phase_evolution.md` | Session 1→6 evolution, blind spots, breakthrough logic, LLM collaboration analysis |
| `REPORT_early_dev_phase_anomaly_v1.md` | Early phase analysis — regression tracing, first working VCF |
| `DEV_NEW_ANALYSIS_TOOLS_PROPOSAL.md` | Proposal for 10 new RE analysis tools |
| `Gemini_RD_VCF.txt` | LLM methodology research notes |

### Knowledge base (docs/)

| Document | Description |
|----------|-------------|
| `GROUND_TRUTH_VCF_DXF_RE_SEMANTIC_COMPILATION.json` | Ground truth — semantic VCF/DXF correlation |
| `SYSTEQ_VCF_STACK_ANATOMY_V2.md` | Full binary stack anatomy (header→body→trailer) |
| `VCF_Reverse_Engineering_Inference_Workflow_2026.md` | Systematic RE inference methodology |
| `KNOWLEDGE_CORPUS_VCUTWORKS_LIGHTBURN.md` | Cross-platform knowledge corpus |
| `RE_CASE_STUDY_VCUTWORKS_LIGHTBURN_v2.md` | Complete RE case study with methodology |
| `STATISTICAL_ANALYSIS_INTERPRETATION.md` | Statistical analysis of VCF corpus |
| `ACI_MAPOVANI_RESEARCH_V2.md` | ACI color mapping research |
| `DXF_PREDICTIVE_PARSER_METHODOLOGY.md` | Predictive DXF→VCF parsing |
| `dxf_to_vcf_pipeline_design.md` | End-to-end pipeline design |
| `narrative_report_v1.md` / `v2_b2b_pipeline.md` | Narrative development reports |
| `handoff_session_2026-06-27.json` (also -29, -30) | Structured LLM session handoffs |

---

## Repo structure overview

```
Vcf-compiler/
├── vcf_parser/            # Core library (6 modules, 1092 LOC)
├── dev_scripts/           # 14 RE analysis tools + orchestrator
├── research_docs/         # 10 RESULT_* outputs + methodology reports
├── docs/                  # 17 documents (ground truth, handoffs, anatomy, case study)
├── demo_data/             # VCF, DXF, JSON reference files (16+ pairs)
├── tests/                 # 30 tests (28 PASS, 2 SKIP)
├── .ai_state.json         # Session tracking (v1.13.0, 14+ sessions)
├── .github/workflows/     # CI matrix + CodeQL + Dependabot
└── pyproject.toml         # Python 3.11+, pytest config
```

## Related ecosystem

This repo is part of a broader CNC/CAM automation platform. Key relationships:

| Package | Role |
|---------|------|
| **vcf_color_service** | Single source of truth for ACI→VCF parameter mapping (pip package, 24 tests) |
| **dxf_integrace** | DXF geometry indexer — semantic embedding, predictive parsing |
| **vcf_parser_b2b** | B2B VCF parser — Streamlit GUI, golden master tests, GCP deployment |
| **mcp-local-server** | MCP server (15 tools) — filesystem, git, VCF validate/analyze/diff, RE pipeline, KB search, ACI lookup |

**Vcf-compiler represents the generative apex of this research** — it is the only component that *creates* VCF files rather than only parsing them. The RE knowledge accumulated across all parser repos (vcf_integrace, vcf_parser_b2b, dxf_integrace) converges here into forward-generation capability.

---

## License

PolyForm Shield License 1.0.0 — commercial use requires a separate license agreement.

See [LICENSE](./LICENSE) for full terms.

Copyright (c) 2026 SYSTEQ
