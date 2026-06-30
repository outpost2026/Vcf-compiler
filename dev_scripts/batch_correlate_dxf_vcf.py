"""
batch_correlate_dxf_vcf.py - Davkovy DXF<->VCF Korelator (P1)

Cil: Najit DXF zdroje v metadatech VCF nebo podle nazvu, spustit korelaci
davkove a agregovat transformacni matice a mapovani barev s confidence score.

Usage:
    python dev_scripts/batch_correlate_dxf_vcf.py
    python dev_scripts/batch_correlate_dxf_vcf.py --vcf-dir "path/to/vcf" --dxf-dir "path/to/dxf"
"""

import sys
import os
import json
import struct
import math
import logging
import re
from pathlib import Path
from collections import defaultdict, Counter

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
    import ezdxf
except ImportError:
    print("ERROR: ezdxf required. pip install ezdxf")
    sys.exit(1)

try:
    from vcf_binary_reader import extract_strings
except ImportError:
    extract_strings = None

GEOMETRY_SIG = b'\x01\x00\x01\x00\x00\xff\xff\xff'


def length_dx_dy(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    return math.hypot(dx, dy), dx, dy


def _entity_color(ent, layer_colors: dict) -> int:
    c = getattr(ent.dxf, 'color', 256)
    if c == 256:
        c = layer_colors.get(ent.dxf.layer, 7)
    return c


def _add_seg(lines: list, x1, y1, x2, y2, layer: str, color: int):
    length, dx, dy = length_dx_dy(x1, y1, x2, y2)
    if length < 1e-9:
        return
    lines.append({"x1": round(x1, 4), "y1": round(y1, 4),
                  "x2": round(x2, 4), "y2": round(y2, 4),
                  "layer_name": layer, "aci_color": color,
                  "length": round(length, 6),
                  "dx": round(dx, 6), "dy": round(dy, 6)})


def extract_dxf_geometry(dxf_path: Path) -> dict:
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    layer_colors = {layer.dxf.name: layer.color for layer in doc.layers}
    lines = []
    total_count = 0

    for ent in msp:
        total_count += 1
        color = _entity_color(ent, layer_colors)
        layer = ent.dxf.layer
        t = ent.dxftype()

        if t == 'LINE':
            s, e = ent.dxf.start, ent.dxf.end
            _add_seg(lines, s.x, s.y, e.x, e.y, layer, color)

        elif t == 'LWPOLYLINE':
            pts = ent.get_points()
            for i in range(len(pts) - 1):
                _add_seg(lines, pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], layer, color)
            if ent.closed and len(pts) > 2:
                _add_seg(lines, pts[-1][0], pts[-1][1], pts[0][0], pts[0][1], layer, color)

        elif t == 'POLYLINE':
            pts = [v.dxf.location for v in ent.vertices]
            for i in range(len(pts) - 1):
                _add_seg(lines, pts[i].x, pts[i].y, pts[i+1].x, pts[i+1].y, layer, color)
            if ent.is_closed and len(pts) > 2:
                _add_seg(lines, pts[-1].x, pts[-1].y, pts[0].x, pts[0].y, layer, color)

        elif t == 'CIRCLE':
            cx, cy = ent.dxf.center.x, ent.dxf.center.y
            r = ent.dxf.radius
            n = max(8, int(2 * math.pi * r / 5))
            for i in range(n):
                a1 = 2 * math.pi * i / n
                a2 = 2 * math.pi * (i + 1) / n
                _add_seg(lines, cx + r*math.cos(a1), cy + r*math.sin(a1),
                         cx + r*math.cos(a2), cy + r*math.sin(a2), layer, color)

    non_line = total_count - sum(1 for e in msp if e.dxftype() == 'LINE')
    return {"lines": lines, "total_entities": total_count, "non_line_entities": non_line}


def extract_vcf_geometry(vcf_path: Path) -> list:
    data = vcf_path.read_bytes()
    segments = []
    offset = 0
    while True:
        pos = data.find(GEOMETRY_SIG, offset)
        if pos == -1:
            break
        p = pos + 45
        if p + 46 >= len(data):
            break
        geom_color = struct.unpack_from('<I', data, pos + 8)[0]
        type_id, pt_count = struct.unpack_from('<II', data, p)[0:2]
        if type_id in (0, 1):
            for i in range(pt_count):
                seg_off = p + i * 74
                if seg_off + 46 <= len(data):
                    x1, y1 = struct.unpack_from('<dd', data, seg_off + 14)
                    x2, y2 = struct.unpack_from('<dd', data, seg_off + 30)
                    length, dx, dy = length_dx_dy(x1, y1, x2, y2)
                    segments.append({
                        "x1": round(x1, 4), "y1": round(y1, 4),
                        "x2": round(x2, 4), "y2": round(y2, 4),
                        "geom_color": geom_color,
                        "length": round(length, 6),
                        "dx": round(dx, 6), "dy": round(dy, 6),
                    })
        offset = pos + 1
    return segments


def correlate_pair(dxf_lines: list, vcf_segments: list, tolerance: float = 1e-2) -> dict:
    if not dxf_lines or not vcf_segments:
        return {"matched": False, "reason": "empty input"}

    dxf_by_len = defaultdict(list)
    for line in dxf_lines:
        dxf_by_len[round(line["length"], 3)].append(line)
    vcf_by_len = defaultdict(list)
    for seg in vcf_segments:
        vcf_by_len[round(seg["length"], 3)].append(seg)

    votes = Counter()
    for length_key, dxf_candidates in dxf_by_len.items():
        vcf_candidates = vcf_by_len.get(length_key, [])
        for dxf in dxf_candidates:
            for vcf in vcf_candidates:
                ox = round(vcf["x1"] - dxf["x1"], 4)
                oy_normal = round(vcf["y1"] - dxf["y1"], 4)
                if abs(vcf["x2"] - (dxf["x2"] + ox)) < tolerance and \
                   abs(vcf["y2"] - (dxf["y2"] + oy_normal)) < tolerance:
                    votes[(ox, oy_normal, False)] += 1

                oy_inv = round(vcf["y1"] + dxf["y1"], 4)
                if abs(vcf["x2"] - (dxf["x2"] + ox)) < tolerance and \
                   abs(vcf["y2"] - (-dxf["y2"] + oy_inv)) < tolerance:
                    votes[(ox, oy_inv, True)] += 1

    if not votes:
        return {"matched": False, "reason": "no transformation found", "total_votes": 0}

    best, count = votes.most_common(1)[0]
    ox, oy, y_inv = best
    total_votes = sum(votes.values())

    # Apply transformation and match
    used_vcf = [False] * len(vcf_segments)
    matched_pairs = []
    unmatched_dxf_indices = []

    for dxf_idx, dxf in enumerate(dxf_lines):
        if y_inv:
            px1, py1 = dxf["x1"] + ox, -dxf["y1"] + oy
            px2, py2 = dxf["x2"] + ox, -dxf["y2"] + oy
        else:
            px1, py1 = dxf["x1"] + ox, dxf["y1"] + oy
            px2, py2 = dxf["x2"] + ox, dxf["y2"] + oy

        best_seg = None
        best_dist = float('inf')
        best_vcf_idx = -1
        for vcf_idx, vcf in enumerate(vcf_segments):
            if used_vcf[vcf_idx]:
                continue
            d1 = math.hypot(px1 - vcf["x1"], py1 - vcf["y1"])
            d2 = math.hypot(px2 - vcf["x2"], py2 - vcf["y2"])
            dist = d1 + d2
            if dist < tolerance * 2 and dist < best_dist:
                best_seg = vcf
                best_vcf_idx = vcf_idx
                best_dist = dist

        if best_seg is not None:
            used_vcf[best_vcf_idx] = True
            matched_pairs.append({
                "dxf_index": dxf_idx,
                "vcf_index": best_vcf_idx,
                "dxf_aci": dxf["aci_color"],
                "vcf_color": best_seg["geom_color"],
                "distance": round(best_dist, 4),
            })
        else:
            unmatched_dxf_indices.append(dxf_idx)

    unmatched_vcf_indices = [i for i, used in enumerate(used_vcf) if not used]

    # Color mapping
    color_map = {}
    for pair in matched_pairs:
        aci = pair["dxf_aci"]
        vc = pair["vcf_color"]
        if aci not in color_map:
            color_map[aci] = []
        color_map[aci].append(vc)

    resolved_colors = {}
    for aci, colors in color_map.items():
        most_common = Counter(colors).most_common(1)[0]
        resolved_colors[aci] = {
            "most_common_vcf_color": most_common[0],
            "count": most_common[1],
            "total": len(colors),
            "confidence": round(most_common[1] / len(colors), 4),
        }

    match_rate = len(matched_pairs) / len(dxf_lines) if dxf_lines else 0

    return {
        "matched": True,
        "transformation": {
            "offset_x": ox,
            "offset_y": oy,
            "y_inverted": y_inv,
            "votes": count,
            "total_votes": total_votes,
            "vote_ratio": round(count / total_votes, 4) if total_votes else 0,
        },
        "stats": {
            "dxf_entities": len(dxf_lines),
            "vcf_segments": len(vcf_segments),
            "matched_pairs": len(matched_pairs),
            "unmatched_dxf": len(unmatched_dxf_indices),
            "unmatched_vcf": len(unmatched_vcf_indices),
            "match_rate": round(match_rate, 4),
        },
        "color_mapping": resolved_colors,
        "pairs": matched_pairs,
    }


def find_dxf_for_vcf(vcf_path: Path, dxf_dir: Path) -> Path | None:
    """Find DXF file matching VCF filename or embedded in metadata."""
    stem = vcf_path.stem
    # Direct match: same stem
    candidates = list(dxf_dir.glob(f"{stem}.dxf"))
    if candidates:
        return candidates[0]

    # Try common name variations
    for suffix in ["_native", "_1_aci", "_single_aci"]:
        if stem.endswith(suffix):
            base = stem[:-len(suffix)]
            candidates = list(dxf_dir.glob(f"{base}.dxf"))
            if candidates:
                return candidates[0]

    # Search in metadata
    if extract_strings is not None:
        try:
            data = vcf_path.read_bytes()
            strings = extract_strings(data)
            for s in strings:
                if s.lower().endswith(".dxf"):
                    s_path = Path(s)
                    if not s_path.is_absolute():
                        s_path = vcf_path.parent / s_path
                    if s_path.exists():
                        return s_path
                    s_path = dxf_dir / s_path.name
                    if s_path.exists():
                        return s_path
        except Exception:
            pass

    return None


def collect_vcf_files(dirs: list) -> list:
    vcf_files = []
    for d in dirs:
        if d.exists():
            vcf_files.extend(sorted(d.glob("*.VCF")))
    exclude = ["synthethic_vcf", "binary_search_variants", "synthetic_vcf", "json_outputs"]
    return [f for f in vcf_files if not any(p in str(f) for p in exclude)]


def generate_report(all_results: list, dxf_root: Path) -> str:
    lines = []
    lines.append("# Batch DXF<->VCF Correlation Report\n")
    lines.append(
        f"**Generated:** by batch_correlate_dxf_vcf.py ? "
        f"{len(all_results)} VCF-DXF pairs analyzed\n"
    )
    lines.append("---\n")

    matched = [r for r in all_results if r.get("result", {}).get("matched")]
    unmatched = [r for r in all_results if not r.get("result", {}).get("matched")]

    lines.append("## 1. Summary\n")
    lines.append(f"- Total VCF files: {len(all_results)}")
    lines.append(f"- DXF found: {len(matched) + len(unmatched)}")
    lines.append(f"- Successful correlations: {len(matched)}")
    lines.append(f"- Failed correlations: {len(unmatched)}")
    lines.append("")

    if matched:
        avg_match = sum(r["result"]["stats"]["match_rate"] for r in matched) / len(matched)
        lines.append(f"- Average match rate: {avg_match*100:.1f}%")
        lines.append("")

    lines.append("## 2. Per-Pair Results\n")
    lines.append("| VCF | DXF | Matched | Total | Match Rate | Offset X | Offset Y | Y Inv |")
    lines.append("|-----|-----|---------|-------|------------|----------|----------|-------|")
    for r in all_results:
        res = r.get("result", {})
        if res.get("matched"):
            t = res["transformation"]
            s = res["stats"]
            lines.append(
                f"| {r['vcf_name']} | {r['dxf_name']} | {s['matched_pairs']} | "
                f"{s['dxf_entities']} | {s['match_rate']*100:.0f}% | "
                f"{t['offset_x']} | {t['offset_y']} | {t['y_inverted']} |"
            )
        else:
            lines.append(
                f"| {r['vcf_name']} | {r['dxf_name'] or 'N/A'} | "
                f"FAIL: {res.get('reason', 'unknown')} | - | - | - | - | - |"
            )
    lines.append("")

    if matched:
        lines.append("## 3. Aggregated Transformation\n")
        offsets_x = [r["result"]["transformation"]["offset_x"] for r in matched]
        offsets_y = [r["result"]["transformation"]["offset_y"] for r in matched]
        y_inv_flags = [r["result"]["transformation"]["y_inverted"] for r in matched]
        lines.append(f"- Median offset_x: {round(sorted(offsets_x)[len(offsets_x)//2], 4)}")
        lines.append(f"- Median offset_y: {round(sorted(offsets_y)[len(offsets_y)//2], 4)}")
        lines.append(f"- Y-inverted: {sum(y_inv_flags)}/{len(y_inv_flags)} pairs")
        lines.append("")

        lines.append("## 4. Aggregated Color Mapping\n")
        all_colors = defaultdict(list)
        for r in matched:
            for aci, info in r["result"]["color_mapping"].items():
                all_colors[aci].append(info)

        lines.append("| ACI | VCF Color Samples | Confidence |")
        lines.append("|-----|-------------------|------------|")
        for aci in sorted(all_colors.keys()):
            infos = all_colors[aci]
            colors = list(set(i["most_common_vcf_color"] for i in infos))
            avg_conf = round(sum(i["confidence"] for i in infos) / len(infos), 4)
            lines.append(f"| {aci} | {', '.join(f'0x{c:08x}' for c in colors[:3])} | {avg_conf} |")
        lines.append("")

    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Batch DXF<->VCF Correlator ? aggregate RE transformation matrix"
    )
    parser.add_argument("--vcf-dir", type=str, default=None)
    parser.add_argument("--dxf-dir", type=str, default=None)
    parser.add_argument("--out", type=str, default=str(OUT))
    parser.add_argument("--tolerance", type=float, default=1e-2)
    args = parser.parse_args()

    print("=" * 60)
    print("  Batch DXF<->VCF Correlator (P1)")
    print("=" * 60)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    vcf_dirs = [DEMO, NATIVE_VCF]
    if args.vcf_dir:
        vcf_dirs.insert(0, Path(args.vcf_dir))
    if TRAINING_DB.exists():
        vcf_dirs.append(TRAINING_DB)

    dxf_root = Path(args.dxf_dir) if args.dxf_dir else DEMO

    vcf_files = collect_vcf_files(vcf_dirs)
    print(f"  Scanning {len(vcf_files)} VCF files for DXF matches ...")

    all_results = []
    for vcf_path in vcf_files:
        dxf_path = find_dxf_for_vcf(vcf_path, dxf_root)
        if dxf_path is None:
            continue

        print(f"  {vcf_path.name} <-> {dxf_path.name} ...", end=" ")

        try:
            dxf_data = extract_dxf_geometry(dxf_path)
            vcf_segs = extract_vcf_geometry(vcf_path)

            if not dxf_data["lines"]:
                print("SKIP (no DXF lines)")
                all_results.append({
                    "vcf_name": vcf_path.name, "dxf_name": dxf_path.name,
                    "result": {"matched": False, "reason": "no LINE entities in DXF"},
                })
                continue

            result = correlate_pair(dxf_data["lines"], vcf_segs, tolerance=args.tolerance)
            all_results.append({
                "vcf_name": vcf_path.name,
                "dxf_name": dxf_path.name,
                "dxf_info": dxf_data,
                "result": result,
            })

            if result.get("matched"):
                s = result["stats"]
                t = result["transformation"]
                print(f"OK ({s['matched_pairs']}/{s['dxf_entities']} matched, "
                      f"ox={t['offset_x']}, oy={t['offset_y']}, y_inv={t['y_inverted']})")
            else:
                print(f"FAIL: {result.get('reason', 'unknown')}")
        except Exception as e:
            print(f"ERROR: {e}")
            all_results.append({
                "vcf_name": vcf_path.name, "dxf_name": dxf_path.name,
                "result": {"matched": False, "reason": str(e)},
            })

    if not all_results:
        print("  No DXF-VCF pairs found.")
        return

    json_path = out_dir / "RESULT_correlation_master.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n  JSON -> {json_path}")

    md_content = generate_report(all_results, dxf_root)
    md_path = out_dir / "RESULT_correlation_master.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"  MD  -> {md_path}")

    matched = [r for r in all_results if r.get("result", {}).get("matched")]
    print(f"\n  Summary:")
    print(f"    VCF files:  {len(vcf_files)}")
    print(f"    DXF pairs:  {len(all_results)}")
    print(f"    Matched:    {len(matched)}")
    print(f"    Failed:     {len(all_results) - len(matched)}")
    if matched:
        avg_mr = sum(r["result"]["stats"]["match_rate"] for r in matched) / len(matched)
        print(f"    Avg match:  {avg_mr*100:.1f}%")
        tx = [r["result"]["transformation"]["offset_x"] for r in matched]
        ty = [r["result"]["transformation"]["offset_y"] for r in matched]
        print(f"    Median ox:  {round(sorted(tx)[len(tx)//2], 4)}")
        print(f"    Median oy:  {round(sorted(ty)[len(ty)//2], 4)}")
    print(f"\n  Done.")


if __name__ == "__main__":
    main()
