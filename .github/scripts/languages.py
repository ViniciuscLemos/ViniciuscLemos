"""Draws assets/languages.svg: the languages of my own repos, by size of code.

The public github-readme-stats server kept going down (rate limits), so this runs in
a weekly Action and the README points at a file in this repo instead.
"""

import json
import os
import sys
import urllib.request
from html import escape

USER = "ViniciuscLemos"
TOP = 8
# files that aren't really "languages I write" or that one generated report would inflate
SKIP = {"HTML", "Dockerfile", "Makefile", "Batchfile", "PowerShell", "Procfile"}

# colors from GitHub's linguist, so they match the bars on each repo page
COLORS = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572A5", "Java": "#b07219",
    "C": "#555555", "CSS": "#663399", "Shell": "#89e051", "PLpgSQL": "#336790", "SQL": "#e38c00",
    "C++": "#f34b7d", "Go": "#00ADD8", "Rust": "#dea584", "Kotlin": "#A97BFF",
}


def get(url: str):
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": USER})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def totals() -> dict[str, int]:
    repos = get(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner")
    sizes: dict[str, int] = {}
    for repo in repos:
        if repo["fork"] or repo["archived"] or repo["name"] == USER:
            continue
        for language, size in get(repo["languages_url"]).items():
            if language not in SKIP:
                sizes[language] = sizes.get(language, 0) + size
    return sizes


def svg(sizes: dict[str, int]) -> str:
    top = sorted(sizes.items(), key=lambda kv: -kv[1])[:TOP]
    total = sum(size for _, size in top) or 1
    width, bar_y = 340, 44

    parts = [f'<text x="20" y="28" class="title">Most used languages</text>']
    # the stacked bar, clipped to rounded ends
    x = 20.0
    bar = []
    for language, size in top:
        w = (width - 40) * size / total
        bar.append(f'<rect x="{x:.2f}" y="{bar_y}" width="{w:.2f}" height="8" fill="{COLORS.get(language, "#8b949e")}"/>')
        x += w
    parts.append(f'<clipPath id="round"><rect x="20" y="{bar_y}" width="{width - 40}" height="8" rx="4"/></clipPath>')
    parts.append(f'<g clip-path="url(#round)">{"".join(bar)}</g>')

    # two columns underneath, in the same order as the bar
    for i, (language, size) in enumerate(top):
        col, row = i % 2, i // 2
        lx, ly = 20 + col * 160, 80 + row * 22
        color = COLORS.get(language, "#8b949e")
        parts.append(f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{color}"/>')
        parts.append(f'<text x="{lx + 16}" y="{ly}" class="name">{escape(language)}</text>')
        parts.append(f'<text x="{lx + 150}" y="{ly}" class="pct" text-anchor="end">{100 * size / total:.1f}%</text>')

    height = 80 + ((len(top) + 1) // 2) * 22
    # a grey that reads on both the light and the dark GitHub theme
    style = ("<style>text{font-family:-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;fill:#8b949e}"
             ".title{font-size:15px;font-weight:600;fill:#58a6ff}.name{font-size:12.5px}.pct{font-size:12px}</style>")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'role="img" aria-label="Most used languages: {escape(", ".join(l for l, _ in top))}">'
            f'{style}{"".join(parts)}</svg>\n')


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "assets/languages.svg"
    data = totals()
    if not data:
        sys.exit("No languages found, keeping the old file.")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg(data))
    print(f"Wrote {out}: {', '.join(sorted(data, key=lambda k: -data[k])[:TOP])}")
