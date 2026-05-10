import json
import os
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path


USERNAME = os.environ.get("GITHUB_USERNAME", "felipenunes07")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "dist"))

BG = "#1a1b27"
BORDER = "#2f334d"
TITLE = "#70a5fd"
TEXT = "#c9d1d9"
MUTED = "#a9b1d6"
ACCENT = "#bf91f3"
GREEN = "#9ece6a"

LANG_COLORS = {
    "TypeScript": "#3178c6",
    "JavaScript": "#f7df1e",
    "Python": "#3572A5",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Jupyter Notebook": "#DA5B0B",
    "Shell": "#89e051",
    "Dockerfile": "#384d54",
    "Vue": "#41b883",
    "Go": "#00ADD8",
    "Rust": "#dea584",
}


def api(path):
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fmt_date(value):
    if not value:
        return "sem data"
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt.strftime("%d/%m/%Y")


def owned_repos():
    repos = []
    page = 1
    while True:
        batch = api(
            f"/users/{USERNAME}/repos?per_page=100&page={page}&sort=updated&type=owner"
        )
        if not batch:
            break
        repos.extend(repo for repo in batch if not repo.get("fork"))
        page += 1
    return repos


def repo_languages(repos):
    totals = Counter()
    for repo in repos:
        language = repo.get("language")
        if language:
            totals[language] += 1
    return totals


def card_shell(width, height, title, body):
    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg" role="img">
  <title>{escape(title)}</title>
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="4.5" fill="{BG}" stroke="{BORDER}"/>
  <text x="24" y="34" fill="{TITLE}" font-family="Segoe UI, Ubuntu, sans-serif" font-size="18" font-weight="700">{escape(title)}</text>
{body}
</svg>
"""


def github_stats_card(user, repos, languages):
    total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)
    total_forks = sum(repo.get("forks_count", 0) for repo in repos)
    recent = max((repo.get("updated_at") for repo in repos if repo.get("updated_at")), default="")
    active = sum(
        1
        for repo in repos
        if repo.get("updated_at")
        and datetime.fromisoformat(repo["updated_at"].replace("Z", "+00:00"))
        > datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year - 1)
    )

    rows = [
        ("Repos publicos", str(user.get("public_repos", len(repos))), "#70a5fd"),
        ("Stars recebidas", str(total_stars), GREEN),
        ("Forks", str(total_forks), ACCENT),
        ("Projetos ativos", str(active), "#ff9e64"),
        ("Ultima atividade", fmt_date(recent), "#bb9af7"),
    ]

    y = 68
    parts = []
    for label, value, color in rows:
        parts.append(f'  <circle cx="30" cy="{y - 5}" r="4" fill="{color}"/>')
        parts.append(
            f'  <text x="44" y="{y}" fill="{TEXT}" font-family="Segoe UI, Ubuntu, sans-serif" font-size="14">{escape(label)}:</text>'
        )
        parts.append(
            f'  <text x="178" y="{y}" fill="{MUTED}" font-family="Segoe UI, Ubuntu, sans-serif" font-size="14" font-weight="600">{escape(value)}</text>'
        )
        y += 24

    return card_shell(420, 180, f"{USERNAME}'s GitHub Stats", "\n".join(parts))


def top_langs_card(languages):
    total = sum(languages.values()) or 1
    top = languages.most_common(7)
    start_x = 24
    bar_y = 54
    bar_width = 372
    x = start_x
    parts = []

    for lang, amount in top:
        width = max(2, int(bar_width * amount / total))
        color = LANG_COLORS.get(lang, "#70a5fd")
        parts.append(
            f'  <rect x="{x}" y="{bar_y}" width="{width}" height="8" fill="{color}" rx="2"/>'
        )
        x += width

    y = 91
    col_x = [24, 220]
    for idx, (lang, amount) in enumerate(top):
        pct = amount / total * 100
        x = col_x[idx % 2]
        if idx == 6:
            x = 24
        color = LANG_COLORS.get(lang, "#70a5fd")
        parts.append(f'  <circle cx="{x + 4}" cy="{y - 5}" r="4" fill="{color}"/>')
        parts.append(
            f'  <text x="{x + 16}" y="{y}" fill="{TEXT}" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13">{escape(lang)}</text>'
        )
        parts.append(
            f'  <text x="{x + 142}" y="{y}" fill="{MUTED}" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13">{pct:.1f}%</text>'
        )
        if idx % 2 == 1:
            y += 25

    return card_shell(420, 180, "Top Languages", "\n".join(parts))


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    user = api(f"/users/{USERNAME}")
    repos = owned_repos()
    languages = repo_languages(repos)

    (OUTPUT_DIR / "github-stats.svg").write_text(
        github_stats_card(user, repos, languages), encoding="utf-8"
    )
    (OUTPUT_DIR / "top-langs.svg").write_text(
        top_langs_card(languages), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
