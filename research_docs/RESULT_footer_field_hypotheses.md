# Footer Field Dissection Report

**Generated:** by dissect_footers.py — 62 VCF files analyzed

---

## 1. Cross-File Summary

- Files with multi-element footers: 51
- Files without footers: 11
- Total elements across all files: 14425
- Footer size distribution: {196: 51, 245: 20, 392: 1, 253: 1}

### Common ASCII strings in footers

| String | Files |
|--------|-------|
| ffff | 4 |
| fffff | 3 |
| 3333 | 3 |
| rxNm | 2 |
| ZB.h | 2 |
| 1w-e | 2 |

### Field hypothesis distribution

| Hypothesis | Count |
|------------|-------|
| unused/padding | 1792 |
| ascii_data | 358 |
| constant_default | 341 |
| constant_float64 | 137 |
| offset_or_address | 64 |
| per_element_float32 | 50 |
| per_element_float64 | 27 |
| per_element_uint32 | 21 |

## 2. Per-File Footer Analysis

### 1ks.VCF
- Elements: 7
- Footers: 6 ([196])
- ASCII: ['r0Bs']

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | YES | no | no | 0..0 | unused/padding |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | no | 16470..4094443606 | per_element_float32 |
| 32 | no | no | YES | no | 0..16574 | per_element_float64 |
| 36 | no | no | no | no | 0..3288334336 | per_element_float32 |
| 40 | no | no | no | no | 0..402653184 | offset_or_address |
| 44 | no | no | no | no | 0..738197504 | per_element_float32 |
| 48 | no | no | no | no | 0..16546 | offset_or_address |
| 52 | YES | YES | no | no | 0..0 | unused/padding |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### 1ks.VCF
- Elements: 7
- Footers: 6 ([196])
- ASCII: ['fffff']

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | no | no | no | 1699388..1699388 | constant_default |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..3771547734 | ascii_data |
| 32 | no | no | YES | YES | 0..2071463625 | ascii_data |
| 36 | no | no | no | no | 0..4098097152 | per_element_float32 |
| 40 | no | no | YES | no | 0..3973056203 | per_element_float64 |
| 44 | no | no | no | no | 0..4160778889 | per_element_float32 |
| 48 | no | no | no | no | 0..2963278932 | per_element_float32 |
| 52 | no | no | no | no | 0..32768 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### 2560x150 s fazetou 45st hl6.VCF
- Elements: 3
- Footers: 2 ([196])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | no | no | no | 1699564..1699564 | constant_default |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | no | no | 2147483648..2147483648 | constant_default |
| 28 | YES | no | no | no | 16470..16470 | constant_default |
| 32 | YES | YES | YES | no | 0..0 | unused/padding |
| 36 | YES | no | no | no | 1236205568..1236205568 | constant_default |
| 40 | YES | no | no | no | 3137360744..3137360744 | constant_default |
| 44 | YES | no | no | no | 32769..32769 | constant_default |
| 48 | YES | YES | no | no | 0..0 | unused/padding |
| 52 | YES | YES | no | no | 0..0 | unused/padding |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### 26ks skladba.VCF
- Elements: 183
- Footers: 182 ([196])
- ASCII: ['rxNm']

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | YES | no | no | 0..0 | unused/padding |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4101259350 | ascii_data |
| 32 | no | no | YES | YES | 0..4118806528 | ascii_data |
| 36 | no | no | no | YES | 0..4160749568 | ascii_data |
| 40 | no | no | YES | YES | 0..4261440914 | ascii_data |
| 44 | no | no | no | YES | 0..4294935083 | ascii_data |
| 48 | no | no | no | YES | 0..4118806528 | ascii_data |
| 52 | no | no | no | no | 0..42941 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### 26ks skladba_nesting.VCF
- Elements: 573
- Footers: 572 ([196, 245])
- ASCII: ['rxNm']

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | no | 0..2147483648 | offset_or_address |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4101259350 | ascii_data |
| 32 | no | no | YES | YES | 0..4118806528 | ascii_data |
| 36 | no | no | no | YES | 0..4160749568 | ascii_data |
| 40 | no | no | YES | YES | 0..4261440914 | ascii_data |
| 44 | no | no | no | YES | 0..4294935083 | ascii_data |
| 48 | no | no | no | YES | 0..4118806528 | ascii_data |
| 52 | no | no | no | no | 0..42941 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### 26ks_skladba.VCF
- Elements: 183
- Footers: 182 ([196])
- ASCII: ['Hf1J', 'Ob6N', 'r8aR', 'rhFR']

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | YES | no | no | 0..0 | unused/padding |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4101259350 | ascii_data |
| 32 | no | no | YES | YES | 0..4118806528 | ascii_data |
| 36 | no | no | no | YES | 0..4248335053 | ascii_data |
| 40 | no | no | YES | YES | 0..4261431253 | ascii_data |
| 44 | no | no | no | YES | 0..4101259426 | ascii_data |
| 48 | no | no | no | YES | 0..4118806528 | ascii_data |
| 52 | no | no | no | no | 0..38032 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### 2790x1200 s fazetou.VCF
- Elements: 2
- Footers: 1 ([196])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | no | no | no | 1702020..1702020 | constant_default |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | YES | no | no | YES | 1146110038..1146110038 | constant_default |
| 32 | YES | no | no | no | 4082107973..4082107973 | constant_default |
| 36 | YES | no | no | no | 447219257..447219257 | constant_default |
| 40 | YES | no | no | no | 2785019023..2785019023 | constant_default |
| 44 | YES | no | no | no | 4554753..4554753 | constant_default |
| 48 | YES | no | no | no | 165675008..165675008 | constant_default |
| 52 | YES | no | no | no | 2661..2661 | constant_default |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### Arbyd_výrobní data_V1 20.5.2025.VCF
- Elements: 418
- Footers: 417 ([196, 245, 392])
- ASCII: ['0000', '9999', 'Arial Black', 'Fs.SHX', 'kozen']

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | YES | 1077543104..1086049754 | ascii_data |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4098113622 | ascii_data |
| 32 | no | no | YES | YES | 0..3561029632 | ascii_data |
| 36 | no | no | no | YES | 0..4287758461 | ascii_data |
| 40 | no | no | YES | YES | 0..4216323760 | ascii_data |
| 44 | no | no | no | no | 0..4098097152 | per_element_float32 |
| 48 | no | no | no | YES | 0..3917070528 | ascii_data |
| 52 | no | no | no | no | 0..47710 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### Big_coffee_dune_2790_600.VCF
- Elements: 14
- Footers: 13 ([196, 245])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | no | 1701832..1702020 | per_element_uint32 |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | no | no | 2147483648..2147483648 | constant_default |
| 28 | YES | no | no | no | 16470..16470 | constant_default |
| 32 | YES | YES | no | no | 0..0 | unused/padding |
| 36 | YES | YES | no | no | 0..0 | unused/padding |
| 40 | YES | YES | no | no | 0..0 | unused/padding |
| 44 | YES | YES | no | no | 0..0 | unused/padding |
| 48 | YES | YES | no | no | 0..0 | unused/padding |
| 52 | YES | YES | no | no | 0..0 | unused/padding |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### FLUENZ BOLD M_Varianta A 2ks skladba.VCF
- Elements: 136
- Footers: 135 ([196, 245])
- ASCII: ['ZB.h']

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | YES | 1701832..1083478896 | ascii_data |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4294918230 | ascii_data |
| 32 | no | no | YES | YES | 0..4104916183 | ascii_data |
| 36 | no | no | no | YES | 0..4294929488 | ascii_data |
| 40 | no | no | YES | YES | 0..4130013184 | ascii_data |
| 44 | no | no | no | YES | 0..4294929488 | ascii_data |
| 48 | no | no | no | YES | 0..4124576922 | ascii_data |
| 52 | no | no | no | no | 0..65535 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### FLUENZ BOLD M_Varianta A.VCF
- Elements: 65
- Footers: 64 ([196, 245])
- ASCII: ['ZB.h']

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | YES | 1699200..1083943906 | ascii_data |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4294918230 | ascii_data |
| 32 | no | no | YES | YES | 0..4104916183 | ascii_data |
| 36 | no | no | no | YES | 0..4294929488 | ascii_data |
| 40 | no | no | YES | YES | 0..4130013184 | ascii_data |
| 44 | no | no | no | YES | 0..4294929488 | ascii_data |
| 48 | no | no | no | YES | 0..4124576922 | ascii_data |
| 52 | no | no | no | no | 0..65535 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### FLUENZ BOLD S upr.VCF
- Elements: 44
- Footers: 43 ([196])
- ASCII: ['HvirdD']

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | YES | 1084407185..1084594168 | ascii_data |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4287381590 | ascii_data |
| 32 | no | no | YES | YES | 0..3489678443 | ascii_data |
| 36 | no | no | no | YES | 0..4098097152 | ascii_data |
| 40 | no | no | YES | YES | 0..3669639312 | ascii_data |
| 44 | no | no | no | YES | 0..4098097152 | ascii_data |
| 48 | no | no | no | YES | 0..4201858185 | ascii_data |
| 52 | no | no | no | no | 0..58195 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### FLUENZ BOLD S_Zdroj světla dole.VCF
- Elements: 62
- Footers: 61 ([196, 245])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | YES | 1699200..1084465756 | ascii_data |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4250943574 | ascii_data |
| 32 | no | no | YES | YES | 0..4285009013 | ascii_data |
| 36 | no | no | no | YES | 0..4104929449 | ascii_data |
| 40 | no | no | YES | YES | 0..4104916051 | ascii_data |
| 44 | no | no | no | YES | 0..4239999145 | ascii_data |
| 48 | no | no | no | YES | 0..4141613475 | ascii_data |
| 52 | no | no | no | no | 0..49274 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### FLUENZ BOLD S_Zdroj světla nahoře.VCF
- Elements: 72
- Footers: 71 ([196, 245])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | YES | 1699200..1083943719 | ascii_data |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4104929366 | ascii_data |
| 32 | no | no | YES | YES | 0..4104916051 | ascii_data |
| 36 | no | no | no | YES | 0..4132306147 | ascii_data |
| 40 | no | no | YES | YES | 0..4104916051 | ascii_data |
| 44 | no | no | no | YES | 0..4294931541 | ascii_data |
| 48 | no | no | no | YES | 0..4158914560 | ascii_data |
| 52 | no | no | no | no | 0..64822 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### FLUENZ BOLD S_ozub kolo na objímku.VCF
- Elements: 2
- Footers: 1 ([196])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | no | no | no | 1084624407..1084624407 | constant_default |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | no | no | 2147483648..2147483648 | constant_default |
| 28 | YES | no | no | no | 16470..16470 | constant_default |
| 32 | YES | no | YES | no | 2942566400..2942566400 | constant_float64 |
| 36 | YES | no | no | no | 3208413047..3208413047 | constant_default |
| 40 | YES | no | no | YES | 4136943732..4136943732 | constant_default |
| 44 | YES | no | no | no | 2331533062..2331533062 | constant_default |
| 48 | YES | no | no | no | 16570..16570 | constant_default |
| 52 | YES | YES | no | no | 0..0 | unused/padding |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### FLUENZ L.VCF
- Elements: 137
- Footers: 136 ([196, 245])
- ASCII: ['3333']

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | YES | 1699200..1084755133 | ascii_data |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4294918230 | ascii_data |
| 32 | no | no | YES | YES | 0..4104914167 | ascii_data |
| 36 | no | no | no | YES | 0..4294931541 | ascii_data |
| 40 | no | no | YES | YES | 0..4104914167 | ascii_data |
| 44 | no | no | no | YES | 0..4294931541 | ascii_data |
| 48 | no | no | no | YES | 0..4104914167 | ascii_data |
| 52 | no | no | no | no | 0..65535 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### FLUENZ M.VCF
- Elements: 63
- Footers: 62 ([196, 245])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | YES | 1699200..1084364221 | ascii_data |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4124328022 | ascii_data |
| 32 | no | no | YES | YES | 0..4104916718 | ascii_data |
| 36 | no | no | no | YES | 0..4103605998 | ascii_data |
| 40 | no | no | YES | no | 0..2250772206 | per_element_float64 |
| 44 | no | no | no | YES | 0..4294929400 | ascii_data |
| 48 | no | no | no | YES | 0..4104454143 | ascii_data |
| 52 | no | no | no | no | 0..3822 | per_element_uint32 |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### FLUENZ S.VCF
- Elements: 72
- Footers: 71 ([196, 245])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | YES | 1699200..1084650425 | ascii_data |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4104929366 | ascii_data |
| 32 | no | no | YES | YES | 0..4104916718 | ascii_data |
| 36 | no | no | no | YES | 0..4103605998 | ascii_data |
| 40 | no | no | YES | no | 0..2250772206 | per_element_float64 |
| 44 | no | no | no | YES | 0..4294929400 | ascii_data |
| 48 | no | no | no | YES | 0..4104454143 | ascii_data |
| 52 | no | no | no | no | 0..3822 | per_element_uint32 |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### FLUENZ XL.VCF
- Elements: 78
- Footers: 77 ([196, 245])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | YES | 1699200..1083409321 | ascii_data |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..3057401942 | ascii_data |
| 32 | no | no | YES | YES | 0..3745202361 | ascii_data |
| 36 | no | no | no | YES | 0..4098097152 | ascii_data |
| 40 | no | no | YES | no | 0..2898984981 | per_element_float64 |
| 44 | no | no | no | no | 0..4098097152 | per_element_float32 |
| 48 | no | no | no | no | 0..2786328597 | per_element_float32 |
| 52 | no | no | no | no | 0..600 | per_element_uint32 |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### Fishbone 2790x1200.VCF
- Elements: 14
- Footers: 13 ([196, 245])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | no | 1700040..1700228 | per_element_uint32 |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..3169796182 | ascii_data |
| 32 | no | no | YES | no | 0..16529 | per_element_float64 |
| 36 | no | no | no | no | 0..1220542464 | per_element_float32 |
| 40 | no | no | YES | no | 0..1444 | per_element_float64 |
| 44 | no | no | no | no | 0..1220542464 | per_element_float32 |
| 48 | no | no | no | no | 0..1444 | per_element_uint32 |
| 52 | YES | YES | no | no | 0..0 | unused/padding |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### PCB.VCF
- Elements: 1106
- Footers: 1105 ([196, 253])
- ASCII: ['08JTNYR7', '4Q9N3XWX', 'EUUD2A5K', 'H656BRP1', 'J9UHFFYX']

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | YES | 0..3226960744 | ascii_data |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4226433110 | ascii_data |
| 32 | no | no | YES | YES | 0..4294918288 | ascii_data |
| 36 | no | no | no | YES | 0..4241809408 | ascii_data |
| 40 | no | no | YES | YES | 0..3758127379 | ascii_data |
| 44 | no | no | no | no | 0..4194451456 | per_element_float32 |
| 48 | no | no | no | YES | 0..4294901760 | ascii_data |
| 52 | no | no | no | no | 0..40960 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### V měřítku.VCF
- Elements: 660
- Footers: 659 ([196])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | YES | 0..1084235349 | ascii_data |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4275322966 | ascii_data |
| 32 | no | no | YES | YES | 0..4101250074 | ascii_data |
| 36 | no | no | no | YES | 0..4099934665 | ascii_data |
| 40 | no | no | YES | YES | 0..4056940544 | ascii_data |
| 44 | no | no | no | YES | 0..2362798763 | ascii_data |
| 48 | no | no | no | YES | 0..4046454784 | ascii_data |
| 52 | no | no | no | no | 0..39512 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### big coffee 12.8.2790x1200 bezotočení.VCF
- Elements: 13
- Footers: 12 ([196, 245])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | no | 1700040..1700228 | per_element_uint32 |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..2527215702 | ascii_data |
| 32 | no | no | YES | no | 0..3137505519 | per_element_float64 |
| 36 | no | no | no | no | 0..2031567015 | per_element_float32 |
| 40 | no | no | YES | YES | 0..999643186 | ascii_data |
| 44 | no | no | no | YES | 0..4011737012 | ascii_data |
| 48 | no | no | no | YES | 0..3123799063 | ascii_data |
| 52 | no | no | no | no | 0..29318 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### bigcoffee 12.8. 2790x1200.VCF
- Elements: 13
- Footers: 12 ([196])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | no | no | no | 1699388..1699388 | constant_default |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | no | no | 2147483648..2147483648 | constant_default |
| 28 | YES | no | no | no | 16470..16470 | constant_default |
| 32 | YES | YES | no | no | 0..0 | unused/padding |
| 36 | YES | YES | no | no | 0..0 | unused/padding |
| 40 | YES | YES | no | no | 0..0 | unused/padding |
| 44 | YES | YES | no | no | 0..0 | unused/padding |
| 48 | YES | YES | no | no | 0..0 | unused/padding |
| 52 | YES | YES | no | no | 0..0 | unused/padding |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### bigcoffee_12_8_2790x1200.VCF
- Elements: 13
- Footers: 12 ([196])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | YES | no | no | 0..0 | unused/padding |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | no | no | 2147483648..2147483648 | constant_default |
| 28 | YES | no | no | no | 16470..16470 | constant_default |
| 32 | no | no | YES | no | 0..4118806528 | per_element_float64 |
| 36 | no | no | no | YES | 0..4101259429 | ascii_data |
| 40 | no | no | YES | no | 0..4099935159 | per_element_float64 |
| 44 | no | no | no | no | 0..3758096384 | per_element_float32 |
| 48 | no | no | no | YES | 0..3762290688 | ascii_data |
| 52 | no | no | no | no | 0..32768 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### botanic 2790 x1200.VCF
- Elements: 19
- Footers: 18 ([196, 245])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | YES | 1699200..1084272896 | ascii_data |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | no | 16470..4179509334 | per_element_float32 |
| 32 | no | no | no | YES | 0..2984739203 | ascii_data |
| 36 | no | no | no | no | 0..2914205836 | per_element_float32 |
| 40 | no | no | YES | YES | 0..2930032058 | ascii_data |
| 44 | no | no | no | YES | 0..3655876749 | ascii_data |
| 48 | no | no | no | no | 0..2952812633 | per_element_float32 |
| 52 | no | no | no | no | 0..65535 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### botanic vše_3780.VCF
- Elements: 1091
- Footers: 1090 ([196])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | no | 0..19511684 | offset_or_address |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4288102486 | ascii_data |
| 32 | no | no | YES | YES | 0..4244638233 | ascii_data |
| 36 | no | no | no | YES | 0..4105175040 | ascii_data |
| 40 | no | no | YES | YES | 0..4288102593 | ascii_data |
| 44 | no | no | no | YES | 0..4288102581 | ascii_data |
| 48 | no | no | no | YES | 0..4118806528 | ascii_data |
| 52 | no | no | no | no | 0..65431 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### botanic_2790x1200.VCF
- Elements: 19
- Footers: 18 ([196])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | no | 0..1084301056 | per_element_float32 |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..3430432854 | ascii_data |
| 32 | no | no | YES | YES | 0..4099935068 | ascii_data |
| 36 | no | no | no | no | 0..4294901760 | per_element_float32 |
| 40 | no | no | YES | YES | 0..3590278542 | ascii_data |
| 44 | no | no | no | YES | 0..4294919086 | ascii_data |
| 48 | no | no | no | YES | 0..3939500032 | ascii_data |
| 52 | no | no | no | no | 0..32769 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### botanic_simple_1_aci.VCF
- Elements: 16
- Footers: 15 ([196])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | no | 0..1084301056 | per_element_float32 |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | no | no | 2147483648..2147483648 | constant_default |
| 28 | YES | no | no | no | 16470..16470 | constant_default |
| 32 | YES | YES | no | no | 0..0 | unused/padding |
| 36 | YES | YES | no | no | 0..0 | unused/padding |
| 40 | YES | YES | no | no | 0..0 | unused/padding |
| 44 | YES | YES | no | no | 0..0 | unused/padding |
| 48 | YES | YES | no | no | 0..0 | unused/padding |
| 52 | YES | YES | no | no | 0..0 | unused/padding |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### data řez.VCF
- Elements: 30
- Footers: 29 ([196, 245])
- ASCII: ['Laye', 'VERTEX', 'yer_11']

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | no | 1699200..1699388 | per_element_uint32 |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4098113622 | ascii_data |
| 32 | no | no | no | YES | 0..825319282 | ascii_data |
| 36 | no | no | no | no | 0..908075018 | per_element_float32 |
| 40 | no | no | no | no | 0..939524096 | per_element_float32 |
| 44 | no | no | no | no | 0..908075018 | per_element_float32 |
| 48 | no | no | no | no | 0..170986038 | offset_or_address |
| 52 | no | no | no | no | 0..8224 | per_element_uint32 |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### double_line_1_aci.VCF
- Elements: 2
- Footers: 1 ([196])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | YES | no | no | 0..0 | unused/padding |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | no | no | 2147483648..2147483648 | constant_default |
| 28 | YES | no | no | no | 16470..16470 | constant_default |
| 32 | YES | YES | no | no | 0..0 | unused/padding |
| 36 | YES | YES | no | no | 0..0 | unused/padding |
| 40 | YES | YES | no | no | 0..0 | unused/padding |
| 44 | YES | YES | no | no | 0..0 | unused/padding |
| 48 | YES | YES | no | no | 0..0 | unused/padding |
| 52 | YES | YES | no | no | 0..0 | unused/padding |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### double_line_2_aci.VCF
- Elements: 2
- Footers: 1 ([196])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | YES | no | no | 0..0 | unused/padding |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | no | no | 2147483648..2147483648 | constant_default |
| 28 | YES | no | no | no | 16470..16470 | constant_default |
| 32 | YES | YES | no | no | 0..0 | unused/padding |
| 36 | YES | YES | no | no | 0..0 | unused/padding |
| 40 | YES | YES | no | no | 0..0 | unused/padding |
| 44 | YES | YES | no | no | 0..0 | unused/padding |
| 48 | YES | YES | no | no | 0..0 | unused/padding |
| 52 | YES | YES | no | no | 0..0 | unused/padding |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### fishbone_2790x1200.VCF
- Elements: 14
- Footers: 13 ([196])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | YES | no | no | 0..0 | unused/padding |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | no | no | 2147483648..2147483648 | constant_default |
| 28 | YES | no | no | no | 16470..16470 | constant_default |
| 32 | no | no | no | no | 0..3942121472 | per_element_float32 |
| 36 | no | no | no | no | 0..2146962268 | offset_or_address |
| 40 | no | no | YES | no | 0..3892314112 | per_element_float64 |
| 44 | no | no | no | no | 0..3758096384 | per_element_float32 |
| 48 | no | no | no | no | 0..3762290688 | per_element_float32 |
| 52 | no | no | no | no | 0..32768 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### fluenz_xl.VCF
- Elements: 78
- Footers: 77 ([196])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | YES | 0..1082819662 | ascii_data |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4240588886 | ascii_data |
| 32 | no | no | YES | YES | 0..4118806528 | ascii_data |
| 36 | no | no | no | YES | 0..4143792328 | ascii_data |
| 40 | no | no | YES | YES | 0..4118806528 | ascii_data |
| 44 | no | no | no | YES | 0..4283632478 | ascii_data |
| 48 | no | no | no | YES | 0..4118806528 | ascii_data |
| 52 | no | no | no | no | 0..38535 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### line_10_elements.VCF
- Elements: 10
- Footers: 9 ([196])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | YES | no | no | 0..0 | unused/padding |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | no | no | 2147483648..2147483648 | constant_default |
| 28 | YES | no | no | no | 16470..16470 | constant_default |
| 32 | YES | YES | no | no | 0..0 | unused/padding |
| 36 | YES | YES | no | no | 0..0 | unused/padding |
| 40 | YES | YES | no | no | 0..0 | unused/padding |
| 44 | YES | YES | no | no | 0..0 | unused/padding |
| 48 | YES | YES | no | no | 0..0 | unused/padding |
| 52 | YES | YES | no | no | 0..0 | unused/padding |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### manchester vše_3781.VCF
- Elements: 72
- Footers: 71 ([196, 245])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | no | 0..3221225472 | per_element_float32 |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4104929366 | ascii_data |
| 32 | no | no | YES | YES | 0..4104916330 | ascii_data |
| 36 | no | no | no | no | 0..4103605610 | per_element_float32 |
| 40 | no | no | no | YES | 0..2250771818 | ascii_data |
| 44 | no | no | no | YES | 0..4294929028 | ascii_data |
| 48 | no | no | no | YES | 0..4104454143 | ascii_data |
| 52 | no | no | no | no | 0..30408 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### manchester_3_subjobs.VCF
- Elements: 72
- Footers: 71 ([196])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | YES | no | no | 0..0 | unused/padding |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4240588886 | ascii_data |
| 32 | no | no | YES | YES | 0..4118806528 | ascii_data |
| 36 | no | no | no | YES | 0..4217703262 | ascii_data |
| 40 | no | no | YES | YES | 0..4261431253 | ascii_data |
| 44 | no | no | no | YES | 0..4283632478 | ascii_data |
| 48 | no | no | no | YES | 0..4118806528 | ascii_data |
| 52 | no | no | no | no | 0..38535 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### musica 2790x1200.VCF
- Elements: 49
- Footers: 48 ([196, 245])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | YES | 1701832..1083671942 | ascii_data |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..3259580502 | ascii_data |
| 32 | no | no | YES | YES | 0..4164436100 | ascii_data |
| 36 | no | no | no | YES | 0..3772779803 | ascii_data |
| 40 | no | no | no | no | 0..16529 | offset_or_address |
| 44 | YES | YES | no | no | 0..0 | unused/padding |
| 48 | YES | YES | no | no | 0..0 | unused/padding |
| 52 | YES | YES | no | no | 0..0 | unused/padding |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### single_circle_1500_elements_2.VCF
- Elements: 2
- Footers: 1 ([196])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | no | no | YES | 1081408661..1081408661 | constant_default |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | no | no | 2147483648..2147483648 | constant_default |
| 28 | YES | no | no | no | 16470..16470 | constant_default |
| 32 | YES | YES | no | no | 0..0 | unused/padding |
| 36 | YES | YES | no | no | 0..0 | unused/padding |
| 40 | YES | YES | no | no | 0..0 | unused/padding |
| 44 | YES | YES | no | no | 0..0 | unused/padding |
| 48 | YES | YES | no | no | 0..0 | unused/padding |
| 52 | YES | YES | no | no | 0..0 | unused/padding |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### single_curve_elements_2.VCF
- Elements: 2
- Footers: 1 ([196])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | no | no | YES | 1081357357..1081357357 | constant_default |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | no | no | 2147483648..2147483648 | constant_default |
| 28 | YES | no | no | no | 16470..16470 | constant_default |
| 32 | YES | YES | no | no | 0..0 | unused/padding |
| 36 | YES | YES | no | no | 0..0 | unused/padding |
| 40 | YES | YES | no | no | 0..0 | unused/padding |
| 44 | YES | YES | no | no | 0..0 | unused/padding |
| 48 | YES | YES | no | no | 0..0 | unused/padding |
| 52 | YES | YES | no | no | 0..0 | unused/padding |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### single_line_2000_elements_2.VCF
- Elements: 2
- Footers: 1 ([196])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | YES | no | no | 0..0 | unused/padding |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | no | no | 2147483648..2147483648 | constant_default |
| 28 | YES | no | no | no | 16470..16470 | constant_default |
| 32 | YES | YES | no | no | 0..0 | unused/padding |
| 36 | YES | YES | no | no | 0..0 | unused/padding |
| 40 | YES | YES | no | no | 0..0 | unused/padding |
| 44 | YES | YES | no | no | 0..0 | unused/padding |
| 48 | YES | YES | no | no | 0..0 | unused/padding |
| 52 | YES | YES | no | no | 0..0 | unused/padding |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### single_square_500_elements_2.VCF
- Elements: 2
- Footers: 1 ([196])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | YES | no | no | 0..0 | unused/padding |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | no | no | 2147483648..2147483648 | constant_default |
| 28 | YES | no | no | no | 16470..16470 | constant_default |
| 32 | YES | YES | no | no | 0..0 | unused/padding |
| 36 | YES | YES | no | no | 0..0 | unused/padding |
| 40 | YES | YES | no | no | 0..0 | unused/padding |
| 44 | YES | YES | no | no | 0..0 | unused/padding |
| 48 | YES | YES | no | no | 0..0 | unused/padding |
| 52 | YES | YES | no | no | 0..0 | unused/padding |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### small coffee 2790x1200.VCF
- Elements: 37
- Footers: 36 ([196, 245])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | no | 1699200..1699388 | per_element_uint32 |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4280893526 | ascii_data |
| 32 | no | no | YES | no | 0..3590369877 | per_element_float64 |
| 36 | no | no | no | no | 0..4267248594 | per_element_float32 |
| 40 | no | no | YES | no | 0..4099407872 | per_element_float64 |
| 44 | no | no | no | no | 0..4290510848 | per_element_float32 |
| 48 | no | no | no | YES | 0..3945005056 | ascii_data |
| 52 | no | no | no | no | 0..32770 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### small fishbone 2790x1200.VCF
- Elements: 26
- Footers: 25 ([196, 245])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | no | 1701832..1702020 | per_element_uint32 |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | no | no | 2147483648..2147483648 | constant_default |
| 28 | YES | no | no | no | 16470..16470 | constant_default |
| 32 | YES | YES | no | no | 0..0 | unused/padding |
| 36 | no | no | no | no | 0..737345536 | per_element_float32 |
| 40 | no | no | no | no | 0..486566054 | offset_or_address |
| 44 | no | no | no | no | 0..32768 | offset_or_address |
| 48 | YES | YES | no | no | 0..0 | unused/padding |
| 52 | YES | YES | no | no | 0..0 | unused/padding |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### square_5_elements.VCF
- Elements: 5
- Footers: 4 ([196])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | YES | no | no | 0..0 | unused/padding |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | no | no | 2147483648..2147483648 | constant_default |
| 28 | YES | no | no | no | 16470..16470 | constant_default |
| 32 | YES | YES | no | no | 0..0 | unused/padding |
| 36 | YES | YES | no | no | 0..0 | unused/padding |
| 40 | YES | YES | no | no | 0..0 | unused/padding |
| 44 | YES | YES | no | no | 0..0 | unused/padding |
| 48 | YES | YES | no | no | 0..0 | unused/padding |
| 52 | YES | YES | no | no | 0..0 | unused/padding |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### stripe sixty 1200x2790.VCF
- Elements: 155
- Footers: 154 ([196, 245])
- ASCII: ['-2816.6895', '1097.', '3339.3458', '716.6895', 'Layer_1']

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | YES | no | no | 0..0 | unused/padding |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4294918230 | ascii_data |
| 32 | no | no | YES | YES | 0..4104454143 | ascii_data |
| 36 | no | no | no | YES | 0..4104929448 | ascii_data |
| 40 | no | no | YES | YES | 0..4278240597 | ascii_data |
| 44 | no | no | no | YES | 0..4103604913 | ascii_data |
| 48 | no | no | no | no | 0..2329608192 | per_element_float32 |
| 52 | no | no | no | no | 0..32768 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### vyrobni_data_Pernerka-Service for office_Camel_12mm.VCF
- Elements: 1754
- Footers: 1753 ([196])
- ASCII: ['0.Ui', '3333', '3333s', '9EGr9', 'ffff']

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | no | 0..19511684 | offset_or_address |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4268048470 | ascii_data |
| 32 | no | no | YES | YES | 0..4180082688 | ascii_data |
| 36 | no | no | no | YES | 0..4287073330 | ascii_data |
| 40 | no | no | YES | YES | 0..4216913920 | ascii_data |
| 44 | no | no | no | YES | 0..4283039744 | ascii_data |
| 48 | no | no | no | YES | 0..4216668344 | ascii_data |
| 52 | no | no | no | no | 0..65506 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### vyrobni_data_Pernerka-Service for office_Dark Knight_12mm.VCF
- Elements: 755
- Footers: 754 ([196])
- ASCII: ['.4112', '1w-e', '2244.2496', '3333', '33333']

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | YES | no | no | 0..0 | unused/padding |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4266147926 | ascii_data |
| 32 | no | no | YES | YES | 0..4276619759 | ascii_data |
| 36 | no | no | no | YES | 0..4272425455 | ascii_data |
| 40 | no | no | YES | YES | 0..4258793967 | ascii_data |
| 44 | no | no | no | YES | 0..4259842543 | ascii_data |
| 48 | no | no | no | YES | 0..4265085423 | ascii_data |
| 52 | no | no | no | no | 0..54316 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### vyrobni_data_Pernerka-Service for office_Matcha_12mm.VCF
- Elements: 4159
- Footers: 4158 ([196])
- ASCII: ['Di s', 'ffff', 'vmo7', 'xzzgP']

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | no | no | no | no | 0..19511684 | offset_or_address |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4272701526 | ascii_data |
| 32 | no | no | YES | YES | 0..4160815104 | ascii_data |
| 36 | no | no | no | YES | 0..4263247872 | ascii_data |
| 40 | no | no | YES | YES | 0..4279320701 | ascii_data |
| 44 | no | no | no | YES | 0..4288210238 | ascii_data |
| 48 | no | no | no | YES | 0..4266148024 | ascii_data |
| 52 | no | no | no | no | 0..64340 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### vyrobni_data_Pernerka-Service for office_Savanna_12mm.VCF
- Elements: 675
- Footers: 674 ([196])
- ASCII: []

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | YES | no | no | 0..0 | unused/padding |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4290461782 | ascii_data |
| 32 | no | no | YES | no | 0..3559915520 | per_element_float64 |
| 36 | no | no | no | YES | 0..4291952641 | ascii_data |
| 40 | no | no | YES | YES | 0..3322216459 | ascii_data |
| 44 | no | no | no | YES | 0..4293591041 | ascii_data |
| 48 | no | no | no | YES | 0..3762569285 | ascii_data |
| 52 | no | no | no | no | 0..54312 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

### vyrobni_data_Pernerka-Service for office_Terracota_12mm.VCF
- Elements: 1427
- Footers: 1426 ([196])
- ASCII: ['1w-e', 'a2U0', 'ffff', 'fffff', 'ffffff']

| Offset | Constant? | All Zero? | Has Float64? | Has ASCII? | U32 Range | Hypothesis |
|--------|-----------|-----------|--------------|------------|-----------|------------|
| 0 | YES | YES | no | no | 0..0 | unused/padding |
| 4 | YES | YES | no | no | 0..0 | unused/padding |
| 8 | YES | YES | no | no | 0..0 | unused/padding |
| 12 | YES | YES | no | no | 0..0 | unused/padding |
| 16 | YES | YES | no | no | 0..0 | unused/padding |
| 20 | YES | no | no | no | 16404..16404 | constant_default |
| 24 | YES | no | YES | no | 2147483648..2147483648 | constant_float64 |
| 28 | no | no | no | YES | 16470..4230955094 | ascii_data |
| 32 | no | no | YES | YES | 0..4288086016 | ascii_data |
| 36 | no | no | no | YES | 0..4275240960 | ascii_data |
| 40 | no | no | YES | YES | 0..4288086016 | ascii_data |
| 44 | no | no | no | YES | 0..4263706624 | ascii_data |
| 48 | no | no | no | YES | 0..4246880451 | ascii_data |
| 52 | no | no | no | no | 0..58091 | offset_or_address |
| 56 | YES | YES | no | no | 0..0 | unused/padding |
| 60 | YES | YES | no | no | 0..0 | unused/padding |
| 64 | YES | YES | no | no | 0..0 | unused/padding |
| 68 | YES | YES | no | no | 0..0 | unused/padding |
| 72 | YES | YES | no | no | 0..0 | unused/padding |
| 76 | YES | YES | no | no | 0..0 | unused/padding |
| 80 | YES | YES | no | no | 0..0 | unused/padding |
| 84 | YES | YES | no | no | 0..0 | unused/padding |
| 88 | YES | YES | no | no | 0..0 | unused/padding |
| 92 | YES | YES | no | no | 0..0 | unused/padding |
| 96 | YES | YES | no | no | 0..0 | unused/padding |
| 100 | YES | YES | no | no | 0..0 | unused/padding |
| 104 | YES | YES | no | no | 0..0 | unused/padding |
| 108 | YES | YES | no | no | 0..0 | unused/padding |
| 112 | YES | no | no | no | 1075052544..1075052544 | constant_default |
| 116 | YES | YES | no | no | 0..0 | unused/padding |

## 3. Detailed Footer Dumps (First 5 Files)

### 1ks.VCF

```
  Element 0 @ 0x2663a: size=196B, color=0x0000ff00, pts=24
  Element 1 @ 0x26e1b: size=196B, color=0x0000ff00, pts=28
  Element 2 @ 0x27724: size=196B, color=0x0000ff00, pts=24
```

### 1ks.VCF

```
  Element 0 @ 0xd4a6: size=196B, color=0xff901e00, pts=24
  Element 1 @ 0xdc87: size=196B, color=0xff901e00, pts=28
  Element 2 @ 0xe590: size=196B, color=0xff901e00, pts=24
```

### 2560x150 s fazetou 45st hl6.VCF

```
  Element 0 @ 0xd579: size=196B, color=0x00ff0000, pts=1
  Element 1 @ 0xd6b4: size=196B, color=0x00000000, pts=1
```

### 26ks skladba.VCF

```
  Element 0 @ 0x26899: size=196B, color=0x0000ff00, pts=4
  Element 1 @ 0x26ab2: size=196B, color=0xffff0000, pts=24
  Element 2 @ 0x27293: size=196B, color=0xffff0000, pts=28
```

### 26ks skladba_nesting.VCF

```
  Element 0 @ 0x26d5d: size=196B, color=0x0000ff00, pts=4
  Element 1 @ 0x26f76: size=196B, color=0xffff0000, pts=24
  Element 2 @ 0x27757: size=196B, color=0xffff0000, pts=28
```

## 4. Field Meaning Hypotheses

### Known / Confirmed fields:

- Offset 0-3: likely DXF group code data
- Offset 4-196: bounding box values, element metadata
- Offset 196-245 (variant only): extra 49B (purpose unknown)

### Based on statistical analysis:

- **ascii_data**: offsets @28, @36, @28, @124, @0, @28, @28, @28, @28, @0
- **constant_default**: offsets @20, @20, @20, @20, @20, @20, @20, @20, @20, @20
- **constant_float64**: offsets @24, @24, @120, @24, @120, @24, @24, @24, @120, @24
- **offset_or_address**: offsets @40, @52, @52, @52, @36, @52, @52, @52, @52, @0
- **per_element_float32**: offsets @28, @44, @0, @0, @32, @36, @44, @36, @132, @28
- **per_element_float64**: offsets @32, @32, @128, @40, @40, @208, @32, @32, @40, @40
- **per_element_uint32**: offsets @240, @0, @0, @0, @0, @240, @240, @52, @52, @52
- **unused/padding**: offsets @0, @0, @0, @4, @4, @0, @0, @0, @4, @0
