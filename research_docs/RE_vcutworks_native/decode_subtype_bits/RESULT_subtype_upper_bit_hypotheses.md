# Subtype Upper-Bit Decoding — Hypotheses Report

**Generated:** by decode_subtype_bits.py analyzing 11 VCF files

---

## 1. Summary

- Total files analyzed: 11
- Unique upper 16-bit values: 1 (0x0000)

## 2. Per-File Upper Bits

| File | Upper Bits | Low 16 | Elements | Layers | Speeds | Cutters | Type IDs | Version |
|------|------------|--------|----------|--------|--------|---------|---------|---------|
| empty_canvas.VCF |  |  | 0 | 0 |  |  |  | 1.0.013 |
| line_10_elements.VCF | 0x0000 | 0x0000 | 10 | 1 | 200 | Vibrate cutter | 0 | 1.0.013 |
| single_circle_1500.VCF | 0x0000 | 0x0003 | 1 | 1 | 200 | Vibrate cutter | 1 | 1.0.013 |
| single_circle_1500_elements_2.VCF | 0x0000 | 0x0003 | 2 | 1 | 200 | Vibrate cutter | 1 | 1.0.013 |
| single_curve.VCF | 0x0000 | 0x0003 | 1 | 1 | 200 | Vibrate cutter | 0 | 1.0.013 |
| single_curve_elements_2.VCF | 0x0000 | 0x0003 | 2 | 1 | 200 | Vibrate cutter | 0 | 1.0.013 |
| single_line_2000.VCF | 0x0000 | 0x0000 | 1 | 1 | 200 | Vibrate cutter | 0 | 1.0.013 |
| single_line_2000_elements_2.VCF | 0x0000 | 0x0000 | 2 | 1 | 200 | Vibrate cutter | 0 | 1.0.013 |
| single_square_500.VCF | 0x0000 | 0x0000 | 1 | 1 | 200 | Vibrate cutter | 1 | 1.0.013 |
| single_square_500_elements_2.VCF | 0x0000 | 0x0000 | 2 | 1 | 200 | Vibrate cutter | 1 | 1.0.013 |
| square_5_elements.VCF | 0x0000 | 0x0000 | 5 | 1 | 200 | Vibrate cutter | 1 | 1.0.013 |

## 3. Upper-Bit Clusters

| Upper Bits | Files | Speeds | Cutters | Versions | Type IDs | Hash Unique? |
|------------|-------|--------|---------|----------|----------|--------------|
| 0x0000 | line_10_elements.VCF, single_circle_1500.V, single_circle_1500_e, single_curve.VCF ... (+6) | 200 | Vibrate cutter | 1.0.013 | 0, 1 | YES |

## 4. Bit Field Analysis

| Bit | Files with bit | Speeds (with) | Speeds (without) | Cutters (with) | Cutters (without) |
|-----|---------------|---------------|------------------|----------------|-------------------|

## 5. Hypotheses

### H1: File checksum / hash of first N bytes

- Evidence: Each upper-bit group has 1 unique MD5 in first 64 bytes.
- Verdict: LIKELY — upper bits may be a hash/checksum of header data

### H2: Cutter configuration profile ID

- Evidence: All upper-bit groups map to a single cutter type.
- Verdict: LIKELY — upper bits may encode cutter config

### H3: Speed range encoding

- Evidence: 1/1 groups have speed range ≤ 200 mm/s
- Verdict: LIKELY

### H4: Material / Job ID

- Evidence: 0/11 files contain DXF references in metadata
- Verdict: INCONCLUSIVE — needs cross-reference with operator job names

## 6. Conclusion

Based on statistical analysis:

- Upper bits are CONSTANT across all files → unknown global constant or version marker

### Recommended next step:

1. Group files by upper bits and inspect their header bytes (first 256B) for common patterns

2. Cross-reference with operator job names extracted from file metadata strings

3. Decode as bit field: test if individual bits toggle with specific layer parameters (speed, cutter, h2 sign)
