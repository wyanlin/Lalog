# -*- coding: utf-8 -*-
"""
将 PNG 图标转换为 Windows ICO 格式。

使用方法：
    pip install Pillow
    python scripts/create_icon.py
"""
import os

try:
    from PIL import Image
except ImportError:
    print("请先安装 Pillow: pip install Pillow")
    exit(1)


def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    png_path = os.path.join(base, "resources", "icon.png")
    ico_path = os.path.join(base, "resources", "icon.ico")

    if not os.path.exists(png_path):
        print(f"PNG 图标不存在: {png_path}")
        exit(1)

    img = Image.open(png_path)

    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icons = []
    for size in sizes:
        resized = img.resize(size, Image.Resampling.LANCZOS)
        icons.append(resized)

    icons[0].save(
        ico_path,
        format="ICO",
        sizes=sizes,
        append_images=icons[1:],
    )
    print(f"已生成 ICO 图标: {ico_path}")


if __name__ == "__main__":
    main()