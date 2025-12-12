import csv
import statistics
from collections import defaultdict
from pathlib import Path
import re
import math

from detect_lsb import (
    extract_lsb,
    chi_square_test,
    rs_analysis,
    sample_pair_stat,
)

PROJECT = Path(__file__).resolve().parents[1]

CLEAN_DIR = PROJECT / "dataset" / "clean"
STEGO_DIR = PROJECT / "dataset" / "stego"
OUTPUT_CSV = PROJECT / "results" / "analysis_results.csv"


def process_image(image_path, label):
    # Extract LSBs for chi-square and sample-pair
    lsbs = extract_lsb(str(image_path))

    # Chi-square statistics (block-based + bias)
    # chi_square_test is expected to return:
    #   chi_mean, chi_std, chi_frac_sig, chi_bias
    chi_mean, chi_std, chi_frac_sig, chi_bias = chi_square_test(lsbs)

    # Multi-mask RS analysis (expected to return RS_mean, RS_std)
    RS_mean, RS_std = rs_analysis(str(image_path))

    # Sample-pair statistics
    sp_ratio, sp_dev = sample_pair_stat(lsbs)

    return {
        "filename": image_path.name,   # just the file name, used for matching
        "label": label,                # "clean", "5percent", "10percent", "25percent"
        "chi_mean": chi_mean,
        "chi_std": chi_std,
        "chi_frac_p_lt_0_05": chi_frac_sig,
        "chi_bias": chi_bias,
        "RS_mean": RS_mean,
        "RS_std": RS_std,
        "SP_equal_ratio": sp_ratio,
        "SP_dev_from_0_5": sp_dev,
        # will fill in later:
        # "suspicious_score": ...
        # "susp_z": ...
    }


def get_base_name(fname: str) -> str:
    """
    Extract base filename:
        img001.png           -> img001
        img001_5percent.png  -> img001
        img001_10percent.png -> img001
        img001_25percent.png -> img001
    """
    stem = fname.rsplit(".", 1)[0]  # remove extension
    stem = re.sub(r"_(5percent|10percent|25percent)$", "", stem)
    return stem


def summarize_by_label(rows):
    labels = sorted({row["label"] for row in rows})
    metrics = ["chi_mean", "RS_mean", "SP_equal_ratio", "SP_dev_from_0_5", "suspicious_score"]

    print("\n=== Per-label summary (means) ===")
    for label in labels:
        subset = [r for r in rows if r["label"] == label]
        print(f"\nLabel: {label}  (n={len(subset)})")
        for m in metrics:
            values = [r[m] for r in subset]
            mean_val = statistics.mean(values) if values else float("nan")
            print(f"  {m:18s}: {mean_val:.4f}")


def summarize_detection(rows, thresholds=(0.05, 0.1, 0.2)):
    clean = [r for r in rows if r["label"] == "clean"]
    stego = [r for r in rows if r["label"] != "clean"]

    if not clean or not stego:
        print("\n[Detection summary] Not enough data to compute (need both clean and stego).")
        return

    print("\n=== Detection performance (using suspicious_score) ===")
    print(f"Total clean images: {len(clean)}")
    print(f"Total stego images: {len(stego)}")

    for thresh in thresholds:
        tp = sum(r["suspicious_score"] >= thresh for r in stego)
        fn = len(stego) - tp
        fp = sum(r["suspicious_score"] >= thresh for r in clean)
        tn = len(clean) - fp

        tpr = tp / len(stego) if stego else 0.0
        fpr = fp / len(clean) if clean else 0.0

        print(f"\nThreshold = {thresh:.2f}")
        print(f"  TPR (recall on stego): {tpr:.3f}")
        print(f"  FPR (false alarm rate): {fpr:.3f}")
        print(f"  TP={tp}, FN={fn}, FP={fp}, TN={tn}")


def summarize_detection_per_payload(rows, thresholds=(0.05, 0.1, 0.2)):
    clean = [r for r in rows if r["label"] == "clean"]
    payload_labels = ["5percent", "10percent", "25percent"]

    if not clean:
        print("\n[Per-payload detection] No clean images found; cannot compute FPR.")
        return

    print("\n=== Detection by payload level (using suspicious_score) ===")
    print(f"Total clean images: {len(clean)}")
    for pl in payload_labels:
        count_pl = sum(r["label"] == pl for r in rows)
        print(f"Total {pl} images: {count_pl}")

    for thresh in thresholds:
        print(f"\nThreshold = {thresh:.2f}")

        # False positives on clean (same for all payloads at this threshold)
        fp = sum(r["suspicious_score"] >= thresh for r in clean)
        fpr = fp / len(clean) if len(clean) else 0.0
        print(f"  Clean false-positive rate: {fpr:.3f} (FP={fp}/{len(clean)})")

        # Per-payload true positive rate
        for pl in payload_labels:
            subset = [r for r in rows if r["label"] == pl]
            if not subset:
                continue
            tp = sum(r["suspicious_score"] >= thresh for r in subset)
            fn = len(subset) - tp
            tpr = tp / len(subset) if subset else 0.0
            print(
                f"  Payload {pl:9s}: TPR={tpr:.3f} "
                f"(TP={tp}/{len(subset)}, FN={fn})"
            )


# --- Confidence interval helpers ---

def mean_ci(values, confidence=0.95):
    n = len(values)
    mean = statistics.mean(values)
    std = statistics.pstdev(values)
    z = 1.96  # 95%
    margin = z * std / math.sqrt(n)
    return mean, mean - margin, mean + margin


def summarize_confidence_intervals(rows):
    labels = ["clean", "5percent", "10percent", "25percent"]
    metrics = ["suspicious_score", "chi_mean", "RS_mean", "SP_equal_ratio", "SP_dev_from_0_5"]

    print("\n=== 95% Confidence Intervals by Label ===")

    for label in labels:
        subset = [r for r in rows if r["label"] == label]
        print(f"\nLabel: {label} (n={len(subset)})")

        for m in metrics:
            vals = [r[m] for r in subset]
            mean, lower, upper = mean_ci(vals)
            print(f"  {m:18s}: mean={mean:.4f}, CI=({lower:.4f}, {upper:.4f})")


def ci_wilson(successes, total, z=1.96):
    if total == 0:
        return 0, 0, 0
    p = successes / total
    denom = 1 + (z**2 / total)
    center = p + (z**2 / (2 * total))
    margin = z * math.sqrt((p * (1 - p) / total) + (z**2 / (4 * total**2)))
    lower = (center - margin) / denom
    upper = (center + margin) / denom
    return p, lower, upper


def summarize_detection_ci(rows, thresholds=(0.05, 0.1, 0.2)):
    clean = [r for r in rows if r["label"] == "clean"]
    payload_labels = ["5percent", "10percent", "25percent"]

    print("\n=== 95% Confidence Intervals for Detection Rates ===")

    for thresh in thresholds:
        print(f"\nThreshold = {thresh:.2f}")

        # Clean false positives
        fp = sum(r["suspicious_score"] >= thresh for r in clean)
        p, lo, hi = ci_wilson(fp, len(clean))
        print(f"  Clean FPR: {p:.3f}, CI=({lo:.3f}, {hi:.3f})")

        # Per-payload TPRs
        for pl in payload_labels:
            subset = [r for r in rows if r["label"] == pl]
            tp = sum(r["suspicious_score"] >= thresh for r in subset)
            p, lo, hi = ci_wilson(tp, len(subset))
            print(f"  {pl:10s} TPR: {p:.3f}, CI=({lo:.3f}, {hi:.3f})")


def main():
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    rows = []

    # --- Pass 1: collect raw metrics for all images ---

    # Process clean images
    for img in CLEAN_DIR.glob("*.png"):
        rows.append(process_image(img, "clean"))

    # Process each stego payload directory
    for folder in ["5percent", "10percent", "25percent"]:
        path = STEGO_DIR / folder
        for img in path.glob("*.png"):
            rows.append(process_image(img, folder))

    if not rows:
        print("No images processed, CSV not written.")
        return

    # --- Pass 2: compute raw suspicious scores by comparing to clean baseline ---

    groups: dict[str, dict[str, int]] = defaultdict(dict)

    for idx, row in enumerate(rows):
        fname = row["filename"]
        label = row["label"]
        base = get_base_name(fname)
        groups[base][label] = idx

    # Initialize raw suspicious scores to 0 for all images (clean or unmatched)
    for row in rows:
        row["raw_suspicious_score"] = 0.0

    # For each base name that has a clean version, compare its stego variants
    for base, labels_dict in groups.items():
        if "clean" not in labels_dict:
            continue

        clean_idx = labels_dict["clean"]
        clean_row = rows[clean_idx]

        clean_sp = clean_row["SP_dev_from_0_5"]
        clean_chi = clean_row["chi_mean"]
        clean_rs = clean_row["RS_mean"]

        for stego_label in ["5percent", "10percent", "25percent"]:
            if stego_label not in labels_dict:
                continue

            stego_idx = labels_dict[stego_label]
            stego_row = rows[stego_idx]

            stego_sp = stego_row["SP_dev_from_0_5"]
            stego_chi = stego_row["chi_mean"]
            stego_rs = stego_row["RS_mean"]

            # Deltas: how far has this stego image moved away from its clean baseline
            sp_delta = max(clean_sp - stego_sp, 0.0)
            chi_delta = max(clean_chi - stego_chi, 0.0)
            rs_delta = max(clean_rs - stego_rs, 0.0)

            # Weighted combination into a raw suspicious score
            raw_score = 0.5 * sp_delta + 0.3 * chi_delta + 0.2 * rs_delta
            rows[stego_idx]["raw_suspicious_score"] = raw_score

    # --- Pass 3: normalize raw suspicious scores into [0, 1] and add z-score ---

    raw_scores = [row["raw_suspicious_score"] for row in rows]
    min_raw = min(raw_scores)
    max_raw = max(raw_scores)

    if max_raw > min_raw:
        for row in rows:
            raw = row["raw_suspicious_score"]
            norm = (raw - min_raw) / (max_raw - min_raw)
            row["suspicious_score"] = float(norm)
    else:
        for row in rows:
            row["suspicious_score"] = 0.0

    scores = [row["suspicious_score"] for row in rows]
    mean_score = statistics.mean(scores)
    std_score = statistics.pstdev(scores) if len(scores) > 1 else 0.0

    for row in rows:
        if std_score > 0.0:
            z = (row["suspicious_score"] - mean_score) / std_score
        else:
            z = 0.0
        row["susp_z"] = float(z)

    # --- Summaries for report ---

    summarize_by_label(rows)
    summarize_detection(rows, thresholds=(0.05, 0.10, 0.20))
    summarize_detection_per_payload(rows, thresholds=(0.05, 0.10, 0.20))
    summarize_confidence_intervals(rows)
    summarize_detection_ci(rows, thresholds=(0.05, 0.10, 0.20))

    # --- Cleanup and write CSV ---

    for row in rows:
        del row["raw_suspicious_score"]

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print("\nAnalysis complete →", OUTPUT_CSV)



if __name__ == "__main__":
    main()

