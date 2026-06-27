import struct
import math
import re
import logging

logger = logging.getLogger(__name__)

GEOMETRY_SIG = b'\x01\x00\x01\x00\x00\xff\xff\xff'

COLOR_MAP = {
    "000000": "Černá", "00ff00": "Zelená", "0000ff": "Modrá",
    "ffff00": "Žlutá", "ff0000": "Červená", "00cccc": "Azurová (Cyan)",
    "800040": "Vínová / Fialová", "5790fa": "Světle modrá",
    "73dd75": "Světle zelená", "ffffff": "Bílá", "808080": "Šedá",
    "ff00ff": "Růžová / Purpurová", "ffa500": "Oranžová", "00ffff": "Tyrkysová",
}

CUTTER_MAP = {0: "Vibrate cutter", 1: "Wheel", 2: "Milling cutter", 3: "V-slot", 4: "Vibrate cut"}
DIR_MAP = {0: "Left", 1: "Right", 2: "Cut both side"}
CUTTER_ID_MAP = {"Vibrate cutter": 1, "Wheel": 2, "Milling cutter": 3, "V-slot": 4, "Vibrate cut": 5}
DIR_ID_MAP = {"Left": 1, "Right": 2, "Cut both side": 3, "N/A": 0}


def get_color_name(hex_val: str) -> str:
    val = hex_val.lower().replace("0x", "").strip()
    val = val.zfill(8)
    rgb = val[2:] if len(val) == 8 else val
    if rgb in COLOR_MAP:
        return COLOR_MAP[rgb]
    return f"Vlastní ({hex_val})"


def extract_strings(binary_data: bytes) -> list:
    strings = re.findall(b'[A-Za-z0-9_ \\-\\.]{4,}', binary_data)
    decoded = set()
    for s in strings:
        try:
            text = s.decode('windows-1250').strip()
            if ".dxf" in text.lower():
                decoded.add(text)
            elif any(c.isalpha() for c in text) and len(text) > 3:
                decoded.add(text)
        except UnicodeError:
            continue
    return sorted(list(decoded))


def extract_active_layers_details(binary_data: bytes) -> list:
    version = "1.0.013"
    for s in [b"RDVCUTFILEVER1.0.012", b"VER1.0.012"]:
        if s in binary_data:
            version = "1.0.012"
            break

    block_size = 610 if version == "1.0.013" else 210
    header_size = 54
    active_layers = []

    max_blocks = min((len(binary_data) - header_size) // block_size, 257)

    for block_idx in range(max_blocks):
        pos = header_size + block_idx * block_size

        try:
            output_flag = struct.unpack_from('<I', binary_data, pos)[0]
            if output_flag != 1:
                continue

            speed = struct.unpack('<d', binary_data[pos + 4:pos + 12])[0]
            if not (1.0 <= speed <= 2000.0 and speed.is_integer() and speed % 5 == 0):
                continue

            color_val = struct.unpack_from('<I', binary_data, pos + 12)[0]

            cutter_type_raw = struct.unpack('<i', binary_data[pos + 32:pos + 36])[0]
            cutter_type = cutter_type_raw & 0xffff

            feed_num = struct.unpack('<i', binary_data[pos + 84:pos + 88])[0]
            start_height_h1 = struct.unpack('<d', binary_data[pos + 76:pos + 84])[0]
            end_height_h2 = struct.unpack('<d', binary_data[pos + 92:pos + 100])[0]

            b_comp = color_val & 0xff
            g_comp = (color_val >> 8) & 0xff
            r_comp = (color_val >> 16) & 0xff

            cutter_name = CUTTER_MAP.get(cutter_type, "Unknown")

            layer_info = {
                "speed_mms": int(speed),
                "cutter_type": cutter_name,
                "cutter_type_id": CUTTER_ID_MAP.get(cutter_name, 0),
                "number_of_feeding": feed_num,
                "start_height_h1_mm": round(start_height_h1, 3),
                "travel_safety_height_mm": round(start_height_h1, 3),
                "end_height_h2_mm": round(end_height_h2, 3),
                "total_cut_length_mm": 0.0,
                "color_hex": f"0x{color_val:08x}",
                "color_val": color_val,
                "color_rgb": [r_comp, g_comp, b_comp],
                "direction": "N/A",
                "direction_id": 0,
                "v_slot_width_comp_mm": 0.0,
                "starting_extension_mm": 0.0,
                "ending_extension_mm": 0.0,
                "is_output_yes": True,
                "operation_type": "N/A",
                "complexity": {
                    "avg_segment_length_mm": 0.0,
                    "curvature_index": 0.0,
                    "sharp_corners_count": 0,
                    "total_direction_changes": 0,
                },
            }

            try:
                start_ext = struct.unpack('<d', binary_data[pos + 110:pos + 118])[0]
                end_ext = struct.unpack('<d', binary_data[pos + 118:pos + 126])[0]
                if not (math.isnan(start_ext) or math.isinf(start_ext)):
                    layer_info["starting_extension_mm"] = round(start_ext, 3)
                if not (math.isnan(end_ext) or math.isinf(end_ext)):
                    layer_info["ending_extension_mm"] = round(end_ext, 3)
            except (struct.error, ValueError) as e:
                logger.warning("Could not parse extensions at layer offset %d: %s", pos, e)

            if cutter_type == 3:
                try:
                    direction_raw = struct.unpack('<H', binary_data[pos + 100:pos + 102])[0]
                    v_slot_comp = struct.unpack('<d', binary_data[pos + 102:pos + 110])[0]
                    dir_name = DIR_MAP.get(direction_raw, "Unknown")
                    layer_info["direction"] = dir_name
                    layer_info["direction_id"] = DIR_ID_MAP.get(dir_name, -1)
                    if not (math.isnan(v_slot_comp) or math.isinf(v_slot_comp)):
                        layer_info["v_slot_width_comp_mm"] = round(v_slot_comp, 3)
                except (struct.error, ValueError) as e:
                    logger.warning("Could not parse V-slot direction at offset %d: %s", pos, e)

            active_layers.append(layer_info)
        except Exception:
            continue

    return active_layers
