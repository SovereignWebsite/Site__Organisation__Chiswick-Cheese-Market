#!/usr/bin/env python3
"""Shrink the design screenshots from tools/thumbs.js to 640 x 400 WebP for the "Choose a design" panel."""
import glob, os
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "site", "assets", "designs")
for png in sorted(glob.glob(os.path.join(OUT, "*.png"))):
    im = Image.open(png).convert("RGB").resize((640, 400), Image.LANCZOS)
    im.save(png[:-4] + ".webp", "WEBP", quality=72, method=6)
    os.remove(png)
    print("wrote", os.path.basename(png[:-4] + ".webp"))
