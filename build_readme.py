"""Keep the profile README fresh.

Runs once a day from .github/workflows/build.yml:
  * draws a card (light and dark) for each featured project into assets/cards/
  * fills the "Recently pushed" list between the recent_repos markers
"""

import html
import json
import os
import pathlib
import re
import textwrap
import urllib.request

USER = "Kea-nhlapo"
HOW_MANY = 6
ROOT = pathlib.Path(__file__).parent
CARDS = ROOT / "assets" / "cards"

# Repos shown as cards, with the line I'd use to describe them.
FEATURED = {
    "Kea-nhlapo/mint-uptime-guarantee": "Flags machines that are likely to fail and gets the repair approved and booked.",
    "wattwiseg13/wattwise": "Tracks household electricity use from an Arduino and links it to municipal fault reports.",
    "Kea-nhlapo/civiclens-ai": "Turns a photo of road damage into a draft report for the municipality.",
    "Kea-nhlapo/fieldwise": None,
}

THEMES = {
    "light": {"bg": "#ffffff", "border": "#d0d7de", "title": "#0b5cd5", "text": "#424a53", "muted": "#6e7781"},
    "dark": {"bg": "#0d1117", "border": "#30363d", "title": "#6ea8fe", "text": "#c9d1d9", "muted": "#8b949e"},
}

LANGUAGE_COLOURS = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572A5", "Java": "#b07219",
    "C#": "#178600", "HTML": "#e34c26", "CSS": "#663399", "Go": "#00ADD8", "HCL": "#844FBA",
}


def api(path):
    request = urllib.request.Request(
        f"https://api.github.com/{path}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": USER},
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def card_svg(repo, blurb, theme):
    colours = THEMES[theme]
    name = html.escape(repo["name"])
    description = blurb or repo.get("description") or ""
    lines = textwrap.wrap(description, 54)[:2]
    language = repo.get("language")
    stars = repo.get("stargazers_count", 0)

    text = "".join(
        f'<text x="20" y="{62 + i * 20}" class="desc">{html.escape(line)}</text>'
        for i, line in enumerate(lines)
    )
    footer = ""
    if language:
        dot = LANGUAGE_COLOURS.get(language, colours["muted"])
        footer += f'<circle cx="26" cy="116" r="6" fill="{dot}"/><text x="38" y="120" class="meta">{html.escape(language)}</text>'
    if stars:
        footer += f'<text x="{38 + 9 * len(language or "") + 24}" y="120" class="meta">★ {stars}</text>'

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="140" viewBox="0 0 400 140" role="img" aria-label="{name}">
<style>
.title {{ font: 600 17px 'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif; fill: {colours['title']}; }}
.desc {{ font: 400 13px 'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif; fill: {colours['text']}; }}
.meta {{ font: 400 12px 'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif; fill: {colours['muted']}; }}
</style>
<rect x="0.5" y="0.5" width="399" height="139" rx="8" fill="{colours['bg']}" stroke="{colours['border']}"/>
<text x="20" y="34" class="title">{name}</text>
{text}
{footer}
</svg>
"""


def draw_cards():
    CARDS.mkdir(parents=True, exist_ok=True)
    for full_name, blurb in FEATURED.items():
        try:
            repo = api(f"repos/{full_name}")
        except Exception as error:  # keep the last good card if the API hiccups
            print(f"skipped {full_name}: {error}")
            continue
        for theme in THEMES:
            (CARDS / f"{repo['name']}-{theme}.svg").write_text(card_svg(repo, blurb, theme))


def recent_repos(repos):
    picked = [
        repo for repo in repos
        if not repo["fork"] and not repo["archived"] and repo["name"].lower() != USER.lower()
    ]
    return picked[:HOW_MANY]


def render_recent(repos):
    lines = []
    for repo in repos:
        line = f"- [{repo['name']}]({repo['html_url']}) <sub>{repo['pushed_at'][:10]}</sub>"
        if repo.get("description"):
            line += f"<br><sub>{repo['description']}</sub>"
        lines.append(line)
    return "\n".join(lines)


def replace_chunk(content, marker, chunk):
    pattern = re.compile(rf"<!-- {marker} starts -->.*<!-- {marker} ends -->", re.DOTALL)
    return pattern.sub(f"<!-- {marker} starts -->\n{chunk}\n<!-- {marker} ends -->", content)


if __name__ == "__main__":
    draw_cards()
    readme = ROOT / "README.md"
    content = readme.read_text()
    repos = api(f"users/{USER}/repos?sort=pushed&per_page=50")
    content = replace_chunk(content, "recent_repos", render_recent(recent_repos(repos)))
    readme.write_text(content)
