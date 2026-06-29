"""
VCF Binary Search Variant Generator

Generates VCF variants with features toggled on/off to isolate
which structural change causes VCutWorks "neočekávaný formát souboru".

Variants (least features → most features):
  A  — Minimal: active-first, no MP, no trailer, color@12 only, no linked-list, no empty blocks
  B  — A + empty blocks (empty-first), block index counter
  C  — B + linked-list (next/prev block pointers)
  D  — C + MACHINE_PROFILE
  E  — D + trailer
  F  — E + GEOMETRY_HEADER_TEMPLATE + full layer encoding (= current writer)

Patched variants:
  G  — F + native empty block init data (patch from native)
  H  — F but no trailer
  I  — F but no MACHINE_PROFILE
  J  — F but active-first (no empty blocks)
"""

import struct
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vcf_parser._writer import (
    VcfLayer, VcfWriter,
    HEADER_MAGIC, HEADER_MAGIC_012, VCF_PREFIX, VCF_POST_MAGIC,
    POST_STOCK_HEADER, MACHINE_PROFILE, TRAILER_PREFIX,
    GEOMETRY_HEADER_TEMPLATE, GEOMETRY_SIG,
    EMPTY_BLOCK_COUNT, LAYER_BLOCK_SIZE,
    STOCK_WIDTH, STOCK_HEIGHT,
    CUTTER_NAME_TO_INDEX, DIR_NAME_TO_INDEX,
)

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "demo_data" / "binary_search_variants"
NATIVE_PATH = BASE_DIR / "demo_data" / "square_1_aci.VCF"
SYNTHETIC_PATH = BASE_DIR / "demo_data" / "synthethic_vcf" / "square_1_aci.VCF"

HEADER_SIZE = 472  # 1 + 20 + 3 + 8 + 8 + 14 + 418 = 472
PRE_MP_SIZE = 54   # 1 + 20 + 3 + 8 + 8 + 14 = 54


def encode_layer_block_minimal(layer: VcfLayer, block_size: int, color_at_12: bool = True) -> bytes:
    block = bytearray(block_size)
    struct.pack_into('<I', block, 0, 1 if layer._is_output else 0)
    struct.pack_into('<d', block, 4, float(layer._speed))
    if color_at_12:
        color_bgr = (layer._color[0] << 16) | (layer._color[1] << 8) | layer._color[2]
        struct.pack_into('<I', block, 12, color_bgr)
    cutter_idx = CUTTER_NAME_TO_INDEX.get(layer._cutter_type, 0)
    struct.pack_into('<i', block, 32, cutter_idx)
    return bytes(block)


def build_minimal_header(version="1.0.013", include_mp=False):
    data = bytearray()
    data += VCF_PREFIX
    data += HEADER_MAGIC if version == "1.0.013" else HEADER_MAGIC_012
    data += VCF_POST_MAGIC
    data += struct.pack('<d', STOCK_WIDTH)
    data += struct.pack('<d', STOCK_HEIGHT)
    data += POST_STOCK_HEADER
    if include_mp:
        data += MACHINE_PROFILE
    return bytes(data)


def build_variant_A(layers, dxf_path=None, version="1.0.013"):
    """Minimal: active-first, no MP, no trailer, no linked-list, color@12 only."""
    data = bytearray(build_minimal_header(version, include_mp=False))
    for layer in layers:
        data += encode_layer_block_minimal(layer, LAYER_BLOCK_SIZE)
    for layer_idx, layer in enumerate(layers):
        for path in layer._paths:
            data += VcfWriter.encode_geometry_element(path, layer, layer_idx)
    return bytes(data)


def build_variant_B(layers, dxf_path=None, version="1.0.013"):
    """Variant A + empty blocks (empty-first), block index @10."""
    data = bytearray(build_minimal_header(version, include_mp=False))
    n_layers = len(layers)
    for i in range(256):
        block = bytearray(LAYER_BLOCK_SIZE)
        struct.pack_into('<H', block, 10, i)
        data += bytes(block)
    for layer in layers:
        data += encode_layer_block_minimal(layer, LAYER_BLOCK_SIZE)
    for layer_idx, layer in enumerate(layers):
        for path in layer._paths:
            data += VcfWriter.encode_geometry_element(path, layer, layer_idx)
    return bytes(data)


def build_variant_C(layers, dxf_path=None, version="1.0.013"):
    """Variant B + linked-list."""
    data = bytearray(build_minimal_header(version, include_mp=False))
    n_layers = len(layers)
    total_blocks = 256 + n_layers
    blocks_data = bytearray()
    for i in range(256):
        block = bytearray(LAYER_BLOCK_SIZE)
        struct.pack_into('<H', block, 10, i)
        blocks_data += bytes(block)
    for layer in layers:
        blocks_data += encode_layer_block_minimal(layer, LAYER_BLOCK_SIZE)
    for i in range(total_blocks):
        off = i * LAYER_BLOCK_SIZE
        if i < total_blocks - 1:
            nxt = layers[0] if (i + 1) >= 256 else None
            c = (nxt._color[0] << 16) | (nxt._color[1] << 8) | nxt._color[2] if nxt else 0
            struct.pack_into('<I', blocks_data, off + LAYER_BLOCK_SIZE - 8, 1)
            struct.pack_into('<I', blocks_data, off + LAYER_BLOCK_SIZE - 4, c)
    data += bytes(blocks_data)
    for layer_idx, layer in enumerate(layers):
        for path in layer._paths:
            data += VcfWriter.encode_geometry_element(path, layer, layer_idx)
    return bytes(data)


def build_variant_D(layers, dxf_path=None, version="1.0.013"):
    """Variant C + MACHINE_PROFILE."""
    data = bytearray(build_minimal_header(version, include_mp=True))
    n_layers = len(layers)
    total_blocks = 256 + n_layers
    blocks_data = bytearray()
    for i in range(256):
        block = bytearray(LAYER_BLOCK_SIZE)
        struct.pack_into('<H', block, 10, i)
        blocks_data += bytes(block)
    for layer in layers:
        blocks_data += encode_layer_block_minimal(layer, LAYER_BLOCK_SIZE)
    for i in range(total_blocks):
        off = i * LAYER_BLOCK_SIZE
        if i < total_blocks - 1:
            nxt = layers[0] if (i + 1) >= 256 else None
            c = (nxt._color[0] << 16) | (nxt._color[1] << 8) | nxt._color[2] if nxt else 0
            struct.pack_into('<I', blocks_data, off + LAYER_BLOCK_SIZE - 8, 1)
            struct.pack_into('<I', blocks_data, off + LAYER_BLOCK_SIZE - 4, c)
    data += bytes(blocks_data)
    for layer_idx, layer in enumerate(layers):
        for path in layer._paths:
            data += VcfWriter.encode_geometry_element(path, layer, layer_idx)
    return bytes(data)


def build_variant_E(layers, dxf_path=None, version="1.0.013"):
    """Variant D + trailer."""
    data = bytearray(build_minimal_header(version, include_mp=True))
    n_layers = len(layers)
    total_blocks = 256 + n_layers
    blocks_data = bytearray()
    for i in range(256):
        block = bytearray(LAYER_BLOCK_SIZE)
        struct.pack_into('<H', block, 10, i)
        blocks_data += bytes(block)
    for layer in layers:
        blocks_data += encode_layer_block_minimal(layer, LAYER_BLOCK_SIZE)
    for i in range(total_blocks):
        off = i * LAYER_BLOCK_SIZE
        if i < total_blocks - 1:
            nxt = layers[0] if (i + 1) >= 256 else None
            c = (nxt._color[0] << 16) | (nxt._color[1] << 8) | nxt._color[2] if nxt else 0
            struct.pack_into('<I', blocks_data, off + LAYER_BLOCK_SIZE - 8, 1)
            struct.pack_into('<I', blocks_data, off + LAYER_BLOCK_SIZE - 4, c)
    data += bytes(blocks_data)
    for layer_idx, layer in enumerate(layers):
        for path in layer._paths:
            data += VcfWriter.encode_geometry_element(path, layer, layer_idx)
    # Trailer (minimal — no DXF path)
    trailer = bytearray(TRAILER_PREFIX)
    data += bytes(trailer)
    return bytes(data)


def build_variant_F(layers, dxf_path=None, version="1.0.013"):
    """Full current writer."""
    writer = VcfWriter(layers=layers, version=version, dxf_source_path=dxf_path)
    return writer.header() + writer.body() + writer.trailer()


def build_variant_G():
    """F + native empty block init data patched in."""
    if not NATIVE_PATH.exists() or not SYNTHETIC_PATH.exists():
        print("  SKIP: native or synthetic not found")
        return None
    native = NATIVE_PATH.read_bytes()
    synthetic = SYNTHETIC_PATH.read_bytes()
    
    # Patch empty block init data from native into synthetic
    # Empty blocks are [HEADER_SIZE : HEADER_SIZE + 256*610]
    result = bytearray(synthetic)
    native_blk_start = HEADER_SIZE
    native_blk_end = HEADER_SIZE + 256 * LAYER_BLOCK_SIZE
    result[native_blk_start:native_blk_end] = native[native_blk_start:native_blk_end]
    return bytes(result)


def build_variant_H():
    """Current writer but WITHOUT trailer."""
    native = NATIVE_PATH.read_bytes()
    synthetic = SYNTHETIC_PATH.read_bytes()
    
    # Find where geometry ends = where trailer starts in synthetic
    # Trailer starts where the last byte of geometry data ends
    # We know synthetic = header + blocks + geometry + trailer
    # and native = header + blocks + geometry + trailer
    # Remove trailer from synthetic
    
    # The trailer starts after the last GEOMETRY_SIG data
    # Alternative: use the current writer but skip trailer
    # Actually, let's just read the current VCF and truncate at body end:
    # Search for last GEOMETRY_SIG and truncate there + element size
    from vcf_parser._reader import GEOMETRY_SIG as GSIG
    last_pos = synthetic.rfind(GSIG)
    if last_pos == -1:
        return None
    
    # Parse the element at last_pos to find its end
    p = last_pos + 45
    pt_count = struct.unpack_from('<I', synthetic, p + 4)[0]
    element_size = 45 + pt_count * 74
    body_end = last_pos + element_size
    return synthetic[:body_end]


def build_variant_I():
    """Current writer but WITHOUT MACHINE_PROFILE."""
    synthetic = SYNTHETIC_PATH.read_bytes()
    # Remove MP: header without MP is 54 bytes (PRE_MP_SIZE)
    # After removing MP, blocks+geometry+trailer follow immediately
    # Header with MP: 472 bytes (PRE_MP_SIZE + MP_SIZE)
    # Header without MP: 54 bytes (PRE_MP_SIZE)
    # MP size = 418 bytes
    # Remove MP by: keep pre-MP header, skip MP, keep rest
    
    pre_mp = synthetic[:PRE_MP_SIZE]  # 54 bytes
    post_mp = synthetic[HEADER_SIZE:]  # blocks + geometry + trailer
    return pre_mp + post_mp


def build_variant_J():
    """Current writer but active-first (no empty blocks)."""
    synthetic = SYNTHETIC_PATH.read_bytes()
    # Keep header (472 bytes), remove all 256 empty blocks (256*610),
    # keep active blocks + geometry + trailer
    active_start = HEADER_SIZE + 256 * LAYER_BLOCK_SIZE
    active_data_start = active_start  # first active block
    # We need at least the first active layer block
    # For square_1_aci with 1 active layer: 1 block = 610 bytes
    header = synthetic[:HEADER_SIZE]
    rest = synthetic[HEADER_SIZE:]  # All blocks + geometry + trailer
    # Find where active block is (256 blocks in)
    active_block = rest[256 * LAYER_BLOCK_SIZE:]
    return header + active_block


# ── Main ──

def get_demo_layers():
    """Recreate layers matching square_1_aci."""
    path = [(100.0, 100.0), (500.0, 100.0), (500.0, 500.0), (100.0, 500.0), (100.0, 100.0)]
    layer = VcfLayer(
        paths=[path],
        speed=800.0,
        cutter_type="Vibrate cutter",
        h1=2.0,
        h2=12.0,
        color=[0, 0, 0],
        direction="N/A",
        is_output=True,
        feed_count=1,
    )
    return [layer]


def hex_diff(file1_bytes, file2_bytes, label1="file1", label2="file2", max_regions=20):
    """Simple hex diff, returns list of (offset, length, bytes1, bytes2)."""
    regions = []
    i = 0
    while i < min(len(file1_bytes), len(file2_bytes)):
        if file1_bytes[i] != file2_bytes[i]:
            start = i
            while i < min(len(file1_bytes), len(file2_bytes)) and file1_bytes[i] != file2_bytes[i]:
                i += 1
            regions.append((start, i - start,
                          file1_bytes[start:i], file2_bytes[start:i]))
        else:
            i += 1
    return regions


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    layers = get_demo_layers()

    # ── Generate A-F variants ──
    builders = [
        ("A_minimal_active_first", lambda: build_variant_A(layers)),
        ("B_empty_blocks", lambda: build_variant_B(layers)),
        ("C_linked_list", lambda: build_variant_C(layers)),
        ("D_machine_profile", lambda: build_variant_D(layers)),
        ("E_trailer", lambda: build_variant_E(layers)),
        ("F_full_current", lambda: build_variant_F(layers)),
    ]

    print("=== A-F variants (fresh generation) ===")
    variants = {}
    for name, builder in builders:
        data = builder()
        path = OUTPUT_DIR / f"var_{name}.VCF"
        path.write_bytes(data)
        variants[name] = data
        print(f"  {path.name:40s} {len(data):>7d} B")

    # ── Generate G-J patch variants ──
    print("\n=== G-J variants (patched from synthetic) ===")
    patch_builders = [
        ("G_native_empty_init", build_variant_G),
        ("H_no_trailer", build_variant_H),
        ("I_no_mp", build_variant_I),
        ("J_active_first", build_variant_J),
    ]
    for name, builder in patch_builders:
        data = builder()
        if data is None:
            print(f"  var_{name}.VCF      SKIP (missing source)")
            continue
        path = OUTPUT_DIR / f"var_{name}.VCF"
        path.write_bytes(data)
        variants[name] = data
        print(f"  {path.name:40s} {len(data):>7d} B")

    # ── Size comparison ──
    native = NATIVE_PATH.read_bytes()
    syn = SYNTHETIC_PATH.read_bytes()
    print(f"\n=== Size comparison vs native ({len(native)} B) ===")
    print(f"  {'CURRENT synthetic':40s} {len(syn):>7d} B ({len(syn)-len(native):+d})")
    for name, data in variants.items():
        print(f"  var_{name:40s} {len(data):>7d} B ({len(data)-len(native):+d})")

    # ── Hex diff summaries for key variants ──
    print(f"\n=== Hex diff summaries (first 10 regions) ===")
    for key in ["F_full_current", "G_native_empty_init", "H_no_trailer"]:
        if key not in variants:
            continue
        data = variants[key]
        regions = hex_diff(native, data, "native", key)
        total_diff_bytes = sum(r[1] for r in regions)
        print(f"\n  {key}: {len(regions)} regions, {total_diff_bytes} total diff bytes")
        for idx, (off, length, b1, b2) in enumerate(regions[:10]):
            # Determine which section
            if off < HEADER_SIZE:
                section = "HEADER"
            elif off < HEADER_SIZE + 256 * LAYER_BLOCK_SIZE:
                section = "EMPTY_BLOCKS"
            elif off < HEADER_SIZE + 257 * LAYER_BLOCK_SIZE:
                section = "ACTIVE_BLOCK"
            else:
                section = "GEOMETRY/TRAILER"
            print(f"    [{idx+1}] @{off:#x} len={length} ({section})")
            if length <= 16:
                print(f"      native:    {b1.hex()}")
                print(f"      synthetic: {b2.hex()}")


if __name__ == "__main__":
    main()
