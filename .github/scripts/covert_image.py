#!/usr/bin/env python3
"""Convert a base PNG image into OS-specific icons for desktop apps.

Generates:
- Windows ICO (multi-size)
- Linux PNG 256x256
- macOS ICNS (app + DMG)
"""
# ruff: noqa: T201
import sys
from pathlib import Path

from PIL import Image

try:
    import icnsutil  # type: ignore  # noqa: PGH003
    ICNS_AVAILABLE = True
except ImportError:
    ICNS_AVAILABLE = False

WINDOWS_SIZES = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
MAC_SIZES = [16, 32, 64, 128, 256, 512, 1024]

def create_windows_icon(base_img: Image.Image, output_path: Path) -> None:
    """Create a Windows ICO file with multiple sizes.

    :param base_img: Base PIL Image
    :param output_path: Path to save the ICO file
    """
    base_img.save(output_path, format="ICO", sizes=WINDOWS_SIZES)
    print(f"Windows ICO saved: {output_path}")

def create_linux_icon(base_img: Image.Image, output_path: Path) -> None:
    """Create a Linux PNG icon (256x256).

    :param base_img: Base PIL Image
    :param output_path: Path to save the PNG file
    """
    base_img.resize((256, 256), Image.LANCZOS).save(output_path)
    print(f"Linux PNG (256x256) saved: {output_path}")

def create_mac_icon(base_img: Image.Image, output_path: Path) -> None:
    """Create a macOS ICNS icon.

    :param base_img: Base PIL Image
    :param output_path: Path to save the ICNS file
    """
    if not ICNS_AVAILABLE:
        print("icnsutil not installed. Skipping macOS ICNS generation.")
        return
    iconset = icnsutil.IconSet()
    for size in MAC_SIZES:
        resized = base_img.resize((size, size), Image.LANCZOS)
        iconset.add_image(resized)
    iconset.write(output_path)
    print(f"macOS ICNS saved: {output_path}")

def main() -> None:
    """Convert base PNG to OS-specific icons."""
    if len(sys.argv) != 3:
        print("Usage: python convert_icons.py <base_png> <output_dir>")
        sys.exit(1)

    base_png = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(parents=True, exist_ok=True)

    if not base_png.exists():
        print(f"Base PNG not found: {base_png}")
        sys.exit(1)

    base_img = Image.open(base_png).convert("RGBA")

    # Windows ICO
    create_windows_icon(base_img, output_dir / "scoreboard_app.ico")

    # Linux PNG 256x256
    create_linux_icon(base_img, output_dir / "scoreboard_256.png")

    # macOS ICNS (app + DMG)
    create_mac_icon(base_img, output_dir / "scoreboard_app.icns")
    create_mac_icon(base_img, output_dir / "scoreboard_volume.icns")

if __name__ == "__main__":
    main()
