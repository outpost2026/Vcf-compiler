"""Diagnose multi-element VCF files — analyze element structure, ec@92, offset606.

Scans VCF files from training DB or custom path. Reports:
- Format version (1.0.012 / 1.0.013 / other)
- Element count via GEOMETRY_SIG scanning + offset606 cross-check (1.0.013 only)
- Layer block metadata for 1.0.013 format
- Footer presence anomalies

Note: 1.0.012 files have different structure (no machine profile, fewer blocks).
Full layer block analysis (ec@92, offset606) only applies to 1.0.013.

Usage:
    python dev_scripts/diagnose_multi_element.py
    python dev_scripts/diagnose_multi_element.py --path "C:/path/to/vcf/files"
    python dev_scripts/diagnose_multi_element.py --file "path/to/single.VCF" --verbose
"""
import struct
import sys
import argparse
from pathlib import Path

GEOMETRY_SIG = bytes([0x01, 0x00, 0x01, 0x00, 0x00, 0xff, 0xff, 0xff])
LAYER_BLOCK_SIZE = 610
EMPTY_BLOCK_COUNT = 256
HEADER_SIZE_013 = 472  # 1B prefix + 20B magic + 3B post + 16B stock + 14B post_stock + 418B profile

def find_all_geom_sigs(data: bytes) -> list[int]:
    offsets = []
    start = 0
    while True:
        pos = data.find(GEOMETRY_SIG, start)
        if pos == -1:
            break
        offsets.append(pos)
        start = pos + 1
    return offsets

def detect_format(data: bytes) -> dict:
    magic_013 = b'RDVCUTFILEVER1.0.013'
    magic_012 = b'RDVCUTFILEVER1.0.012'
    info = {'version': 'unknown', 'has_blocks': False}
    
    if len(data) > 25:
        m = data[1:1+len(magic_013)]
        if m == magic_013:
            info['version'] = '1.0.013'
        elif m == magic_012:
            info['version'] = '1.0.012'
    
    return info

def get_013_block_fields(data: bytes, blk_start: int) -> dict | None:
    """Read 610B layer block fields for 1.0.013 format."""
    blk = data[blk_start:blk_start+LAYER_BLOCK_SIZE]
    if len(blk) < LAYER_BLOCK_SIZE:
        return None
    speed = struct.unpack_from('<d', blk, 4)[0]
    is_active = 0 < speed < 2000
    return {
        'start': blk_start,
        'block_num': struct.unpack_from('<H', blk, 10)[0] & 0xFF,
        'ec92': blk[92],
        'offset606': struct.unpack_from('<I', blk, 606)[0],
        'offset602': struct.unpack_from('<I', blk, 602)[0],
        'color': struct.unpack_from('<I', blk, 12)[0],
        'speed': speed,
        'is_active': is_active,
    }

def find_last_active_block_013(data: bytes) -> dict | None:
    """For 1.0.013: find last active 610B block before first GEOMETRY_SIG.
    
    Tries different header sizes (simulating production file variants),
    checks if block area aligns to 610B boundaries, then scans backward
    from the last block for one with valid speed.
    """
    first_sig = data.find(GEOMETRY_SIG)
    if first_sig < 0:
        return None
    
    # Try plausible header sizes (472 is our writer, others are production variants)
    for hs in [472, 469, 466, 463, 460, 448, 418, 414, 412, 410, 408, 400,
               256, 128, 64, 48, 40]:
        block_bytes = first_sig - hs
        if block_bytes < LAYER_BLOCK_SIZE:
            continue
        if block_bytes % LAYER_BLOCK_SIZE != 0:
            continue
        total_blocks = block_bytes // LAYER_BLOCK_SIZE
        # Scan last 20 blocks for active one
        start_idx = max(0, total_blocks - 20)
        for idx in range(total_blocks - 1, start_idx - 1, -1):
            blk_start = hs + idx * LAYER_BLOCK_SIZE
            if blk_start + LAYER_BLOCK_SIZE > len(data):
                continue
            speed = struct.unpack_from('<d', data, blk_start + 4)[0]
            if 0 < speed < 2000:
                return get_013_block_fields(data, blk_start)
    return None

def parse_elements(data: bytes, sig_offsets: list[int]) -> list[dict]:
    elements = []
    for i, pos in enumerate(sig_offsets):
        next_pos = sig_offsets[i + 1] if i + 1 < len(sig_offsets) else len(data)
        raw = data[pos:next_pos]
        p = 45
        type_id = struct.unpack_from('<I', raw, p)[0]
        pt_count = struct.unpack_from('<I', raw, p + 4)[0]
        subtype = struct.unpack_from('<I', raw, p + 8)[0]
        geom_color = struct.unpack_from('<I', raw, 8)[0]
        
        expected_196 = 45 + pt_count * 74 + 196
        actual_size = len(raw)
        footer_start = 45 + pt_count * 74
        footer = raw[footer_start:footer_start+196]
        
        elements.append({
            'idx': i, 'pos': pos, 'color': hex(geom_color),
            'type_id': type_id, 'pt_count': pt_count, 'subtype': subtype,
            'expected_196': expected_196, 'actual_size': actual_size,
            'has_footer': actual_size >= expected_196 - 10,
            'footer_len': len(footer),
        })
    return elements

def analyze_vcf(path: Path) -> dict:
    data = path.read_bytes()
    sigs = find_all_geom_sigs(data)
    elements = parse_elements(data, sigs)
    fmt = detect_format(data)
    
    last_block = None
    if fmt['version'] == '1.0.013':
        last_block = find_last_active_block_013(data)
    
    trailer_5zeros = len(data) >= 5 and data[-5:] == b'\x00' * 5
    return {
        'path': path, 'size': len(data), 'format': fmt['version'],
        'sig_count': len(sigs), 'elements': elements,
        'last_block': last_block, 'trailer_5zeros': trailer_5zeros,
    }

def scan_directory(directory: Path) -> list[Path]:
    return sorted(directory.glob('*.VCF'))

def print_summary_table(results: list[dict]):
    print(f"\n{'='*95}")
    print(f"{'SUMMARY TABLE':^95}")
    print(f"{'='*95}")
    hdr = f"{'File':<45} {'Size':>8} {'Fmt':>8} {'Elem':>6} {'ec@92':>6} {'off606':>8} {'Match':>7} {'Trl':>5}"
    print(hdr)
    print(f"{'-'*45} {'-'*8} {'-'*8} {'-'*6} {'-'*6} {'-'*8} {'-'*7} {'-'*5}")
    
    ok = mismatch = no_blk = not_applicable = 0
    for r in results:
        name = r['path'].name[:44]
        fmt = r['format']
        n_sigs = r['sig_count']
        lb = r['last_block']
        
        if fmt == '1.0.013' and lb:
            ec = lb['ec92']
            off = lb['offset606']
            is_match = (off == n_sigs)
            if is_match:
                ok += 1
            else:
                mismatch += 1
            ms = 'OK' if is_match else 'MIS'
            ec_s = str(ec)
            off_s = str(off)
        elif fmt == '1.0.013':
            ec_s = '?'
            off_s = '?'
            ms = 'N/A'
            no_blk += 1
        else:
            ec_s = '-'
            off_s = '-'
            ms = 'N/A'
            not_applicable += 1
        
        trl = 'OK' if r['trailer_5zeros'] else 'BAD'
        print(f"{name:<45} {r['size']:>8} {fmt:>8} {n_sigs:>6} {ec_s:>6} {off_s:>8} {ms:>7} {trl:>5}")
    
    print(f"{'-'*95}")
    print(f"Total: {len(results)} | offset606==sigs: {ok} | mismatch: {mismatch} | no_block: {no_blk} | N/A(012): {not_applicable}")

def print_verbose(result: dict):
    p = result['path']
    print(f"\n{'='*80}")
    print(f"  {p.name}  [{result['format']}]  ({result['size']}B)")
    print(f"  Elements: {result['sig_count']}  |  Trailer 5x00: {result['trailer_5zeros']}")
    
    lb = result['last_block']
    if lb:
        print(f"  Last active block @{lb['start']}: blk_num={lb['block_num']}, "
              f"speed={lb['speed']}, color=#{lb['color']:06x}")
        print(f"    ec@92={lb['ec92']}, offset602={lb['offset602']}, offset606={lb['offset606']}")
        m = "MATCH" if lb['offset606'] == result['sig_count'] else "MISMATCH"
        print(f"    offset606={lb['offset606']} vs GEOMETRY_SIGs={result['sig_count']} -> {m}")
    elif result['format'] == '1.0.013':
        print(f"  (no active layer block found)")
    else:
        print(f"  (1.0.012 format — different structure, no block analysis)")
    
    for el in result['elements'][:3]:
        print(f"  Elem {el['idx']} @{el['pos']}: color={el['color']}, "
              f"segments={el['pt_count']}, subtype={el['subtype']}, "
              f"footer_196={el['has_footer']} ({el['actual_size']}B)")
    if len(result['elements']) > 3:
        print(f"  ... and {len(result['elements']) - 3} more")

def main():
    ap = argparse.ArgumentParser(description='Diagnose multi-element VCF files')
    ap.add_argument('--path', default=r'C:\Users\PC\Documents\Repozitar_Dev\_github\VCF_files_moodpasta')
    ap.add_argument('--file', help='Single VCF file')
    ap.add_argument('--verbose', '-v', action='store_true')
    args = ap.parse_args()
    
    if args.file:
        files = [Path(args.file)]
    else:
        scan_path = Path(args.path)
        if not scan_path.exists():
            print(f"ERROR: Path not found: {scan_path}")
            sys.exit(1)
        files = scan_directory(scan_path)
    
    if not files:
        print("No .VCF files found.")
        return
    
    print(f"Scanning {len(files)} VCF files...")
    results = []
    for f in files:
        try:
            r = analyze_vcf(f)
            results.append(r)
            if args.verbose or args.file:
                print_verbose(r)
        except Exception as e:
            print(f"ERROR: {f.name}: {e}")
    
    print_summary_table(results)

if __name__ == '__main__':
    main()
