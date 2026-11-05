"""Draws assets/contributions.svg: contributions in the last year, the current and the
longest streak, and the last 26 weeks as a small grid.

Same reason as languages.py: the public streak-stats server kept failing ("Failed to
retrieve contributions"), so a daily Action draws the card into this repo.
"""

import json
import os
import sys
import urllib.request
from datetime import date

USER = "ViniciuscLemos"
WEEKS = 26
QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""
# GitHub's own green scale for the grid, from "a few" to "a lot"
GREENS = ["#0e4429", "#006d32", "#26a641", "#39d353"]
EMPTY = "#8b949e33"


def calendar() -> tuple[int, list[tuple[date, int]]]:
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    request = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
        "Content-Type": "application/json",
        "User-Agent": USER,
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    if "errors" in data:
        sys.exit(f"GitHub said: {data['errors']}")
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [(date.fromisoformat(d["date"]), d["contributionCount"])
            for week in cal["weeks"] for d in week["contributionDays"]]
    return cal["totalContributions"], days


def streaks(days: list[tuple[date, int]]) -> tuple[int, int]:
    longest = run = 0
    for _, count in days:
        run = run + 1 if count else 0
        longest = max(longest, run)
    # today not having a commit yet doesn't break the streak, the day isn't over
    current = 0
    for i, (_, count) in enumerate(reversed(days)):
        if count:
            current += 1
        elif i > 0:
            break
    return current, longest


def shade(count: int, top: int) -> str:
    if not count:
        return EMPTY
    return GREENS[min(3, (count - 1) * 4 // max(top, 1))]


def svg(total: int, days: list[tuple[date, int]]) -> str:
    current, longest = streaks(days)
    width, height = 360, 165

    parts = ['<text x="20" y="28" class="title">Contributions</text>']
    numbers = [(f"{total:,}", "last year"), (str(current), "day streak"), (str(longest), "longest streak")]
    for i, (value, label) in enumerate(numbers):
        x = 20 + i * 110
        parts.append(f'<text x="{x}" y="62" class="num">{value}</text>')
        parts.append(f'<text x="{x}" y="80" class="label">{label}</text>')

    # the last WEEKS weeks, one column per week, Sunday on top like on the profile
    recent = days[-WEEKS * 7 - days[-1][0].isoweekday() % 7 - 1:]
    start = recent[0][0]
    top = max((c for _, c in recent), default=1)
    cell, gap = 7, 2
    for d, count in recent:
        offset = (d - start).days + start.isoweekday() % 7
        col, row = offset // 7, offset % 7
        parts.append(f'<rect x="{20 + col * (cell + gap)}" y="{96 + row * (cell + gap)}" '
                     f'width="{cell}" height="{cell}" rx="1.5" fill="{shade(count, top)}">'
                     f'<title>{d.isoformat()}: {count}</title></rect>')

    style = ("<style>text{font-family:-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;fill:#8b949e}"
             ".title{font-size:15px;font-weight:600;fill:#58a6ff}.num{font-size:22px;font-weight:600;fill:#58a6ff}"
             ".label{font-size:12px}</style>")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'role="img" aria-label="{total} contributions in the last year, {current} day streak, longest {longest}">'
            f'{style}{"".join(parts)}</svg>\n')


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "assets/contributions.svg"
    total, days = calendar()
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg(total, days))
    print(f"Wrote {out}: {total} contributions, streaks {streaks(days)}")
