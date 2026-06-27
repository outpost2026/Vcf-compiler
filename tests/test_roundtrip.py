import json
import struct
import pytest
from pathlib import Path


def _parse_vcf_simple(binary_data: bytes) -> dict:
    from vcf_parser._reader import extract_active_layers_details, GEOMETRY_SIG

    layers = extract_active_layers_details(binary_data)

    elements = []
    offset = 0
    while True:
        pos = binary_data.find(GEOMETRY_SIG, offset)
        if pos == -1:
            break
        p = pos + 45
        if p >= len(binary_data):
            break
        geom_color = struct.unpack_from('<I', binary_data, pos + 8)[0]
        type_id = struct.unpack_from('<I', binary_data, p)[0]
        pt_count = struct.unpack_from('<I', binary_data, p + 4)[0]
        subtype = struct.unpack_from('<I', binary_data, p + 8)[0]

        vertices = []
        for i in range(pt_count):
            seg_start = pos + 45 + i * 74
            x1 = struct.unpack('<d', binary_data[seg_start + 14:seg_start + 22])[0]
            y1 = struct.unpack('<d', binary_data[seg_start + 22:seg_start + 30])[0]
            x2 = struct.unpack('<d', binary_data[seg_start + 30:seg_start + 38])[0]
            y2 = struct.unpack('<d', binary_data[seg_start + 38:seg_start + 46])[0]
            if i == 0:
                vertices.append((x1, y1))
            vertices.append((x2, y2))

        geom_type = "Line"
        if type_id == 1 and (subtype & 0xFFFF) == 3:
            geom_type = "Circle" if pt_count <= 8 else "Polygon"
        elif type_id == 0:
            geom_type = "Line" if pt_count == 1 else "Polyline"
        elif type_id == 1:
            geom_type = "Polygon"

        layer_idx = -1
        for idx, l in enumerate(layers):
            color_rgb = l["color_rgb"]
            layer_color_bgr = (color_rgb[0] << 16) | (color_rgb[1] << 8) | color_rgb[2]
            if geom_color == ((layer_color_bgr << 8) & 0xffffffff):
                layer_idx = idx
                break

        element = {
            "geom_type": geom_type,
            "vertices": vertices,
            "layer_index": layer_idx,
            "is_output_yes": True,
        }
        elements.append(element)
        offset = pos + 1

    return {"layers": layers, "elements": elements}


def _strip_parsed(data: dict) -> dict:
    layers = []
    for l in data.get("layers", []):
        layers.append({
            "cutter_type": l["cutter_type"],
            "speed_mms": l["speed_mms"],
            "start_height_h1_mm": l["start_height_h1_mm"],
            "end_height_h2_mm": l["end_height_h2_mm"],
            "color_rgb": l["color_rgb"],
            "direction": l.get("direction", "N/A"),
            "starting_extension_mm": l.get("starting_extension_mm", 0.0),
            "ending_extension_mm": l.get("ending_extension_mm", 0.0),
            "is_output_yes": l["is_output_yes"],
            "number_of_feeding": l.get("number_of_feeding", 1),
        })
    elements = []
    for el in data.get("elements", []):
        elements.append({
            "geom_type": el["geom_type"],
            "vertices": [(round(v[0], 4), round(v[1], 4)) for v in el["vertices"]],
            "layer_index": el["layer_index"],
            "is_output_yes": el.get("is_output_yes", True),
        })
    return {"layers": layers, "elements": elements}


def _build_spec(layers: list, elements: list) -> dict:
    return {
        "layers": [
            {
                "cutter_type": l["cutter_type"],
                "speed_mms": l["speed_mms"],
                "start_height_h1_mm": l["start_height_h1_mm"],
                "end_height_h2_mm": l["end_height_h2_mm"],
                "color_rgb": l["color_rgb"],
                "direction": l.get("direction", "N/A"),
                "starting_extension_mm": l.get("starting_extension_mm", 0.0),
                "ending_extension_mm": l.get("ending_extension_mm", 0.0),
                "is_output_yes": l["is_output_yes"],
                "number_of_feeding": l.get("number_of_feeding", 1),
            }
            for l in layers
        ],
        "elements": [
            {
                "geom_type": el["geom_type"],
                "vertices": el["vertices"],
                "layer_index": el["layer_index"],
                "is_output_yes": el.get("is_output_yes", True),
            }
            for el in elements
        ],
    }


@pytest.mark.integration
@pytest.mark.parametrize("filename", [
    "line_x0_y1000.VCF",
    "test_primitive.VCF",
    "empty_01.VCF",
])
def test_roundtrip_known_files(filename, demo_dir, test_output_dir):
    vcf_path = Path(demo_dir) / filename
    if not vcf_path.exists():
        pytest.skip(f"Demo file not found: {vcf_path}")

    raw = vcf_path.read_bytes()
    parsed = _parse_vcf_simple(raw)

    if not parsed["layers"]:
        pytest.skip(f"No layers detected in {filename}")

    spec = _build_spec(parsed["layers"], parsed["elements"])

    from vcf_parser._writer import write
    out_path = Path(test_output_dir) / f"roundtrip_{filename}"
    write(spec, str(out_path))

    reparsed_raw = out_path.read_bytes()
    reparsed = _parse_vcf_simple(reparsed_raw)

    assert len(reparsed["layers"]) == len(parsed["layers"]), (
        f"Layer count mismatch: {len(reparsed['layers'])} vs {len(parsed['layers'])}"
    )

    assert len(reparsed["elements"]) == len(parsed["elements"]), (
        f"Element count mismatch: {len(reparsed['elements'])} vs {len(parsed['elements'])}"
    )

    for i, (orig_l, new_l) in enumerate(zip(parsed["layers"], reparsed["layers"])):
        for key in ("speed_mms", "cutter_type", "start_height_h1_mm", "end_height_h2_mm",
                     "is_output_yes"):
            assert orig_l.get(key) == new_l.get(key), (
                f"Layer {i} {key}: {orig_l.get(key)} vs {new_l.get(key)}"
            )

    for i, (orig_el, new_el) in enumerate(zip(parsed["elements"], reparsed["elements"])):
        assert orig_el["geom_type"] == new_el["geom_type"], (
            f"Element {i} geom_type: {orig_el['geom_type']} vs {new_el['geom_type']}"
        )
        assert orig_el["layer_index"] == new_el["layer_index"], (
            f"Element {i} layer_index: {orig_el['layer_index']} vs {new_el['layer_index']}"
        )


def test_roundtrip_synthetic_line(test_output_dir):
    from vcf_parser._writer import write

    spec = {
        "layers": [
            {
                "cutter_type": "Vibrate cutter",
                "speed_mms": 500.0,
                "start_height_h1_mm": 2.0,
                "end_height_h2_mm": 12.0,
                "color_rgb": [255, 0, 0],
                "direction": "N/A",
                "starting_extension_mm": 0.0,
                "ending_extension_mm": 0.0,
                "is_output_yes": True,
                "number_of_feeding": 1,
            }
        ],
        "elements": [
            {
                "geom_type": "Polyline",
                "vertices": [(600.0, 1950.0), (600.0, 950.0)],
                "layer_index": 0,
                "is_output_yes": True,
            }
        ],
    }

    out_path = Path(test_output_dir) / "synthetic_line.VCF"
    write(spec, str(out_path))

    reparsed = _parse_vcf_simple(out_path.read_bytes())

    assert len(reparsed["layers"]) == 1
    assert reparsed["layers"][0]["speed_mms"] == 500.0
    assert reparsed["layers"][0]["cutter_type"] == "Vibrate cutter"
    assert len(reparsed["elements"]) == 1


def test_roundtrip_two_layers(test_output_dir):
    from vcf_parser._writer import write

    spec = {
        "layers": [
            {
                "cutter_type": "Vibrate cutter",
                "speed_mms": 800.0,
                "start_height_h1_mm": 2.0,
                "end_height_h2_mm": 12.0,
                "color_rgb": [255, 0, 0],
                "direction": "N/A",
                "starting_extension_mm": 0.0,
                "ending_extension_mm": 0.0,
                "is_output_yes": True,
                "number_of_feeding": 1,
            },
            {
                "cutter_type": "V-slot",
                "speed_mms": 400.0,
                "start_height_h1_mm": 2.0,
                "end_height_h2_mm": 6.0,
                "color_rgb": [0, 0, 255],
                "direction": "Left",
                "starting_extension_mm": 2.5,
                "ending_extension_mm": 2.5,
                "is_output_yes": True,
                "number_of_feeding": 1,
            },
        ],
        "elements": [
            {
                "geom_type": "Polyline",
                "vertices": [(100.0, 100.0), (500.0, 100.0)],
                "layer_index": 0,
                "is_output_yes": True,
            },
            {
                "geom_type": "Polyline",
                "vertices": [(100.0, 200.0), (500.0, 200.0)],
                "layer_index": 1,
                "is_output_yes": True,
            },
        ],
    }

    out_path = Path(test_output_dir) / "two_layers.VCF"
    write(spec, str(out_path))

    reparsed = _parse_vcf_simple(out_path.read_bytes())
    assert len(reparsed["layers"]) == 2
    assert len(reparsed["elements"]) == 2
    assert reparsed["layers"][0]["cutter_type"] == "Vibrate cutter"
    assert reparsed["layers"][1]["cutter_type"] == "V-slot"


def test_roundtrip_vslot_params(test_output_dir):
    from vcf_parser._writer import write

    spec = {
        "layers": [
            {
                "cutter_type": "V-slot",
                "speed_mms": 300.0,
                "start_height_h1_mm": 2.0,
                "end_height_h2_mm": 6.0,
                "color_rgb": [0, 255, 0],
                "direction": "Cut both side",
                "starting_extension_mm": 3.0,
                "ending_extension_mm": 3.0,
                "is_output_yes": True,
                "number_of_feeding": 1,
            }
        ],
        "elements": [
            {
                "geom_type": "Polyline",
                "vertices": [(0.0, 0.0), (1000.0, 0.0)],
                "layer_index": 0,
                "is_output_yes": True,
            }
        ],
    }

    out_path = Path(test_output_dir) / "vslot_test.VCF"
    write(spec, str(out_path))

    reparsed = _parse_vcf_simple(out_path.read_bytes())
    vslot_layer = reparsed["layers"][0]
    assert vslot_layer["cutter_type"] == "V-slot"
    assert vslot_layer.get("direction") == "Cut both side"


def test_roundtrip_determinism(test_output_dir):
    from vcf_parser._writer import write

    spec = {
        "layers": [
            {
                "cutter_type": "Vibrate cutter",
                "speed_mms": 600.0,
                "start_height_h1_mm": 2.0,
                "end_height_h2_mm": 12.0,
                "color_rgb": [255, 0, 0],
                "direction": "N/A",
                "starting_extension_mm": 0.0,
                "ending_extension_mm": 0.0,
                "is_output_yes": True,
                "number_of_feeding": 1,
            }
        ],
        "elements": [
            {
                "geom_type": "Polyline",
                "vertices": [(0.0, 0.0), (2790.0, 0.0)],
                "layer_index": 0,
                "is_output_yes": True,
            }
        ],
    }

    from vcf_parser._writer import write
    out1 = Path(test_output_dir) / "det1.VCF"
    out2 = Path(test_output_dir) / "det2.VCF"
    write(spec, str(out1))
    write(spec, str(out2))
    assert out1.read_bytes() == out2.read_bytes(), "Determinism failure: two writes differ"
