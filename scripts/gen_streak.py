"""Build transparent GitHub streak cards (dark + light) from the GraphQL API.

Usage: GITHUB_TOKEN=... python gen_streak.py [out_dir]
Writes streak-dark.svg and streak-light.svg.
"""
import json
import os
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone

USER = "FROST8ytes"
MONO = "ui-monospace,'JetBrains Mono','DejaVu Sans Mono',Menlo,Consolas,monospace"
THEMES = {
    "dark": dict(num="#ebdbb2", label="#fabd2f", ring="#fabd2f", fire="#fe8019", dates="#a89984", stroke="#504945"),
    "light": dict(num="#3c3836", label="#b57614", ring="#b57614", fire="#af3a03", dates="#7c6f64", stroke="#d5c4a1"),
}


def gql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.load(r)
    if "errors" in out:
        raise RuntimeError(out["errors"])
    return out["data"]


def fetch_days():
    created = gql("query($u:String!){user(login:$u){createdAt}}", {"u": USER})["user"]["createdAt"]
    start = datetime.fromisoformat(created.replace("Z", "+00:00")).year
    q = """query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){contributionsCollection(from:$f,to:$t){
      contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""
    days = {}
    now = datetime.now(timezone.utc)
    for y in range(start, now.year + 1):
        f = datetime(y, 1, 1, tzinfo=timezone.utc)
        t = min(datetime(y, 12, 31, 23, 59, 59, tzinfo=timezone.utc), now)
        cal = gql(q, {"u": USER, "f": f.isoformat(), "t": t.isoformat()})["user"]["contributionsCollection"]["contributionCalendar"]
        for w in cal["weeks"]:
            for d in w["contributionDays"]:
                days[date.fromisoformat(d["date"])] = d["contributionCount"]
    return dict(sorted(days.items()))


def stats(days):
    total = sum(days.values())
    first = next((d for d, c in days.items() if c), min(days))
    cur_len, cur_start = 0, None
    best = (0, None, None)
    for d, c in days.items():
        if c:
            cur_start = d if cur_len == 0 else cur_start
            cur_len += 1
            if cur_len > best[0]:
                best = (cur_len, cur_start, d)
        else:
            cur_len = 0
    today = max(days)
    # current streak: today may still be 0 without breaking it
    d = today if days[today] else today - timedelta(days=1)
    n, end = 0, d
    while days.get(d, 0):
        n, d = n + 1, d - timedelta(days=1)
    cur = (n, d + timedelta(days=1), end) if n else (0, today, today)
    return dict(total=total, first=first, today=today, cur=cur, best=best)


def fmt(d):
    return d.strftime("%b %-d, %Y") if d else ""


def rng(a, b):
    if not a:
        return ""
    if a == b:
        return fmt(a)
    return f"{a.strftime('%b %-d')} - {fmt(b)}"


def svg(s, c):
    cur, best = s["cur"], s["best"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="720" height="190" viewBox="0 0 720 190" role="img">
<title>{USER} contribution streak</title>
<style>
text{{font-family:{MONO};text-anchor:middle}}
.n{{font-size:30px;font-weight:700;fill:{c['num']}}}
.l{{font-size:14px;fill:{c['label']}}}
.d{{font-size:12px;fill:{c['dates']}}}
.f{{opacity:0;animation:in .6s ease-out forwards}}
@keyframes in{{to{{opacity:1}}}}
</style>
<line x1="240" y1="35" x2="240" y2="155" stroke="{c['stroke']}"/>
<line x1="480" y1="35" x2="480" y2="155" stroke="{c['stroke']}"/>
<g class="f"><text class="n" x="120" y="88">{s['total']:,}</text>
<text class="l" x="120" y="122">Total Contributions</text>
<text class="d" x="120" y="146">{fmt(s['first'])} - Present</text></g>
<g class="f" style="animation-delay:.3s">
<circle cx="360" cy="78" r="40" fill="none" stroke="{c['ring']}" stroke-width="5"/>
<path d="M360 26c4 6 9 9 9 16a9 9 0 0 1-18 0c0-4 3-6 4-9 1 3 3 4 5 4-1-4-1-7 0-11z" fill="{c['fire']}"/>
<text class="n" x="360" y="89">{cur[0]}</text>
<text class="l" x="360" y="146" style="font-weight:700">Current Streak</text>
<text class="d" x="360" y="166">{rng(cur[1], cur[2]) if cur[0] else 'No active streak'}</text></g>
<g class="f" style="animation-delay:.6s"><text class="n" x="600" y="88">{best[0]}</text>
<text class="l" x="600" y="122">Longest Streak</text>
<text class="d" x="600" y="146">{rng(best[1], best[2])}</text></g>
</svg>
'''


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    s = stats(fetch_days())
    for name, c in THEMES.items():
        with open(os.path.join(out, f"streak-{name}.svg"), "w") as f:
            f.write(svg(s, c))
    print(f"streak: total={s['total']} current={s['cur'][0]} longest={s['best'][0]}")


if __name__ == "__main__":
    main()
