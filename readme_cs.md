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
| Writer testy | 28/28 PASS |
| VCutWorks kompatibilita | ✅ LOAD OK, geometrie se vykresluje |
| Kritické diffs oproti native | 0 v HEADER, GEOMETRY, TRAILER |
| Zbývající diffs | 4 denormalizované byty (sémanticky identické) |

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
├── _writer.py        # VcfWriter — header/body/trailer serializace (421 LOC)
├── _reader.py        # VCF reader — RE konstanty, mapy barev/nožů/směrů
├── _dxf_adapter.py   # DXF→VCF bridge, ACI→VCF mapping parametrů
├── _geometry.py      # Bbox, délka cest
└── _config.py        # Fallback machine profilu
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

| Dokument | Popis |
|----------|-------|
| `research_docs/DEV_REPORT_VCF_COMPILER_DEBUG_v2.md` | Plný RE report — hypotézy, binary search metodologie, formát layer bloku |
| `research_docs/REPORT_dev_phase_evolution.md` | Session 1→6 evoluce, slepé uličky, breakthrough logika, LLM kolaborace |
| `research_docs/REPORT_early_dev_phase_anomaly_v1.md` | Analýza early phase — první fungující VCF, tracing regresí |
| `research_docs/Gemini_RD_VCF.txt` | LLM metodologický výzkum |

---

## Související ekosystém

Toto repo je součástí širší CNC/CAM automatizační platformy:

| Balíček | Role |
|---------|------|
| **vcf_color_service** | Jediný zdroj pravdy pro ACI→VCF mapování parametrů (pip balíček, 24 testů) |
| **dxf_integrace** | DXF geometry indexer — sémantické embeddování, prediktivní parsing |
| **vcf_parser_b2b** | B2B VCF parser — Streamlit GUI, golden master testy, GCP deployment |

**Vcf-compiler představuje generační vrchol tohoto výzkumu** — je to jediná komponenta, která *vytváří* VCF soubory, nejen je parsuje. RE knowledge nashromážděná napříč všemi parser repy (vcf_integrace, vcf_parser_b2b, dxf_integrace) se zde sbíhá do forward-generation capability.

---

## Autor

**Ondřej Soušek** — [outpost2026](https://github.com/outpost2026)  
Reverzní inženýrství & clean-slate implementace Ruida VCutWorks binárního formátu pro CNC automatizaci.

Licence: PolyForm Shield License 1.0.0 — komerční využití vyžaduje samostatnou licenční smlouvu.

Viz [LICENSE](./LICENSE) pro plná pravidla.

Copyright (c) 2026 SYSTEQ
