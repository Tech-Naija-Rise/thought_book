# icon_maker.py
# Simple perpetual PNG/JPG → ICO converter

import sys
from pathlib import Path
from PIL import Image

def make_ico(input_path, output_path=None):
    input_path = Path(input_path)
    if not input_path.exists():
        print(f"File not found: {input_path}")
        return

    if output_path is None:
        output_path = input_path.with_suffix(".ico")

    # Open image
    img = Image.open(input_path)

    # ICOs usually look crisp if you export multiple sizes
    sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]

    img.save(output_path, format="ICO", sizes=sizes)
    print(f"✅ Saved icon: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python icon_maker.py input.png [output.ico]")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        make_ico(input_file, output_file)
