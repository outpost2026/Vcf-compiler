"""
DXF → VCF adaptér.

Bridge between dxf_integrace.index_dxf() and vcf_parser.write().
Vytváří VCF spec dict z DXF souboru pomocí ACI barevného mapování.

Usage:
    from vcf_parser import compile_dxf
    compile_dxf("input.dxf", "output.VCF")
"""

import json
import logging
import math
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ACI → RGB lookup (AutoCAD Color Index)
# ---------------------------------------------------------------------------

ACI_TO_RGB = {
    0: (10, 10, 10),
    1: (255, 0, 0),
    2: (255, 255, 0),
    3: (0, 255, 0),
    4: (0, 255, 255),
    5: (0, 0, 255),
    6: (255, 0, 255),
    7: (0, 0, 0),
    8: (128, 128, 128),
    9: (192, 192, 192),
    30: (255, 165, 0),
    52: (0, 204, 204),
    92: (8, 145, 178),
}

# ---------------------------------------------------------------------------
# Lazy import DXF indexer
# ---------------------------------------------------------------------------

_DXF_INDEXER = None


def _get_dxf_indexer():
    global _DXF_INDEXER
    if _DXF_INDEXER is not None:
        return _DXF_INDEXER
    try:
        import dxf_geometry_indexer_v2 as m
        _DXF_INDEXER = m
        return m
    except ImportError:
        pass
    repo_path = Path(__file__).parents[1] / ".." / "dxf_integrace" / "src"
    if repo_path.exists():
        sys.path.insert(0, str(repo_path.resolve()))
        try:
            import dxf_geometry_indexer_v2 as m
            _DXF_INDEXER = m
            return m
        except ImportError:
            pass
    raise ImportError(
        "dxf_geometry_indexer_v2 not found. "
        "Install dxf_integrace (pip install -e ../dxf_integrace) "
        "or ensure it's on PYTHONPATH."
    )

# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

_CONFIG_DEFAULTS = {
    "h1_mm": 24.0,
    "number_of_feeding": 1,
    "fallback_cutter_type": "Vibrate cutter",
    "fallback_speed_mms": 200.0,
    "fallback_direction": "N/A",
    "fallback_h2_mm": -0.3,
    "fallback_start_extension_mm": 0.0,
    "fallback_end_extension_mm": 0.0,
    "fallback_is_output": True,
}


def _load_config(path=None):
    if path:
        p = Path(path)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if "defaults" not in cfg:
                cfg["defaults"] = dict(_CONFIG_DEFAULTS)
            return cfg
    default_path = Path("vcf_compiler_map_config.json")
    if default_path.exists():
        with open(default_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            if "defaults" not in cfg:
                cfg["defaults"] = dict(_CONFIG_DEFAULTS)
            return cfg
    logger.warning("vcf_compiler_map_config.json not found — using built-in defaults")
    return {"aci_color_mapping": {}, "defaults": dict(_CONFIG_DEFAULTS)}


def _resolve_aci(aci_str, tool_config):
    aci_map = tool_config.get("aci_color_mapping", {})
    if aci_str in aci_map:
        return aci_map[aci_str]
    return None


def _aci_to_rgb(aci):
    rgb = ACI_TO_RGB.get(aci)
    if rgb:
        return list(rgb)
    logger.warning("Unknown ACI %d — fallback to white", aci)
    return [255, 255, 255]


_DXF_TO_VCF_OFFSET_X = 67.5
_DXF_TO_VCF_OFFSET_Y = -287.5

_DEDUP_EPSILON = 0.01


def _apply_coord_transform(vertices):
    return [
        (x + _DXF_TO_VCF_OFFSET_X, y + _DXF_TO_VCF_OFFSET_Y)
        for x, y in vertices
    ]


def _dedup_consecutive(vertices, eps=_DEDUP_EPSILON):
    if not vertices:
        return vertices
    result = [vertices[0]]
    for v in vertices[1:]:
        dx = v[0] - result[-1][0]
        dy = v[1] - result[-1][1]
        if dx * dx + dy * dy > eps * eps:
            result.append(v)
    return result


def _points_on_circle(vertices, tolerance=0.5):
    n = len(vertices)
    if n < 3:
        return None
    xs = [v[0] for v in vertices]
    ys = [v[1] for v in vertices]
    cx = (min(xs) + max(xs)) / 2.0
    cy = (min(ys) + max(ys)) / 2.0
    r = math.sqrt((max(xs) - min(xs)) ** 2 + (max(ys) - min(ys)) ** 2) / 2.0
    if r < 1e-6:
        return None
    for v in vertices:
        d = math.sqrt((v[0] - cx) ** 2 + (v[1] - cy) ** 2)
        if abs(d - r) > tolerance:
            return None
    return {"cx": cx, "cy": cy, "radius": r}

# ---------------------------------------------------------------------------
# VCF spec builder
# ---------------------------------------------------------------------------


def _build_vcf_spec(entities, layer_card, tool_config, h1_default, feed_default):
    defaults = tool_config.get("defaults", _CONFIG_DEFAULTS)
    aci_mapping = tool_config.get("aci_color_mapping", {})

    aci_groups = {}
    for e in entities:
        ci = e["color_index"]
        aci_groups.setdefault(ci, []).append(e)

    vcf_layers = []
    aci_to_layer_index = {}

    for aci in sorted(aci_groups.keys()):
        aci_str = str(aci)
        mapping = aci_mapping.get(aci_str)

        if mapping and mapping.get("cutter_type") == "ambiguous":
            group = aci_groups[aci]
            total_pts = sum(e["point_count"] for e in group)
            total_len = sum(e["length_mm"] for e in group)
            density = total_pts / (total_len / 1000) if total_len > 0 else 0
            rules = mapping.get("density_rules", {})
            if density > rules.get("vibrate_if_density_gt", 30):
                ct = "Vibrate cutter"
                sp = rules.get("vibrate_speed_mms", 50)
                dr = "N/A"
                h2 = defaults.get("fallback_h2_mm", -0.3)
                se = 0.0
                ee = 0.0
            else:
                ct = "V-slot"
                sp = rules.get("vslot_speed_mms", 200)
                dr = rules.get("vslot_direction", "Cut both side")
                h2 = defaults.get("fallback_h2_mm", 6.0)
                se = rules.get("vslot_start_extension_mm", 2.0)
                ee = rules.get("vslot_end_extension_mm", 2.0)
            is_output = True
            vs_comp = 0.0
            note = ""
        elif mapping:
            ct = mapping.get("cutter_type", defaults["fallback_cutter_type"])
            sp = mapping.get("speed_mms", defaults["fallback_speed_mms"])
            dr = mapping.get("direction", defaults["fallback_direction"])
            h2 = mapping.get("h2_mm", defaults["fallback_h2_mm"])
            se = mapping.get("start_extension_mm", defaults["fallback_start_extension_mm"])
            ee = mapping.get("end_extension_mm", defaults["fallback_end_extension_mm"])
            is_output = mapping.get("is_output", defaults["fallback_is_output"])
            vs_comp = mapping.get("vs_comp_mm", 0.0)
            note = mapping.get("_note", "")
        else:
            ct = defaults["fallback_cutter_type"]
            sp = defaults["fallback_speed_mms"]
            dr = defaults["fallback_direction"]
            h2 = defaults["fallback_h2_mm"]
            se = defaults["fallback_start_extension_mm"]
            ee = defaults["fallback_end_extension_mm"]
            is_output = defaults["fallback_is_output"]
            vs_comp = 0.0
            note = f"Unmapped ACI {aci} — using fallback"
            logger.warning(note)

        layer = {
            "cutter_type": ct,
            "speed_mms": float(sp),
            "start_height_h1_mm": mapping.get("h1_mm", h1_default) if mapping else h1_default,
            "end_height_h2_mm": float(h2),
            "color_rgb": _aci_to_rgb(aci),
            "direction": dr,
            "starting_extension_mm": float(se),
            "ending_extension_mm": float(ee),
            "is_output_yes": is_output,
            "number_of_feeding": mapping.get("number_of_feeding", feed_default) if mapping else feed_default,
        }
        vcf_layers.append(layer)
        aci_to_layer_index[aci] = len(vcf_layers) - 1

    vcf_elements = []
    for e in entities:
        ci = e["color_index"]
        raw_vertices = e.get("vertices", [])
        if not raw_vertices or len(raw_vertices) < 2:
            continue
        vertices = _apply_coord_transform(raw_vertices)
        vertices = _dedup_consecutive(vertices)
        if len(vertices) < 2:
            continue
        etype = e.get("type", "")
        geom_type = "Circle" if etype == "CIRCLE" else "Polyline"
        elem = {
            "geom_type": geom_type,
            "vertices": vertices,
            "layer_index": aci_to_layer_index.get(ci, 0),
            "is_output_yes": True,
        }
        if etype == "CIRCLE":
            cx = e.get("circle_cx")
            cy = e.get("circle_cy")
            r = e.get("circle_radius")
            if cx is not None and cy is not None and r is not None:
                elem["circle_params"] = {
                    "cx": cx + _DXF_TO_VCF_OFFSET_X,
                    "cy": cy + _DXF_TO_VCF_OFFSET_Y,
                    "radius": r
                }
        else:
            circle_info = _points_on_circle(vertices)
            if circle_info:
                elem["geom_type"] = "Circle"
                elem["circle_params"] = {
                    "cx": circle_info["cx"],
                    "cy": circle_info["cy"],
                    "radius": circle_info["radius"],
                }
        vcf_elements.append(elem)

    return {"layers": vcf_layers, "elements": vcf_elements}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compile_dxf(dxf_path, output_path, config_path=None, h1_default=2.0, feed_default=1):
    """
    Kompletní DXF → VCF pipeline.

    Args:
        dxf_path: Cesta ke vstupnímu DXF souboru.
        output_path: Cesta k výstupnímu VCF souboru.
        config_path: Cesta k vcf_compiler_map_config.json.
                     Pokud None, hledá se v CWD.
        h1_default: Fallback H1 výška (start_height_h1_mm).
        feed_default: Fallback number_of_feeding.
    """
    dxf_path = Path(dxf_path)
    if not dxf_path.exists():
        raise FileNotFoundError(f"DXF file not found: {dxf_path}")

    idx = _get_dxf_indexer()
    tool_config = _load_config(config_path)

    logger.info("Parsing DXF: %s", dxf_path)
    result = idx.index_dxf(dxf_path, tool_config, keep_vertices=True)
    if result is None:
        raise ValueError(f"index_dxf returned None for {dxf_path} (no entities?)")

    entities = result.get("entities", [])
    if not entities:
        raise ValueError(f"No entities found in {dxf_path}")

    layer_card = result.get("layer_card", {})
    spec = _build_vcf_spec(entities, layer_card, tool_config, h1_default, feed_default)

    if not spec["layers"]:
        raise ValueError("No layers generated — check ACI mapping")

    if not spec["elements"]:
        raise ValueError("No elements generated — check entity geometry")

    from vcf_parser._writer import write
    write(spec, str(output_path), dxf_source_path=str(dxf_path))

    logger.info(
        "Compiled DXF → VCF: %s (%d layers, %d elements, %.1f m path)",
        output_path,
        len(spec["layers"]),
        len(spec["elements"]),
        sum(e["length_mm"] for e in entities),
    )
