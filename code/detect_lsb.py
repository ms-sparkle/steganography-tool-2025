import cv2
import numpy as np
from scipy.stats import chisquare

# Limit number of bits analyzed per image for speed
MAX_BITS = 10_000

# -------------------------------
# LSB Extraction
# -------------------------------
def extract_lsb(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not read image: " + image_path)

    # Extract blue channel
    blue = img[:, :, 0].flatten()

    # Extract LSBs
    lsbs = blue & 1

    # Limit size for performance
    if lsbs.size > MAX_BITS:
        lsbs = lsbs[:MAX_BITS]

    return lsbs


# -------------------------------
# Chi-Square Test
# -------------------------------
def chi_square_test(lsb_array, block_size=32):
    n = len(lsb_array)
    if n == 0:
        return 0.0, 0.0, 0.0, 0.0  # mean_chi, std_chi, frac_sig, mean_bias

    if n < block_size:
        counts = np.bincount(lsb_array, minlength=2)
        total = counts.sum()
        expected = [total * 0.5, total * 0.5]
        chi, p = chisquare(counts, f_exp=expected)

        # bias for this tiny block
        prop_1 = counts[1] / total if total > 0 else 0.0
        bias = abs(prop_1 - 0.5)

        frac_sig = 1.0 if p < 0.05 else 0.0
        return float(chi), 0.0, float(frac_sig), float(bias)

    n_blocks = n // block_size
    trimmed = lsb_array[:n_blocks * block_size].reshape(n_blocks, block_size)

    chi_values = []
    p_values = []
    bias_values = []

    for block in trimmed:
        counts = np.bincount(block, minlength=2)
        total = counts.sum()
        expected = [total * 0.5, total * 0.5]
        chi, p = chisquare(counts, f_exp=expected)

        chi_values.append(chi)
        p_values.append(p)

        # LSB bias for this block
        prop_1 = counts[1] / total if total > 0 else 0.0
        bias_values.append(abs(prop_1 - 0.5))

    chi_values = np.array(chi_values)
    p_values = np.array(p_values)
    bias_values = np.array(bias_values)

    mean_chi = float(chi_values.mean())
    std_chi = float(chi_values.std())
    frac_sig = float((p_values < 0.05).mean())
    mean_bias = float(bias_values.mean())

    return mean_chi, std_chi, frac_sig, mean_bias
# -------------------------------
# RS Analysis
# -------------------------------
import cv2
import numpy as np

MAX_BITS = 10_000
# assumes MAX_BITS is already defined above in your file

def rs_analysis(image_path, group_size=4):
    """
    RS analysis with multiple flip masks on 4-pixel groups.
    Returns a single scalar: mean normalized RS score across masks.
    """
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not read: " + image_path)

    # Use blue channel, same as your other code
    blue = img[:, :, 0].astype(np.int16)
    flat = blue.flatten()

    # Limit to a fixed number of bits/groups for consistency
    max_groups = MAX_BITS // group_size
    if flat.size > max_groups * group_size:
        flat = flat[:max_groups * group_size]

    n = len(flat) // group_size
    if n == 0:
        return 0.0

    groups = flat[:n * group_size].reshape(-1, group_size)

    # Discrimination function: sum of absolute differences between neighbors
    def discr(g):
        return np.sum(np.abs(np.diff(g)))

    orig_D = np.apply_along_axis(discr, 1, groups)

    # Multiple flip masks: which pixels in the group to flip
    # 1 = flip that pixel's LSB, 0 = leave it
    masks = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
        [1, 1, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 1, 1],
        [1, 0, 1, 0],
    ], dtype=np.int8)

    rs_values = []

    for mask in masks:
        flipped = groups.copy()

        # Flip LSBs according to the mask
        for i in range(group_size):
            if mask[i]:
                flipped[:, i] ^= 1

        flipped_D = np.apply_along_axis(discr, 1, flipped)

        R = np.sum(flipped_D > orig_D)  # regular groups
        S = np.sum(flipped_D < orig_D)  # singular groups

        if R + S == 0:
            rs_norm = 0.0
        else:
            rs_norm = (R - S) / (R + S)

        rs_values.append(rs_norm)

    rs_values = np.array(rs_values, dtype=np.float64)

    # You can also return rs_values.std() if you want a second feature
    RS_mean = float(rs_values.mean())
    RS_std = float(rs_values.std())
    return RS_mean, RS_std

# -------------------------------
# Sample Pair Analysis
# -------------------------------
def sample_pair_stat(lsb_array):
    if len(lsb_array) < 2:
        return None, None

    n = len(lsb_array) // 2
    pairs = lsb_array[:2 * n].reshape(-1, 2)

    equal_pairs = np.sum(pairs[:, 0] == pairs[:, 1])
    total_pairs = pairs.shape[0]

    pair_equal_ratio = equal_pairs / total_pairs
    deviation_from_half = abs(pair_equal_ratio - 0.5)

    return float(pair_equal_ratio), float(deviation_from_half)

# -------------------------------
# Suspicious Score Calculation
# -------------------------------
def suspicious_score(lsb_array, image_path):

    stego_rs = rs_analysis(str(image_path))
    stego_sp = sample_pair_stat(lsb_array)
    stego_chi = chi_square_test(lsb_array)

    clean_lsb = extract_lsb("dataset/clean/img004.png")

    clean_rs = rs_analysis("dataset/clean/img004.png")
    clean_sp = sample_pair_stat(clean_lsb)
    clean_chi = chi_square_test(clean_lsb)

    # Deltas: how far has this stego image moved away from its clean baseline
    sp_delta = max(clean_sp - stego_sp, 0.0)
    chi_delta = max(clean_chi - stego_chi, 0.0)
    rs_delta = max(clean_rs - stego_rs, 0.0)

    # Weighted combination into a raw suspicious score
    raw_score = 0.5 * sp_delta + 0.3 * chi_delta + 0.2 * rs_delta
    return raw_score