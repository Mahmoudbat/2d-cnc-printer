import subprocess
import cv2
import sys
import os
from PIL import Image

# Configuration
temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../Temp")
input_png = os.path.join(temp_dir, "input.png")
input_jpg = os.path.join(temp_dir, "input.jpg")
output = os.path.join(temp_dir, "output")
verbose = False #toggle if debugging

# convert png to jpg if available
if os.path.exists(input_png):
    img = Image.open(input_png).convert("RGB")
    img.save(input_jpg, "JPEG")
    if verbose:   
        if not os.path.exists(input_jpg):
            print("❌ failed to convert png to jpg")
            sys.exit(1)

# load image + convert to grayscale
img = cv2.imread(input_jpg, cv2.IMREAD_GRAYSCALE)
if img is None:
    print("❌ failed to load image")
    sys.exit(1)
if verbose:
    print("✅ png to jpg success")

# Binarization using Otsu's method
_, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
if binary is None:
    print("❌ failed to binarize image")
    sys.exit(1)
if verbose:
    print("✅ binarize success")

# save the binary image
pbm_output = os.path.join(temp_dir, "output.pbm")
cv2.imwrite(pbm_output , binary)

# .svg convertion using potrace
final_result = subprocess.run(['potrace', pbm_output, '-s', '-o', output + '.svg'])
if final_result.returncode != 0:
    print("❌ potrace failed")
    sys.exit(1)

print("✅ converting to svg success")



