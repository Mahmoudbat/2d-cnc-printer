import subprocess
import sys
import cv2
import os
from PIL import Image

# Configuration
script_dir = os.path.dirname(os.path.abspath(__file__))
temp_dir = os.path.join(script_dir, "../Temp")
input_png = os.path.join(temp_dir, "input.png")
input_jpg = os.path.join(temp_dir, "input.jpg")
output = os.path.join(temp_dir, "output")

# Use PNG if available and convert to JPG
if os.path.exists(input_png):
    # Convert to JPG
    img = Image.open(input_png).convert("RGB")
    img.save(input_jpg, "JPEG")
    print(f"✅ Converted PNG to JPG: {input_jpg}")

input_p = input_jpg  # Use JPG as input

# 1. Load image
img = cv2.imread(input_p, cv2.IMREAD_GRAYSCALE)
if img is None:
    print(f"❌ Error: Could not read {input_p}")
    sys.exit(1)

# 2. Binarize using Otsu's thresholding
_, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# 3. Save as PBM (for Potrace)
pbm_path = output + '.pbm'
cv2.imwrite(pbm_path, binary)

# 4. Convert PBM to SVG with Potrace
result = subprocess.run(["potrace", pbm_path, "-s", "-o", output + ".svg"])
if result.returncode != 0:
    print("❌ Potrace failed")
    sys.exit(1)

print("✅ SVG file created at:", output + ".svg")