"""Fill the "Recently pushed" section of README.md from the GitHub API."""

import json
import os
import pathlib
import re
import urllib.request

USER = "Kea-nhlapo"
HOW_MANY = 6
ROOT = pathlib.Path(__file__).parent


def fetch_repos():
    request = urllib.request.Request(
        f"https://api.github.com/users/{USER}/repos?sort=pushed&per_page=50",
        headers={"Accept": "application/vnd.github+json", "User-Agent": USER},
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def recent_repos(repos):
    picked = [
        repo for repo in repos
        if not repo["fork"] and not repo["archived"] and repo["name"].lower() != USER.lower()
    ]
    return picked[:HOW_MANY]


def render(repos):
    lines = []
    for repo in repos:
        line = f"[{repo['name']}]({repo['html_url']}) - {repo['pushed_at'][:10]}"
        if repo.get("description"):
            line += f"<br><sub>{repo['description']}</sub>"
        lines.append(line)
    lines.append(f"\nMore on [my repositories page](https://github.com/{USER}?tab=repositories).")
    return "\n\n".join(lines)


def replace_chunk(content, marker, chunk):
    pattern = re.compile(
        rf"<!-- {marker} starts -->.*<!-- {marker} ends -->", re.DOTALL
    )
    return pattern.sub(
        f"<!-- {marker} starts -->\n{chunk}\n<!-- {marker} ends -->", content
    )


if __name__ == "__main__":
    readme = ROOT / "README.md"
    content = readme.read_text()
    content = replace_chunk(content, "recent_repos", render(recent_repos(fetch_repos())))
    readme.write_text(content)
