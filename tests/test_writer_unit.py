import struct
import math
import pytest
from vcf_parser._writer import (
    VcfLayer, VcfWriter, VcfWriterError,
    GEOMETRY_SIG, CUTTER_NAME_TO_INDEX
)


def test_vcflayer_defaults():
    layer = VcfLayer()
    assert layer._speed == 800.0
    assert layer._cutter_type == "Vibrate cutter"
    assert layer._h1 == 2.0
    assert layer._h2 == 12.0
    assert layer._color == [255, 0, 0]
    assert layer._is_output is True


def test_encode_float64():
    val = VcfWriter.encode_float64(150.0)
    assert struct.unpack('<d', val)[0] == 150.0


def test_encode_uint32():
    val = VcfWriter.encode_uint32(0xFF00FF)
    assert struct.unpack('<I', val)[0] == 0xFF00FF


def test_layer_block_size():
    layer = VcfLayer(speed=500.0, color=[0, 255, 0])
    block_610 = VcfWriter.encode_layer_block(layer, 610)
    block_210 = VcfWriter.encode_layer_block(layer, 210)
    assert len(block_610) == 610
    assert len(block_210) == 210


def test_layer_block_speed():
    layer = VcfLayer(speed=500.0)
    block = VcfWriter.encode_layer_block(layer, 610)
    speed = struct.unpack('<d', block[4:12])[0]
    assert speed == 500.0


def test_layer_block_color_bgr():
    layer = VcfLayer(color=[255, 0, 0])
    block = VcfWriter.encode_layer_block(layer, 610)
    color_val = struct.unpack('<I', block[76:80])[0]
    expected_bgr = (255 << 16) | (0 << 8) | 0
    assert color_val == expected_bgr


def test_layer_block_cutter_id():
    layer = VcfLayer(cutter_type="V-slot")
    block = VcfWriter.encode_layer_block(layer, 610)
    cutter_raw = struct.unpack('<i', block[32:36])[0]
    assert cutter_raw == CUTTER_NAME_TO_INDEX["V-slot"]


def test_layer_block_h1_h2():
    layer = VcfLayer(h1=3.0, h2=15.0)
    block = VcfWriter.encode_layer_block(layer, 610)
    h1 = struct.unpack('<d', block[80:88])[0]
    h2 = struct.unpack('<d', block[96:104])[0]
    assert h1 == 3.0
    assert h2 == 15.0


def test_layer_block_output_flag():
    layer = VcfLayer(is_output=False)
    block = VcfWriter.encode_layer_block(layer, 610)
    flag = struct.unpack('<I', block[0:4])[0]
    assert flag == 0

    layer2 = VcfLayer(is_output=True)
    block2 = VcfWriter.encode_layer_block(layer2, 610)
    flag2 = struct.unpack('<I', block2[0:4])[0]
    assert flag2 == 1


def test_layer_block_feed_count():
    layer = VcfLayer(feed_count=3)
    block = VcfWriter.encode_layer_block(layer, 610)
    feed = struct.unpack('<i', block[88:92])[0]
    assert feed == 3


def test_geometry_element_geom_sig():
    path = [(0.0, 0.0), (100.0, 100.0)]
    layer = VcfLayer()
    data = VcfWriter.encode_geometry_element(path, layer, 0)
    assert data[:8] == GEOMETRY_SIG


def test_geometry_element_color():
    path = [(0.0, 0.0), (100.0, 0.0)]
    layer = VcfLayer(color=[255, 0, 0])
    data = VcfWriter.encode_geometry_element(path, layer, 0)
    color_bgr = (255 << 16) | (0 << 8) | 0
    expected_geom_color = (color_bgr << 8) & 0xffffffff
    stored_color = struct.unpack('<I', data[8:12])[0]
    assert stored_color == expected_geom_color


def test_geometry_element_coordinates():
    path = [(10.0, 20.0), (30.0, 40.0)]
    layer = VcfLayer()
    data = VcfWriter.encode_geometry_element(path, layer, 0)

    seg_start = 45
    x1 = struct.unpack('<d', data[seg_start + 14:seg_start + 22])[0]
    y1 = struct.unpack('<d', data[seg_start + 22:seg_start + 30])[0]
    x2 = struct.unpack('<d', data[seg_start + 30:seg_start + 38])[0]
    y2 = struct.unpack('<d', data[seg_start + 38:seg_start + 46])[0]

    assert x1 == 10.0
    assert y1 == 20.0
    assert x2 == 30.0
    assert y2 == 40.0


def test_geometry_element_type_count():
    path = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0)]
    layer = VcfLayer()
    data = VcfWriter.encode_geometry_element(path, layer, 0)

    p = 45
    type_id = struct.unpack('<I', data[p:p+4])[0]
    pt_count = struct.unpack('<I', data[p+4:p+8])[0]
    subtype = struct.unpack('<I', data[p+8:p+12])[0]

    assert type_id == 0
    assert pt_count == 2
    assert subtype == 0


def test_geometry_element_segment_size():
    path = [(0.0, 0.0), (100.0, 0.0), (200.0, 0.0)]
    layer = VcfLayer()
    data = VcfWriter.encode_geometry_element(path, layer, 0)
    expected_size = 45 + 2 * 74
    assert len(data) == expected_size


def test_geometry_element_invalid_path():
    layer = VcfLayer()
    with pytest.raises(VcfWriterError):
        VcfWriter.encode_geometry_element([(0.0, 0.0)], layer, 0)


def test_circle_element():
    layer = VcfLayer()
    data = VcfWriter.encode_circle_element(500.0, 500.0, 100.0, layer, 0)
    assert data[:8] == GEOMETRY_SIG
    p = 45
    type_id = struct.unpack('<I', data[p:p+4])[0]
    pt_count = struct.unpack('<I', data[p+4:p+8])[0]
    subtype = struct.unpack('<I', data[p+8:p+12])[0]
    assert type_id == 1
    assert pt_count == 4
    assert subtype == 3
    seg0_x1 = struct.unpack('<d', data[45+14:45+22])[0]
    assert seg0_x1 == 400.0  # cx - radius


def test_header_magic():
    layer = VcfLayer()
    writer = VcfWriter(layers=[layer], version="1.0.013")
    h = writer.header()
    MAGIC_013 = b"RDVCUTFILEVER1.0.013"
    assert h[0] == 0x13
    assert h[1:21] == MAGIC_013


def test_header_magic_012():
    layer = VcfLayer()
    writer = VcfWriter(layers=[layer], version="1.0.012")
    h = writer.header()
    MAGIC_012 = b"RDVCUTFILEVER1.0.012"
    assert h[0] == 0x13
    assert h[1:21] == MAGIC_012


def test_header_layer_order():
    layer1 = VcfLayer(color=[255, 0, 0], speed=100.0)
    layer2 = VcfLayer(color=[0, 255, 0], speed=200.0)
    writer = VcfWriter(layers=[layer1, layer2])
    h = writer.header()
    HEADER_PREAMBLE_SIZE = 54
    last_block = HEADER_PREAMBLE_SIZE + 256 * 610
    prev_block = HEADER_PREAMBLE_SIZE + 255 * 610
    speed_layer2 = struct.unpack('<d', h[last_block + 4:last_block + 12])[0]
    speed_layer1 = struct.unpack('<d', h[prev_block + 4:prev_block + 12])[0]
    assert speed_layer1 == 100.0
    assert speed_layer2 == 200.0


def test_trailer():
    writer = VcfWriter()
    h = writer.header()
    b = writer.body()
    raw = h + b
    assert raw[-1] != 0xd7


def test_write_roundtrip_single_line(tmp_path):
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
            }
        ],
        "elements": [
            {
                "geom_type": "Polyline",
                "vertices": [(100.0, 100.0), (200.0, 100.0)],
                "layer_index": 0,
                "is_output_yes": True,
            }
        ],
    }

    out = tmp_path / "test_single_line.VCF"
    write(spec, str(out))
    assert out.exists()
    assert out.stat().st_size > 0

    raw = out.read_bytes()
    assert raw[0] == 0x13
    MAGIC_013 = b"RDVCUTFILEVER1.0.013"
    assert raw[1:21] == MAGIC_013
    assert raw[-1] != 0xd7


def test_subminimal_path_ok(tmp_path):
    spec = {
        "layers": [{"color_rgb": [255, 0, 0], "speed_mms": 100.0}],
        "elements": [{"vertices": [(0.0, 0.0)], "layer_index": 0}],
    }
    out = tmp_path / "empty.VCF"
    from vcf_parser._writer import write
    write(spec, str(out))
    assert out.exists()
    assert out.stat().st_size > 0
