import os
from pathlib import Path
import numpy as np
import cv2
import csv
import random

# Set a seed for reproducibility (optional)
random.seed(42)
np.random.seed(42)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLEAN_DIR = PROJECT_ROOT / "dataset" / "clean"
STEGO_BASE_DIR = PROJECT_ROOT / "dataset" / "stego"

# Payload ratios (5%, 10%, 25% of pixels)
PAYLOAD_RATIOS = {
    "5percent": 0.05,
    "10percent": 0.10,
    "25percent": 0.25,
}

def embed_random_lsb_png(input_path: Path, output_path: Path, payload_ratio: float, channel: int = 0):
    img = cv2.imread(str(input_path), cv2.IMREAD_UNCHANGED)

    if img is None:
        print(f"Warning: could not read {input_path}")
        return False

    # Handle grayscale vs RGB(A)
    if img.ndim == 2:
        # Grayscale: add fake channel axis
        h, w = img.shape
        img = img.reshape(h, w, 1)
    h, w, c = img.shape

    if channel >= c:
        # If requested channel doesn't exist, just use the last channel
        channel = c - 1

    # Work on a copy
    stego = img.copy()
    chan = stego[:, :, channel]

    total_pixels = h * w
    num_payload_bits = int(total_pixels * payload_ratio)

    if num_payload_bits == 0:
        print(f"Payload ratio too small for {input_path}, skipping.")
        return False

    # Flatten indices and randomly pick which pixels to modify
    all_indices = np.arange(total_pixels)
    np.random.shuffle(all_indices)
    selected_indices = all_indices[:num_payload_bits]

    # Generate random bits to embed
    payload_bits = np.random.randint(0, 2, size=num_payload_bits, dtype=np.uint8)

    # Flatten the channel for easy indexing
    flat_chan = chan.flatten()

    # Clear LSB and set to payload bit
    # new_value = (old_value & 0b11111110) | bit
    flat_chan[selected_indices] = (flat_chan[selected_indices] & 0xFE) | payload_bits

    # Reshape back to 2D
    stego[:, :, channel] = flat_chan.reshape(h, w)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save as PNG
    success = cv2.imwrite(str(output_path), stego)
    if not success:
        print(f"Error: could not write stego image {output_path}")
    return success

def main():
    # Prepare CSV log of what we created
    log_path = STEGO_BASE_DIR / "stego_mapping.csv"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["clean_image", "stego_image", "payload_label", "payload_ratio"])

        png_files = sorted(CLEAN_DIR.glob("*.png"))

        if not png_files:
            print(f"No PNG files found in {CLEAN_DIR}")
            return

        for clean_path in png_files:
            clean_name = clean_path.name
            stem = clean_path.stem

            for label, ratio in PAYLOAD_RATIOS.items():
                out_dir = STEGO_BASE_DIR / label
                out_dir.mkdir(parents=True, exist_ok=True)

                out_name = f"{stem}_{label}.png"
                out_path = out_dir / out_name

                ok = embed_random_lsb_png(
                    input_path=clean_path,
                    output_path=out_path,
                    payload_ratio=ratio,
                    channel=0,  # blue channel (0=B, 1=G, 2=R) if RGB
                )

                if ok:
                    writer.writerow([clean_name, out_name, label, ratio])

    print("Stego generation complete.")
    print(f"Log saved to: {log_path}")

if __name__ == "__main__":
    main()

