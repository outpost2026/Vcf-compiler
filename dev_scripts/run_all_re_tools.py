"""
run_all_re_tools.py — Run all high-SNR RE tools against both datasets via subprocess.

Usage:
    python dev_scripts/run_all_re_tools.py
"""

import sys, os, json, shutil, subprocess, logging
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
OUT_BASE = REPO / "research_docs"

DATASETS = {
    "moodpasta": Path(r"C:\Users\PC\Documents\Repozitar_Dev\_github\VCF_files_moodpasta"),
    "vcutworks_native": REPO / "demo_data" / "native_vcf" / "Compile_vcutworks_native_vcf",
}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PYTHON = sys.executable


def run_script(script_name: str, args: list, cwd=None):
    script_path = HERE / script_name
    cmd = [PYTHON, str(script_path)] + args
    logger.info("  Running: %s", " ".join(str(a) for a in cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or REPO)
    if result.returncode != 0:
        logger.error("  FAILED (rc=%d): %s", result.returncode, result.stderr[:500])
        return None
    return result.stdout


def run_dissect_footers(vcf_dir: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info("=== dissect_footers: %s ===", vcf_dir)
    # Tool writes to research_docs/ by default; run and copy
    run_script("dissect_footers.py", ["--dir", str(vcf_dir)])
    # Copy output files
    for f in REPO.glob("research_docs/RESULT_footer*"):
        shutil.copy2(f, out_dir / f.name)
        logger.info("  Copied: %s -> %s", f.name, out_dir.name)


def run_decode_subtype_bits(vcf_dir: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info("=== decode_subtype_bits: %s ===", vcf_dir)
    run_script("decode_subtype_bits.py", ["--dir", str(vcf_dir)])
    for f in REPO.glob("research_docs/RESULT_subtype*"):
        shutil.copy2(f, out_dir / f.name)
        logger.info("  Copied: %s -> %s", f.name, out_dir.name)


def run_diagnose_multi_element(vcf_dir: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info("=== diagnose_multi_element: %s ===", vcf_dir)
    stdout = run_script("diagnose_multi_element.py", ["--path", str(vcf_dir)])
    if stdout:
        (out_dir / "diagnosis_output.txt").write_text(stdout, encoding="utf-8")
        logger.info("  Output saved: diagnosis_output.txt")


def run_segment_geometry_stats(vcf_dir: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info("=== segment_geometry_stats: %s ===", vcf_dir)
    run_script("segment_geometry_stats.py", ["--dir", str(vcf_dir)])
    for f in REPO.glob("research_docs/RESULT_segment*"):
        shutil.copy2(f, out_dir / f.name)
        logger.info("  Copied: %s -> %s", f.name, out_dir.name)


def run_element_types_catalog(vcf_dirs: list, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info("=== build_element_types_catalog: combined ===")
    # This tool has no --dir flag; it scans hardcoded paths.
    # Run with defaults then copy.
    run_script("build_element_types_catalog.py", [])
    for f in REPO.glob("research_docs/element_types_catalog*"):
        shutil.copy2(f, out_dir / f.name)
        logger.info("  Copied: %s -> %s", f.name, out_dir.name)


def run_dissect_layer_blocks(vcf_dir: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info("=== dissect_layer_blocks: %s ===", vcf_dir)
    # This tool has only --file flag — run without args (processes default paths), then copy
    run_script("dissect_layer_blocks.py", [])
    for f in REPO.glob("research_docs/RESULT_layer*"):
        shutil.copy2(f, out_dir / f.name)
        logger.info("  Copied: %s -> %s", f.name, out_dir.name)


def run_batch_correlate(vcf_dir: Path, dxf_dir: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.info("=== batch_correlate_dxf_vcf: %s ===", vcf_dir)
    run_script("batch_correlate_dxf_vcf.py", [
        "--vcf-dir", str(vcf_dir),
        "--dxf-dir", str(dxf_dir),
    ])
    for f in REPO.glob("research_docs/RESULT_correlation*"):
        shutil.copy2(f, out_dir / f.name)
        logger.info("  Copied: %s -> %s", f.name, out_dir.name)


def main():
    logger.info("Starting RE tool run on %d datasets", len(DATASETS))

    for name, vcf_dir in DATASETS.items():
        logger.info("\n%s", "=" * 60)
        logger.info("DATASET: %s  (%s)", name, vcf_dir)
        logger.info("%s", "=" * 60)

        if not vcf_dir.exists():
            logger.warning("  SKIP: directory not found: %s", vcf_dir)
            continue

        base_out = OUT_BASE / f"RE_{name}"

        run_dissect_footers(vcf_dir, base_out / "dissect_footers")
        run_decode_subtype_bits(vcf_dir, base_out / "decode_subtype_bits")
        run_diagnose_multi_element(vcf_dir, base_out / "diagnose_multi_element")
        run_segment_geometry_stats(vcf_dir, base_out / "segment_geometry_stats")
        run_dissect_layer_blocks(vcf_dir, base_out / "dissect_layer_blocks")

    # Element types catalog — combined across all datasets
    elem_out = OUT_BASE / "RE_combined" / "element_types_catalog"
    run_element_types_catalog(
        [d for d in DATASETS.values() if d.exists()],
        elem_out,
    )

    # Correlation — only for vcutworks_native (has DXF counterparts)
    if DATASETS["vcutworks_native"].exists():
        dxf_dir = REPO / "demo_data" / "dxf_original"
        corr_out = OUT_BASE / "RE_vcutworks_native" / "correlation"
        run_batch_correlate(DATASETS["vcutworks_native"], dxf_dir, corr_out)

        # Also correlate moodpasta files if they have DXF counterparts
        if DATASETS["moodpasta"].exists():
            corr_out2 = OUT_BASE / "RE_moodpasta" / "correlation"
            # moodpasta DXFs might be elsewhere; try with dxf_original first
            run_batch_correlate(DATASETS["moodpasta"], dxf_dir, corr_out2)

    logger.info("\n=== ALL DONE ===")
    logger.info("Output directories:")
    for name in DATASETS:
        d = OUT_BASE / f"RE_{name}"
        if d.exists():
            for sub in sorted(d.iterdir()):
                if sub.is_dir():
                    files = list(sub.glob("*"))
                    logger.info("  %s/ (%d files)", sub.relative_to(OUT_BASE), len(files))
    d = OUT_BASE / "RE_combined"
    if d.exists():
        for sub in sorted(d.iterdir()):
            if sub.is_dir():
                files = list(sub.glob("*"))
                logger.info("  %s/ (%d files)", sub.relative_to(OUT_BASE), len(files))


if __name__ == "__main__":
    main()
