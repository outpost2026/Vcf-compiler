"""
segment_geometry_stats.py — Segment Geometry Statistics (P1)

Cil: Spocitat distribuce geometrickych vlastnosti segmentu (delky, uhly,
krivosti, arc parametry) napric training DB pro definici "normalni produkcnich
geometrie" a identifikaci anomalii.

Usage:
    python dev_scripts/segment_geometry_stats.py
    python dev_scripts/segment_geometry_stats.py --file "path/to/file.VCF"
"""

import sys
import os
import json
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
    from vcf_parser_v20 import RuidaVcfEngineV20
except ImportError:
    RuidaVcfEngineV20 = None


def compute_segment_length(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def compute_segment_angle(x1: float, y1: float, x2: float, y2: float) -> float:
    dx = x2 - x1
    dy = y2 - y1
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return 0.0
    return math.degrees(math.atan2(dy, dx))


def compute_curvature(x1, y1, x2, y2, x3, y3) -> float:
    """Three-point curvature approximation."""
    d1 = compute_segment_length(x1, y1, x2, y2)
    d2 = compute_segment_length(x2, y2, x3, y3)
    chord = compute_segment_length(x1, y1, x3, y3)
    if d1 < 1e-9 or d2 < 1e-9:
        return 0.0
    area = abs((x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)) / 2.0
    if area < 1e-12:
        return 0.0
    r = (d1 * d2 * chord) / (4.0 * area)
    return 1.0 / r if r > 1e-9 else 0.0


def compute_angle_between(x1, y1, x2, y2, x3, y3) -> float:
    """Interior angle at point (x2,y2) formed by vectors to (x1,y1) and (x3,y3)."""
    v1x, v1y = x1 - x2, y1 - y2
    v2x, v2y = x3 - x2, y3 - y2
    dot = v1x * v2x + v1y * v2y
    n1 = math.sqrt(v1x**2 + v1y**2)
    n2 = math.sqrt(v2x**2 + v2y**2)
    if n1 < 1e-9 or n2 < 1e-9:
        return 180.0
    cos_angle = max(-1.0, min(1.0, dot / (n1 * n2)))
    return math.degrees(math.acos(cos_angle))


def analyze_element_segments(parsed_element: dict) -> dict:
    """Extract segment-level geometry from a parsed element."""
    vertices = parsed_element.get("vertices") or []
    arc_data = parsed_element.get("segment_arc_data") or []
    pt_count = parsed_element.get("point_count", 0)

    segments = []
    for i in range(pt_count):
        if i + 1 >= len(vertices):
            break
        x1, y1 = vertices[i]
        x2, y2 = vertices[i + 1]

        d0 = d1 = d2 = 0.0
        if i < len(arc_data):
            tup = arc_data[i]
            if isinstance(tup, (list, tuple)) and len(tup) >= 3:
                d0, d1, d2 = tup[0], tup[1], tup[2]

        length = compute_segment_length(x1, y1, x2, y2)
        angle = compute_segment_angle(x1, y1, x2, y2)
        has_arc = not (abs(d0) < 1e-9 and abs(d1) < 1e-9 and abs(d2) < 1e-9)

        segments.append({
            "index": i,
            "x1": x1, "y1": y1, "x2": x2, "y2": y2,
            "length_mm": round(length, 4),
            "angle_deg": round(angle, 2),
            "d0": d0, "d1": d1, "d2": d2,
            "has_arc": has_arc,
        })

    element = {
        "segment_count": len(segments),
        "segments": segments,
        "total_length_mm": parsed_element.get("length_mm", 0.0),
        "geom_type": parsed_element.get("geom_type", "unknown"),
        "type_id": parsed_element.get("type_id", -1),
        "subtype": parsed_element.get("subtype", 0),
        "layer_index": parsed_element.get("layer_index", -1),
    }

    # Curvature and sharp corners from consecutive segment midpoints
    if len(segments) >= 3:
        sharp_corners = 0
        curvatures = []
        for i in range(1, len(segments)):
            s0 = segments[i - 1]
            s1 = segments[i]
            cx1 = (s0["x1"] + s0["x2"]) / 2
            cy1 = (s0["y1"] + s0["y2"]) / 2
            cx2 = (s1["x1"] + s1["x2"]) / 2
            cy2 = (s1["y1"] + s1["y2"]) / 2
            if i >= 2:
                s_prev = segments[i - 2]
                cx0 = (s_prev["x1"] + s_prev["x2"]) / 2
                cy0 = (s_prev["y1"] + s_prev["y2"]) / 2
                curv = compute_curvature(cx0, cy0, cx1, cy1, cx2, cy2)
                curvatures.append(curv)

                interior = compute_angle_between(
                    s_prev["x2"], s_prev["y2"],
                    s0["x2"], s0["y2"],
                    s1["x1"], s1["y1"],
                )
                if interior < 60:
                    sharp_corners += 1

        element["curvature_index"] = round(
            sum(curvatures) / len(curvatures), 6
        ) if curvatures else 0.0
        element["sharp_corners"] = sharp_corners
        element["max_curvature"] = round(max(curvatures), 6) if curvatures else 0.0

    return element


def analyze_vcf_geometry(filepath: Path) -> dict:
    """Parse VCF and extract geometry statistics."""
    data = filepath.read_bytes()

    result = {
        "filename": filepath.name,
        "size_bytes": len(data),
    }

    if RuidaVcfEngineV20 is None:
        result["error"] = "vcf_parser_v20 not available"
        return result

    try:
        engine = RuidaVcfEngineV20(data, filename=filepath.name)
        parsed = engine.parsed_data
    except Exception as e:
        result["error"] = f"parse failed: {e}"
        return result

    elements_raw = parsed.get("elements", [])
    layers = parsed.get("layers_details", [])

    elements = []
    all_segments = []

    for el in elements_raw:
        elem = analyze_element_segments(el)
        elements.append(elem)
        all_segments.extend(elem.get("segments", []))

    result["element_count"] = len(elements)
    result["segment_count"] = len(all_segments)
    result["layer_count"] = len(layers)
    result["elements"] = elements
    result["segments"] = all_segments

    return result


def compute_histogram(values: list, bins: int = 10) -> list:
    """Simple histogram generator."""
    if not values:
        return []
    mn, mx = min(values), max(values)
    if mx == mn:
        return [{"bin_start": mn, "bin_end": mx, "count": len(values)}]
    bin_width = (mx - mn) / bins
    histogram = []
    for i in range(bins):
        lo = mn + i * bin_width
        hi = lo + bin_width
        count = sum(1 for v in values if lo <= v < hi)
        histogram.append({
            "bin_start": round(lo, 4),
            "bin_end": round(hi, 4),
            "count": count,
        })
    return histogram


def build_statistics(results: list) -> dict:
    """Aggregate geometry statistics across all files."""
    all_lengths = []
    all_angles = []
    all_curvatures = []
    all_arc_d0 = []
    all_arc_d1 = []
    all_arc_d2 = []
    arc_segments = 0
    total_segments = 0
    sharp_corner_count = 0
    total_elements_with_corners = 0
    all_sharp_counts = []
    geom_type_dist = defaultdict(int)
    file_size_hist = []
    element_counts = []
    segment_counts = []

    for r in results:
        if "error" in r:
            continue
        file_size_hist.append(r["size_bytes"])
        element_counts.append(r["element_count"])
        segment_counts.append(r["segment_count"])

        for elem in r.get("elements", []):
            gt = elem.get("geom_type", "unknown")
            geom_type_dist[gt] += 1

            segs = elem.get("segments", [])
            for seg in segs:
                if math.isfinite(seg["length_mm"]) and abs(seg["length_mm"]) < 1e10:
                    all_lengths.append(seg["length_mm"])
                if math.isfinite(seg["angle_deg"]):
                    all_angles.append(seg["angle_deg"])
                total_segments += 1

                if seg["has_arc"]:
                    arc_segments += 1
                    if math.isfinite(seg["d0"]) and abs(seg["d0"]) < 1e10:
                        all_arc_d0.append(seg["d0"])
                    if math.isfinite(seg["d1"]) and abs(seg["d1"]) < 1e10:
                        all_arc_d1.append(seg["d1"])
                    if math.isfinite(seg["d2"]) and abs(seg["d2"]) < 1e10:
                        all_arc_d2.append(seg["d2"])

                if "curvature_index" in elem and math.isfinite(elem["curvature_index"]):
                    all_curvatures.append(elem["curvature_index"])

                if "sharp_corners" in elem:
                    all_sharp_counts.append(elem["sharp_corners"])
                    sharp_corner_count += elem["sharp_corners"]
                    total_elements_with_corners += 1

    stats = {
        "files_analyzed": len([r for r in results if "error" not in r]),
        "total_segments": total_segments,
        "total_elements": sum(r.get("element_count", 0) for r in results if "error" not in r),
        "arc_segment_ratio": round(arc_segments / total_segments, 4) if total_segments else 0,
    }

    def percentile(vals, p):
        if not vals:
            return None
        sv = sorted(vals)
        idx = int(len(sv) * p / 100)
        return round(sv[min(idx, len(sv) - 1)], 4)

    def moments(vals, max_abs=1e100):
        if not vals:
            return {}
        vals = [v for v in vals if math.isfinite(v) and abs(v) < max_abs]
        if not vals:
            return {}
        n = len(vals)
        mn = sum(vals) / n
        variance = sum((v - mn) ** 2 for v in vals) / n if n > 1 else 0
        return {
            "n": n,
            "min": round(min(vals), 4),
            "max": round(max(vals), 4),
            "mean": round(mn, 4),
            "std": round(math.sqrt(variance), 4),
            "p5": percentile(vals, 5),
            "p25": percentile(vals, 25),
            "p50": percentile(vals, 50),
            "p75": percentile(vals, 75),
            "p95": percentile(vals, 95),
        }

    stats["segment_length_mm"] = moments(all_lengths)
    stats["segment_angle_deg"] = moments(all_angles)
    stats["curvature_index"] = moments(all_curvatures) if all_curvatures else {}
    stats["sharp_corners_per_element"] = moments(all_sharp_counts) if all_sharp_counts else {}
    stats["arc_d0"] = moments(all_arc_d0) if all_arc_d0 else {}
    stats["arc_d1"] = moments(all_arc_d1) if all_arc_d1 else {}
    stats["arc_d2"] = moments(all_arc_d2) if all_arc_d2 else {}
    stats["geom_type_distribution"] = dict(geom_type_dist)
    stats["file_size_bytes"] = moments(file_size_hist) if file_size_hist else {}
    stats["elements_per_file"] = moments(element_counts) if element_counts else {}
    stats["segments_per_file"] = moments(segment_counts) if segment_counts else {}

    # Histograms
    stats["histogram_segment_lengths"] = compute_histogram(all_lengths, 20)
    stats["histogram_segment_angles"] = compute_histogram(all_angles, 16)

    # Outliers: segments > mean + 3*std
    if all_lengths:
        mean_l = stats["segment_length_mm"]["mean"]
        std_l = stats["segment_length_mm"]["std"]
        threshold = mean_l + 3 * std_l
        outliers = [l for l in all_lengths if l > threshold]
        stats["outliers_3sigma"] = {
            "threshold_mm": round(threshold, 4),
            "count": len(outliers),
            "ratio": round(len(outliers) / len(all_lengths), 4) if all_lengths else 0,
            "max_outlier": round(max(outliers), 4) if outliers else 0,
        }

    return stats


def generate_geometry_report(results: list, stats: dict) -> str:
    lines = []
    lines.append("# Segment Geometry Statistics Report\n")
    lines.append(
        f"**Generated:** by segment_geometry_stats.py — "
        f"{stats['files_analyzed']} files, {stats['total_segments']} segments\n"
    )
    lines.append("---\n")

    lines.append("## 1. Summary\n")
    lines.append(f"- Files analyzed: {stats['files_analyzed']}")
    lines.append(f"- Total elements: {stats['total_elements']}")
    lines.append(f"- Total segments: {stats['total_segments']}")
    lines.append(f"- Arc segment ratio: {stats['arc_segment_ratio']*100:.1f}%")
    lines.append("")

    lines.append("## 2. Segment Length Distribution (mm)\n")
    s = stats["segment_length_mm"]
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Count | {s['n']} |")
    lines.append(f"| Min | {s['min']} |")
    lines.append(f"| Max | {s['max']} |")
    lines.append(f"| Mean | {s['mean']} |")
    lines.append(f"| Std | {s['std']} |")
    lines.append(f"| P5 | {s['p5']} |")
    lines.append(f"| P25 | {s['p25']} |")
    lines.append(f"| P50 | {s['p50']} |")
    lines.append(f"| P75 | {s['p75']} |")
    lines.append(f"| P95 | {s['p95']} |")
    lines.append("")

    if "outliers_3sigma" in stats:
        o = stats["outliers_3sigma"]
        lines.append("### Statistical Outliers (> mean + 3σ)\n")
        lines.append(f"- Threshold: {o['threshold_mm']} mm")
        lines.append(f"- Count: {o['count']} ({o['ratio']*100:.1f}% of all segments)")
        lines.append(f"- Max outlier: {o['max_outlier']} mm")
        lines.append("")

    lines.append("## 3. Arc Parameter Distribution\n")
    for arc_param in ["arc_d0", "arc_d1", "arc_d2"]:
        a = stats.get(arc_param, {})
        if a:
            lines.append(f"### {arc_param}\n")
            lines.append(f"| Metric | Value |")
            lines.append(f"|--------|-------|")
            for k in ["n", "min", "max", "mean", "std", "p5", "p50", "p95"]:
                lines.append(f"| {k} | {a.get(k, 'N/A')} |")
            lines.append("")

    lines.append("## 4. Curvature Index Distribution\n")
    c = stats.get("curvature_index", {})
    if c:
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        for k in ["n", "min", "max", "mean", "std", "p5", "p50", "p95"]:
            lines.append(f"| {k} | {c.get(k, 'N/A')} |")
        lines.append("")

    lines.append("## 5. Sharp Corners per Element\n")
    sc = stats.get("sharp_corners_per_element", {})
    if sc:
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        for k in ["n", "min", "max", "mean", "std", "p50"]:
            lines.append(f"| {k} | {sc.get(k, 'N/A')} |")
        lines.append("")

    lines.append("## 6. Geometry Type Distribution\n")
    lines.append("| Type | Count |")
    lines.append("|------|-------|")
    for gt, count in sorted(stats.get("geom_type_distribution", {}).items(), key=lambda x: -x[1]):
        lines.append(f"| {gt} | {count} |")
    lines.append("")

    lines.append("## 7. Segment Length Histogram (20 bins)\n")
    lines.append("```")
    for h in stats.get("histogram_segment_lengths", []):
        bar = "#" * min(h["count"] // max(1, max(
            s["count"] for s in stats.get("histogram_segment_lengths", [])
        ) // 40), 40)
        lines.append(f"  {h['bin_start']:8.1f}-{h['bin_end']:<8.1f}: {h['count']:6d} {bar}")
    lines.append("```\n")

    lines.append("## 8. Per-File Summary\n")
    lines.append("| File | Elements | Segments | Avg Length | Max Length | Arc % |")
    lines.append("|------|----------|----------|------------|------------|-------|")
    for r in sorted(results, key=lambda x: x["filename"]):
        if "error" in r:
            lines.append(f"| {r['filename']} | ERROR: {r['error']} | - | - | - | - |")
        else:
            segs = r.get("segments", [])
            lengths = [s["length_mm"] for s in segs]
            avg_l = round(sum(lengths) / len(lengths), 2) if lengths else 0
            max_l = round(max(lengths), 2) if lengths else 0
            arc_pct = round(
                sum(1 for s in segs if s["has_arc"]) / len(segs) * 100, 1
            ) if segs else 0
            lines.append(
                f"| {r['filename']} | {r['element_count']} | {r['segment_count']} "
                f"| {avg_l} | {max_l} | {arc_pct}% |"
            )
    lines.append("")

    return "\n".join(lines)


def collect_vcf_files(dirs: list) -> list:
    vcf_files = []
    for d in dirs:
        if d.exists():
            vcf_files.extend(sorted(d.glob("*.VCF")))
    exclude = ["synthethic_vcf", "binary_search_variants", "synthetic_vcf", "json_outputs"]
    return [f for f in vcf_files if not any(p in str(f) for p in exclude)]


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Segment Geometry Statistics — VCF geometry analysis"
    )
    parser.add_argument("--dir", type=str, default=None)
    parser.add_argument("--file", type=str, default=None)
    parser.add_argument("--out", type=str, default=str(OUT))
    args = parser.parse_args()

    print("=" * 60)
    print("  Segment Geometry Statistics (P1)")
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
            analysis = analyze_vcf_geometry(vcf_path)
            results.append(analysis)
            if "error" in analysis:
                print(f"  {vcf_path.name}: ERROR: {analysis['error']}")
            else:
                print(f"  {vcf_path.name}: {analysis['element_count']} elements, "
                      f"{analysis['segment_count']} segments")
        except Exception as e:
            print(f"  {vcf_path.name}: FAIL: {e}")

    if not results:
        print("  No files analyzed.")
        return

    stats = build_statistics(results)

    json_path = out_dir / "RESULT_segment_geometry_histograms.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"stats": stats, "per_file": results}, f, indent=2, ensure_ascii=False)
    print(f"\n  JSON -> {json_path}")

    md_content = generate_geometry_report(results, stats)
    md_path = out_dir / "RESULT_segment_geometry_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"  MD  -> {md_path}")

    print(f"\n  Summary:")
    s = stats["segment_length_mm"]
    print(f"    Files:    {stats['files_analyzed']}")
    print(f"    Segments: {s['n']}")
    print(f"    Length:   mean={s['mean']} mm, P50={s['p50']} mm, P95={s['p95']} mm")
    print(f"    Arc segs: {stats['arc_segment_ratio']*100:.1f}%")
    print(f"    Outliers: {stats.get('outliers_3sigma', {}).get('count', 0)}")
    print(f"\n  Done.")


if __name__ == "__main__":
    main()
