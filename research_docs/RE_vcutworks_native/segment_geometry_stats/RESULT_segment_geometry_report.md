# Segment Geometry Statistics Report

**Generated:** by segment_geometry_stats.py — 62 files, 100264 segments

---

## 1. Summary

- Files analyzed: 62
- Total elements: 14425
- Total segments: 100264
- Arc segment ratio: 36.9%

## 2. Segment Length Distribution (mm)

| Metric | Value |
|--------|-------|
| Count | 100264 |
| Min | 0.1289 |
| Max | 2900.0002 |
| Mean | 62.8232 |
| Std | 249.106 |
| P5 | 1.4717 |
| P25 | 9.1404 |
| P50 | 20.0 |
| P75 | 45.0706 |
| P95 | 94.2009 |

### Statistical Outliers (> mean + 3σ)

- Threshold: 810.1412 mm
- Count: 1328 (1.3% of all segments)
- Max outlier: 2900.0002 mm

## 3. Arc Parameter Distribution

### arc_d0

| Metric | Value |
|--------|-------|
| n | 30977 |
| min | -2520.792 |
| max | 5083.8662 |
| mean | 999.5747 |
| std | 1629.932 |
| p5 | -1906.0479 |
| p50 | 1090.2573 |
| p95 | 4420.6851 |

### arc_d1

| Metric | Value |
|--------|-------|
| n | 36945 |
| min | 0.0 |
| max | 7178.0195 |
| mean | 2104.3898 |
| std | 1826.9375 |
| p5 | 1.0 |
| p50 | 1607.984 |
| p95 | 5216.0166 |

### arc_d2

| Metric | Value |
|--------|-------|
| n | 36945 |
| min | -2520.4409 |
| max | 5089.0122 |
| mean | 818.5925 |
| std | 1538.6735 |
| p5 | -1794.3511 |
| p50 | 812.6772 |
| p95 | 4339.5605 |

## 4. Curvature Index Distribution

| Metric | Value |
|--------|-------|
| n | 90881 |
| min | 0.0 |
| max | 0.8414 |
| mean | 0.0562 |
| std | 0.0845 |
| p5 | 0.0001 |
| p50 | 0.0317 |
| p95 | 0.2246 |

## 5. Sharp Corners per Element

| Metric | Value |
|--------|-------|
| n | 90881 |
| min | 0 |
| max | 0 |
| mean | 0.0 |
| std | 0.0 |
| p50 | 0 |

## 6. Geometry Type Distribution

| Type | Count |
|------|-------|
| Line | 5593 |
| Polyline | 4679 |
| Polygon | 3845 |
| Circle | 308 |

## 7. Segment Length Histogram (20 bins)

```
       0.1-145.1   :  96298 ########################################
     145.1-290.1   :    830 
     290.1-435.1   :    815 
     435.1-580.1   :    479 
     580.1-725.1   :    447 
     725.1-870.1   :     73 
     870.1-1015.1  :    287 
    1015.1-1160.1  :     28 
    1160.1-1305.1  :    213 
    1305.1-1450.1  :      1 
    1450.1-1595.1  :      0 
    1595.1-1740.1  :      0 
    1740.1-1885.0  :      2 
    1885.0-2030.0  :    184 
    2030.0-2175.0  :     14 
    2175.0-2320.0  :      2 
    2320.0-2465.0  :      2 
    2465.0-2610.0  :     50 
    2610.0-2755.0  :      0 
    2755.0-2900.0  :    539 
```

## 8. Per-File Summary

| File | Elements | Segments | Avg Length | Max Length | Arc % |
|------|----------|----------|------------|------------|-------|
| 1ks.VCF | 7 | 140 | 26.46 | 100.0 | 0.0% |
| 1ks.VCF | 7 | 140 | 26.46 | 100.0 | 0.0% |
| 2560x150 s fazetou 45st hl6.VCF | 3 | 3 | 2560.0 | 2560.0 | 0.0% |
| 26ks skladba.VCF | 183 | 3644 | 28.69 | 2900.0 | 0.0% |
| 26ks skladba_nesting.VCF | 573 | 13360 | 26.34 | 2900.0 | 0.0% |
| 26ks_skladba.VCF | 183 | 3644 | 28.69 | 2900.0 | 0.0% |
| 2790x1200 s fazetou.VCF | 2 | 8 | 1995.0 | 2790.0 | 0.0% |
| Arbyd_výrobní data_V1 20.5.2025.VCF | 418 | 11467 | 26.93 | 1348.32 | 99.5% |
| Big_coffee_dune_2790_600.VCF | 14 | 46 | 859.06 | 2790.0 | 65.2% |
| FLUENZ BOLD M_Varianta A 2ks skladba.VCF | 136 | 5903 | 16.28 | 2900.0 | 99.3% |
| FLUENZ BOLD M_Varianta A.VCF | 65 | 1816 | 18.63 | 1220.0 | 99.3% |
| FLUENZ BOLD S upr.VCF | 44 | 1584 | 14.34 | 1220.0 | 99.0% |
| FLUENZ BOLD S_Zdroj světla dole.VCF | 62 | 1902 | 13.82 | 1200.0 | 96.1% |
| FLUENZ BOLD S_Zdroj světla nahoře.VCF | 72 | 2026 | 14.31 | 1200.0 | 99.0% |
| FLUENZ BOLD S_ozub kolo na objímku.VCF | 2 | 144 | 11.9 | 15.02 | 97.2% |
| FLUENZ L.VCF | 137 | 3455 | 17.54 | 1220.0 | 99.0% |
| FLUENZ M.VCF | 63 | 1551 | 15.2 | 1220.0 | 99.2% |
| FLUENZ S.VCF | 72 | 1786 | 13.8 | 1220.0 | 99.3% |
| FLUENZ XL.VCF | 78 | 2071 | 18.11 | 1220.0 | 99.4% |
| Fishbone 2790x1200.VCF | 14 | 47 | 844.93 | 2790.0 | 83.0% |
| PCB.VCF | 1106 | 4313 | 43.13 | 2550.0 | 1.6% |
| V měřítku.VCF | 660 | 1436 | 17.1 | 225.0 | 87.6% |
| big coffee 12.8.2790x1200 bezotočení.VCF | 13 | 39 | 798.63 | 2790.0 | 79.5% |
| bigcoffee 12.8. 2790x1200.VCF | 13 | 39 | 798.63 | 2790.0 | 0.0% |
| bigcoffee_12_8_2790x1200.VCF | 13 | 39 | 798.63 | 2790.0 | 0.0% |
| botanic 2790 x1200.VCF | 19 | 325 | 195.23 | 2790.0 | 97.5% |
| botanic vše_3780.VCF | 1091 | 4311 | 74.22 | 2790.0 | 0.0% |
| botanic_2790x1200.VCF | 19 | 325 | 195.23 | 2790.0 | 92.9% |
| botanic_one_curve_1_aci.VCF | 1 | 15 | 186.14 | 637.41 | 93.3% |
| botanic_simple_1_aci.VCF | 16 | 316 | 141.46 | 951.18 | 94.3% |
| circle_500_single_aci.VCF | 1 | 4 | 24.53 | 24.54 | 0.0% |
| circle_diameter_600_native.VCF | 1 | 4 | 58.88 | 58.89 | 0.0% |
| data řez.VCF | 30 | 66 | 1743.79 | 2570.0 | 50.0% |
| double_line_1_aci.VCF | 2 | 2 | 1000.0 | 1000.0 | 0.0% |
| double_line_2_aci.VCF | 2 | 2 | 1000.0 | 1000.0 | 0.0% |
| empty_canvas.VCF | 0 | 0 | 0 | 0 | 0% |
| fishbone_2790x1200.VCF | 14 | 47 | 845.1 | 2792.0 | 0.0% |
| fluenz_xl.VCF | 78 | 2077 | 20.93 | 2400.0 | 0.0% |
| line_10_elements.VCF | 10 | 10 | 2000.0 | 2000.0 | 0.0% |
| manchester vše_3781.VCF | 72 | 81 | 2665.43 | 2790.0 | 0.0% |
| manchester_3_subjobs.VCF | 72 | 81 | 2665.43 | 2790.0 | 0.0% |
| musica 2790x1200.VCF | 49 | 921 | 66.15 | 2792.0 | 99.1% |
| single_circle_1500.VCF | 1 | 4 | 73.6 | 73.61 | 0.0% |
| single_circle_1500_elements_2.VCF | 2 | 8 | 73.6 | 73.61 | 0.0% |
| single_curve.VCF | 1 | 2 | 770.88 | 1224.29 | 100.0% |
| single_curve_elements_2.VCF | 2 | 4 | 770.88 | 1224.29 | 100.0% |
| single_line_1_aci.VCF | 1 | 1 | 1000.0 | 1000.0 | 0.0% |
| single_line_2000.VCF | 1 | 1 | 2000.0 | 2000.0 | 0.0% |
| single_line_2000_elements_2.VCF | 2 | 2 | 2000.0 | 2000.0 | 0.0% |
| single_square_500.VCF | 1 | 4 | 500.0 | 500.0 | 0.0% |
| single_square_500_elements_2.VCF | 2 | 8 | 500.0 | 500.0 | 0.0% |
| single_star_1_aci.VCF | 1 | 10 | 294.53 | 299.73 | 0.0% |
| small coffee 2790x1200.VCF | 37 | 99 | 454.89 | 2790.0 | 91.9% |
| small fishbone 2790x1200.VCF | 26 | 143 | 437.53 | 2790.0 | 94.4% |
| square_1_aci.VCF | 1 | 4 | 1000.0 | 1000.0 | 0.0% |
| square_5_elements.VCF | 5 | 20 | 500.0 | 500.0 | 0.0% |
| stripe sixty 1200x2790.VCF | 155 | 191 | 434.66 | 2792.0 | 0.0% |
| vyrobni_data_Pernerka-Service for office_Camel_12mm.VCF | 1754 | 5849 | 120.08 | 2850.0 | 0.0% |
| vyrobni_data_Pernerka-Service for office_Dark Knight_12mm.VCF | 755 | 1661 | 163.28 | 2850.0 | 0.0% |
| vyrobni_data_Pernerka-Service for office_Matcha_12mm.VCF | 4159 | 17151 | 88.22 | 2850.0 | 0.0% |
| vyrobni_data_Pernerka-Service for office_Savanna_12mm.VCF | 675 | 2721 | 94.04 | 2850.0 | 0.0% |
| vyrobni_data_Pernerka-Service for office_Terracota_12mm.VCF | 1427 | 3191 | 150.62 | 2850.0 | 0.0% |
