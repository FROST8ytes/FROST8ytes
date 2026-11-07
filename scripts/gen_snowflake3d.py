"""Pre-render a 3D snowflake rotating on its vertical axis as ASCII frames.

Run locally (needs numpy + scipy + pillow): python scripts/gen_snowflake3d.py
Writes assets/snowflake3d.txt (frames separated by a line containing only '---').
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, label

ASSETS = Path(__file__).resolve().parents[1] / "assets"
SRC = ASSETS / "avatar.jpg"  # white snowflake on teal
OUT = ASSETS / "snowflake3d.txt"
CHARS = ".,-~:;=!*#$@"
COLS, ROWS = 68, 28
FRAMES = 36
S = 360  # mask resolution


def snowflake_mask():
    """White, low-saturation pixels of the avatar = the snowflake."""
    im = Image.open(SRC).convert("RGB")
    a = np.asarray(im).astype(int)
    mx, mn = a.max(axis=2), a.min(axis=2)
    m = (mn > 200) & (mx - mn < 40)
    lab, n = label(m)  # drop JPEG specks: keep only sizeable blobs
    sizes = np.bincount(lab.ravel())
    keep = np.nonzero(sizes > 0.0005 * m.size)[0]
    m = np.isin(lab, keep[keep > 0])
    ys, xs = np.nonzero(m)
    cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
    half = max(ys.max() - ys.min(), xs.max() - xs.min()) / 2 * 1.02
    box = (int(cx - half), int(cy - half), int(cx + half), int(cy + half))
    mi = Image.fromarray((m * 255).astype("uint8")).crop(box).resize((S, S), Image.LANCZOS)
    return np.asarray(mi) > 110


def build_points():
    m = snowflake_mask()
    h = gaussian_filter(m.astype(float), 7) * m  # soft rounded bevel
    h = h / h.max() * 0.08  # bevel height (relative to radius 1)
    gy, gx = np.gradient(h * S / 2)
    ys, xs = np.nonzero(m)
    x = (xs - S / 2) / (S / 2)
    y = (ys - S / 2) / (S / 2)
    z = h[ys, xs] + 0.015
    nx, ny = -gx[ys, xs], -gy[ys, xs]
    nz = np.ones_like(nx)
    n = np.sqrt(nx**2 + ny**2 + nz**2)
    nx, ny, nz = nx / n, ny / n, nz / n
    # front and back surfaces
    P = np.concatenate([np.stack([x, y, z]), np.stack([x, y, -z])], axis=1)
    N = np.concatenate([np.stack([nx, ny, nz]), np.stack([nx, ny, -nz])], axis=1)
    return P, N


SX, SY = 4, 8  # supersampling per character cell


def render(P, N, theta):
    c, s = math.cos(theta), math.sin(theta)
    rot = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    p, n = rot @ P, rot @ N
    light = np.array([-0.15, -0.35, -0.92])
    light /= np.linalg.norm(light)
    lum = 0.25 + 0.75 * np.abs(light @ n)  # two-sided lighting
    dist = 3.0
    zc = p[2] + dist
    W, H = COLS * SX, ROWS * SY
    sx = (p[0] * dist / zc * (W / 2 - 2) + W / 2).astype(int)
    sy = (p[1] * dist / zc * (H / 2 - 2) + H / 2).astype(int)
    ok = (sx >= 0) & (sx < W) & (sy >= 0) & (sy < H)
    sx, sy, zc, lum = sx[ok], sy[ok], zc[ok], lum[ok]
    # z-buffer: keep nearest point per sub-pixel
    order = np.argsort(-zc)  # far first, near overwrites
    img = np.full((H, W), np.nan)
    img[sy[order], sx[order]] = lum[order]
    cells = img.reshape(ROWS, SY, COLS, SX)
    cov = np.mean(~np.isnan(cells), axis=(1, 3))
    avg = np.nanmean(np.where(np.isnan(cells), np.nan, cells), axis=(1, 3))
    out = []
    for r in range(ROWS):
        row = ""
        for q in range(COLS):
            if cov[r, q] < 0.18:
                row += " "
            else:
                v = avg[r, q] * min(1.0, 0.4 + cov[r, q])
                row += CHARS[min(len(CHARS) - 1, int(v * (len(CHARS) - 1) + 0.5))]
        out.append(row.rstrip())
    return out


def main():
    P, N = build_points()
    frames = [render(P, N, 2 * math.pi * f / FRAMES) for f in range(FRAMES)]
    OUT.write_text("\n---\n".join("\n".join(fr) for fr in frames) + "\n")
    print(f"wrote {len(frames)} frames to {OUT}")


if __name__ == "__main__":
    main()
