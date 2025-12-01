import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
CSV = PROJECT / "results" / "analysis_results.csv"
RESULT_DIR = PROJECT / "results" / "graphs"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(CSV)
labels = ["clean", "5percent", "10percent", "25percent"]

# --- 1. Chi-square mean distribution ---
plt.figure()
for label in labels:
    subset = df[df["label"] == label]
    plt.hist(subset["chi_mean"], alpha=0.5, bins=20, label=label)
plt.title("Chi-Square Statistic (mean) distribution")
plt.xlabel("chi_mean")
plt.ylabel("Count")
plt.legend()
plt.tight_layout()
plt.savefig(RESULT_DIR / "chi_mean_distribution.png")

# --- 2. RS_mean boxplot ---
plt.figure()
plt.boxplot(
    [
        df[df["label"] == "clean"]["RS_mean"],
        df[df["label"] == "5percent"]["RS_mean"],
        df[df["label"] == "10percent"]["RS_mean"],
        df[df["label"] == "25percent"]["RS_mean"],
    ],
    labels=["clean", "5%", "10%", "25%"],
)
plt.title("RS Mean Across Payload Levels")
plt.ylabel("RS_mean")
plt.tight_layout()
plt.savefig(RESULT_DIR / "rs_mean_boxplot.png")

# --- 3. Sample Pair equal ratio distribution ---
plt.figure()
for label in labels:
    subset = df[df["label"] == label]
    plt.hist(subset["SP_equal_ratio"], alpha=0.5, bins=20, label=label)
plt.title("Sample Pair Equal-Ratio Distribution")
plt.xlabel("SP_equal_ratio")
plt.ylabel("Count")
plt.legend()
plt.tight_layout()
plt.savefig(RESULT_DIR / "sample_pair_equal_ratio.png")

# --- 4. Deviation from 0.5 (how 'random' pairs look) ---
plt.figure()
plt.boxplot(
    [
        df[df["label"] == "clean"]["SP_dev_from_0_5"],
        df[df["label"] == "5percent"]["SP_dev_from_0_5"],
        df[df["label"] == "10percent"]["SP_dev_from_0_5"],
        df[df["label"] == "25percent"]["SP_dev_from_0_5"],
    ],
    labels=["clean", "5%", "10%", "25%"],
)
plt.title("Sample Pair Deviation from 0.5")
plt.ylabel("|SP_equal_ratio - 0.5|")
plt.tight_layout()
plt.savefig(RESULT_DIR / "sample_pair_deviation.png")

# --- 5. Suspicious score by label (boxplot) ---
plt.figure()
plt.boxplot(
    [
        df[df["label"] == "clean"]["suspicious_score"],
        df[df["label"] == "5percent"]["suspicious_score"],
        df[df["label"] == "10percent"]["suspicious_score"],
        df[df["label"] == "25percent"]["suspicious_score"],
    ],
    labels=["clean", "5%", "10%", "25%"],
)
plt.title("Suspicious Score by Label")
plt.ylabel("suspicious_score")
plt.tight_layout()
plt.savefig(RESULT_DIR / "suspicious_score_boxplot.png")

# --- 6. Suspicious score histograms ---
plt.figure()
for label in labels:
    subset = df[df["label"] == label]
    plt.hist(subset["suspicious_score"], alpha=0.5, bins=20, label=label)
plt.title("Suspicious Score Distribution")
plt.xlabel("suspicious_score")
plt.ylabel("Count")
plt.legend()
plt.tight_layout()
plt.savefig(RESULT_DIR / "suspicious_score_hist.png")
