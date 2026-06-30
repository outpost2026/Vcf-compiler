"""
dissect_layer_blocks.py — Layer Block Forensics (P0)

Cil: Kompletne zmapovat vsech 610 B layer bloku (1.0.013) — aktivnich i prazdnych —
a vytvorit definitivni field map. Analyzuje kazdy 4/8 B usek, statistiku napric
aktivnimi bloky, prazdnymi bloky a cross-file agregaci.

Usage:
    python dev_scripts/dissect_layer_blocks.py
    python dev_scripts/dissect_layer_blocks.py --file "path/to/single.VCF" --verbose
"""

import sys
import os
import json
import struct
import math
import logging
from pathlib import Path
from collections import defaultdict

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DEMO = REPO / "demo_data"
NATIVE_VCF = DEMO / "native_vcf"
TRAINING_DB = Path(r"C:\Users\PC\Documents\Repozitar_Dev\_github\VCF_files_moodpasta")
OUT = REPO / "research_docs"

B2B_SRC = Path(r"C:\Users\PC\Documents\Repozitar_Dev\_github\vcf_parser_b2b\src")
sys.path.insert(0, str(B2B_SRC))

try:
    from vcf_binary_reader import GEOMETRY_SIG, extract_active_layers_details
except ImportError:
    GEOMETRY_SIG = b'\x01\x00\x01\x00\x00\xff\xff\xff'
    extract_active_layers_details = None

GEOMETRY_SIG_LOCAL = GEOMETRY_SIG
LAYER_BLOCK_SIZE = 610
EMPTY_BLOCK_COUNT = 256
HEADER_SIZE_013 = 472

# Known fields with their offset, format, and label
KNOWN_FIELDS = {
    0: ("<I", "output_flag"),
    4: ("<d", "speed_mms"),
    10: ("<H", "block_index"),
    12: ("<I", "color_val"),
    32: ("<i", "cutter_type_raw"),
    40: ("<d", "field_40"),
    76: ("<I", "color_76"),
    80: ("<d", "h1_mm"),
    88: ("<i", "feed_count"),
    92: ("<B", "element_count_flag"),
    96: ("<d", "h2_mm"),
    104: ("<H", "direction"),
    106: ("<d", "field_106"),
    114: ("<d", "start_extension"),
    122: ("<d", "end_extension"),
    197: ("<B", "field_197"),
    198: ("<d", "field_198"),
    602: ("<I", "next_layer_flag"),
    606: ("<I", "next_layer_color"),
}


def detect_format(data: bytes) -> str:
    if b"RDVCUTFILEVER1.0.013" in data or b"VER1.0.013" in data:
        return "1.0.013"
    if b"RDVCUTFILEVER1.0.012" in data or b"VER1.0.012" in data:
        return "1.0.012"
    return "unknown"


def find_first_geometry_sig(data: bytes) -> int | None:
    pos = data.find(GEOMETRY_SIG_LOCAL)
    return pos if pos != -1 else None


def extract_block_fields(data: bytes, block_offset: int) -> dict:
    """Extract all known + unknown fields from a 610B block."""
    fields = {}

    for off, (fmt, label) in KNOWN_FIELDS.items():
        try:
            val = struct.unpack_from(fmt, data, block_offset + off)[0]
            if fmt == "<d":
                if not (math.isnan(val) or math.isinf(val)):
                    fields[label] = round(val, 4)
            else:
                fields[label] = val
        except (struct.error, ValueError):
            pass

    # Unknown fields: every 4 bytes
    unknown_4b = {}
    for off in range(0, LAYER_BLOCK_SIZE - 3, 4):
        if off in KNOWN_FIELDS:
            continue
        try:
            chunk = data[block_offset + off:block_offset + off + 4]
            u32 = struct.unpack("<I", chunk)[0]
            as_f32 = struct.unpack("<f", chunk)[0]
            unknown_4b[off] = {
                "hex": chunk.hex(),
                "uint32": u32,
                "float32": None if math.isnan(as_f32) or math.isinf(as_f32) else round(as_f32, 6),
            }
        except Exception:
            pass

    fields["_unknown_4b"] = unknown_4b
    fields["_block_offset"] = block_offset
    return fields


def locate_all_blocks(data: bytes, first_geom_sig: int) -> dict:
    """Locate all layer blocks (256 empty + active) before first geometry."""
    version = detect_format(data)
    if version != "1.0.013":
        return {
            "version": version,
            "note": "only 1.0.013 format supports 610B block analysis",
            "blocks": [],
        }

    # Empty blocks: before first active block
    # Active blocks: immediately before first geometry sig (backward scan)
    blocks = []

    # First active block is right before first geometry sig
    # But we need to find the start of block region
    # Blocks are contiguous: 256 empty + N active, each 610B
    # The first geometry sig starts immediately after the last active block

    # Scan backward from first_geom_sig to find the block region start
    # The block region starts at header_size_013 and extends to first_geom_sig
    header_end = HEADER_SIZE_013
    block_region_size = first_geom_sig - header_end
    total_blocks = block_region_size // LAYER_BLOCK_SIZE
    remainder = block_region_size % LAYER_BLOCK_SIZE

    if total_blocks == 0:
        return {
            "version": version,
            "note": "no blocks found before geometry sig",
            "blocks": [],
        }

    for i in range(total_blocks):
        block_offset = header_end + i * LAYER_BLOCK_SIZE
        block_data = data[block_offset:block_offset + LAYER_BLOCK_SIZE]
        if len(block_data) < LAYER_BLOCK_SIZE:
            break
        fields = extract_block_fields(data, block_offset)
        fields["block_index_in_file"] = i
        output_flag_raw = struct.unpack_from("<I", data, block_offset)[0]
        fields["_output_flag_raw"] = output_flag_raw
        fields["is_active"] = (output_flag_raw == 1)
        fields["hash_hex"] = hash(block_data) % (2**32)
        blocks.append(fields)



    return {
        "version": version,
        "block_count": len(blocks),
        "empty_block_count": sum(1 for b in blocks if not b["is_active"]),
        "active_block_count": sum(1 for b in blocks if b["is_active"]),
        "expected_empty": EMPTY_BLOCK_COUNT,
        "expected_total": EMPTY_BLOCK_COUNT + 32,
        "remainder_bytes": remainder,
        "blocks": blocks,
    }


def compute_empty_block_stats(blocks: list) -> dict:
    """Analyze empty (non-active) blocks for patterns."""
    empty = [b for b in blocks if not b["is_active"]]
    if not empty:
        return {"count": 0}

    # Check if all empty blocks are identical
    hashes = set(b.get("hash_hex", 0) for b in empty)
    all_identical = len(hashes) == 1

    # Check block index pattern
    indices = [b.get("block_index", -1) for b in empty if b.get("block_index") is not None]

    # Check for any varying field in empty blocks
    varying_offsets = set()
    if len(empty) > 1:
        first_unknown = empty[0].get("_unknown_4b", {})
        for b in empty[1:]:
            bu = b.get("_unknown_4b", {})
            for off in first_unknown:
                if off in bu and first_unknown[off]["hex"] != bu[off]["hex"]:
                    varying_offsets.add(off)

    return {
        "count": len(empty),
        "all_identical": all_identical,
        "unique_hashes": len(hashes),
        "indices": sorted(set(indices))[:16],
        "varying_unknown_offsets": sorted(varying_offsets)[:10],
    }


def compute_active_block_stats(blocks: list) -> dict:
    """Compute per-field statistics across active blocks."""
    active = [b for b in blocks if b["is_active"]]
    if not active:
        return {"count": 0}

    stats = {"count": len(active)}
    for label in KNOWN_FIELDS.values():
        label = label[1] if isinstance(label, tuple) else label
        values = [b.get(label) for b in active if b.get(label) is not None]
        if not values:
            continue

        numeric = [v for v in values if isinstance(v, (int, float))]
        if numeric:
            stats[label] = {
                "n": len(numeric),
                "constant": len(set(numeric)) == 1,
                "min": min(numeric) if numeric else None,
                "max": max(numeric) if numeric else None,
                "avg": round(sum(numeric) / len(numeric), 4) if numeric else None,
                "unique": sorted(set(numeric))[:8] if len(set(numeric)) <= 8 else f"many ({len(set(numeric))})",
            }
        else:
            stats[label] = {
                "n": len(values),
                "unique": sorted(set(values))[:8],
            }

    # Unknown 4B fields: which vary across active blocks
    unknown_variation = defaultdict(set)
    for b in active:
        for off, info in b.get("_unknown_4b", {}).items():
            unknown_variation[off].add(info["hex"])

    varying_unknown = {str(off): len(vals) for off, vals in unknown_variation.items() if len(vals) > 1}
    constant_unknown = [off for off, vals in unknown_variation.items() if len(vals) == 1]

    stats["_unknown_4b_varying"] = {
        "total_unknown_offsets": len(unknown_variation),
        "varying_count": len(varying_unknown),
        "constant_count": len(constant_unknown),
        "most_varying": sorted(varying_unknown.items(), key=lambda x: -x[1])[:10],
    }

    return stats


def analyze_vcf_blocks(filepath: Path, verbose: bool = False) -> dict:
    data = filepath.read_bytes()
    version = detect_format(data)
    first_geom = find_first_geometry_sig(data)

    result = {
        "filename": filepath.name,
        "size_bytes": len(data),
        "version": version,
    }

    if version != "1.0.013":
        result["block_analysis"] = {"note": f"unsupported version: {version}"}
        return result

    if first_geom is None:
        result["block_analysis"] = {"note": "no geometry sig found, cannot locate blocks"}
        return result

    block_info = locate_all_blocks(data, first_geom)
    blocks = block_info.get("blocks", [])

    empty_stats = compute_empty_block_stats(blocks)
    active_stats = compute_active_block_stats(blocks)

    result["block_analysis"] = {
        "version": version,
        "first_geom_offset": first_geom,
        "header_size": HEADER_SIZE_013,
        "block_region_start": HEADER_SIZE_013,
        "block_region_end": first_geom,
        "block_region_size": first_geom - HEADER_SIZE_013,
        "found_blocks": block_info.get("block_count", 0),
        "expected_blocks": EMPTY_BLOCK_COUNT + 32,
        "remainder_bytes": block_info.get("remainder_bytes", 0),
        "empty_blocks": empty_stats,
        "active_blocks": active_stats,
    }

    if verbose:
        print(f"\n  Blocks in {filepath.name}:")
        print(f"    Total: {block_info.get('block_count', 0)} "
              f"(empty: {empty_stats.get('count', 0)}, "
              f"active: {active_stats.get('count', 0)})")
        print(f"    Empty identical: {empty_stats.get('all_identical', 'N/A')}")

    return result


def build_crossfile_block_report(results: list) -> dict:
    """Aggregate block metadata across all 1.0.013 files."""
    files_013 = [r for r in results if r.get("version") == "1.0.013"]

    # Empty block patterns
    empty_patterns = defaultdict(int)
    for r in files_013:
        ba = r.get("block_analysis", {})
        es = ba.get("empty_blocks", {})
        pattern_key = str(es.get("all_identical", "?"))
        empty_patterns[f"identical={pattern_key}"] += 1

    # Block count analysis
    expected = EMPTY_BLOCK_COUNT + 32
    exact_match = sum(1 for r in files_013
                      if r.get("block_analysis", {}).get("found_blocks", 0) == expected)
    remainder_present = sum(1 for r in files_013
                            if r.get("block_analysis", {}).get("remainder_bytes", 0) > 0)

    return {
        "files_013": len(files_013),
        "empty_block_patterns": dict(empty_patterns),
        "exact_block_count_match": exact_match,
        "files_with_remainder": remainder_present,
    }


def generate_block_report_md(results: list, crossfile: dict) -> str:
    lines = []
    lines.append("# Layer Block Field Map — Forensics Report\n")
    lines.append(
        f"**Generated:** by dissect_layer_blocks.py — "
        f"{len(results)} VCF files analyzed\n"
    )
    lines.append("---\n")

    lines.append("## 1. Cross-File Summary\n")
    lines.append(f"- Files analyzed: {len(results)}")
    lines.append(f"- Files with 1.0.013 format: {crossfile['files_013']}")
    lines.append(f"- Files with exact block count ({EMPTY_BLOCK_COUNT}+32): "
                 f"{crossfile['exact_block_count_match']}")
    lines.append(f"- Files with remainder bytes: {crossfile['files_with_remainder']}")
    lines.append("")

    lines.append("### Empty block patterns\n")
    for pattern, count in sorted(crossfile["empty_block_patterns"].items()):
        lines.append(f"- {pattern}: {count} files")
    lines.append("")

    lines.append("## 2. Per-File Block Summary\n")
    lines.append("| File | Version | Found Blocks | Empty | Active | Empty Identical? | Remainder |")
    lines.append("|------|---------|-------------|-------|--------|-----------------|-----------|")
    for r in sorted(results, key=lambda x: x["filename"]):
        ba = r.get("block_analysis", {})
        if "note" in ba:
            lines.append(f"| {r['filename']} | {r['version']} | {ba.get('note', 'N/A')} | - | - | - | - |")
        else:
            es = ba.get("empty_blocks", {})
            a_stats = ba.get("active_blocks", {})
            lines.append(
                f"| {r['filename']} | {r['version']} | {ba.get('found_blocks', 0)} "
                f"| {es.get('count', 0)} | {a_stats.get('count', 0)} "
                f"| {es.get('all_identical', '?')} "
                f"| {ba.get('remainder_bytes', 0)} B |"
            )
    lines.append("")

    lines.append("## 3. Active Block Field Statistics\n")
    lines.append("### Known fields\n")
    lines.append("| Field | Constant? | Min | Max | Avg | Unique |")
    lines.append("|-------|-----------|-----|-----|-----|--------|")

    # Aggregate field stats across all 1.0.013 files
    field_aggregate = defaultdict(list)
    for r in results:
        ba = r.get("block_analysis", {})
        a_stats = ba.get("active_blocks", {})
        for label, s in a_stats.items():
            if label.startswith("_"):
                continue
            if isinstance(s, dict) and "constant" in s:
                field_aggregate[label].append(s)

    for label in sorted(field_aggregate.keys()):
        stats = field_aggregate[label]
        all_const = all(s.get("constant", False) for s in stats if s.get("n", 0) > 0)
        mins = [s["min"] for s in stats if s.get("min") is not None]
        maxs = [s["max"] for s in stats if s.get("max") is not None]
        avgs = [s["avg"] for s in stats if s.get("avg") is not None]
        lines.append(
            f"| {label} | "
            f"{'YES' if all_const else 'VARIES'} | "
            f"{min(mins) if mins else '-'} | "
            f"{max(maxs) if maxs else '-'} | "
            f"{round(sum(avgs)/len(avgs), 4) if avgs else '-'} | "
            f"|"
        )
    lines.append("")

    lines.append("### Unknown (4B) fields — most varying\n")
    lines.append("| File | Offset | Unique Values | Sample |")
    lines.append("|------|--------|---------------|--------|")
    for r in sorted(results, key=lambda x: x["filename"]):
        ba = r.get("block_analysis", {})
        a_stats = ba.get("active_blocks", {})
        uk = a_stats.get("_unknown_4b_varying", {})
        for off_info in uk.get("most_varying", [])[:5]:
            off, count = off_info
            lines.append(f"| {r['filename']} | {off} | {count} | - |")
    lines.append("")

    lines.append("## 4. Empty Block Analysis\n")
    lines.append("| File | Count | All Identical? | Varying Offsets | Key Pattern |")
    lines.append("|------|-------|---------------|----------------|-------------|")
    for r in sorted(results, key=lambda x: x["filename"]):
        ba = r.get("block_analysis", {})
        es = ba.get("empty_blocks", {})
        if es.get("count", 0) == 0:
            continue
        varying = es.get("varying_unknown_offsets", [])
        lines.append(
            f"| {r['filename']} | {es.get('count', 0)} | "
            f"{'YES' if es.get('all_identical') else 'no'} | "
            f"{varying[:3] if varying else 'none'} | "
            f"indices={es.get('indices', [])[:5]} |"
        )
    lines.append("")

    lines.append("## 5. Field Map Hypothesis\n")
    lines.append("Based on cross-file statistics, the known field map is:\n")
    lines.append("| Offset | Size | Field | Status | Notes |")
    lines.append("|--------|------|-------|--------|-------|")
    known_list = [
        (0, 4, "output_flag", "confirmed"),
        (4, 8, "speed_mms", "confirmed"),
        (10, 2, "block_index", "confirmed"),
        (12, 4, "color_val", "confirmed", "BGR 24-bit"),
        (32, 4, "cutter_type", "confirmed", "0=Vibrate, 3=V-slot"),
        (40, 8, "field_40", "unknown"),
        (76, 4, "color_76", "unknown", "may duplicate color_val"),
        (80, 8, "h1_mm", "confirmed"),
        (88, 4, "feed_count", "confirmed"),
        (92, 1, "element_count_flag", "confirmed", "1=has geometry"),
        (96, 8, "h2_mm", "confirmed"),
        (104, 2, "direction", "confirmed", "V-slot direction"),
        (106, 8, "field_106", "unknown", "V-slot compensation?"),
        (114, 8, "start_extension", "confirmed"),
        (122, 8, "end_extension", "confirmed"),
        (197, 1, "field_197", "unknown"),
        (198, 8, "field_198", "unknown"),
        (602, 4, "next_layer_flag", "confirmed", "linked-list flag"),
        (606, 4, "next_layer_color", "confirmed", "element count/color"),
    ]
    for entry in known_list:
        offset = entry[0]
        size = entry[1]
        label = entry[2]
        status = entry[3]
        notes = entry[4] if len(entry) > 4 else ""
        lines.append(f"| {offset} | {size} B | {label} | {status} | {notes} |")
    lines.append("")

    return "\n".join(lines)


def collect_vcf_files(dirs: list) -> list:
    vcf_files = []
    for d in dirs:
        if d.exists():
            vcf_files.extend(sorted(d.glob("*.VCF")))

    exclude_patterns = ["synthethic_vcf", "binary_search_variants",
                        "synthetic_vcf", "json_outputs"]
    vcf_files = [
        f for f in vcf_files
        if not any(p in str(f) for p in exclude_patterns)
    ]
    return vcf_files


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Layer Block Forensics — RE tool for VCF format"
    )
    parser.add_argument("--dir", type=str, default=None)
    parser.add_argument("--file", type=str, default=None)
    parser.add_argument("--out", type=str, default=str(OUT))
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("  Layer Block Forensics (P0)")
    print("=" * 60)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.file:
        vcf_files = [Path(args.file)]
    else:
        dirs = [NATIVE_VCF]
        if args.dir:
            dirs.insert(0, Path(args.dir))
        if TRAINING_DB.exists():
            dirs.append(TRAINING_DB)
        vcf_files = collect_vcf_files(dirs)

    print(f"  Scanning {len(vcf_files)} VCF files ...")

    results = []
    for vcf_path in vcf_files:
        try:
            analysis = analyze_vcf_blocks(vcf_path, verbose=args.verbose)
            results.append(analysis)
            ba = analysis.get("block_analysis", {})
            if "note" in ba:
                print(f"  {vcf_path.name}: {ba['note']}")
            else:
                print(f"  {vcf_path.name}: {ba.get('found_blocks', 0)} blocks "
                      f"({ba.get('empty_blocks', {}).get('count', 0)} empty, "
                      f"{ba.get('active_blocks', {}).get('count', 0)} active)")
        except Exception as e:
            print(f"  {vcf_path.name}: FAIL: {e}")

    crossfile = build_crossfile_block_report(results)

    # Write JSON
    report_json = {
        "meta": {
            "tool": "dissect_layer_blocks.py",
            "files_analyzed": len(results),
        },
        "crossfile_summary": crossfile,
        "per_file": results,
    }
    json_path = out_dir / "RESULT_layer_block_field_map.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2, ensure_ascii=False)
    print(f"\n  JSON -> {json_path}")

    # Write MD
    md_content = generate_block_report_md(results, crossfile)
    md_path = out_dir / "RESULT_layer_block_field_map.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"  MD  -> {md_path}")

    print(f"\n  Summary:")
    print(f"    Files:              {len(results)}")
    print(f"    Files 1.0.013:      {crossfile['files_013']}")
    print(f"    Exact block count:  {crossfile['exact_block_count_match']}")
    print(f"\n  Done.")


if __name__ == "__main__":
    main()
