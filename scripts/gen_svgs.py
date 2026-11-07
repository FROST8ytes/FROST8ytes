"""Generate the transparent, animated wordmark and ticker SVGs (dark + light).

Run: python scripts/gen_svgs.py   -> assets/{wordmark,ticker}-{dark,light}.svg
Edit TICKER below to change the scrolling text.
"""
from pathlib import Path
from xml.sax.saxutils import escape

ASSETS = Path(__file__).resolve().parents[1] / "assets"
MONO = "ui-monospace,'JetBrains Mono','DejaVu Sans Mono',Menlo,Consolas,monospace"

THEMES = {
    "dark": dict(main="#fabd2f", accent="#fe8019", text="#ebdbb2", dim="#928374", glow="#fe8019", tick="#fabd2f", dot=1.0),
    "light": dict(main="#b57614", accent="#af3a03", text="#3c3836", dim="#7c6f64", glow="#d65d0e", tick="#af3a03", dot=1.3),
}

TICKER = [
    "(cyber) security analyst @ srkk",
    "soc / blue team",
    "red team & swe at heart",
    "sc-200 · sc-401 · sangfor x6",
    "universiti teknologi petronas",
    "zed · neovim",
    "malaysia",
]


def wordmark(c):
    letters = "FROST8ytes"
    fs, cw = 48, 48 * 0.6  # monospace advance ≈ 0.6em
    x0 = (720 - cw * len(letters)) / 2
    spans, css = [], []
    for i, ch in enumerate(letters):
        col = c["accent"] if ch == "8" else c["main"]
        spans.append(f'<text class="l l{i}" x="{x0 + i * cw:.1f}" y="62" fill="{col}">{ch}</text>')
        css.append(f".l{i}{{animation-delay:{0.12 * i:.2f}s}}")
    cur_x = x0 + len(letters) * cw
    reveal_end = 0.12 * len(letters) + 0.1
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="720" height="110" viewBox="0 0 720 110" role="img">
<title>FROST8ytes</title>
<style>
text{{font-family:{MONO};font-weight:700}}
.l{{font-size:{fs}px;opacity:0;animation:in .25s ease-out forwards}}
{''.join(css)}
@keyframes in{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
.cur{{font-size:{fs}px;opacity:0;animation:blink 1s step-end {reveal_end:.2f}s infinite}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:0}}}}
.tag{{font-size:15px;font-weight:400;opacity:0;animation:in .6s ease-out {reveal_end:.2f}s forwards}}
@media (prefers-reduced-motion:reduce){{.l,.tag{{animation:none;opacity:1}}.cur{{animation:none;opacity:1}}}}
</style>
{''.join(spans)}
<text class="cur" x="{cur_x:.1f}" y="62" fill="{c['text']}">_</text>
<text class="tag" x="360" y="92" text-anchor="middle" fill="{c['dim']}">blue team by day · red team &amp; SWE at heart</text>
</svg>
'''


def ticker(c):
    msg = "  •  ".join(TICKER) + "  •  "
    fs = 20
    adv = fs * 0.6 * 1.05
    L = round(len(msg) * adv, 1)
    speed = 38  # px per second
    m = escape(msg)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="720" height="40" viewBox="0 0 720 40" role="img">
<title>{escape(" · ".join(TICKER))}</title>
<style>
.t{{animation:scroll {L / speed:.1f}s linear infinite}}
@keyframes scroll{{from{{transform:translateX(0)}}to{{transform:translateX(-{L}px)}}}}
@media (prefers-reduced-motion:reduce){{.t{{animation:none}}}}
</style>
<defs>
<pattern id="dots" width="3" height="3" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="{c['dot']}" fill="#fff"/></pattern>
<linearGradient id="edge"><stop offset="0" stop-color="#000"/><stop offset=".08" stop-color="#fff"/><stop offset=".92" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>
<mask id="fade"><rect width="720" height="40" fill="url(#edge)"/></mask>
<mask id="grid"><rect width="720" height="40" fill="url(#dots)"/></mask>
<filter id="glow" x="-5%" y="-80%" width="110%" height="260%">
<feGaussianBlur in="SourceAlpha" stdDeviation="2.5" result="b"/>
<feFlood flood-color="{c['glow']}" flood-opacity=".55"/><feComposite in2="b" operator="in" result="halo"/>
<feMerge><feMergeNode in="halo"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
</defs>
<g mask="url(#fade)"><g mask="url(#grid)"><g class="t" filter="url(#glow)" fill="{c['tick']}" font-family="{MONO}" font-size="{fs}" font-weight="700">
<text x="0" y="27" textLength="{L}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">{m}</text>
<text x="{L}" y="27" textLength="{L}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">{m}</text>
<text x="{2 * L}" y="27" textLength="{L}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">{m}</text>
</g></g></g>
</svg>
'''


def main():
    for name, c in THEMES.items():
        (ASSETS / f"wordmark-{name}.svg").write_text(wordmark(c))
        (ASSETS / f"ticker-{name}.svg").write_text(ticker(c))
    print("wrote wordmark/ticker dark+light")


if __name__ == "__main__":
    main()
