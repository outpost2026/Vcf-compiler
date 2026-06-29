"""Diagnose why VCutWorks shows 1 element for multi-element line files."""
import struct
import sys
from pathlib import Path

GEOMETRY_SIG = b'\x53\x48\x58\x43\x55\x54\x00\x00'
BASE = Path(__file__).resolve().parent.parent
DEMO = BASE / 'demo_data'

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

def parse_elements(data: bytes, sig_offsets: list[int]) -> list[dict]:
    elements = []
    for i, pos in enumerate(sig_offsets):
        # find next sig to determine element boundary
        next_pos = sig_offsets[i + 1] if i + 1 < len(sig_offsets) else len(data)
        raw = data[pos:next_pos]
        
        geom_color = struct.unpack_from('<I', raw, 8)[0]
        
        p = 45  # type_offset
        type_id = struct.unpack_from('<I', raw, p)[0]
        pt_count = struct.unpack_from('<I', raw, p + 4)[0]
        subtype = struct.unpack_from('<I', raw, p + 8)[0]
        
        vertices = []
        for seg_i in range(pt_count):
            seg_start = p + seg_i * 74
            x1 = struct.unpack('<d', raw[seg_start+14:seg_start+22])[0]
            y1 = struct.unpack('<d', raw[seg_start+22:seg_start+30])[0]
            x2 = struct.unpack('<d', raw[seg_start+30:seg_start+38])[0]
            y2 = struct.unpack('<d', raw[seg_start+38:seg_start+46])[0]
            if seg_i == 0:
                vertices.append((x1, y1))
            vertices.append((x2, y2))
        
        # Determine element size: look for TRAILER (5 zeros) or end of file
        # The footer is 196 bytes, so element = 45 + pt_count*74 + 196
        expected_elem_size = 45 + pt_count * 74 + 196
        actual_elem_size = len(raw)
        
        # Check footer content
        footer_start = 45 + pt_count * 74
        footer = raw[footer_start:footer_start+196]
        
        elements.append({
            'idx': i,
            'pos': pos,
            'geom_color': hex(geom_color),
            'type_id': type_id,
            'pt_count': pt_count,
            'subtype': subtype,
            'vertices': vertices,
            'expected_elem_size': expected_elem_size,
            'actual_elem_size': actual_elem_size,
            'footer_first_4': footer[:4].hex(),
            'footer_last_4': footer[-4:].hex() if len(footer) >= 4 else 'N/A',
            'footer_len': len(footer),
        })
    return elements

def analyze_vcf(path: Path, label: str):
    data = path.read_bytes()
    sigs = find_all_geom_sigs(data)
    print(f"\n{'='*80}")
    print(f"{label}: {path.name}")
    print(f"File size: {len(data)} bytes")
    print(f"GEOMETRY_SIG count: {len(sigs)}")
    print(f"Last 10 bytes: {data[-10:].hex()}")
    print(f"Total elements detected: {len(sigs)}")
    
    elements = parse_elements(data, sigs)
    for el in elements:
        print(f"\n  Element {el['idx']} @ offset {el['pos']}:")
        print(f"    color={el['geom_color']}, type={el['type_id']}, segments={el['pt_count']}, subtype={el['subtype']}")
        print(f"    vertices (first,last): {el['vertices'][0]} -> {el['vertices'][-1]}")
        print(f"    expected_size={el['expected_elem_size']}, actual_raw_size={el['actual_elem_size']}")
        print(f"    footer: {el['footer_first_4']} ... {el['footer_last_4']} (len={el['footer_len']})")
    
    return data, sigs, elements

# Compare native vs synthetic 2-element line
native_2 = DEMO / 'native_vcf' / 'single_line_2000_elements_2.VCF'
synth_2 = DEMO / 'synthethic_vcf' / 'single_line_2000_elements_2_inversion.VCF'

n_data, n_sigs, n_elems = analyze_vcf(native_2, 'NATIVE')
s_data, s_sigs, s_elems = analyze_vcf(synth_2, 'SYNTH')

print(f"\n{'='*80}")
print("COMPARISON SUMMARY:")
print(f"  Element counts: native={len(n_sigs)}, synth={len(s_sigs)}")
if len(n_sigs) == len(s_sigs):
    for i in range(len(n_sigs)):
        ne = n_elems[i]
        se = s_elems[i]
        print(f"\n  Element {i}:")
        print(f"    color: native={ne['geom_color']}, synth={se['geom_color']}, match={ne['geom_color']==se['geom_color']}")
        print(f"    segments: native={ne['pt_count']}, synth={se['pt_count']}, match={ne['pt_count']==se['pt_count']}")
        print(f"    expected_size: native={ne['expected_elem_size']}, synth={se['expected_elem_size']}")
        
        # Check for any difference in binary within geometry section only (skip footer)
        n_geom_end = ne['pos'] + 45 + ne['pt_count'] * 74
        s_geom_end = se['pos'] + 45 + se['pt_count'] * 74
        n_geom = n_data[ne['pos']:n_geom_end]
        s_geom = s_data[se['pos']:s_geom_end]
        
        # But exclude color byte (offset 8-12)
        print(f"    Geometry section binary match (excluding color@8-12): ", end='')
        n_geom_masked = bytearray(n_geom)
        s_geom_masked = bytearray(s_geom)
        # Zero out color bytes for comparison
        n_geom_masked[8:12] = b'\x00\x00\x00\x00'
        s_geom_masked[8:12] = b'\x00\x00\x00\x00'
        if n_geom_masked == s_geom_masked:
            print("YES")
        else:
            print("DIFFERS!")
            diff_positions = []
            for j in range(min(len(n_geom_masked), len(s_geom_masked))):
                if n_geom_masked[j] != s_geom_masked[j]:
                    diff_positions.append((j, n_geom[j], s_geom[j]))
            for pos, nb, sb in diff_positions[:20]:
                print(f"      offset +{pos}: native={nb:02x}, synth={sb:02x}")

# Also check single-element files for comparison
native_1 = DEMO / 'native_vcf' / 'single_line_2000.VCF'
synth_1 = DEMO / 'synthethic_vcf' / 'single_line_2000_inversion.VCF'

print(f"\n{'='*80}")
print("SINGLE ELEMENT FILES (for comparison):")
n1_data, n1_sigs, n1_elems = analyze_vcf(native_1, 'NATIVE (1-elem)')
s1_data, s1_sigs, s1_elems = analyze_vcf(synth_1, 'SYNTH (1-elem)')

# Check footer differences between 1-elem and 2-elem
print(f"\n{'='*80}")
print("FOOTER COMPARISON (native 1-elem vs 2-elem):")
f1 = n1_data[n1_sigs[0] + 45 + n1_elems[0]['pt_count'] * 74 : n1_sigs[0] + 45 + n1_elems[0]['pt_count'] * 74 + 196]
f2a = n_data[n_sigs[0] + 45 + n_elems[0]['pt_count'] * 74 : n_sigs[0] + 45 + n_elems[0]['pt_count'] * 74 + 196]
f2b = n_data[n_sigs[1] + 45 + n_elems[1]['pt_count'] * 74 : n_sigs[1] + 45 + n_elems[1]['pt_count'] * 74 + 196]
print(f"1-elem footer == 2-elem element#0 footer: {f1 == f2a}")
print(f"1-elem footer == 2-elem element#1 footer: {f1 == f2b}")
print(f"2-elem element#0 footer == element#1 footer: {f2a == f2b}")

# Check TRAILER after native 2-elem
after_last_elem = n_data[n_sigs[1] + 45 + n_elems[1]['pt_count'] * 74 + 196:]
print(f"\nTrailer after last element in native 2-elem: {after_last_elem[:20].hex()} (len={len(after_last_elem)})")

# Check TRAILER after synth 2-elem
after_last_elem_s = s_data[s_sigs[1] + 45 + s_elems[1]['pt_count'] * 74 + 196:]
print(f"Trailer after last element in synth 2-elem: {after_last_elem_s[:20].hex()} (len={len(after_last_elem_s)})")
