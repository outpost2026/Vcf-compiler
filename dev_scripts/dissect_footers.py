"""
dissect_footers.py — Footer Field Dissector (P0)

Cil: Systematicky rozpitvat 196/245/253 B footer struktury na jednotliva pole
a statisticky urcit jejich vyznam. Analyzuje strukturu pole po poli napric
vsemi elementy v multi-element VCF a napric celou training DB.

Usage:
    python dev_scripts/dissect_footers.py
    python dev_scripts/dissect_footers.py --dir "C:/path/to/vcf/files"
    python dev_scripts/dissect_footers.py --file "path/to/single.VCF" --verbose
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
    from vcf_binary_reader import GEOMETRY_SIG
except ImportError:
    GEOMETRY_SIG = b'\x01\x00\x01\x00\x00\xff\xff\xff'

GEOMETRY_SIG_LOCAL = GEOMETRY_SIG
SEGMENT_SIZE = 74
FOOTER_CANDIDATES = [196, 245, 253]
MAX_EMPTY_BLOCKS = 256
LAYER_BLOCK_SIZE = 610


def find_all_geometry_sigs(data: bytes) -> list:
    sig = GEOMETRY_SIG_LOCAL
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
        results.append({
            "offset": pos,
            "geom_color": geom_color,
            "type_id": type_id,
            "pt_count": pt_count,
            "subtype": subtype,
            "subtype_hex": f"0x{subtype:08x}",
        })
        offset = pos + 1

    for i in range(len(results) - 1):
        results[i]["next_offset"] = results[i + 1]["offset"]
    if results:
        results[-1]["next_offset"] = None

    return results


def compute_expected_element_size(pt_count: int) -> int:
    return 45 + pt_count * SEGMENT_SIZE


def locate_footers(data: bytes, sigs: list) -> list:
    """Find footer blobs between consecutive elements."""
    footers = []
    for i, sig in enumerate(sigs):
        if sig["next_offset"] is None:
            continue
        expected_end = sig["offset"] + compute_expected_element_size(sig["pt_count"])
        actual_next = sig["next_offset"]
        delta = actual_next - expected_end
        if delta > 0:
            footer_data = data[expected_end:actual_next]
            footers.append({
                "element_index": i,
                "sig_offset": sig["offset"],
                "expected_end": expected_end,
                "actual_next": actual_next,
                "size": len(footer_data),
                "data": footer_data,
                "geom_color": sig["geom_color"],
                "type_id": sig["type_id"],
                "pt_count": sig["pt_count"],
                "subtype": sig["subtype"],
            })
    return footers


def detect_footer_size(footer_data: bytes, data: bytes, end_pos: int) -> int:
    """Detect whether this footer is 196, 245, or 253 bytes."""
    for size in sorted(FOOTER_CANDIDATES, reverse=True):
        if len(footer_data) == size:
            return size
        if len(footer_data) >= size:
            chunk = footer_data[:size]
            next_byte = data[end_pos - len(footer_data) + size] if end_pos - len(footer_data) + size < len(data) else None
            if next_byte is not None and next_byte == 0x01:
                return size
    return len(footer_data)


def try_interpret_as_float64(raw_bytes: bytes) -> float | None:
    """Test if 8 bytes can be interpreted as IEEE 754 float64."""
    try:
        val = struct.unpack("<d", raw_bytes)[0]
        if math.isnan(val) or math.isinf(val):
            return None
        if abs(val) > 1e-15 and abs(val) < 1e300:
            return val
        return None
    except (struct.error, ValueError):
        return None


def try_interpret_as_float32(raw_bytes: bytes) -> float | None:
    """Test if 4 bytes can be interpreted as IEEE 754 float32."""
    try:
        val = struct.unpack("<f", raw_bytes)[0]
        if math.isnan(val) or math.isinf(val):
            return None
        if abs(val) > 1e-15 and abs(val) < 1e40:
            return val
        return None
    except (struct.error, ValueError):
        return None


def try_interpret_ascii(raw_bytes: bytes) -> str | None:
    """Test if bytes contain printable ASCII string."""
    try:
        s = raw_bytes.decode("windows-1250")
        if all(c.isprintable() or c in '\n\r\t' for c in s):
            if any(c.isalpha() for c in s) and len(s.strip()) > 2:
                return s.strip()
        return None
    except UnicodeDecodeError:
        return None


def dissect_footer_fieldwise(footer_data: bytes, base_offset: int) -> dict:
    """Dissect footer bytes into individual fields with type detection."""
    fields = {}

    # Analyze as uint32 (4-byte windows)
    for offset in range(0, len(footer_data) - 3, 4):
        chunk = footer_data[offset:offset + 4]
        val_u32 = struct.unpack("<I", chunk)[0]
        val_i32 = struct.unpack("<i", chunk)[0]
        val_f32 = try_interpret_as_float32(chunk)
        ascii_str = try_interpret_ascii(chunk)

        field = {
            "offset": base_offset + offset,
            "offset_in_footer": offset,
            "hex": chunk.hex(),
            "uint32": val_u32,
            "int32": val_i32,
            "float32": val_f32,
            "ascii": ascii_str,
        }
        fields[offset] = field

    # Analyze as float64 (8-byte windows)
    for offset in range(0, len(footer_data) - 7, 8):
        chunk = footer_data[offset:offset + 8]
        val_f64 = try_interpret_as_float64(chunk)
        if val_f64 is not None:
            if offset not in fields:
                fields[offset] = {}
            fields[offset]["float64"] = val_f64

    return fields


def compute_field_statistics(footers: list) -> dict:
    """Compute per-offset statistics across all footers in a file."""
    if not footers:
        return {}

    all_fields = defaultdict(list)
    for footer in footers:
        fd = footer["dissected"]
        for off, field in fd.items():
            all_fields[off].append(field)

    stats = {}
    for offset, field_list in sorted(all_fields.items()):
        u32_values = [f.get("uint32") for f in field_list if f.get("uint32") is not None]
        f32_values = [f.get("float32") for f in field_list if f.get("float32") is not None]
        f64_values = [f.get("float64") for f in field_list if f.get("float64") is not None]
        ascii_values = [f["ascii"] for f in field_list if f.get("ascii")]
        raw_hex = [f["hex"] for f in field_list]

        stats[offset] = {
            "n": len(field_list),
            "constant": len(set(u32_values)) <= 1,
            "all_zero": all(v == 0 for v in u32_values),
            "all_same_hex": len(set(raw_hex)) == 1,
            "u32_min": min(u32_values) if u32_values else None,
            "u32_max": max(u32_values) if u32_values else None,
            "u32_avg": round(sum(u32_values) / len(u32_values), 1) if u32_values else None,
            "u32_values": sorted(set(u32_values))[:8] if len(set(u32_values)) <= 8 else "many",
            "has_ascii": len(ascii_values) > 0,
            "ascii_values": ascii_values[:5] if ascii_values else [],
            "has_float32": len(f32_values) > 0,
            "has_float64": len(f64_values) > 0,
            "first_hex": raw_hex[0] if raw_hex else None,
            "sample_hexes": list(set(raw_hex))[:3] if len(set(raw_hex)) <= 3 else raw_hex[:3],
        }
    return stats


def classify_field_meaning(stats: dict) -> dict:
    """Hypothesize the meaning of each field based on statistics."""
    hypotheses = {}
    for offset, s in stats.items():
        if s["all_zero"]:
            hypotheses[offset] = "unused/padding"
        elif s["constant"] and s.get("has_float64"):
            hypotheses[offset] = "constant_float64"
        elif s["constant"] and not s["all_zero"]:
            hypotheses[offset] = "constant_default"
        elif s.get("has_ascii"):
            hypotheses[offset] = "ascii_data"
        elif s.get("has_float64"):
            hypotheses[offset] = "per_element_float64"
        elif s.get("has_float32"):
            hypotheses[offset] = "per_element_float32"
        elif s["u32_min"] == 0 and s["u32_max"] is not None and s["u32_max"] <= len(stats):
            hypotheses[offset] = "element_counter_or_index"
        elif s["u32_min"] is not None and s["u32_max"] is not None and s["u32_max"] - s["u32_min"] > 10000:
            hypotheses[offset] = "offset_or_address"
        elif not s["constant"]:
            hypotheses[offset] = "per_element_uint32"
        else:
            hypotheses[offset] = "unknown"
    return hypotheses


def extract_ascii_from_footer(footer_data: bytes) -> list:
    """Extract all ASCII strings from footer data."""
    import re
    strings = re.findall(b'[A-Za-z0-9_ \\-\\.]{4,}', footer_data)
    result = []
    for s in strings:
        try:
            text = s.decode("windows-1250").strip()
            if len(text) > 3:
                result.append(text)
        except UnicodeDecodeError:
            continue
    return result


def analyze_vcf_footers(filepath: Path, verbose: bool = False) -> dict:
    data = filepath.read_bytes()
    sigs = find_all_geometry_sigs(data)

    result = {
        "filename": filepath.name,
        "size_bytes": len(data),
        "element_count": len(sigs),
    }

    if len(sigs) < 2:
        result["footer_analysis"] = {
            "has_footers": False,
            "note": "single element only, no inter-element footers",
        }
        return result

    footers = locate_footers(data, sigs)
    if not footers:
        result["footer_analysis"] = {
            "has_footers": False,
            "note": "no gaps between elements (delta=0)",
        }
        return result

    # Detect footer size
    sizes = set(f["size"] for f in footers)
    result["footer_analysis"] = {
        "has_footers": True,
        "footer_count": len(footers),
        "sizes_present": sorted(sizes),
        "dominant_size": max(set(sizes), key=list(sizes).count) if sizes else None,
    }

    # Dissect each footer
    for footer in footers:
        footer["dissected"] = dissect_footer_fieldwise(footer["data"], footer["expected_end"])

    # Compute statistics
    field_stats = compute_field_statistics(footers)
    result["footer_analysis"]["field_statistics"] = field_stats

    # Classify fields
    hypotheses = classify_field_meaning(field_stats)
    result["footer_analysis"]["field_hypotheses"] = hypotheses

    # ASCII extraction
    all_ascii = []
    for footer in footers:
        all_ascii.extend(extract_ascii_from_footer(footer["data"]))
    result["footer_analysis"]["ascii_extracts"] = sorted(set(all_ascii)) if all_ascii else []

    # Footer size comparison (196 vs 245 vs 253)
    if len(sizes) > 1:
        size_analysis = {}
        for size in sizes:
            footer_subset = [f for f in footers if f["size"] == size]
            extra_bytes = footer_subset[0]["data"][196:] if footer_subset else b""
            size_analysis[str(size)] = {
                "count": len(footer_subset),
                "extra_bytes_hex": extra_bytes.hex() if extra_bytes else "",
                "extra_bytes_len": len(extra_bytes),
            }
        result["footer_analysis"]["size_variants"] = size_analysis

    # Per-element footer summary
    result["footer_analysis"]["per_element"] = [
        {
            "index": f["element_index"],
            "size": f["size"],
            "sig_offset": f["sig_offset"],
            "geom_color": f"0x{f['geom_color']:08x}",
            "pt_count": f["pt_count"],
        }
        for f in footers
    ]

    if verbose:
        print(f"\n  Footers in {filepath.name}:")
        print(f"    Count: {len(footers)}, Sizes: {sizes}")
        print(f"    Fields analyzed: {len(field_stats)}")
        print(f"    ASCII strings: {result['footer_analysis']['ascii_extracts'][:5]}")

    return result


def build_crossfile_footer_report(results: list) -> dict:
    """Aggregate footer metadata across all files."""
    files_with_footers = [r for r in results if r["footer_analysis"].get("has_footers")]
    total_elements = sum(r["element_count"] for r in results)

    all_sizes = defaultdict(int)
    all_hypotheses = defaultdict(list)
    all_ascii = defaultdict(int)

    for r in files_with_footers:
        fa = r["footer_analysis"]
        for s in fa.get("sizes_present", []):
            all_sizes[s] += 1
        for off, hyp in fa.get("field_hypotheses", {}).items():
            all_hypotheses[hyp].append(off)
        for text in fa.get("ascii_extracts", []):
            all_ascii[text] += 1

    return {
        "files_with_footers": len(files_with_footers),
        "files_without_footers": len(results) - len(files_with_footers),
        "total_files": len(results),
        "total_elements": total_elements,
        "footer_size_distribution": dict(all_sizes),
        "hypothesis_summary": {k: len(v) for k, v in all_hypotheses.items()},
        "common_ascii_strings": sorted(
            [(text, count) for text, count in all_ascii.items() if count > 1],
            key=lambda x: -x[1],
        )[:20],
    }


def generate_footer_report_md(results: list, crossfile: dict) -> str:
    lines = []
    lines.append("# Footer Field Dissection Report\n")
    lines.append(
        f"**Generated:** by dissect_footers.py — {len(results)} VCF files analyzed\n"
    )
    lines.append("---\n")

    lines.append("## 1. Cross-File Summary\n")
    lines.append(f"- Files with multi-element footers: {crossfile['files_with_footers']}")
    lines.append(f"- Files without footers: {crossfile['files_without_footers']}")
    lines.append(f"- Total elements across all files: {crossfile['total_elements']}")
    lines.append(f"- Footer size distribution: {crossfile['footer_size_distribution']}")
    lines.append("")

    lines.append("### Common ASCII strings in footers\n")
    if crossfile["common_ascii_strings"]:
        lines.append("| String | Files |")
        lines.append("|--------|-------|")
        for text, count in crossfile["common_ascii_strings"]:
            lines.append(f"| {text} | {count} |")
    else:
        lines.append("None found.\n")
    lines.append("")

    lines.append("### Field hypothesis distribution\n")
    lines.append("| Hypothesis | Count |")
    lines.append("|------------|-------|")
    for hyp, count in sorted(crossfile["hypothesis_summary"].items(), key=lambda x: -x[1]):
        lines.append(f"| {hyp} | {count} |")
    lines.append("")

    lines.append("## 2. Per-File Footer Analysis\n")
    for r in sorted(results, key=lambda x: x["filename"]):
        fa = r["footer_analysis"]
        if not fa.get("has_footers"):
            continue
        lines.append(f"### {r['filename']}")
        lines.append(f"- Elements: {r['element_count']}")
        lines.append(f"- Footers: {fa.get('footer_count')} ({fa.get('sizes_present')})")
        lines.append(f"- ASCII: {fa.get('ascii_extracts', [])[:5]}")
        lines.append("")

        fs = fa.get("field_statistics", {})
        if fs:
            lines.append("| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |")
            lines.append("|--------|-----------|-----------|--------------|------------|-----------|------------|")
            for off, s in sorted(fs.items())[:30]:
                hyp = fa.get("field_hypotheses", {}).get(off, "?")
                u32_range = f"{s['u32_min']}..{s['u32_max']}" if s['u32_min'] is not None else "N/A"
                lines.append(
                    f"| {off} | {'YES' if s['constant'] else 'no'} | "
                    f"{'YES' if s['all_zero'] else 'no'} | "
                    f"{'YES' if s['has_float64'] else 'no'} | "
                    f"{'YES' if s['has_ascii'] else 'no'} | "
                    f"{u32_range} | {hyp} |"
                )
            lines.append("")

    lines.append("## 3. Detailed Footer Dumps (First 5 Files)\n")
    count = 0
    for r in sorted(results, key=lambda x: x["filename"]):
        if count >= 5:
            break
        fa = r["footer_analysis"]
        if not fa.get("has_footers"):
            continue
        lines.append(f"### {r['filename']}\n")
        lines.append("```")
        for f in fa.get("per_element", [])[:3]:
            lines.append(
                f"  Element {f['index']} @ {f['sig_offset']:#x}: "
                f"size={f['size']}B, color={f['geom_color']}, "
                f"pts={f['pt_count']}"
            )
        lines.append("```\n")
        count += 1

    lines.append("## 4. Field Meaning Hypotheses\n")
    lines.append("### Known / Confirmed fields:\n")
    lines.append("- Offset 0-3: likely DXF group code data")
    lines.append("- Offset 4-196: bounding box values, element metadata")
    lines.append("- Offset 196-245 (variant only): extra 49B (purpose unknown)")
    lines.append("")
    lines.append("### Based on statistical analysis:\n")
    for hyp in sorted(set(
        h for r in results
        for h in r.get("footer_analysis", {}).get("field_hypotheses", {}).values()
    )):
        examples = []
        for r in results:
            fa = r.get("footer_analysis", {})
            for off, h in fa.get("field_hypotheses", {}).items():
                if h == hyp:
                    examples.append(f"@{off}")
                    break
        lines.append(f"- **{hyp}**: offsets {', '.join(examples[:10])}")
    lines.append("")

    return "\n".join(lines)


def collect_vcf_files(dirs: list, single_file: Path = None) -> list:
    if single_file:
        return [single_file]

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
        description="Footer Field Dissector — RE tool for VCF format"
    )
    parser.add_argument("--dir", type=str, default=None)
    parser.add_argument("--file", type=str, default=None)
    parser.add_argument("--out", type=str, default=str(OUT))
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("  Footer Field Dissector (P0)")
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
            analysis = analyze_vcf_footers(vcf_path, verbose=args.verbose)
            results.append(analysis)
            fa = analysis["footer_analysis"]
            if fa.get("has_footers"):
                print(f"  {vcf_path.name}: {fa['footer_count']} footers, "
                      f"sizes={fa['sizes_present']}, "
                      f"fields={len(fa.get('field_statistics', {}))}, "
                      f"ascii={len(fa.get('ascii_extracts', []))}")
            else:
                print(f"  {vcf_path.name}: {fa.get('note', 'no footers')}")
        except Exception as e:
            print(f"  {vcf_path.name}: FAIL: {e}")

    if not results:
        print("  No files analyzed.")
        return

    crossfile = build_crossfile_footer_report(results)

    # Write JSON
    report_json = {
        "meta": {
            "tool": "dissect_footers.py",
            "files_analyzed": len(results),
        },
        "crossfile_summary": crossfile,
        "per_file": results,
    }
    json_path = out_dir / "RESULT_footer_matrix.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2, ensure_ascii=False)
    print(f"\n  JSON -> {json_path}")

    # Write MD
    md_content = generate_footer_report_md(results, crossfile)
    md_path = out_dir / "RESULT_footer_field_hypotheses.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"  MD  -> {md_path}")

    # Summary
    print(f"\n  Summary:")
    print(f"    Files:              {len(results)}")
    print(f"    Files w/ footers:   {crossfile['files_with_footers']}")
    print(f"    Sizes observed:     {crossfile['footer_size_distribution']}")
    ascii_total = len(crossfile.get("common_ascii_strings", []))
    print(f"    Common ASCII strs:  {ascii_total}")
    print(f"\n  Done.")


if __name__ == "__main__":
    main()
