import sys
from pathlib import Path

def hex_diff_to_md(file1: str, file2: str, context_bytes: int = 32, output_file: str = "hex_diff_report.md"):
    """Porovná dva binární soubory a vytvoří jeden MD report s odlišnými bloky."""
    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        data1 = f1.read()
        data2 = f2.read()

    max_len = max(len(data1), len(data2))
    diff_regions = []
    i = 0
    while i < max_len:
        b1 = data1[i] if i < len(data1) else None
        b2 = data2[i] if i < len(data2) else None
        if b1 != b2:
            start = max(0, i - context_bytes)
            end = i
            while end < max_len and ((data1[end] if end < len(data1) else None) != (data2[end] if end < len(data2) else None)):
                end += 1
            end = min(max_len, end + context_bytes)
            block1 = data1[start:end] if start < len(data1) else b''
            block2 = data2[start:end] if start < len(data2) else b''
            diff_regions.append({
                'offset_start': i,
                'offset_end': end,
                'hex1': block1.hex(' '),
                'hex2': block2.hex(' '),
                'ascii1': ''.join(chr(b) if 32 <= b < 127 else '.' for b in block1),
                'ascii2': ''.join(chr(b) if 32 <= b < 127 else '.' for b in block2)
            })
            i = end
        else:
            i += 1

    # Sestavení Markdown reportu
    md_lines = []
    md_lines.append(f"# Hex Diff Report\n")
    md_lines.append(f"**Soubor 1:** `{file1}`  \n")
    md_lines.append(f"**Soubor 2:** `{file2}`  \n")
    md_lines.append(f"**Velikost 1:** {len(data1)} bytů  \n")
    md_lines.append(f"**Velikost 2:** {len(data2)} bytů  \n")
    md_lines.append(f"**Počet rozdílných regionů:** {len(diff_regions)}\n")
    md_lines.append("\n---\n\n")

    for idx, reg in enumerate(diff_regions, 1):
        md_lines.append(f"## Region {idx}\n")
        md_lines.append(f"- **Offset:** `0x{reg['offset_start']:08X}` – `0x{reg['offset_end']:08X}` (délka {reg['offset_end'] - reg['offset_start']} bytů)\n")
        md_lines.append("\n### Hexdump – Soubor 1\n")
        md_lines.append("```\n")
        md_lines.append(f"{reg['hex1']}\n")
        md_lines.append("```\n")
        md_lines.append("\n### Hexdump – Soubor 2\n")
        md_lines.append("```\n")
        md_lines.append(f"{reg['hex2']}\n")
        md_lines.append("```\n")
        md_lines.append("\n### ASCII reprezentace – Soubor 1\n")
        md_lines.append("```\n")
        md_lines.append(f"{reg['ascii1']}\n")
        md_lines.append("```\n")
        md_lines.append("\n### ASCII reprezentace – Soubor 2\n")
        md_lines.append("```\n")
        md_lines.append(f"{reg['ascii2']}\n")
        md_lines.append("```\n")
        md_lines.append("---\n\n")

    # Uložení pouze jednoho MD souboru
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(md_lines)
    print(f"Diff report saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python hex_diff.py <file1> <file2>")
        sys.exit(1)
    hex_diff_to_md(sys.argv[1], sys.argv[2])