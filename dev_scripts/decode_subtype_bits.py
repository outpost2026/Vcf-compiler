"""
decode_subtype_bits.py — Subtype Upper-Bit Correlator (P0)

Cil: Statisticky urcit, co koduje hornich 16 bitu subtype hodnoty,
ktera se lisi soubor od souboru. Testovane hypotezy:
  - File-level checksum/hash
  - Cutter configuration profile ID
  - Material ID
  - Speed range encoding
  - Bit field s vice vyznamy

Usage:
    python dev_scripts/decode_subtype_bits.py
    python dev_scripts/decode_subtype_bits.py --dir "C:/path/to/vcf/files"
    python dev_scripts/decode_subtype_bits.py --file "path/to/single.VCF"
"""

import sys
import os
import json
import struct
import hashlib
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
    from vcf_binary_reader import GEOMETRY_SIG, extract_active_layers_details, extract_strings
except ImportError as e:
    logger.error("Cannot import vcf_parser_b2b: %s", e)
    GEOMETRY_SIG = b'\x01\x00\x01\x00\x00\xff\xff\xff'
    extract_active_layers_details = None
    extract_strings = None


GEOMETRY_SIG_LOCAL = GEOMETRY_SIG
SEGMENT_SIZE = 74


def detect_format(data: bytes) -> str:
    if b"RDVCUTFILEVER1.0.013" in data or b"VER1.0.013" in data:
        return "1.0.013"
    if b"RDVCUTFILEVER1.0.012" in data or b"VER1.0.012" in data:
        return "1.0.012"
    return "unknown"


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
            "geom_color_hex": f"0x{geom_color:08x}",
            "type_id": type_id,
            "pt_count": pt_count,
            "subtype": subtype,
            "subtype_hex": f"0x{subtype:08x}",
            "subtype_low16": subtype & 0xFFFF,
            "subtype_low16_hex": f"0x{(subtype & 0xFFFF):04x}",
            "subtype_upper16": (subtype >> 16) & 0xFFFF,
            "subtype_upper16_hex": f"0x{(subtype >> 16) & 0xFFFF:04x}",
        })
        offset = pos + 1
    return results


def extract_layer_block_upper_bits(data: bytes, sigs: list) -> list:
    """Try to extract and correlate layer block parameters with subtype."""
    if not sigs or extract_active_layers_details is None:
        return []
    try:
        layers = extract_active_layers_details(data)
    except Exception:
        return []

    for layer in layers:
        speed = layer.get("speed_mms", 0)
        cutter = layer.get("cutter_type", "")
        h2 = layer.get("end_height_h2_mm", 0.0)
        color = layer.get("color_val", 0)
        layer["params_hash"] = hash((speed, cutter, h2, color))

    return layers


def compute_file_hash(data: bytes) -> dict:
    return {
        "md5_first_64": hashlib.md5(data[:64]).hexdigest(),
        "md5_first_256": hashlib.md5(data[:256]).hexdigest(),
        "md5_full": hashlib.md5(data).hexdigest(),
        "size_bytes": len(data),
    }


def analyze_vcf(filepath: Path) -> dict:
    data = filepath.read_bytes()
    version = detect_format(data)

    result = {
        "filename": filepath.name,
        "filepath": str(filepath),
        "size_bytes": len(data),
        "version": version,
        "file_hash": compute_file_hash(data),
    }

    sigs = find_all_geometry_sigs(data)
    result["element_count"] = len(sigs)
    result["elements"] = sigs

    upper_bits = set(s["subtype_upper16"] for s in sigs)
    result["upper_bits_summary"] = {
        "unique_upper_bits": sorted(upper_bits),
        "unique_upper_bits_hex": sorted(set(s["subtype_upper16_hex"] for s in sigs)),
        "count": len(upper_bits),
    }

    low16_bits = set(s["subtype_low16"] for s in sigs)
    result["low16_summary"] = {
        "unique_low16": sorted(low16_bits),
        "unique_low16_hex": sorted(set(s["subtype_low16_hex"] for s in sigs)),
    }

    type_ids = set(s["type_id"] for s in sigs)
    result["type_ids"] = sorted(type_ids)

    layers = extract_layer_block_upper_bits(data, sigs)
    result["layers"] = layers
    result["layer_count"] = len(layers)

    if extract_strings is not None:
        try:
            result["metadata_strings"] = extract_strings(data)
        except Exception:
            result["metadata_strings"] = []

    result["unique_speeds"] = sorted(set(
        l["speed_mms"] for l in layers if "speed_mms" in l
    ))
    result["unique_cutters"] = list(set(
        l["cutter_type"] for l in layers if "cutter_type" in l
    ))

    return result


def bit_field_test(results: list) -> dict:
    """Test if upper 16 bits encode individual features as bit flags."""
    all_upper = set()
    for r in results:
        for e in r["elements"]:
            all_upper.add(e["subtype_upper16"])

    bit_positions = set()
    for val in all_upper:
        for bit in range(16):
            if val & (1 << bit):
                bit_positions.add(bit)

    bit_correlations = {}
    for bit in sorted(bit_positions):
        mask = 1 << bit
        # Check if this bit correlates with any feature
        speed_corr = feature_bit_correlation(results, mask, "speed_cutter")
        bit_correlations[f"bit_{bit}"] = {
            "present_in": sum(1 for r in results for e in r["elements"] if e["subtype_upper16"] & mask),
            "feature_correlation": speed_corr,
        }

    return bit_correlations


def feature_bit_correlation(results: list, bit_mask: int, feature: str) -> dict:
    """Check if a bit correlates with a specific feature."""
    files_with_bit = []
    files_without_bit = []

    for r in results:
        has_bit = any(e["subtype_upper16"] & bit_mask for e in r["elements"])
        if has_bit:
            files_with_bit.append(r)
        else:
            files_without_bit.append(r)

    # Compare speeds between groups
    speeds_with = set()
    for r in files_with_bit:
        speeds_with.update(r.get("unique_speeds", []))
    speeds_without = set()
    for r in files_without_bit:
        speeds_without.update(r.get("unique_speeds", []))

    return {
        "files_with_bit": len(files_with_bit),
        "files_without_bit": len(files_without_bit),
        "speeds_with": sorted(speeds_with),
        "speeds_without": sorted(speeds_without),
        "cutters_with": list(set(c for r in files_with_bit for c in r.get("unique_cutters", []))),
        "cutters_without": list(set(c for r in files_without_bit for c in r.get("unique_cutters", []))),
    }


def build_correlation_matrix(results: list) -> dict:
    upper_groups = defaultdict(list)
    for r in results:
        for ub in r["upper_bits_summary"]["unique_upper_bits"]:
            upper_groups[ub].append(r["filename"])

    correlation = {}
    for ub, files in sorted(upper_groups.items()):
        speeds = sorted(set(
            s for r in results if r["filename"] in files
            for s in r.get("unique_speeds", [])
        ))
        cutters = list(set(
            c for r in results if r["filename"] in files
            for c in r.get("unique_cutters", [])
        ))
        versions = list(set(
            r["version"] for r in results if r["filename"] in files
        ))
        type_ids = sorted(set(
            tid for r in results if r["filename"] in files
            for tid in r.get("type_ids", [])
        ))
        hashes = list(set(
            r["file_hash"]["md5_first_64"] for r in results if r["filename"] in files
        ))

        correlation[f"0x{ub:04x}"] = {
            "files": files,
            "count": len(files),
            "speeds": speeds,
            "cutters": cutters,
            "versions": versions,
            "type_ids": type_ids,
            "unique_hashes_count": len(hashes),
        }

    return correlation


def generate_hypothesis_report(results: list, correlation: dict, bit_tests: dict) -> str:
    lines = []
    lines.append("# Subtype Upper-Bit Decoding — Hypotheses Report\n")
    lines.append(
        f"**Generated:** by decode_subtype_bits.py analyzing {len(results)} VCF files\n"
    )
    lines.append("---\n")

    # === Summary ===
    lines.append("## 1. Summary\n")
    all_upper = set()
    for r in results:
        all_upper.update(r["upper_bits_summary"]["unique_upper_bits"])
    lines.append(f"- Total files analyzed: {len(results)}")
    lines.append(f"- Unique upper 16-bit values: {len(all_upper)} ({', '.join(f'0x{v:04x}' for v in sorted(all_upper))})")
    lines.append("")

    # === Per-file upper bits ===
    lines.append("## 2. Per-File Upper Bits\n")
    lines.append("| File | Upper Bits | Low 16 | Elements | Layers | Speeds | Cutters | Type IDs | Version |")
    lines.append("|------|------------|--------|----------|--------|--------|---------|---------|---------|")
    for r in sorted(results, key=lambda x: x["filename"]):
        ub = ", ".join(r["upper_bits_summary"]["unique_upper_bits_hex"])
        lb = ", ".join(r["low16_summary"]["unique_low16_hex"])
        speeds = ", ".join(str(s) for s in r.get("unique_speeds", []))
        cutters = ", ".join(r.get("unique_cutters", []))
        lines.append(
            f"| {r['filename']} | {ub} | {lb} | {r['element_count']} "
            f"| {r['layer_count']} | {speeds} | {cutters} "
            f"| {', '.join(str(t) for t in r['type_ids'])} | {r['version']} |"
        )
    lines.append("")

    # === Correlation clusters ===
    lines.append("## 3. Upper-Bit Clusters\n")
    lines.append("| Upper Bits | Files | Speeds | Cutters | Versions | Type IDs | Hash Unique? |")
    lines.append("|------------|-------|--------|---------|----------|----------|--------------|")
    for ub_hex, info in sorted(correlation.items()):
        files_short = ", ".join(f[:20] for f in info["files"][:4])
        if len(info["files"]) > 4:
            files_short += f" ... (+{len(info['files'])-4})"
        lines.append(
            f"| {ub_hex} | {files_short} "
            f"| {', '.join(str(s) for s in info['speeds'])} "
            f"| {', '.join(info['cutters'])} "
            f"| {', '.join(info['versions'])} "
            f"| {', '.join(str(t) for t in info['type_ids'])} "
            f"| {'YES' if info['unique_hashes_count'] == 1 else 'NO' if info['unique_hashes_count'] > 0 else 'N/A'} |"
        )
    lines.append("")

    # === Bit field test ===
    lines.append("## 4. Bit Field Analysis\n")
    lines.append("| Bit | Files with bit | Speeds (with) | Speeds (without) | Cutters (with) | Cutters (without) |")
    lines.append("|-----|---------------|---------------|------------------|----------------|-------------------|")
    for bit_name, info in sorted(bit_tests.items()):
        fc = info["feature_correlation"]
        lines.append(
            f"| {bit_name} | {fc['files_with_bit']} "
            f"| {', '.join(str(s) for s in fc['speeds_with'][:5])} "
            f"| {', '.join(str(s) for s in fc['speeds_without'][:5])} "
            f"| {', '.join(fc['cutters_with'][:3])} "
            f"| {', '.join(fc['cutters_without'][:3])} |"
        )
    lines.append("")

    # === Hypotheses ===
    lines.append("## 5. Hypotheses\n")

    # Hypothesis 1: File checksum
    hash_unique_counts = set()
    for ub_hex, info in correlation.items():
        hash_unique_counts.add(info["unique_hashes_count"])
    checksum_likely = all(c == 1 for c in hash_unique_counts if c > 0)
    lines.append("### H1: File checksum / hash of first N bytes\n")
    lines.append(
        f"- Evidence: Each upper-bit group has {'1 unique MD5' if checksum_likely else 'multiple MD5 hashes'} "
        f"in first 64 bytes."
    )
    lines.append(
        f"- Verdict: {'LIKELY' if checksum_likely else 'UNLIKELY'} — "
        f"{'upper bits may be a hash/checksum of header data' if checksum_likely else 'not a simple file hash'}"
    )
    lines.append("")

    # Hypothesis 2: Cutter config profile ID
    # If each upper bit group has consistent cutter types
    cutter_consistent = all(
        len(info["cutters"]) == 1 for info in correlation.values()
    )
    lines.append("### H2: Cutter configuration profile ID\n")
    lines.append(
        f"- Evidence: {'All' if cutter_consistent else 'Some'} upper-bit groups map to a single cutter type."
    )
    lines.append(
        f"- Verdict: {'LIKELY' if cutter_consistent else 'PARTIAL'} — "
        f"upper bits {'may encode' if cutter_consistent else 'partially correlate with'} cutter config"
    )
    lines.append("")

    # Hypothesis 3: Speed range encoding
    lines.append("### H3: Speed range encoding\n")
    speed_variance = {}
    for ub_hex, info in correlation.items():
        if info["speeds"]:
            speed_variance[ub_hex] = max(info["speeds"]) - min(info["speeds"])
    narrow_ranges = sum(1 for v in speed_variance.values() if v <= 200)
    lines.append(f"- Evidence: {narrow_ranges}/{len(speed_variance)} groups have speed range ≤ 200 mm/s")
    lines.append(f"- Verdict: {'LIKELY' if narrow_ranges > len(speed_variance) // 2 else 'INCONCLUSIVE'}")
    lines.append("")

    # Hypothesis 4: Material ID
    lines.append("### H4: Material / Job ID\n")
    files_with_dxf = sum(1 for r in results if any(
        ".dxf" in s.lower() for s in r.get("metadata_strings", [])
    ))
    lines.append(f"- Evidence: {files_with_dxf}/{len(results)} files contain DXF references in metadata")
    lines.append(f"- Verdict: INCONCLUSIVE — needs cross-reference with operator job names")
    lines.append("")

    # === Conclusion ===
    lines.append("## 6. Conclusion\n")
    lines.append("Based on statistical analysis:\n")
    if len(all_upper) <= 1:
        lines.append("- Upper bits are CONSTANT across all files → unknown global constant or version marker")
    elif checksum_likely and cutter_consistent:
        lines.append(
            "- Most likely: upper bits encode a **cutter configuration profile ID** "
            "derived from the header (first 64-256 bytes)"
        )
    else:
        lines.append(
            "- Most likely: upper bits encode **file-level metadata** "
            "(material/job batch ID or cutter config hash)"
        )
    lines.append("")
    lines.append("### Recommended next step:\n")
    lines.append(
        "1. Group files by upper bits and inspect their header bytes "
        "(first 256B) for common patterns\n"
    )
    lines.append(
        "2. Cross-reference with operator job names extracted from file metadata strings\n"
    )
    lines.append(
        "3. Decode as bit field: test if individual bits toggle with specific layer "
        "parameters (speed, cutter, h2 sign)\n"
    )

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
        description="Decode Subtype Upper Bits — RE tool for VCF format"
    )
    parser.add_argument("--dir", type=str, default=None,
                        help="Directory with VCF files (training DB)")
    parser.add_argument("--file", type=str, default=None,
                        help="Single VCF file to analyze")
    parser.add_argument("--out", type=str, default=str(OUT),
                        help="Output directory")
    args = parser.parse_args()

    print("=" * 60)
    print("  Subtype Upper-Bit Correlator (P0)")
    print("=" * 60)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Collect files
    dirs = []
    if args.dir:
        dirs.append(Path(args.dir))
    elif args.file:
        vcf_files = [Path(args.file)]
    else:
        dirs = [NATIVE_VCF]
        if TRAINING_DB.exists():
            dirs.append(TRAINING_DB)

    if not args.file:
        vcf_files = collect_vcf_files(dirs)

    print(f"  Scanning {len(vcf_files)} VCF files ...")

    results = []
    for vcf_path in vcf_files:
        print(f"  Analyzing {vcf_path.name} ...", end=" ")
        try:
            analysis = analyze_vcf(vcf_path)
            results.append(analysis)
            print(f"OK ({analysis['element_count']} elements, "
                  f"{', '.join(analysis['upper_bits_summary']['unique_upper_bits_hex'])})")
        except Exception as e:
            print(f"FAIL: {e}")

    if not results:
        print("  No valid VCF files found.")
        return

    # Build correlation matrix
    correlation = build_correlation_matrix(results)
    bit_tests = bit_field_test(results)

    # Write JSON report
    report_json = {
        "meta": {
            "tool": "decode_subtype_bits.py",
            "files_analyzed": len(results),
            "parser_source": str(B2B_SRC),
        },
        "per_file": results,
        "correlation_matrix": correlation,
        "bit_field_analysis": bit_tests,
    }
    json_path = out_dir / "RESULT_subtype_correlation_matrix.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2, ensure_ascii=False)
    print(f"\n  JSON -> {json_path}")

    # Generate MD hypotheses
    md_content = generate_hypothesis_report(results, correlation, bit_tests)
    md_path = out_dir / "RESULT_subtype_upper_bit_hypotheses.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"  MD  -> {md_path}")

    # Print quick summary
    print(f"\n  Summary:")
    all_upper = set()
    for r in results:
        all_upper.update(r["upper_bits_summary"]["unique_upper_bits"])
    print(f"    Files:              {len(results)}")
    print(f"    Unique upper bits:  {len(all_upper)}")
    print(f"    Groups:             {len(correlation)}")
    for ub_hex, info in sorted(correlation.items()):
        print(f"      {ub_hex}: {len(info['files'])} files, "
              f"cutters={info['cutters']}, speeds={info['speeds'][:3]}...")
    print(f"\n  Done.")


if __name__ == "__main__":
    main()
