<div align="left">
  <a href="https://github.com/outpost2026/Vcf-compiler/blob/main/README.md">
    <img src="https://flagcdn.com/24x18/gb.png" alt="EN" height="18"> English
  </a>
</div>

# Vcf-compiler

**Clean-slate VCF writer pro Ruida VCutWorks (RDD6584G oscilační nůž).**

Generuje binární `.VCF` soubory z DXF vstupu nebo Python specifikace — kompatibilní s CAM softwarem VCutWorks, potvrzeno GUI testováním.

```python
from vcf_parser import write

spec = {
    "layers": [{"cutter_type": "Vibrate cutter", "speed_mms": 500.0, "color_rgb": [255, 0, 0]}],
    "elements": [{"geom_type": "Polyline", "vertices": [(100,100), (500,100)], "layer_index": 0}],
}
write(spec, "output.VCF")
```

---

## Stav: Working Proof of Concept ✅

Po 6 výzkumných session a 19 binary search variantách (A–S) byly **identifikovány a opraveny 3 nezávislé root causes**. Writer nyní produkuje VCF soubory, které se korektně načítají v VCutWorks s vykreslenou geometrií, rozpoznáním ACI vrstev a správnými řeznými parametry.

| Metrika | Hodnota |
|---------|---------|
| Writer testy | 30 testů (28 PASS, 2 SKIP) |
| VCutWorks kompatibilita | ✅ LOAD OK, geometrie se vykresluje |
| Kritické diffs oproti native | 0 v HEADER, GEOMETRY, TRAILER |
| Zbývající diffs | 4 denormalizované byty (sémanticky identické) |
| LOC | 1092 (6 modulů) |
| CI | ✅ matrix (3.11-3.12), nightly, CodeQL, Dependabot |
| AI session tracking | `.ai_state.json` — verzováno, 14+ sessions |

### Root causes (všechny opraveny)

1. **Trailer truncated** → Hard rejection. Writer zapisoval TRAILER_PREFIX, ale přeskakoval DXF path data pokud zdrojová cesta byla None. Fix: vždy zapisovat path data.
2. **Element count @92 = 0** → Žádná geometrie. Writer nechával počet elementů v active bloku na 0. Fix: `struct.pack_into('<B', block, 92, len(layer._paths))`.
3. **Direction @104 = 0** → Chybějící směr řezu. Writer nastavoval direction jen pro V-slot nože. Fix: direction pro VŠECHNY typy nožů, default = 2 ("Cut both side").

---

## Architektura

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

### Struktura balíčku

```
vcf_parser/
├── __init__.py       # write(), compile_dxf(), VcfWriterError
├── _writer.py        # VcfWriter — header/body/trailer serializace (441 LOC)
├── _reader.py        # VCF reader — RE konstanty, mapy barev/nožů/směrů, extrakce stringů
├── _dxf_adapter.py   # DXF→VCF bridge, ACI→VCF mapping parametrů, batch compile
├── _geometry.py      # Bbox, délka cest, circle fit utility
└── _config.py        # Fallback machine profilu, version konstanty
```

### Binární formát VCF (v1.0.013)

```
┌──────────────────────────────────────────────────┐
│ HEADER (472 B)                                    │
│  ├─ Magic: "RDVCUTFILEVER1.0.013" (20 B)          │
│  ├─ Stock: 1220×2900 mm                           │
│  └─ MACHINE_PROFILE (418 B, ověřeno 0 diffs)      │
├──────────────────────────────────────────────────┤
│ LAYER BLOKY (N × 610 B)                           │
│  ├─ 256 prázdných bloků (padding)                 │
│  └─ Active block(y) — zřetězené linked-listem      │
│       @0: output_flag, @4: speed, @12: color_bgr   │
│       @32: cutter, @40: 5.0, @80: h1, @88: feed    │
│       @92: element_count ← KRITICKÉ                 │
│       @96: h2, @104: direction ← KRITICKÉ           │
│       @197: 64, @198: 0.5, @606: terminator         │
├──────────────────────────────────────────────────┤
│ GEOMETRIE                                        │
│  └─ Elementy: GEOMETRY_SIG + barva + souřadnice  │
├──────────────────────────────────────────────────┤
│ TRAILER: 0xD7 prefix + DXF source path string    │
└──────────────────────────────────────────────────┘
```

---

## RE Analysis Toolkit (dev_scripts/)

14 nástrojů pro hromadnou VCF analýzu, automatizovaných přes orchestrátor:

| Nástroj | Účel |
|---------|-------|
| `decode_subtype_bits.py` | Dekóduje bitová pole subtype geometrie |
| `dissect_footers.py` | Rozkládá struktury element footerů |
| `dissect_layer_blocks.py` | Parsuje byte layout layer bloků |
| `segment_geometry_stats.py` | Statistická analýza geometrických segmentů |
| `batch_correlate_dxf_vcf.py` | Křížová korelace DXF↔VCF párů |
| `vcf_dxf_re_correlator_v1.1.py` | RE korelace s DXF referencí |
| `vcf_binary_search.py` | Generátor binary search variant |
| `build_element_types_catalog.py` | Taxonomie element typů z korpusu |
| `diagnose_multi_element.py` | Diagnostika multi-element struktury |
| `analyze_hex_diffs.py` | Analýza hex diff regionů |
| `hex_diff_v2.py` | Vylepšený hex diff s kontextem |
| `batch_compile_dxf.py` | Dávková DXF→VCF kompilace |
| `VcfWrappingAnalyzer.py` | Analýza wrapping patternů |
| `run_all_re_tools.py` | **Orchestrátor** — spustí vše na VCF, agreguje výsledky |

### Výstupy (10 souborů z 62-file batch analýzy)

Dostupné v `research_docs/`:

| Výstup | Obsah |
|--------|-------|
| `RESULT_correlation_master.md` | Hlavní korelační matice napříč VCF/DXF páry |
| `RESULT_footer_field_hypotheses.md` | Hypotézy pro neznámá footer pole |
| `RESULT_layer_block_field_map.json` | Anotované mapování layer block polí |
| `RESULT_segment_geometry_report.md` | Statistický profil geometrických segmentů |
| `RESULT_subtype_correlation_matrix.json` | Korelace subtype bitů↔typ geometrie |
| `RESULT_subtype_upper_bit_hypotheses.md` | Sémantické hypotézy pro horní byte |
| `element_types_catalog.md` | Kompletní taxonomie element typů |

---

## Průlom: Binary Search Variant Methodology

Root causes byly nalezeny pomocí **binary search variant** přístupu — generování VCF souborů s postupně přidávanými structural features a testování každé v reálném VCutWorks GUI.

| Fáze | Varianty | Klíčový objev |
|------|----------|---------------|
| A–D | Inkrementální features | MP + empty blocks + linked-list = load OK, bez geometrie |
| E–G | Trailer varianty | **Trailer bez path dat = hard rejection** |
| H–J | Izolace features | Active block fields způsobují chybějící geometrii |
| **K–O** | **Patched varianty** | **M (native active+trait) = WORKS** — definitivní důkaz |
| P–S | Fixed writer varianty | **Všechny 3 fixy potvrzeny GUI** |

**Proč to fungovalo tam, kde hex diff selhal:** Hex diff ukázal 1055 diff regionů, ale nedokázal rozlišit kritické (12 B) od irelevantních (3740 B empty block padding). GUI testování v reálném VCutWorks byl jediný spolehlivý ground truth.

---

## Testy

```bash
pytest tests/ -v
```

- 28 unit + roundtrip testů (28 PASS, 2 SKIP pro chybějící demo soubory)
- 19 binary search variant v `demo_data/binary_search_variants/` (A–S)
- 7 nativních VCF referencí v `demo_data/`
- Roundtrip: parsuj native → write → reparsuj → porovnej

---

## Dokumentace

### Research (research_docs/)

| Dokument | Popis |
|----------|-------|
| `DEV_REPORT_VCF_COMPILER_DEBUG_v2.md` | Plný RE report — hypotézy, binary search metodologie, formát layer bloku |
| `REPORT_dev_phase_evolution.md` | Session 1→6 evoluce, slepé uličky, breakthrough logika, LLM kolaborace |
| `REPORT_early_dev_phase_anomaly_v1.md` | Analýza early phase — regression tracing, první fungující VCF |
| `DEV_NEW_ANALYSIS_TOOLS_PROPOSAL.md` | Proposal na 10 nových RE nástrojů |
| `Gemini_RD_VCF.txt` | LLM metodologický výzkum |

### Znalostní báze (docs/)

| Dokument | Popis |
|----------|-------|
| `GROUND_TRUTH_VCF_DXF_RE_SEMANTIC_COMPILATION.json` | Ground truth — sémantická VCF/DXF korelace |
| `SYSTEQ_VCF_STACK_ANATOMY_V2.md` | Kompletní anatomie binárního stacku (header→body→trailer) |
| `VCF_Reverse_Engineering_Inference_Workflow_2026.md` | Systematická RE inference metodologie |
| `KNOWLEDGE_CORPUS_VCUTWORKS_LIGHTBURN.md` | Cross-platform knowledge corpus |
| `RE_CASE_STUDY_VCUTWORKS_LIGHTBURN_v2.md` | Kompletní RE case study s metodologií |
| `STATISTICAL_ANALYSIS_INTERPRETATION.md` | Statistická analýza VCF korpusu |
| `ACI_MAPOVANI_RESEARCH_V2.md` | Výzkum ACI barevného mapování |
| `DXF_PREDICTIVE_PARSER_METHODOLOGY.md` | Prediktivní DXF→VCF parsing |
| `dxf_to_vcf_pipeline_design.md` | Návrh end-to-end pipeline |
| `narrative_report_v1.md` / `v2_b2b_pipeline.md` | Narrative vývojové reporty |
| `handoff_session_2026-06-27.json` (též -29, -30) | Strukturované LLM session handoffy |

---

## Přehled struktury repa

```
Vcf-compiler/
├── vcf_parser/            # Core knihovna (6 modulů, 1092 LOC)
├── dev_scripts/           # 14 RE nástrojů + orchestrátor
├── research_docs/         # 10 RESULT_* výstupů + metodologické reporty
├── docs/                  # 17 dokumentů (ground truth, handoffy, anatomie, case study)
├── demo_data/             # VCF, DXF, JSON referenční soubory (16+ párů)
├── tests/                 # 30 testů (28 PASS, 2 SKIP)
├── .ai_state.json         # Session tracking (v1.13.0, 14+ sessions)
├── .github/workflows/     # CI matrix + CodeQL + Dependabot
└── pyproject.toml         # Python 3.11+, pytest config
```

## Související ekosystém

Toto repo je součástí širší CNC/CAM automatizační platformy:

| Balíček | Role |
|---------|------|
| **vcf_color_service** | Jediný zdroj pravdy pro ACI→VCF mapování parametrů (pip balíček, 24 testů) |
| **dxf_integrace** | DXF geometry indexer — sémantické embeddování, prediktivní parsing |
| **vcf_parser_b2b** | B2B VCF parser — Streamlit GUI, golden master testy, GCP deployment |
| **mcp-local-server** | MCP server (15 nástrojů) — filesystem, git, VCF validace/analyza/diff, RE pipeline, KB search, ACI lookup |

**Vcf-compiler představuje generační vrchol tohoto výzkumu** — je to jediná komponenta, která *vytváří* VCF soubory, nejen je parsuje. RE knowledge nashromážděná napříč všemi parser repy (vcf_integrace, vcf_parser_b2b, dxf_integrace) se zde sbíhá do forward-generation capability.

---

## Autor

**Ondřej Soušek** — [outpost2026](https://github.com/outpost2026)  
Reverzní inženýrství & clean-slate implementace Ruida VCutWorks binárního formátu pro CNC automatizaci.

Licence: PolyForm Shield License 1.0.0 — komerční využití vyžaduje samostatnou licenční smlouvu.

Viz [LICENSE](./LICENSE) pro plná pravidla.

Copyright (c) 2026 SYSTEQ
