#!/usr/bin/env python3
# ==============================================================================
# Script: Windows Japanese Cursor to Multi-Size Linux X11 Theme Converter
# Description: Detects Japanese cursor naming conventions (通常, 待ち状態, リンク選択...)
#              and converts Windows (.ani / .cur) files into a Linux X11/KDE Plasma
#              theme supporting multiple sizes (24, 32, 48, 64px).
#
# Prerequisites:
#   - Fedora/RHEL:   sudo dnf install -y xcursorgen python3-pillow python3-pip
#   - Ubuntu/Debian: sudo apt install -y x11-apps python3-pil python3-pip
#   - Install win2xcur: pip install win2xcur
#
# Usage:
#   1. Open terminal in the directory containing your Japanese .ani / .cur files:
#      cd "/path/to/japanese_cursor_folder"
#   2. Run the script:
#      python3 win_jp_cursor_converter.py
#
# Options to customize below:
#   - THEME_NAME : Display name for the theme in KDE (default: "JapaneseCustomCursor")
#   - SIZES      : Target DPI size list (default: [24, 32, 48, 64])
#   - TEMP_DIR   : Temporary build directory (default: "/tmp/cursor_jp_build")
# ==============================================================================

import os
import glob
import subprocess
import struct
from PIL import Image

# ----------------- CONFIGURATION OPTIONS -----------------
THEME_NAME = "JapaneseCustomCursor"  # Change to your desired theme name
SIZES = [24, 32, 48, 64]             # Supported DPI scales
TEMP_DIR = "/tmp/cursor_jp_build"
# ---------------------------------------------------------

icons_dir = os.path.expanduser(f"~/.local/share/icons/{THEME_NAME}/cursors")
theme_root = os.path.expanduser(f"~/.local/share/icons/{THEME_NAME}")

os.makedirs(icons_dir, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# 1. Scan for all .ani and .cur files in current directory
files = glob.glob("*.ani") + glob.glob("*.cur")
if not files:
    print("[-] ERROR: No .ani or .cur files found in the current directory!")
    exit(1)

print(f"[+] Found {len(files)} Japanese cursor files. Extracting raw frames...")

# 2. Convert to raw X11 files in temporary folder
win2xcur_bin = os.path.expanduser("~/.local/bin/win2xcur")
if not os.path.exists(win2xcur_bin):
    win2xcur_bin = "win2xcur"

subprocess.run([win2xcur_bin, "-o", TEMP_DIR] + files)

# 3. Japanese keyword mapping -> Linux X11 Standard Aliases
jp_map = {
    "通常": ["default", "left_ptr", "arrow"],
    "リンク選択": ["pointing_hand", "hand2", "hand", "pointer"],
    "待ち状態": ["wait", "watch"],
    "バックグラウンド作業中": ["progress", "left_ptr_watch", "half-busy"],
    "テキスト選択": ["xterm", "text", "ibeam"],
    "ヘルプの選択": ["help", "question_arrow"],
    "利用不可": ["not-allowed", "forbidden", "circle", "crossed_circle"],
    "移動": ["move", "all-scroll", "fleur"],
    "左右に拡大・縮小": ["ew-resize", "size_hor", "h_double_arrow"],
    "上下に拡大・縮小": ["ns-resize", "size_ver", "v_double_arrow"],
    "斜めに拡大・縮小1": ["nwse-resize", "size_fdiag"],
    "斜めに拡大・縮小2": ["nesw-resize", "size_bdiag"],
    "領域選択": ["crosshair", "cross"],
    "手書き": ["pencil"],
    "代替選択": ["up-arrow", "center_ptr"]
}

def parse_xcursor(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    if len(data) < 16:
        return []
    magic, header_size, version, ntoc = struct.unpack("<4sIII", data[:16])
    if magic != b"Xcur":
        return []
    images = []
    for i in range(ntoc):
        toc_type, toc_subtype, toc_pos = struct.unpack("<III", data[16 + i*12 : 28 + i*12])
        if toc_type == 0xfffd0002:  # IMAGE chunk
            chunk = data[toc_pos:]
            c_header, c_type, c_subtype, c_version, width, height, xhot, yhot, delay = struct.unpack("<IIIIIIIII", chunk[:36])
            raw_pixels = chunk[36 : 36 + width*height*4]
            img_data = bytearray(len(raw_pixels))
            for p in range(0, len(raw_pixels), 4):
                b, g, r, a = raw_pixels[p:p+4]
                img_data[p:p+4] = bytes([r, g, b, a])
            img = Image.frombytes("RGBA", (width, height), bytes(img_data))
            images.append({"img": img, "xhot": xhot, "yhot": yhot, "delay": delay, "orig_w": width, "orig_h": height})
    return images

# 4. Multi-size scale and packaging via xcursorgen
print("[+] Resizing frames and generating multi-size packages...")
for idx_f, f in enumerate(os.listdir(TEMP_DIR)):
    f_path = os.path.join(TEMP_DIR, f)
    if not os.path.isfile(f_path) or f.endswith(".png") or f.endswith(".cursor"):
        continue
    frames = parse_xcursor(f_path)
    if not frames:
        continue

    cfg_lines = []
    base_name = f"cursor_{idx_f}"
    for s in SIZES:
        for idx, frame in enumerate(frames):
            scaled_img = frame["img"].resize((s, s), Image.Resampling.LANCZOS)
            png_name = f"{base_name}_{s}_{idx}.png"
            scaled_img.save(os.path.join(TEMP_DIR, png_name))
            scale_ratio = s / frame["orig_w"]
            xhot = int(frame["xhot"] * scale_ratio)
            yhot = int(frame["yhot"] * scale_ratio)
            delay = frame["delay"] if frame["delay"] > 0 else 50
            cfg_lines.append(f"{s} {xhot} {yhot} {TEMP_DIR}/{png_name} {delay}")

    cfg_path = os.path.join(TEMP_DIR, f"{base_name}.cursor")
    with open(cfg_path, "w") as out_cfg:
        out_cfg.write("\n".join(cfg_lines))

    out_cursor = os.path.join(icons_dir, f)
    subprocess.run(["xcursorgen", cfg_path, out_cursor])

# 5. Create symlinks using the Japanese dictionary
print("[+] Creating symlinks based on Japanese keyword map...")
for keyword, linux_names in jp_map.items():
    for f in os.listdir(icons_dir):
        if keyword in f and not os.path.islink(os.path.join(icons_dir, f)):
            for l_name in linux_names:
                dst = os.path.join(icons_dir, l_name)
                if os.path.exists(dst) or os.path.islink(dst):
                    os.remove(dst)
                os.symlink(f, dst)
            break

# 6. Generate index.theme metadata
with open(os.path.join(theme_root, "index.theme"), "w", encoding="utf-8") as out:
    out.write(f"[Icon Theme]\nName={THEME_NAME}\nComment={THEME_NAME} Multi-Size Cursor Theme\n")

print(f"[✓] SUCCESS! Theme created at: ~/.local/share/icons/{THEME_NAME}")
