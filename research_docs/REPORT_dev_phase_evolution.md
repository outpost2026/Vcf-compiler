# REPORT: VCF Compiler Debug — Evolution of Reverse Engineering (Session 1→6)

**Version:** 1.0
**Date:** 2026-06-29
**Author:** SYSTEQ research team + LLM-assisted analysis
**Purpose:** Comprehensive documentation of the full reverse engineering journey of the Ruida VCF binary format, from initial failure through breakthrough to working Proof of Concept. Covers the evolution of methodology, critical blind spots, the binary search variant innovation, and how LLM collaboration led to the breakthrough.

---

## 1. EXECUTIVE CHRONOLOGY

### 1.1 Timeline Overview

| Session | Date | Focus | Outcome |
|---------|------|-------|---------|
| Session 1 | 2026-06-27 | Initial writer implementation | First functional VCF writer; files load in VCutWorks but have structural issues |
| Session 2 | 2026-06-27 | MACHINE_PROFILE + empty blocks | Writer expanded; files grow to ~157KB but still broken |
| Session 3 | 2026-06-28 | Hex diff analysis, research docs | 1055 diff regions identified; layer blocks ~90% zeros |
| Session 4 | 2026-06-29 | color@12 fix, field identification | color@12 restored, MACHINE_PROFILE verified 0 diffs |
| Session 5 | 2026-06-29 | Binary search variant generator | Variants A–J created; variant G reduces diffs to 11 regions |
| Session 6 | 2026-06-29 | GUI testing + breakthrough | **3 root causes identified and fixed. Working PoC confirmed.** |

### 1.2 Key Metrics

| Metric | Session 3 (pre-breakthrough) | Session 6 (post-breakthrough) |
|--------|------------------------------|-------------------------------|
| Diff regions (hex diff) | 1055 | 4 (in active block, semantically identical) |
| Writer test pass rate | 23/23 | 28/28 |
| VCutWorks compatibility | NOT LOADING | ✅ LOADS + renders geometry |
| Known root causes | 0 | 3 (all fixed) |
| Unknown fields in layer block | ~20+ zones | 4 remaining denormalized bytes (8e-320 vs 0.0) |

---

## 2. SESSION-BY-SESSION EVOLUTION

### 2.1 Session 1: Initial Implementation (2026-06-27)

**Goal:** Create a minimal VCF writer that produces a file VCutWorks can load.

**Approach:** Clean-slate implementation based on hex analysis of native VCF exports. The writer used an "active-first" layout — writing the active layer block immediately after the header, without the 256 empty block padding.

**Result:** The writer produced 1005-byte files that technically loaded in VCutWorks (showed a black canvas) but rendered no geometry. This was actually the best result seen for weeks — later regressions made files completely unloadable.

**Commit:** `4ba9446` — "feat: VCF header format + dxf adapter + ACI mapping (PRVNÍ FUNKČNÍ)"

**Key Lesson:** The "first working" version was structurally incomplete (no empty blocks, no trailer) but somehow bypassed critical validations that later versions triggered. This should have been a warning sign that more data does not necessarily mean more correct.

### 2.2 Session 2: Structural Expansion (2026-06-27)

**Goal:** Add MACHINE_PROFILE, empty block padding, and trailer structure to match native file size (~157KB).

**Approach:** Extracted MACHINE_PROFILE (418 bytes) from native VCF, implemented 256 empty blocks with block index counters, and added TRAILER_PREFIX with DXF path embedding.

**Changes:**
- MACHINE_PROFILE included in header (418B, hardcoded constant)
- EMPTY_BLOCK_COUNT = 256 (producing 157KB files matching native size)
- Block color at offset 76 set to black (0x000000)
- Block index counter at [10] (uint16, 0-255 across empty blocks)
- TRAILER_PREFIX constant (199 bytes from native VCF)
- trailer() method with DXF path embedding

**Result:** Files grew to ~157KB but now VCutWorks rejected them entirely ("neočekávaný formát souboru"). This was a regression — the simple 1005-byte version loaded (empty canvas), but the structurally complete 157KB version did not.

**Key Lesson:** Adding structure made things worse, not better. The assumption that "more native-like = better" was wrong. This should have triggered a more systematic investigation, but instead the team proceeded with hex diff analysis.

### 2.3 Session 3: Hex Diff Analysis (2026-06-28)

**Goal:** Quantify the differences between native and synthetic VCF using binary hex diff.

**Approach:** Ran `hex_diff_v2.py` comparing `square_1_aci.VCF` (native, 157868B) vs `square_from_dxf.VCF` (synthetic, 157165B).

**Findings:**
- 1055 diff regions identified
- Layer blocks were ~90% zeros in synthetic vs populated data in native
- Size difference: 703B (synthetic smaller)
- Pattern A: Machine profile area differences
- Pattern B: Layer block area — native has data across entire 610B, synthetic only at specific fields
- Pattern C: Linked-list pointers

**Documents created:**
- `DEV_REPORT_VCF_COMPILER_DEBUG_v1.md` (497 lines, 5 hypotheses H1-H5)
- `Gemini_RD_VCF.txt` (542 lines — methodology research)

**Hypotheses generated:**
- H1: Layer blocks are incomplete (★★★★★)
- H2: Linked-list terminator wrong (★★★★)
- H3: Machine profile mismatch (★★★)
- H4: Missing geometry count/preamble (★★)
- H5: Wrong geom_color format (★★)

**Key Blind Spot:** The 1055 diff regions were dominated by empty block init data (3740 bytes) and various padding areas. The analysis correctly identified *what* was different but could not distinguish *what matters*. Every diff looked equally important.

### 2.4 Session 4: Color Fix & Verification (2026-06-29)

**Goal:** Fix color@12 regression, verify MACHINE_PROFILE and GEOMETRY_HEADER_TEMPLATE.

**Approach:** Detailed byte-by-byte comparison of specific fields.

**Fixes applied:**
- color@12 restored in encode_layer_block() — BGR color now written at block offset 12 (in addition to existing offset 76)
- GEOMETRY_HEADER_TEMPLATE refactored to `b'\x00' + struct.pack('<d', 1.0)*4` (functionally identical)

**Verifications:**
- MACHINE_PROFILE: **0 byte diffs** vs native when correctly aligned at offset 54
- POST_STOCK_HEADER: alignment correct (preamble [0:54] matches native byte-for-byte)
- Last-layer linked-list terminator: native color=1 differs from writer color=0

**Test status:** 28/28 PASS, 2 SKIP

**Key Lesson:** Despite confirming MACHINE_PROFILE and geometry header as correct (disproving H3 and H4), the files still wouldn't load. The hex diff was reduced from 1055 regions to ~12 active block diffs + 3752 empty block diffs + 39 trailer diffs. The size difference shrank from 703B to 1B. Yet VCutWorks still rejected everything.

This is the moment where the limitation of hex diff became critical: **3740 bytes of empty block diffs were drowning out 12 bytes of critical active block diffs.**

### 2.5 Session 5: Binary Search Generator (2026-06-29, morning)

**Goal:** Create a systematic variant generation methodology to isolate which structural features cause VCutWorks rejection.

**Innovation:** LLM proposed the **binary search variant** approach — generate VCF files with incrementally added structural features and test each in real VCutWorks GUI.

**Variant Grid A–J:**

| Var | Empty blocks | Linked-list | MP | Trailer | Full layer |
|-----|-------------|-------------|----|---------|------------|
| A | ✗ | ✗ | ✗ | ✗ | ✗ |
| B | ✓ | ✗ | ✗ | ✗ | ✗ |
| C | ✓ | ✓ | ✗ | ✗ | ✗ |
| D | ✓ | ✓ | ✓ | ✗ | ✗ |
| E | ✓ | ✓ | ✓ | ✓ | ✗ |
| F | ✓ | ✓ | ✓ | ✓ | ✓ |
| G | ✓(native) | ✓ | ✓ | ✓ | ✓ |
| H | ✓ | ✓ | ✓ | ✗ | ✓ |
| I | ✓ | ✓ | ✗ | ✓ | ✓ |
| J | ✗ | ✗ | ✓ | ✓ | ✓ |

**Tool created:** `dev_scripts/vcf_binary_search.py` — generates all variants from a single source VCF by selectively enabling/disabling structural features.

**Preliminary analysis (pre-GUI):** Variant G (native empty block init patch) reduced hex diffs from 2394 regions/3788 bytes to 11 regions/51 bytes. This led to **false hypothesis H6** — that empty block init data was the primary cause.

**Key Blind Spot Reinforced:** The hex diff improvement of variant G (3788→51 bytes) was so dramatic that it *seemed* to confirm empty blocks as the root cause. In reality, G still had the broken trailer — the diff reduction came from matching native empty block padding, but the critical trailer issue was still present in the remaining 51 bytes.

### 2.6 Session 6: GUI Testing & Breakthrough (2026-06-29, afternoon)

**Goal:** Test all variants A–S in real VCutWorks GUI, identify actual root causes.

**Methodology change:** For the first time, the team tested VCF files in the actual target software (VCutWorks) rather than relying on hex diff or reader roundtrip tests.

#### Round 1: Variants A–J

| Variant | VCutWorks Result | Insight |
|---------|-----------------|---------|
| A | no load, black canvas | Minimal structure not enough |
| B | load, no geometry | Empty blocks alone don't help |
| C | load, no geometry | Linked-list alone doesn't help |
| D | load OK, ACI OK, no geometry | MP helps with loading + ACI but geometry missing |
| E | **NO LOAD** | D+trailer causes hard rejection! |
| F | **NO LOAD** | Full current writer also rejected |
| G | **NO LOAD** | Native empties didn't help (not the root cause!) |
| H | load OK, ACI OK, NO GEOMETRY | F-trailer = loads but no geometry |
| I | load, black canvas | No MP = can't even show ACI |
| J | no load | Active-first + trailer = still broken |

**Critical discovery 1:** E fails but D loads. The ONLY difference is the trailer. Therefore: **trailer WITHOUT DXF path data causes hard rejection.**

**Critical discovery 2:** H loads but shows no geometry. H = F minus trailer. Since F has the same active block as H, the issue is not trailer-specific. Therefore: **active block fields cause missing geometry.**

**Critical discovery 3:** G failed despite having native empty block init data. The failure was due to the trailer (same as E, F). Therefore: **H6 (empty block init hypothesis) is DISPROVEN.**

#### Round 2: Patched Variants K–S (breakthrough)

After identifying the two critical areas (trailer and active block), the LLM proposed **patched variants** — injecting native data into synthetic bodies to isolate exactly which bytes are critical.

| Variant | Composition | VCutWorks Result |
|---------|------------|-----------------|
| K | synth body + native trailer | NO LOAD (old active block @92=0, @104=0) |
| L | synth + native DXF path | NO LOAD (same root cause) |
| **M** | **synth + native active block + native trailer** | **✅ WORKS! Geometry, ACI, params all correct!** |
| N | synth + native trailer only | NO LOAD (active block still wrong) |
| O | synth + native active block, no trailer | NO LOAD (trailer missing) |
| **P** | **fixed writer (3 fixes) + demo params** | **✅ LOAD OK, geometry renders** |
| **Q** | **P + native empties** | **✅ LOAD OK (same as P — empties irrelevant)** |
| **R** | **fixed writer + native params + path** | **✅ LOAD OK, params correct (speed=80)** |
| **S** | **fixed writer + native coords + params + path** | **157868B, 0 diffs HEADER/GEOMETRY/TRAILER** |

**Variant M is the definitive proof:** native active block + native trailer = complete solution. The 610B active block contains specific critical fields that the writer was not setting.

#### The 3 Root Causes Identified

1. **Trailer truncated (HARD REJECTION):** `trailer()` only wrote DXF path data when `dxf_source_path` was not None. Once the TRAILER_PREFIX was present, VCutWorks expected valid path data. Empty/missing path → file rejection.

2. **Active block @92=0 (NO GEOMETRY):** Byte @92 in the active layer block stores the element count (`uint8`). Writer left it at 0 (default from `bytearray()`). Native had `@92=1` for single-element VCFs. VCutWorks uses this to locate and display geometry.

3. **Active block @104=0 (NO DIRECTION):** Writer only set direction@104 for V-slot cutters. Native had `direction=2` ("Cut both side") for ALL cutter types, not just V-slot.

**Additional populated fields** (confirmed correct defaults):
- `@40-47`: float64 5.0 (unknown parameter, consistent across all native VCFs)
- `@197`: uint8 64 (0x40, unknown flag)
- `@198-205`: float64 0.5 (unknown parameter)
- `@606`: last-block terminator color = 1 (was 0)

---

## 3. METHODOLOGY EVOLUTION

### 3.1 Phase 1: Intuitive Implementation (Session 1-2)

The initial approach was "implement what we see" — look at native VCF hex, write code that produces similar bytes. This produced a writer that generated structurally correct VCF files (same size, same sections) but with critical semantic errors.

**Failure mode:** The writer produced files that *looked* correct (157KB, same sections as native) but were semantically wrong in ways that hex diff could not distinguish from the 90% of bytes that were truly just padding.

### 3.2 Phase 2: Hex Diff Analysis (Session 3-4)

Hex diff was the first systematic approach — measure every byte difference between native and synthetic. This produced:
- 1055 diff regions identified
- 5 hypotheses formulated
- Multiple fields verified as correct (MACHINE_PROFILE, geometry header)

**Failure mode:** Hex diff is **quantitative**, not **qualitative**. It cannot distinguish between:
- A missing critical field (12 bytes that prevent geometry rendering)
- Missing padding data (3740 bytes that don't matter at all)

The 1055 number was dominated by the latter, creating the illusion that "everything is wrong" when in fact only 3 specific things were wrong.

### 3.3 Phase 3: Binary Search Variants (Session 5-6) — THE BREAKTHROUGH

The LLM proposed a fundamentally different approach: instead of measuring "what's different," ask "what's minimally needed."

**Core innovation:** Generate VCF variants where each variant adds exactly one structural feature. Test each in real VCutWorks. The moment a variant fails (or succeeds), you know precisely which feature caused it.

**Why it worked where hex diff failed:**

1. **Isolation of variables:** Each variant differs from its predecessor by exactly one change. Any difference in behavior maps 1:1 to that change.

2. **Ground truth is VCutWorks, not hex diff:** A file that has 3740 byte diffs but loads correctly is better than a file with 12 byte diffs that doesn't load at all. Hex diff would rank them opposite.

3. **Patched variants eliminate cumulative errors:** When you inject native data into a synthetic body and it works (variant M), you know exactly what was missing. This is like a "binary search" but in feature space rather than code space.

4. **Elimination of false positives:** The 3740 byte empty block diffs were identified as false positives within 2 GUI tests (variants P vs Q produce identical load behavior).

### 3.4 Why the LLM was Essential

The binary search variant methodology was **entirely LLM-proposed**. The human team was focused on hex diff analysis and expanding the writer to cover more fields. The LLM:

1. Recognized that hex diff was a dead end (quantitative ≠ qualitative)
2. Proposing generating variants with systematically varied features
3. Proposed patched variants (injecting native data) to isolate exact byte requirements
4. Suggested specific variant combinations to test (K, L, M, N, O) that directly targeted the two suspect areas

The LLM's ability to step back from the data and see the meta-pattern was critical. A pure human approach would likely have spent weeks populating all fields in the layer block without realizing that only 12 bytes mattered.

---

## 4. BLIND SPOTS ANALYSIS

### 4.1 Blind Spot #1: Hex Diff as Truth (Sessions 1-4)

**The belief:** If we make hex diff go to zero, the file will work.

**The reality:** Hex diff went from 1055 regions to ~12+3740+39 = ~3791 total diff bytes across different versions. The 3740 bytes of empty block diffs were completely irrelevant. Reducing total diff count did not correlate with file loadability.

**Why it was misleading:**
- Empty block init data (3740 bytes) was counted as "critical" because it dominated the diff
- Active block fields (12 bytes) were buried in the noise
- The same diff tool that showed huge numbers also confirmed MACHINE_PROFILE as 0 diffs — creating false confidence in some areas while creating false panic in others

**Lesson:** A diff tool measures *difference*, not *importance*. Always verify findings with behavioral tests in the target system.

### 4.2 Blind Spot #2: Empty Block Init Data (Sessions 4-5)

**The belief:** Variant G reduced diffs from 2394 regions to 11 regions → empty block init data must be the key.

**The reality:** Variant G failed in GUI because of the *trailer*, not the empty blocks. The dramatic diff reduction was real (native empty block data is extensive), but it was irrelevant to VCutWorks loading.

**Why it was seductive:**
- The 2394→11 reduction was the first "success" after weeks of frustration
- It created a clear narrative: "writer missing 3740 bytes of empty block data"
- It took actual GUI testing to disprove — no amount of hex analysis could have revealed it

**Lesson:** A dramatic improvement in one metric (diff count) does not guarantee improvement in the target metric (VCutWorks compatibility). Always validate in the target environment.

### 4.3 Blind Spot #3: Reader Roundtrip Tests (All Sessions)

**The belief:** If our reader can parse what our writer produces, the format is correct.

**The reality:** The reader was built from the same reverse engineering assumptions as the writer. Both were wrong in the same ways. The roundtrip test proved internal consistency, not external correctness.

**The trap:** 28/28 passing tests gave false confidence. The tests verified that writer→reader→compare was consistent, but both writer and reader were bug-compatible.

**Lesson:** Self-consistency is not correctness. You need an independent oracle (VCutWorks GUI) to validate.

### 4.4 Blind Spot #4: "More Native-Like = Better" (Session 2)

**The belief:** Adding more structure (empty blocks, trailer, machine profile) makes the file more native-like and therefore more likely to work.

**The reality:** The minimal 1005-byte file (session 1) loaded in VCutWorks (empty canvas). The 157KB "complete" file (session 2) did not load at all. Adding the trailer introduced a hard rejection that didn't exist before.

**Why this happened:** The added structure triggered new validation paths in VCutWorks. A file without a trailer bypassed trailer validation entirely. A file with a trailer but truncated path data failed that validation.

**Lesson:** In RE, "more complete" can mean "more wrong." Each structural element adds new validation requirements. Progress is not monotonic.

### 4.5 Blind Spot #5: Single-Metric Optimization (All Sessions)

**The belief:** Optimize one metric (diff count) and the problem will be solved.

**The reality:** Three different bugs required three different fixes. No single metric captured all three. Hex diff couldn't find the trailer bug (it just showed "different bytes"). Hex diff couldn't distinguish @92=0 vs @92=1 (a single byte among 157868).

**Lesson:** Complex format compatibility problems are multi-dimensional. A single metric (diff count, test count, file size) cannot capture all dimensions of correctness.

---

## 5. THE BREAKTHROUGH LOGIC

### 5.1 From Variant Grid to Root Cause

The binary search variant methodology worked through logical elimination:

```
A (no features) → black canvas
B (A + empty blocks) → still no geometry
C (B + linked-list) → still no geometry
D (C + MP) → LOADS OK, ACI correct, but NO GEOMETRY
```

At D, we know: header, empty blocks, linked-list, and MP are sufficient for VCutWorks to:
- Parse the file structure ✓
- Identify ACI layers ✓
- Load without error ✓

But geometry is missing. The issue must be in the layer block fields or geometry encoding.

```
E (D + trailer) → NO LOAD (HARD REJECTION)
```

Adding the trailer broke loading. This reveals: VCutWorks validates trailer content strictly when trailer is present.

```
H (F - trailer) → LOADS OK, NO GEOMETRY
```

Removing the trailer restores loading but geometry is still missing. This isolates the geometry problem to the active block (since H has all other features).

### 5.2 Variant M: The Proof

Variant M is the definitive experiment: take a synthetic body (which we know is broken) and patch in ONLY the native active block and native trailer. If this works, then:
- The synthetic body is otherwise correct
- The ONLY problems are in the active block and trailer

Variant M **works perfectly** in VCutWorks. This proves conclusively that the 610B active block and ~200B trailer contain all critical differences. The remaining ~156,000 bytes of the synthetic file are semantically correct.

### 5.3 From Proof to Fix

Once variant M identified the active block as critical, the specific fixes were found by comparing the native 610B block byte-by-byte against the synthetic block:

```python
# BEFORE (broken):
block = bytearray(LAYER_BLOCK_SIZE)
# @92 defaults to 0 (bytearray zero-initialized)
# @104 only set for V-slot

# AFTER (fixed):
struct.pack_into('<B', block, 92, len(layer._paths))  # element count
struct.pack_into('<H', block, 104, dir_val)  # direction for ALL cutter types
struct.pack_into('<d', block, 40, 5.0)  # field_40
struct.pack_into('<B', block, 197, 64)  # field_197
struct.pack_into('<d', block, 198, 0.5)  # field_198
```

For the trailer:
```python
# BEFORE:
if self.dxf_source_path:
    self.data.write(self.dxf_source_path.encode('utf-16-le'))

# AFTER:
path_bytes = self.dxf_source_path.encode('utf-16-le') if self.dxf_source_path else b''
self.data.write(path_bytes)
```

For the terminator:
```python
# BEFORE:
# @606 defaults to 0 (bytearray)

# AFTER:
struct.pack_into('<I', block, 606, 1)  # terminator color = 1
```

---

## 6. FINAL WRITER STATE

### 6.1 What Was Fixed

| Fix | Location | Impact |
|-----|----------|--------|
| trailer() always writes DXF path | `_writer.py:trailer()` | HARD REJECTION resolved |
| direction@104 for ALL cutter types | `_writer.py:encode_layer_block()` | Missing direction resolved |
| element_count@92 = len(layer._paths) | `_writer.py:encode_layer_block()` | NO GEOMETRY resolved |
| field_40@40 = 5.0 | `_writer.py:encode_layer_block()` | Default value conformity |
| field_197@197 = 64 | `_writer.py:encode_layer_block()` | Default value conformity |
| field_198@198 = 0.5 | `_writer.py:encode_layer_block()` | Default value conformity |
| terminator@606 = 1 | `_writer.py:header()` | Linked-list terminator conformity |

### 6.2 What Remains Different

| Location | Writer Value | Native Value | Impact |
|----------|-------------|-------------|--------|
| @176-177 (float64) | 0.0 | ~8e-320 (denormalized) | Semantically identical |
| @184-185 (float64) | 0.0 | ~8e-320 (denormalized) | Semantically identical |
| Empty blocks 0-254 | All zeros | Machine defaults in block 0,1 | NOT critical (GUI confirmed) |

### 6.3 Current Test Status

```
test_writer_unit.py → 23/23 PASS
test_roundtrip.py    → 5/5 PASS (2 SKIP - missing demo files)
Total                → 28/28 PASS
```

### 6.4 Key Constants (Post-Fix)

```python
LAYER_BLOCK_SIZE  = 610
EMPTY_BLOCK_COUNT = 256
STOCK_WIDTH       = 1220.0  # mm
STOCK_HEIGHT      = 2900.0  # mm

# Critical layer block offsets:
OFFSET_ELEMENT_COUNT = 92   # uint8
OFFSET_DIRECTION     = 104  # uint16
OFFSET_FIELD_40      = 40   # float64 = 5.0
OFFSET_FIELD_197     = 197  # uint8 = 64
OFFSET_FIELD_198     = 198  # float64 = 0.5
OFFSET_TERMINATOR    = 606  # uint32 = 1 (for last block)
```

---

## 7. IMPLICATIONS FOR FUTURE RE WORK

### 7.1 Methodology Recommendations

1. **Always test in the target environment early.** Hex diff and reader roundtrip tests cannot substitute for real behavior in the target software.

2. **Use binary search on features, not just code.** The variant methodology isolates which structural elements matter, not just which code paths execute.

3. **Patched variants are powerful.** Injecting known-good data into a broken system isolates the exact bytes that need fixing.

4. **One metric is never enough.** Track multiple metrics: loading behavior, geometry rendering, parameter correctness, byte-level diff, test pass rate.

5. **LLM-human collaboration works.** The LLM's ability to propose novel methodologies (binary search variants, patched variants) combined with human ability to execute GUI tests created a synergy that neither could achieve alone.

### 7.2 LLM Collaboration Lessons

- **The LLM recognized patterns across sessions** that the human team missed (e.g., that hex diff was misleading because it conflated empty block padding with critical fields)
- **The LLM proposed the binary search variant methodology** — a meta-solution that changed *how* we debugged, not just *what* we debugged
- **The LLM suggested specific variant combinations** (K through O) that directly targeted the two suspect areas (trailer and active block fields)
- **The human role was execution**: generating variants, testing in VCutWorks GUI, and implementing the identified fixes

This division of labor — LLM for meta-cognition and strategy, human for execution and domain-specific testing — proved highly effective.

---

## 8. OPEN QUESTIONS & FUTURE WORK

### 8.1 Immediate

- [ ] Regenerate ALL synthetic VCFs via DXF pipeline with fixed writer (compile_dxf)
- [ ] GUI test multi-layer VCFs (manchester_3_subjobs, fishbone)
- [ ] GUI test circle element rendering (4-segment vs 1-segment encoding)
- [ ] Verify element count (@92) for multi-element layers

### 8.2 Short-term

- [ ] Build pywinauto GUI oracle for automated regression testing
- [ ] Create Kaitai Struct .ksy schema for VCF format
- [ ] Fix reader for color@12 compatibility with native VCFs
- [ ] Investigate fishbone element discrepancy (41 vs 14 elements)

### 8.3 Long-term

- [ ] Populate empty block init data with machine defaults for completeness
- [ ] Investigate field_40/197/198 semantics (what do these values control?)
- [ ] Test on different machine profiles (not just RDD6584G)
- [ ] Version negotiation for 1.0.012 vs 1.0.013 compatibility

---

## 9. GLOSSARY

| Term | Definition |
|------|-----------|
| Active block | The last 610-byte layer block containing actual cutting data (not empty padding) |
| Empty blocks | 256 leading 610-byte blocks that serve as padding/placeholders (all zeros in native or with machine defaults) |
| Linked-list | 8-byte pointer at offsets 602-609 of each layer block: 4B next_flag + 4B next_color |
| MACHINE_PROFILE | 418-byte machine-specific configuration embedded in the header |
| TRAILER_PREFIX | 199-byte constant trailer header preceding DXF path data |
| GEOMETRY_SIG | 8-byte geometry signature: `\x01\x00\x01\x00\x00\xff\xff\xff` |
| Variant | A VCF file generated with specific combination of structural features for testing |
| Patched variant | A variant where native data is injected into specific byte ranges of the synthetic body |
| Binary search methodology | The process of generating variants with incrementally added features, testing each in VCutWorks |
| Hex diff | Binary comparison showing every byte that differs between two files |
| Hex diff report | `hex_diff_report.md` — full documentation of 1055 diff regions |

---

## 10. APPENDIX: Variant Grid Summary

### A–J: Original binary search (incremental features)

```
     Empty   L-Link   MP      Trailer  Layer    Result
A    ✗       ✗        ✗       ✗        ✗        no load
B    ✓       ✗        ✗       ✗        ✗        load, no geom
C    ✓       ✓        ✗       ✗        ✗        load, no geom
D    ✓       ✓        ✓       ✗        ✗        load OK, ACI OK, no geom
E    ✓       ✓        ✓       ✓        ✗        NO LOAD ← trailer!
F    ✓       ✓        ✓       ✓        ✓        NO LOAD
G    native   ✓        ✓       ✓        ✓        NO LOAD
H    ✓       ✓        ✓       ✗        ✓        load OK, no geom
I    ✓       ✓        ✗       ✓        ✓        load, black canvas
J    ✗       ✗        ✓       ✓        ✓        no load
```

### K–S: Patched & fixed variants

```
     Composition                          Result
K    synth + native trailer               NO LOAD
L    synth + native DXF path              NO LOAD
M    synth + native active + trailer      ✅ WORKS ← PROOF
N    synth + native trailer only          NO LOAD
O    synth + native active, no trailer    NO LOAD
P    fixed writer + demo params           ✅ WORKS
Q    P + native empties                   ✅ WORKS
R    fixed writer + native params         ✅ WORKS
S    fixed writer + native coords+path    ✅ WORKS, 0 diffs
```

---

*End of document — 2026-06-29*
