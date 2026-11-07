"""Generate the Gruvbox terminal GIF for the FROST8ytes profile README.

Usage: python gen_terminal.py [output-name]   (default: terminal)
The colour scheme comes from ~/.config/gifos/gifos_settings.toml; the
background colour is keyed out afterwards so the GIF is transparent.""" 
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import gifos
from PIL import Image

USER = "FROST8ytes"
FG_Y, FG_G, FG_B, FG_A, FG_R, FG_P, FG_O, GRAY, RST = (
    "\x1b[93m", "\x1b[92m", "\x1b[94m", "\x1b[96m", "\x1b[91m", "\x1b[95m",
    "\x1b[33m", "\x1b[90m", "\x1b[0m",
)


LOGO = Path(__file__).resolve().parents[1] / "assets" / "spider-gwen.png"
ART = Path(__file__).resolve().parents[1] / "assets" / "snowflake3d.txt"
LOGO_H = 220  # px, about 11 terminal rows


def prep_logo(bg_hex, out="logo_tmp.png"):
    """Flatten the transparent PNG onto the Gruvbox bg and scale it."""
    if not LOGO.exists():
        return None
    img = Image.open(LOGO).convert("RGBA")
    img = img.resize((round(img.width * LOGO_H / img.height), LOGO_H), Image.LANCZOS)
    a = img.getchannel("A").point(lambda v: 255 if v > 128 else 0)
    img.putalpha(a)  # hard edges, so no halo once the bg is keyed out
    bg = Image.new("RGBA", img.size, bg_hex)
    Image.alpha_composite(bg, img).convert("RGB").save(out)
    return out


def t_logo_rows(h, row_px):
    import math
    return math.ceil(h / row_px)


def make_transparent(bg, dst, fps=15, frames="frames/frame_%d.png"):
    """Rebuild the GIF from gifos' PNG frames with the terminal bg keyed out.

    Uses ffmpeg (palette with a reserved transparent slot, full frames, no
    inter-frame tricks) so every browser decodes all frames.
    """
    bg = bg.lstrip("#") if isinstance(bg, str) else "%02x%02x%02x" % tuple(bg[:3])
    vf = (
        f"[0:v]colorkey=0x{bg}:0.01:0,split[a][b];"
        "[a]palettegen=reserve_transparent=1:stats_mode=full[p];"
        "[b][p]paletteuse=dither=none:alpha_threshold=128"
    )
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-r", str(fps),
        "-i", frames, "-filter_complex", vf, "-gifflags", "-offsetting-transdiff", dst,
    ]
    subprocess.run(cmd, check=True)


def get_stats():
    if not os.getenv("GITHUB_TOKEN"):
        return None
    try:
        return gifos.utils.fetch_github_stats(user_name=USER)
    except Exception as e:  # never fail the build on API hiccups
        print(f"WARN: stats fetch failed: {e}")
        return None


def main():
    global BG
    t = gifos.Terminal(width=720, height=600, xpad=8, ypad=8)
    BG = t._Terminal__bg_color  # theme background, keyed out later
    t.set_fps(15)
    now = datetime.now(ZoneInfo("Asia/Kuala_Lumpur"))

    # Boot sequence art
    t.toggle_show_cursor(False)
    t.gen_typing_text("Initiating Boot Sequence ", 1, speed=1)
    for _ in range(5):
        t.gen_text(".", 1, contin=True, count=4)
    if ART.exists():
        frames = [f.splitlines() for f in ART.read_text().split("\n---\n")]
        width = max(len(l) for f in frames for l in f)
        pad = max(1, (t.num_cols - width) // 2)
        for f in frames * 2:  # two full rotations
            for i in range(3, t.num_rows + 1):
                t.delete_row(i)
            for i, line in enumerate(f):
                if line.strip():
                    t.gen_text(f"{FG_P}{line}{RST}", 3 + i, pad, count=0, contin=True)
            t.clone_frame(1)
    t.clone_frame(25)
    t.clear_frame()

    # Boot
    t.gen_text(f"{GRAY}spidey BIOS v8.0  (c) {now.year}{RST}", 1, count=5)
    t.toggle_show_cursor(False)
    for i, mod in enumerate(["cpu0 ........ ok", "mem ......... ok", "net ......... ok", "soc-agent ... ok"]):
        t.gen_text(f"[{FG_G}  OK  {RST}] {mod}", 3 + i, count=3)
    t.clone_frame(10)
    t.clear_frame()

    # Login
    t.toggle_show_cursor(True)
    t.gen_text("spidey login: ", 1)
    t.gen_typing_text("frost8ytes", 1, contin=True, speed=2)
    t.gen_text("password: ", 2)
    t.gen_typing_text("********", 2, contin=True, speed=1)
    t.gen_text(f"{GRAY}Last login: {now:%a %b %d %H:%M} on tty1{RST}", 3, count=8)
    t.clear_frame()

    prompt = f"{FG_A}frost8ytes{RST}@{FG_Y}spidey{RST} {FG_B}~{RST}> "
    t.set_prompt(prompt)

    # whoami
    t.gen_prompt(1)
    t.gen_typing_text("whoami", 1, contin=True, speed=2)
    t.gen_text([
        f"{FG_Y}Ammar Farhan{RST}",
        f"(Cyber) Security Analyst {GRAY}@{RST} {FG_O}SRKK{RST}",
        f"{FG_B}Blue team{RST} by day (SOC)  {GRAY}|{RST}  {FG_R}red team{RST} + {FG_G}SWE{RST} at heart",
    ], 2, count=6)

    # certs
    t.gen_prompt(6)
    t.gen_typing_text("tree ~/.certs", 6, contin=True, speed=2)
    t.gen_text([
        f"{FG_B}~/.certs{RST}",
        f"|-- {FG_Y}microsoft{RST}",
        f"|   |-- SC-200  Security Operations Analyst Associate",
        f"|   `-- SC-401  Information Security Administrator Associate",
        f"`-- {FG_O}sangfor{RST}",
        f"    |-- SCTP  Network Secure",
        f"    |-- SCTA  Network Secure",
        f"    |-- SCTA  Endpoint Secure",
        f"    |-- SCTA  IAG",
        f"    |-- SCTA  XDR",
        f"    `-- SCCSM MDR",
        f"",
        f"{GRAY}2 directories, 8 certifications{RST}",
    ], 7, count=4)
    t.clone_frame(40)
    t.clear_frame()

    # fetch
    s = get_stats()
    t.gen_prompt(1)
    t.gen_typing_text("fetch", 1, contin=True, speed=2)
    langs = ", ".join(l[0] for l in s.languages_sorted[:4]) if s else "Python, Rust, TypeScript"
    rows = [
        ("os", "Windows / macOS / Linux / Android / iOS"),
        ("editor", "Zed, Neovim"),
        ("stack", "Defender XDR, Sentinel, KQL"),
        ("uni", "Universiti Teknologi PETRONAS"),
        ("degree", "Bachelor of Computer Science (Hons)"),
        ("major", "Data Analytics"),
        ("minor", "Financial Management"),
        ("certs", "SC-200, SC-401, Sangfor x6"),
        ("langs", langs),
    ]
    if s:
        rows += [
            ("commits", f"{s.total_commits_last_year} (last year)"),
            ("stars", str(s.total_stargazers)),
            ("prs", f"{s.total_pull_requests_made} ({s.pull_requests_merge_percentage}% merged)"),
            ("rank", s.user_rank.level),
        ]
    logo = prep_logo(BG)
    col = 1
    if logo:
        t.paste_image(logo, 2, 1)
        col = t.image_col + 2
        os.remove(logo)
    t.gen_text(f"{FG_Y}frost8ytes{RST}@{FG_Y}spidey{RST}", 2, col, contin=True)
    t.gen_text(f"{GRAY}{'-' * 17}{RST}", 3, col, contin=True)
    for i, (k, v) in enumerate(rows):
        t.gen_text(f"{FG_O}{k:<8}{RST} {v}", 4 + i, col, count=2, contin=True)
    last = 4 + len(rows)
    t.gen_text(
        "".join(f"\x1b[{c}m   " for c in range(41, 47)) + RST, last + 1, col, count=2, contin=True
    )
    if logo:
        row_px = (600 - 2 * 8) / t.num_rows
        last = max(last, 1 + t_logo_rows(LOGO_H, row_px))

    t.gen_prompt(last + 2)
    t.clone_frame(45)
    out = (sys.argv[1] if len(sys.argv) > 1 else "terminal") + ".gif"
    make_transparent(BG, out)


if __name__ == "__main__":
    main()
