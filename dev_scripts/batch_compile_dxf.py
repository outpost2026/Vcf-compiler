"""
Batch compile all DXF files in demo_data/ to synthetic VCFs using the fixed writer.
"""

import sys, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vcf_parser._dxf_adapter import compile_dxf

BASE = Path(__file__).resolve().parent.parent
DEMO = BASE / "demo_data"
OUT  = DEMO / "synthethic_vcf"
CONFIG = BASE / "vcf_compiler_map_config.json"

dxf_files = sorted(DEMO.glob("*.dxf"))

if not dxf_files:
    print("No .dxf files found in demo_data/")
    sys.exit(1)

print(f"Found {len(dxf_files)} DXF files\n")

for dxf in dxf_files:
    out_name = dxf.stem + ".VCF"
    out_path = OUT / out_name
    print(f"  {dxf.name}  ->  {out_path.name} ...", end=" ")
    try:
        compile_dxf(str(dxf), str(out_path), config_path=str(CONFIG))
        size = out_path.stat().st_size
        print(f"OK ({size:,} B)")
    except Exception as e:
        print(f"FAIL: {e}")

print("\nDone.")
