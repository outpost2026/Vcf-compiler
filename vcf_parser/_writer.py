import struct
import math
import logging
from copy import deepcopy
from typing import Optional

from vcf_parser._reader import GEOMETRY_SIG, CUTTER_MAP, DIR_MAP

CUTTER_NAME_TO_INDEX = {name: idx for idx, name in CUTTER_MAP.items()}
DIR_NAME_TO_INDEX = {name: idx for idx, name in DIR_MAP.items()}

logger = logging.getLogger(__name__)


class VcfWriterError(Exception):
    pass


class InvalidGeometryError(VcfWriterError):
    pass


class UnsupportedFeatureError(VcfWriterError):
    pass


class SerializationError(VcfWriterError):
    pass


HEADER_MAGIC = b"RDVCUTFILEVER1.0.013"
HEADER_MAGIC_012 = b"RDVCUTFILEVER1.0.012"
VCF_PREFIX = b"\x13"
VCF_POST_MAGIC = b"\x20\x0a\x00"
EMPTY_BLOCK_COUNT = 256
LAYER_BLOCK_SIZE = 610
STOCK_WIDTH = 1220.0
STOCK_HEIGHT = 2900.0
POST_STOCK_HEADER = struct.pack('<I', 0) + struct.pack('<d', 100.0) + struct.pack('<H', 1)

MACHINE_PROFILE = bytes([
    0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x49, 0x40, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0xf0, 0x3f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x24, 0x40, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0xf0, 0x3f, 0x80, 0x80, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x8f, 0x8f, 0x8f, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x04, 0xcb, 0xce, 0xcc, 0xe5, 0x06, 0x46, 0x53, 0x2e, 0x53, 0x48, 0x58, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x20, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x9a, 0x99, 0x99, 0x99, 0x99, 0x99, 0xb9, 0x3f, 0xfc, 0xa9, 0xf1, 0xd2,
    0x4d, 0x62, 0x50, 0x3f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x9a, 0x99, 0x99, 0x99, 0x99, 0x99, 0xb9, 0x3f,
    0x00, 0x00, 0x00, 0x00, 0x33, 0x33, 0x33, 0x33, 0x33, 0x33, 0xd3, 0x3f, 0x00, 0x00, 0x00, 0x00,
    0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x02, 0x00, 0x9a, 0x99, 0x99, 0x99, 0x99, 0x99, 0xb9, 0x3f, 0x9a, 0x99, 0x99, 0x99,
    0x99, 0x99, 0xb9, 0x3f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xf0, 0x3f, 0x07, 0x6f, 0x70, 0x72,
    0x61, 0x76, 0x69, 0x74, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x59, 0x40, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x59, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x24, 0x40, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x80, 0x6b, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0b, 0x41,
    0x72, 0x69, 0x61, 0x6c, 0x20, 0x42, 0x6c, 0x61, 0x63, 0x6b, 0x06, 0x46, 0x73, 0x2e, 0x53, 0x48,
    0x58, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04,
    0x30, 0x30, 0x30, 0x30, 0x04, 0x30, 0x30, 0x30, 0x30, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x04, 0x39, 0x39, 0x39, 0x39, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x01, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x24, 0x40, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x24, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x54, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x14, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00,
])

TRAILER_PREFIX = bytes([
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x14, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x56, 0x40, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x14, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x56, 0x40, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
])

GEOMETRY_HEADER_TEMPLATE = bytes([
    0, 0, 0, 0,
    0, 0, 0, 240, 63, 0, 0, 0,
    0, 0, 0, 240, 63, 0, 0, 0,
    0, 0, 0, 240, 63, 0, 0, 0,
    0, 0, 0, 240, 63,
])


class VcfLayer:
    def __init__(self, paths=None, speed=None, cutter_type="Vibrate cutter",
                 h1=2.0, h2=12.0, color=None, direction="N/A",
                 start_ext=0.0, end_ext=0.0, is_output=True,
                 feed_count=1):
        self._paths = paths or []
        self._bbox = None
        self._speed = speed or 800.0
        self._cutter_type = cutter_type
        self._h1 = h1
        self._h2 = h2
        self._color = color or [255, 0, 0]
        self._direction = direction
        self._start_ext = start_ext
        self._end_ext = end_ext
        self._is_output = is_output
        self._feed_count = feed_count
        self._path_types = []

    def _compute_bbox(self):
        if not self._paths:
            return [0.0, 0.0, 0.0, 0.0]
        all_x = [p[0] for path in self._paths for p in path]
        all_y = [p[1] for path in self._paths for p in path]
        return [min(all_x), min(all_y), max(all_x), max(all_y)]


class VcfWriter:
    VERSION = "1.0"

    def __init__(self, layers=None, version="1.0.013", globalbbox=None, dxf_source_path=None):
        self._layers = layers or []
        self._version = version
        self._globalbbox = globalbbox
        self._dxf_source_path = dxf_source_path

    def add_layer(self, layer: VcfLayer):
        self._layers.append(layer)

    def set(self, layers=None, globalbbox=None, version=None):
        if layers:
            self._layers = layers
        if globalbbox:
            self._globalbbox = globalbbox
        if version:
            self._version = version

    # ── Header ──

    def header(self) -> bytes:
        data = bytearray()

        data += VCF_PREFIX

        if self._version == "1.0.012":
            data += HEADER_MAGIC_012
        else:
            data += HEADER_MAGIC

        data += VCF_POST_MAGIC

        data += self.encode_float64(STOCK_WIDTH)
        data += self.encode_float64(STOCK_HEIGHT)

        data += POST_STOCK_HEADER

        data += MACHINE_PROFILE

        n_layers = len(self._layers)
        total_blocks = EMPTY_BLOCK_COUNT + n_layers
        empty_count = EMPTY_BLOCK_COUNT

        for i in range(empty_count):
            block = bytearray(LAYER_BLOCK_SIZE)
            struct.pack_into('<H', block, 10, i)
            if i == empty_count - 1 and n_layers > 0:
                next_layer = self._layers[0]
                next_color_bgr = (next_layer._color[0] << 16) | (next_layer._color[1] << 8) | next_layer._color[2]
                struct.pack_into('<I', block, LAYER_BLOCK_SIZE - 8, 1)
                struct.pack_into('<I', block, LAYER_BLOCK_SIZE - 4, next_color_bgr)
            data += bytes(block)

        for i, layer in enumerate(self._layers):
            block = bytearray(self.encode_layer_block(layer, LAYER_BLOCK_SIZE))
            if i < n_layers - 1:
                next_layer = self._layers[i + 1]
                next_color_bgr = (next_layer._color[0] << 16) | (next_layer._color[1] << 8) | next_layer._color[2]
                struct.pack_into('<I', block, LAYER_BLOCK_SIZE - 8, 1)
                struct.pack_into('<I', block, LAYER_BLOCK_SIZE - 4, next_color_bgr)
            data += bytes(block)

        return bytes(data)

    # ── Body ──

    def body(self) -> bytes:
        data = bytearray()
        for layer_idx, layer in enumerate(self._layers):
            if not layer._paths:
                continue
            for pi, path in enumerate(layer._paths):
                if pi < len(layer._path_types) and layer._path_types[pi] == "Circle":
                    cx, cy, radius = self._compute_circle_params(path)
                    data += self.encode_circle_element(cx, cy, radius, layer, layer_idx)
                else:
                    data += self.encode_geometry_element(path, layer, layer_idx)
        return bytes(data)

    # ── Trailer ──

    def trailer(self) -> bytes:
        data = bytearray(TRAILER_PREFIX)
        if self._dxf_source_path:
            raw_path = str(self._dxf_source_path).encode('ascii', errors='replace')
            data.append(0x00)
            data.append(len(raw_path))
            data.extend(raw_path)
        return bytes(data)

    # ── Write ──

    def write(self, fd, scramble=False) -> None:
        if scramble:
            raise UnsupportedFeatureError("VCF format does not support scrambling")
        h = self.header()
        b = self.body()
        t = self.trailer()
        fd.write(h + b + t)

    # ── Encoding utilities ──

    @staticmethod
    def encode_float64(value: float) -> bytes:
        return struct.pack('<d', value)

    @staticmethod
    def encode_uint32(value: int) -> bytes:
        return struct.pack('<I', value)

    @staticmethod
    def encode_uint16(value: int) -> bytes:
        return struct.pack('<H', value)

    @staticmethod
    def encode_int32(value: int) -> bytes:
        return struct.pack('<i', value)

    @staticmethod
    def encode_layer_block(layer: VcfLayer, block_size: int) -> bytes:
        block = bytearray(block_size)

        struct.pack_into('<I', block, 0, 1 if layer._is_output else 0)

        struct.pack_into('<d', block, 4, float(layer._speed))

        cutter_idx = CUTTER_NAME_TO_INDEX.get(layer._cutter_type, 0)
        struct.pack_into('<i', block, 32, cutter_idx)

        struct.pack_into('<I', block, 76, 0)  # Native VCFs always store black at offset 76

        struct.pack_into('<d', block, 80, layer._h1)

        struct.pack_into('<i', block, 88, layer._feed_count)

        struct.pack_into('<d', block, 96, layer._h2)

        if layer._cutter_type == "V-slot":
            dir_idx = DIR_NAME_TO_INDEX.get(layer._direction, 0)
            struct.pack_into('<H', block, 104, dir_idx)
            struct.pack_into('<d', block, 106, 0.0)
            struct.pack_into('<d', block, 114, layer._start_ext)
            struct.pack_into('<d', block, 122, layer._end_ext)

        return bytes(block)

    @staticmethod
    def encode_geometry_element(path: list, layer: VcfLayer, layer_idx: int) -> bytes:
        if not path or len(path) < 2:
            raise InvalidGeometryError(f"Path with <2 points (layer {layer_idx})")

        pt_count = len(path) - 1

        element_size = 45 + pt_count * 74
        data = bytearray(element_size)

        data[0:8] = GEOMETRY_SIG

        color_bgr = (layer._color[0] << 16) | (layer._color[1] << 8) | layer._color[2]
        expected_geom_color = (color_bgr << 8) & 0xffffffff
        struct.pack_into('<I', data, 8, expected_geom_color)

        data[12:45] = GEOMETRY_HEADER_TEMPLATE

        type_offset = 45
        EPS = 0.001
        is_closed = len(path) >= 2 and abs(path[0][0] - path[-1][0]) < EPS and abs(path[0][1] - path[-1][1]) < EPS
        geom_type = 1 if is_closed else 0
        subtype = 0
        struct.pack_into('<I', data, type_offset, geom_type)
        struct.pack_into('<I', data, type_offset + 4, pt_count)
        struct.pack_into('<I', data, type_offset + 8, subtype)

        for i in range(pt_count):
            seg_start = type_offset + i * 74
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            struct.pack_into('<d', data, seg_start + 14, x1)
            struct.pack_into('<d', data, seg_start + 22, y1)
            struct.pack_into('<d', data, seg_start + 30, x2)
            struct.pack_into('<d', data, seg_start + 38, y2)

        return bytes(data)

    @staticmethod
    def _compute_circle_params(path):
        xs = [p[0] for p in path]
        ys = [p[1] for p in path]
        cx = (min(xs) + max(xs)) / 2.0
        cy = (min(ys) + max(ys)) / 2.0
        radius = (max(xs) - min(xs)) / 2.0
        return cx, cy, radius

    @staticmethod
    def encode_circle_element(cx: float, cy: float, radius: float, layer: VcfLayer, layer_idx: int) -> bytes:
        pt_count = 4
        element_size = 45 + pt_count * 74
        data = bytearray(element_size)

        data[0:8] = GEOMETRY_SIG

        color_bgr = (layer._color[0] << 16) | (layer._color[1] << 8) | layer._color[2]
        expected_geom_color = (color_bgr << 8) & 0xffffffff
        struct.pack_into('<I', data, 8, expected_geom_color)

        data[12:45] = GEOMETRY_HEADER_TEMPLATE

        type_offset = 45
        struct.pack_into('<I', data, type_offset, 1)
        struct.pack_into('<I', data, type_offset + 4, pt_count)
        struct.pack_into('<I', data, type_offset + 8, 3)

        arcs = [
            (cx - radius, cy, cx, cy + radius),
            (cx, cy + radius, cx + radius, cy),
            (cx + radius, cy, cx, cy - radius),
            (cx, cy - radius, cx - radius, cy),
        ]

        for i, (x1, y1, x2, y2) in enumerate(arcs):
            seg_start = type_offset + i * 74
            struct.pack_into('<d', data, seg_start + 14, x1)
            struct.pack_into('<d', data, seg_start + 22, y1)
            struct.pack_into('<d', data, seg_start + 30, x2)
            struct.pack_into('<d', data, seg_start + 38, y2)

        return bytes(data)

    def _compute_global_bbox(self):
        if not self._layers:
            return [0.0, 0.0, 2790.0, 1200.0]
        all_x = []
        all_y = []
        for layer in self._layers:
            for path in layer._paths:
                for p in path:
                    all_x.append(p[0])
                    all_y.append(p[1])
        if not all_x:
            return [0.0, 0.0, 2790.0, 1200.0]
        return [min(all_x), min(all_y), max(all_x), max(all_y)]


# ── Top-level API ──

def write(specification: dict, output_path: str, version: str = "1.0.013", dxf_source_path: Optional[str] = None) -> None:
    layers_dict = specification.get("layers", [])
    elements = specification.get("elements", [])

    vcf_layers = []
    element_layer_map = {}

    for lidx, ld in enumerate(layers_dict):
        color_rgb = ld.get("color_rgb", [255, 0, 0])
        paths = []
        path_types = []
        layer_element_indices = [ei for ei, el in enumerate(elements) if el.get("layer_index", 0) == lidx]

        for ei in layer_element_indices:
            el = elements[ei]
            vertices = el.get("vertices", [])
            if vertices and len(vertices) >= 2:
                paths.append(vertices)
                path_types.append(el.get("geom_type", "Polyline"))

        layer = VcfLayer(
            paths=paths,
            speed=ld.get("speed_mms", 800.0),
            cutter_type=ld.get("cutter_type", "Vibrate cutter"),
            h1=ld.get("start_height_h1_mm", 10.0),
            h2=ld.get("end_height_h2_mm", 12.0),
            color=color_rgb,
            direction=ld.get("direction", "N/A"),
            start_ext=ld.get("starting_extension_mm", 0.0),
            end_ext=ld.get("ending_extension_mm", 0.0),
            is_output=ld.get("is_output_yes", True),
            feed_count=ld.get("number_of_feeding", 1),
        )
        layer._path_types = path_types
        vcf_layers.append(layer)

    writer = VcfWriter(layers=vcf_layers, version=version, dxf_source_path=dxf_source_path)

    try:
        with open(output_path, 'wb') as f:
            writer.write(f)
    except (OSError, IOError) as e:
        raise SerializationError(f"Cannot write to {output_path}: {e}") from e

    logger.info("Wrote VCF: %s (%d layers, %d elements)", output_path, len(vcf_layers), len(elements))
