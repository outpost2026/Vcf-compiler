import re

for fname in [
    "hex_diff_line.md",
    "hex_diff_square.md",
    "hex_diff_circle.md",
    "hex_diff_curve.md",
]:
    with open(fname, encoding="utf-8") as f:
        content = f.read()

    regions = re.findall(r"## Region \d+", content)
    sizes = re.findall(r"Velikost \d+: (\d+)", content)
    rc = re.findall(r"Po\u010det rozd\xedln\u00fdch region\u016f: (\d+)", content)
    offsets = re.findall(r"Offset: `(0x[0-9A-Fa-f]+)`", content)

    zeros2 = 0
    for m in re.findall(
        r"### Hexdump \u2013 Soubor 2\n```\n(.+?)\n```", content
    ):
        if all(b == "00" for b in m.strip().split()):
            zeros2 += 1

    print(f"{fname}:")
    print(f'  Regions: {rc[0] if rc else "?"} | Sizes: {" vs ".join(sizes)} B')
    print(f"  Synth-all-zeros regions: {zeros2}/{len(regions)}")
    if offsets:
        first = offsets[0]
        last_region = regions[-1]
        last_offset = offsets[-1] if len(offsets) >= len(regions) else "?"
        print(f"  First diff at: {first}, last region at: {last_offset}")
    print()
