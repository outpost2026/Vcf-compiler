"""
Build Element Types Catalog — Ground Truth from native VCF files.

Parses all native VCF files using the production parser (vcf_parser_b2b)
and generates a deterministic catalog of element types, segment formats,
footer structures, and layer-element relationships.

Outputs:
    research_docs/element_types_catalog.md   (human-readable)
    research_docs/element_types_catalog.json (machine-readable)
"""

import sys
import os
import json
import struct
import math
import logging
from pathlib import Path
from collections import OrderedDict

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

# ── Paths ──────────────────────────────────────────────────────────────

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DEMO = REPO / "demo_data"
OUT = REPO / "research_docs"

# Add vcf_parser_b2b src to path
B2B_SRC = Path(
    r"C:\Users\PC\Documents\Repozitar_Dev\_github\vcf_parser_b2b\src"
)
sys.path.insert(0, str(B2B_SRC))

# ── Imports ────────────────────────────────────────────────────────────

from vcf_parser_v20 import RuidaVcfEngineV20
from vcf_geometry import GEOMETRY_SIG
from vcf_binary_reader import (
    extract_active_layers_details,
    GEOMETRY_SIG as READER_SIG,
)

# ── Constants ──────────────────────────────────────────────────────────

SEGMENT_SIZE = 74  # bytes per segment
FOOTER_CANDIDATE_SIZE = 196  # hypothesized footer size

# ── Helpers ────────────────────────────────────────────────────────────


def _classify_element_type(type_id: int, subtype: int, pt_count: int) -> str:
    """Replicate vcf_geometry.py line 59-69 classification logic."""
    if type_id == 1 and (subtype & 0xFFFF) == 3 and pt_count <= 8:
        return "Circle"
    elif type_id == 0 and pt_count == 1:
        return "Line"
    elif type_id == 0:
        return "Polyline"
    elif type_id == 1:
        return "Polygon"
    return "Unknown"


def _find_all_geometry_sigs(data: bytes) -> list:
    """Return list of (offset, geom_color, raw_subtype_bytes) for each GEOMETRY_SIG."""
    sig = GEOMETRY_SIG
    results = []
    offset = 0
    while True:
        pos = data.find(sig, offset)
        if pos == -1:
            break
        if pos + 45 + 12 > len(data):
            offset = pos + 1
            continue
        try:
            geom_color = struct.unpack_from("<I", data, pos + 8)[0]
            p = pos + 45
            type_id = struct.unpack_from("<I", data, p)[0]
            pt_count = struct.unpack_from("<I", data, p + 4)[0]
            subtype = struct.unpack_from("<I", data, p + 8)[0]
        except (struct.error, ValueError):
            offset = pos + 1
            continue
        results.append(
            {
                "offset": pos,
                "next": None,  # filled later
                "geom_color": geom_color,
                "geom_color_hex": f"0x{geom_color:08x}",
                "type_id": type_id,
                "pt_count": pt_count,
                "subtype": subtype,
                "subtype_hex": f"0x{subtype:08x}",
                "subtype_low16": subtype & 0xFFFF,
                "subtype_low16_hex": f"0x{(subtype & 0xFFFF):04x}",
                "classified_type": _classify_element_type(type_id, subtype, pt_count),
            }
        )
        offset = pos + 1

    # Fill next offsets
    for i in range(len(results) - 1):
        results[i]["next"] = results[i + 1]["offset"]

    return results


def _compute_expected_element_size(pt_count: int) -> int:
    """Expected size of a geometry element: 45 + pt_count * 74."""
    return 45 + pt_count * SEGMENT_SIZE


def _analyze_footers(data: bytes, sigs: list) -> list:
    """For multi-element VCFs, compute delta between actual and expected next offset."""
    footers = []
    for i, sig in enumerate(sigs):
        if sig["next"] is None:
            continue
        expected = sig["offset"] + _compute_expected_element_size(sig["pt_count"])
        actual = sig["next"]
        delta = actual - expected
        if delta > 0:
            footer_bytes = data[expected:actual]
            footers.append(
                {
                    "element_index": i,
                    "offset": sig["offset"],
                    "expected_next": expected,
                    "actual_next": actual,
                    "delta": delta,
                    "footer_size": len(footer_bytes),
                    "footer_hash": hash(footer_bytes),
                    "footer_bytes_hex": footer_bytes[:64].hex()
                    + ("..." if len(footer_bytes) > 64 else ""),
                }
            )
        else:
            footers.append(
                {
                    "element_index": i,
                    "offset": sig["offset"],
                    "expected_next": expected,
                    "actual_next": actual,
                    "delta": delta,
                    "footer_size": 0,
                }
            )
    return footers


def _extract_segment_arc_data(data: bytes, sig_offset: int, pt_count: int) -> list:
    """Extract (x1, y1, x2, y2, d0, d1, d2) for each segment."""
    p = sig_offset + 45
    segments = []
    for i in range(pt_count):
        seg_off = p + i * SEGMENT_SIZE
        if seg_off + 70 > len(data):
            break
        try:
            x1, y1 = struct.unpack_from("<dd", data, seg_off + 14)
            x2, y2 = struct.unpack_from("<dd", data, seg_off + 30)
            d0, d1 = struct.unpack_from("<dd", data, seg_off + 46)
            d2 = struct.unpack_from("<d", data, seg_off + 62)[0]
        except (struct.error, ValueError):
            continue
        segments.append(
            {
                "index": i,
                "x1": round(x1, 4),
                "y1": round(y1, 4),
                "x2": round(x2, 4),
                "y2": round(y2, 4),
                "d0": round(d0, 4),
                "d1": round(d1, 4),
                "d2": round(d2, 4),
                "has_arc": not (abs(d0) < 1e-9 and abs(d1) < 1e-9 and abs(d2) < 1e-9),
                "raw_hex": data[seg_off + 14 : seg_off + 70].hex(),
            }
        )
    return segments


def _extract_layer_at_offset(data: bytes, pos: int) -> dict:
    """Extract layer block fields from a candidate layer block position."""
    block = {}
    try:
        block["output_flag"] = struct.unpack_from("<I", data, pos)[0]
        block["speed"] = struct.unpack_from("<d", data, pos + 4)[0]
        block["color_val"] = struct.unpack_from("<I", data, pos + 12)[0]
        block["cutter_type_raw"] = struct.unpack_from("<i", data, pos + 32)[0]
        block["cutter_type"] = block["cutter_type_raw"] & 0xFFFF
        block["field_40"] = struct.unpack_from("<d", data, pos + 40)[0]
        block["color_76"] = struct.unpack_from("<I", data, pos + 76)[0]
        block["h1"] = struct.unpack_from("<d", data, pos + 80)[0]
        block["feed_count"] = struct.unpack_from("<i", data, pos + 88)[0]
        block["element_count"] = struct.unpack_from("<B", data, pos + 92)[0]
        block["h2"] = struct.unpack_from("<d", data, pos + 96)[0]
        block["direction"] = struct.unpack_from("<H", data, pos + 104)[0]
        block["field_106"] = struct.unpack_from("<d", data, pos + 106)[0]
        block["field_114"] = struct.unpack_from("<d", data, pos + 114)[0]
        block["field_122"] = struct.unpack_from("<d", data, pos + 122)[0]
        block["field_197"] = struct.unpack_from("<B", data, pos + 197)[0]
        block["field_198"] = struct.unpack_from("<d", data, pos + 198)[0]
        block["next_layer_flag"] = struct.unpack_from("<I", data, pos + 602)[0]
        block["next_layer_color"] = struct.unpack_from("<I", data, pos + 606)[0]
    except (struct.error, ValueError):
        pass
    return block


def _detect_footer_template(footers: list) -> dict:
    """Analyze all footers to determine if they are identical or vary."""
    if not footers:
        return {"pattern": "no_footers", "size": 0}
    sizes = set(f["footer_size"] for f in footers)
    hashes = set(f["footer_hash"] for f in footers)
    return {
        "pattern": "identical" if len(hashes) == 1 else "varying",
        "size_mode": "constant" if len(sizes) == 1 else "varying_size",
        "footer_size": list(sizes)[0] if len(sizes) == 1 else list(sizes),
        "count": len(footers),
        "unique_footer_count": len(hashes),
    }


def analyze_vcf(filepath: Path) -> dict:
    """Full analysis of a single native VCF file."""
    data = filepath.read_bytes()
    result = {
        "filename": filepath.name,
        "size_bytes": len(data),
        "modified": filepath.stat().st_mtime,
    }

    # 1. Use production parser
    try:
        engine = RuidaVcfEngineV20(data, filename=filepath.name)
        parsed = engine.parsed_data
        result["production_parser"] = {
            "layers_count": len(parsed.get("layers_details", [])),
            "elements_count": len(parsed.get("elements", [])),
            "warnings": parsed.get("warnings", []),
            "tech_notes": parsed.get("tech_notes", []),
            "canvas_bbox": parsed.get("canvas_bbox"),
            "panel_format": parsed.get("panel_format"),
        }
        # Attach element details
        elements_raw = []
        for el in parsed.get("elements", []):
            elements_raw.append(
                {
                    "element_id": el.get("element_id"),
                    "geom_type": el.get("geom_type"),
                    "type_id": el.get("type_id"),
                    "subtype": el.get("subtype"),
                    "subtype_hex": f"0x{el.get('subtype', 0):08x}",
                    "point_count": el.get("point_count"),
                    "length_mm": el.get("length_mm"),
                    "is_closed_loop": el.get("is_closed_loop"),
                    "layer_index": el.get("layer_index"),
                    "is_output_yes": el.get("is_output_yes"),
                    "segment_count": (
                        len(el.get("segment_arc_data", []))
                        if el.get("segment_arc_data")
                        else 0
                    ),
                    "bbox": el.get("bbox"),
                    "centroid": el.get("centroid"),
                }
            )
        result["production_parser"]["element_details"] = elements_raw
    except Exception as e:
        result["production_parser"] = {"error": str(e)}

    # 2. Raw binary: geometry signatures
    sigs = _find_all_geometry_sigs(data)
    result["geometry_sigs"] = sigs
    result["geometry_count"] = len(sigs)

    # 3. Footer analysis (multi-element only)
    if len(sigs) > 1:
        footers = _analyze_footers(data, sigs)
        result["footer_analysis"] = {
            "has_footers": any(f["delta"] > 0 for f in footers),
            "footer_template": _detect_footer_template(
                [f for f in footers if f["delta"] > 0]
            ),
            "deltas": [f["delta"] for f in footers],
            "details": footers,
        }
    else:
        result["footer_analysis"] = {
            "has_footers": None,
            "note": "single element only, cannot determine footer",
        }

    # 4. Segment arc data (for circle elements)
    for sig in sigs:
        if sig["classified_type"] == "Circle":
            sig["segments"] = _extract_segment_arc_data(
                data, sig["offset"], sig["pt_count"]
            )

    # 5. Layer blocks (raw extraction)
    layer_positions = []
    if sigs:
        first_geom = sigs[0]["offset"]
        block_size = 610
        for k in range(1, 32):
            pos = first_geom - k * block_size
            if pos < 0:
                break
            blk = _extract_layer_at_offset(data, pos)
            if blk.get("speed") and 1.0 <= blk["speed"] <= 2000.0:
                layer_positions.append({"position": pos, "block": blk})
        layer_positions.reverse()
    result["layer_blocks_raw"] = layer_positions

    # 6. Subtype statistics
    subtype_raws = [s["subtype"] for s in sigs]
    result["subtype_stats"] = {
        "unique_values": list(set(subtype_raws)),
        "unique_hex": list(set(s["subtype_hex"] for s in sigs)),
        "low16_values": list(set(s["subtype_low16"] for s in sigs)),
        "low16_hex": list(set(s["subtype_low16_hex"] for s in sigs)),
    }

    # 7. Element type distribution
    type_dist = {}
    for s in sigs:
        t = s["classified_type"]
        type_dist[t] = type_dist.get(t, 0) + 1
    result["element_type_distribution"] = type_dist

    return result


def build_catalog(vcf_dir: Path) -> dict:
    """Build catalog from all native VCF files in a directory."""
    native_vcfs = sorted(vcf_dir.glob("*.VCF"))

    # Filter: exclude synth output and binary search variants
    exclude_patterns = ["synthethic_vcf", "binary_search_variants", "fresh_"]
    native_vcfs = [
        f
        for f in native_vcfs
        if not any(p in str(f) for p in exclude_patterns)
    ]

    catalog = {
        "meta": {
            "generated_by": "build_element_types_catalog.py",
            "parser_source": str(B2B_SRC),
            "vcf_source_dir": str(vcf_dir),
        },
        "element_types": {},
        "files": [],
        "footer_summary": {},
        "subtype_summary": {},
        "gaps_vs_writer": [],
    }

    all_footer_analyses = []
    all_subtypes_low16 = {}
    all_subtypes_raw = {}

    for vcf_path in native_vcfs:
        print(f"  Parsing {vcf_path.name} ...", end=" ")
        try:
            analysis = analyze_vcf(vcf_path)
            catalog["files"].append(analysis)
            print(f"OK ({analysis['geometry_count']} geometry elements)")
        except Exception as e:
            print(f"FAIL: {e}")
            continue

        # Aggregate footer data
        fa = analysis.get("footer_analysis", {})
        if fa.get("has_footers") is True:
            all_footer_analyses.append(
                {
                    "file": analysis["filename"],
                    "template": fa.get("footer_template"),
                }
            )

        # Aggregate subtype data
        for s in analysis.get("geometry_sigs", []):
            t = s["classified_type"]
            key = f"{t}|{s['subtype_hex']}"
            all_subtypes_raw[key] = all_subtypes_raw.get(key, 0) + 1
            low_key = f"{t}|{s['subtype_low16_hex']}"
            all_subtypes_low16[low_key] = all_subtypes_low16.get(low_key, 0) + 1

    # ── Build element_types section ──
    type_groups = {}
    for f in catalog["files"]:
        for s in f.get("geometry_sigs", []):
            t = s["classified_type"]
            if t not in type_groups:
                type_groups[t] = {
                    "type_ids": set(),
                    "subtype_values_raw": set(),
                    "subtype_values_low16": set(),
                    "pt_counts": set(),
                    "has_arc_data": False,
                    "native_examples": [],
                    "segment_float64_count": 4,  # default
                }
            g = type_groups[t]
            g["type_ids"].add(s["type_id"])
            g["subtype_values_raw"].add(s["subtype_hex"])
            g["subtype_values_low16"].add(s["subtype_low16_hex"])
            g["pt_counts"].add(s["pt_count"])
            if s.get("segments"):
                has_arc = any(seg["has_arc"] for seg in s["segments"])
                if has_arc:
                    g["has_arc_data"] = True
                    g["segment_float64_count"] = 8

    for t, g in type_groups.items():
        # Find examples
        for f in catalog["files"]:
            for s in f.get("geometry_sigs", []):
                if s["classified_type"] == t:
                    g["native_examples"].append(
                        f['filename']
                    )
                    break
        # Deduplicate
        g["native_examples"] = list(OrderedDict.fromkeys(g["native_examples"]))
        catalog["element_types"][t] = {
            "type_ids": sorted(g["type_ids"]),
            "subtype_values_raw": sorted(g["subtype_values_raw"]),
            "subtype_values_low16": sorted(g["subtype_values_low16"]),
            "pt_counts": sorted(g["pt_counts"]),
            "has_arc_data": g["has_arc_data"],
            "segment_float64_count": g["segment_float64_count"],
            "segment_size_bytes": g["segment_float64_count"] * 8,
            "native_examples": g["native_examples"],
        }

    # ── Footer summary ──
    if all_footer_analyses:
        first_ft = all_footer_analyses[0]["template"]
        catalog["footer_summary"] = {
            "present_in_files": len(all_footer_analyses),
            "size": first_ft.get("footer_size") if first_ft else None,
            "pattern": first_ft.get("pattern") if first_ft else None,
            "identical_across_elements": (
                first_ft.get("pattern") == "identical" if first_ft else None
            ),
        }

    # ── Subtype summary ──
    catalog["subtype_summary"] = {
        "by_raw_value": dict(
            sorted(all_subtypes_raw.items(), key=lambda x: -x[1])
        ),
        "by_low16": dict(
            sorted(all_subtypes_low16.items(), key=lambda x: -x[1])
        ),
    }

    # ── Gaps vs writer ──
    gaps = []

    # Gap 1: Circle segment uses only 4 float64 (writer) vs 8 (native)
    if "Circle" in catalog["element_types"]:
        circle_gt = catalog["element_types"]["Circle"]
        if circle_gt["segment_float64_count"] == 8:
            gaps.append(
                {
                    "feature": "circle_segment_8_float64",
                    "native": f"{circle_gt['segment_float64_count']} float64/segment",
                    "writer": "4 float64/segment (only x1,y1,x2,y2, no d0,d1,d2)",
                    "priority": "HIGH",
                    "status": "unfixed",
                    "affected_files": circle_gt["native_examples"],
                }
            )

    # Gap 2: Missing 196B footer
    if catalog["footer_summary"].get("size") == 196:
        gaps.append(
            {
                "feature": "element_196B_footer",
                "native": "196B footer present between consecutive elements",
                "writer": "no footer generated",
                "priority": "HIGH",
                "status": "unfixed",
                "affected_files": [
                    f["filename"]
                    for f in catalog["files"]
                    if f.get("footer_analysis", {}).get("has_footers") is True
                ],
            }
        )

    # Gap 3: Subtype upper bits not preserved
    raw_vals = catalog["subtype_summary"].get("by_raw_value", {})
    non_zero_upper = [
        k for k in raw_vals if int(k.split("|")[1], 16) & 0xFFFF0000
    ]
    if non_zero_upper:
        gaps.append(
            {
                "feature": "subtype_upper_bits",
                "native": "upper 16 bits populated (metadata flags)",
                "writer": "always sets upper bits = 0",
                "priority": "MEDIUM",
                "status": "unfixed",
                "examples": non_zero_upper[:5],
            }
        )

    catalog["gaps_vs_writer"] = gaps

    return catalog


def build_markdown_report(catalog: dict) -> str:
    """Generate human-readable markdown catalog."""
    lines = []
    lines.append("# Element Types Catalog — Ground Truth\n")
    lines.append(f"**Generated:** automated\n")
    lines.append(f"**Parser source:** `{catalog['meta']['parser_source']}`\n")
    lines.append(f"**Files analyzed:** {len(catalog['files'])}\n")
    lines.append("---\n")

    # ── Element types table ──
    lines.append("## Element Types\n")
    lines.append(
        "| Type | type_id | subtype (low 16) | pt_count | Segment float64 | Arc data | Examples |"
    )
    lines.append(
        "|------|---------|------------------|----------|-----------------|----------|----------|"
    )

    for tname in sorted(catalog["element_types"].keys()):
        gt = catalog["element_types"][tname]
        lines.append(
            f"| {tname} "
            f"| {', '.join(str(x) for x in gt['type_ids'])} "
            f"| {', '.join(gt['subtype_values_low16'])} "
            f"| {', '.join(str(x) for x in gt['pt_counts'])} "
            f"| {gt['segment_float64_count']} ({gt['segment_size_bytes']} B) "
            f"| {'YES' if gt['has_arc_data'] else 'no'} "
            f"| {', '.join(gt['native_examples'][:3])} "
            f"|"
        )

    lines.append("")

    # ── Subtype detail table ──
    lines.append("## Subtype Values (raw hex)\n")
    lines.append("| Type | subtype (raw) | subtype (low 16) | Count | Files |")
    lines.append("|------|---------------|------------------|-------|-------|")

    for key, count in sorted(
        catalog["subtype_summary"].get("by_raw_value", {}).items(),
        key=lambda x: -x[1],
    ):
        t, raw_hex = key.split("|", 1)
        low16 = f"0x{int(raw_hex, 16) & 0xFFFF:04x}"
        files_containing = []
        for f in catalog["files"]:
            for s in f.get("geometry_sigs", []):
                if s["subtype_hex"] == raw_hex:
                    files_containing.append(f["filename"])
                    break
        lines.append(
            f"| {t} | {raw_hex} | {low16} | {count} | {', '.join(files_containing)} |"
        )
    lines.append("")

    # ── Footer summary ──
    lines.append("## Footer Analysis\n")
    fs = catalog["footer_summary"]
    if fs:
        for f in catalog["files"]:
            fa = f.get("footer_analysis", {})
            lines.append(f"### {f['filename']}")
            lines.append(f"- Geometry elements: {f['geometry_count']}")
            d = f.get("footer_analysis", {})
            if d.get("has_footers") is True:
                ft = d.get("footer_template", {})
                lines.append(
                    f"- Footer present: YES (size={ft.get('footer_size', '?')} B, "
                    f"pattern={ft.get('pattern', '?')})"
                )
                lines.append(f"- Deltas between elements: {d.get('deltas', [])}")
                for detail in d.get("details", []):
                    if detail.get("footer_size", 0) > 0:
                        lines.append(
                            f"  - Element {detail['element_index']} @ {detail['offset']:#x}: "
                            f"footer {detail['footer_size']} B, "
                            f"hash={detail['footer_hash']}"
                        )
                        lines.append(
                            f"    hex first 64B: {detail['footer_bytes_hex']}"
                        )
            elif d.get("has_footers") is None:
                lines.append(f"- Footer: N/A (single element)")
            else:
                lines.append(f"- Footer: NOT DETECTED (delta=0)")
            lines.append("")
    else:
        lines.append("No multi-element VCFs found.\n")

    # ── Circle segment detail ──
    lines.append("## Circle Segment Detail\n")
    for f in catalog["files"]:
        for s in f.get("geometry_sigs", []):
            if s["classified_type"] == "Circle" and s.get("segments"):
                lines.append(f"### {f['filename']} — Element @ {s['offset']:#x}")
                lines.append(f"- type_id={s['type_id']}, subtype={s['subtype_hex']}, "
                             f"pt_count={s['pt_count']}")
                for seg in s["segments"]:
                    lines.append(
                        f"  - Segment {seg['index']}: "
                        f"({seg['x1']}, {seg['y1']}) → ({seg['x2']}, {seg['y2']})  "
                        f"d0={seg['d0']}, d1={seg['d1']}, d2={seg['d2']}  "
                        f"has_arc={seg['has_arc']}"
                    )
                lines.append("")

    # ── Gaps vs writer ──
    lines.append("## Gaps vs Synthetic Writer\n")
    if catalog["gaps_vs_writer"]:
        lines.append(
            "| Feature | Native | Writer | Priority | Status |"
        )
        lines.append(
            "|---------|--------|--------|----------|--------|"
        )
        for gap in catalog["gaps_vs_writer"]:
            lines.append(
                f"| {gap['feature']} | {gap['native']} | {gap['writer']} "
                f"| {gap['priority']} | {gap['status']} |"
            )
    else:
        lines.append("No gaps detected (writer matches GT).")
    lines.append("")

    # ── Per-file summary ──
    lines.append("## Per-File Summary\n")
    lines.append("| File | Size (B) | Layers | Elements | Types | Footer |")
    lines.append("|------|----------|--------|----------|-------|--------|")
    for f in catalog["files"]:
        pp = f.get("production_parser", {})
        n_layers = pp.get("layers_count", "?")
        n_elements = pp.get("elements_count", "?")
        type_dist = ", ".join(
            f"{t}={c}" for t, c in f.get("element_type_distribution", {}).items()
        )
        fa = f.get("footer_analysis", {})
        footer_status = (
            "YES"
            if fa.get("has_footers") is True
            else ("N/A" if fa.get("has_footers") is None else "no")
        )
        lines.append(
            f"| {f['filename']} | {f['size_bytes']} | {n_layers} | {n_elements} "
            f"| {type_dist} | {footer_status} |"
        )
    lines.append("")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Element Types Catalog Builder")
    print("=" * 60)
    print(f"\n  Scanning {DEMO} for native VCF files ...")

    OUT.mkdir(parents=True, exist_ok=True)

    catalog = build_catalog(DEMO)

    # Write JSON
    json_path = OUT / "element_types_catalog.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print(f"\n  JSON -> {json_path}")

    # Write Markdown
    md_content = build_markdown_report(catalog)
    md_path = OUT / "element_types_catalog.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"  MD  -> {md_path}")

    # Summary
    n_et = len(catalog["element_types"])
    n_files = len(catalog["files"])
    n_gaps = len(catalog["gaps_vs_writer"])
    print(f"\n  Summary:")
    print(f"    Files analyzed:     {n_files}")
    print(f"    Element types found: {n_et}")
    print(f"    Gaps vs writer:      {n_gaps}")
    for g in catalog["gaps_vs_writer"]:
        print(f"      [{g['priority']}] {g['feature']} — {g['status']}")
    print(f"\n  Done.")


if __name__ == "__main__":
    main()
