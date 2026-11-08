#!/usr/bin/env python3
"""Builds assets/stats.svg, the stats card of the GitHub profile, from the public GitHub API.

    python tools/stats.py --user itpartypattaya --out assets/stats.svg \
        --maintained-fork hermes-plugin-holographic

Counts public repositories that are not archived and not forks, plus the forks named with
--maintained-fork; the profile repository itself is left out. Shows their stars, releases,
languages by bytes and how many of those with CI are green on the default branch.

A token from GITHUB_TOKEN (or GH_TOKEN) raises the rate limit; no scopes are needed, all data is
public. If any request fails the card is not written, so the old one stays on the profile, and
the exit code is 1. The card holds no date: the same numbers give the same file.

Standard library only.
"""

import argparse
import base64
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from xml.sax.saxutils import escape

API = "https://api.github.com"
HERE = os.path.dirname(os.path.abspath(__file__))
WIDTH, HEIGHT = 1264, 400
BAR_X, BAR_WIDTH = 664, 512.0

# GitHub linguist colours; the ones too dark for the navy card are lightened.
LANG_COLORS = {
    "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "Shell": "#89e051",
    "HTML": "#e34c26", "CSS": "#8a63d2", "PowerShell": "#5391fe", "Astro": "#ff5a03",
    "Kotlin": "#A97BFF", "Java": "#b07219", "Go": "#00ADD8", "Rust": "#dea584", "Lua": "#5a6be0",
    "C": "#a8b9cc", "C++": "#f34b7d", "Dockerfile": "#384d54", "Batchfile": "#C1F12E",
    "Jupyter Notebook": "#DA5B0B", "MDX": "#fcb32c", "Svelte": "#ff3e00", "Vue": "#41b883",
    "Other": "#7d86c2",
}
FALLBACK = ["#f5a623", "#6ee7a0", "#aab4ff", "#ff8a70", "#ffd27a", "#7dd3fc"]


class ApiError(Exception):
    pass


def http_fetch(url, token=None):
    """GET url; returns (status, headers, body bytes). HTTP errors come back as a status."""
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "itpartypattaya-profile-stats",
        **({"Authorization": f"Bearer {token}"} if token else {}),
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), e.read()


class Client:
    def __init__(self, fetch, token=None):
        self.fetch, self.token = fetch, token

    def _get(self, url):
        status, headers, body = self.fetch(url, token=self.token)
        if status != 200:
            try:
                msg = json.loads(body.decode("utf-8")).get("message", "")
            except (ValueError, AttributeError):
                msg = ""
            raise ApiError(f"GET {url}: HTTP {status} {msg}".strip())
        return headers, json.loads(body.decode("utf-8"))

    def get(self, path):
        return self._get(API + path)[1]

    def get_all(self, path):
        url, items = API + path, []
        while url:
            headers, page = self._get(url)
            if not isinstance(page, list):
                raise ApiError(f"GET {url}: expected a list")
            items.extend(page)
            url = next_link(headers.get("Link") or headers.get("link") or "")
        return items


def next_link(link):
    m = re.search(r'<([^>]+)>;\s*rel="next"', link)
    return m.group(1) if m else None


def select_repos(repos, user, maintained_forks):
    """Public, not archived, not the profile repo; forks only when I maintain them."""
    return [r for r in repos
            if not r.get("private") and not r.get("archived")
            and r["name"].lower() != user.lower()
            and (not r.get("fork") or r["name"] in maintained_forks)]


def top_languages(totals, keep=6):
    total = sum(totals.values())
    if total <= 0:
        return []
    ranked = sorted(((n, b) for n, b in totals.items() if b > 0), key=lambda x: (-x[1], x[0]))
    head, tail = ranked[:keep], ranked[keep:]
    out = [{"name": n, "bytes": b} for n, b in head]
    if tail:
        out.append({"name": "Other", "bytes": sum(b for _, b in tail)})
    for item in out:
        item["share"] = item["bytes"] / total
    return out


def collect(user, fetch, maintained_forks=frozenset(), token=None):
    c = Client(fetch, token)
    info = c.get(f"/users/{user}")
    picked = select_repos(c.get_all(f"/users/{user}/repos?per_page=100&type=owner"), user, maintained_forks)
    totals, releases, green, with_ci, lang_repos = {}, 0, 0, 0, 0
    for r in picked:
        base = f"/repos/{user}/{r['name']}"
        langs = c.get(f"{base}/languages")
        if langs:
            lang_repos += 1
        for name, size in langs.items():
            totals[name] = totals.get(name, 0) + int(size)
        releases += len(c.get_all(f"{base}/releases?per_page=100"))
        branch = urllib.parse.quote(r.get("default_branch") or "main", safe="")
        runs = c.get(f"{base}/actions/runs?branch={branch}&status=completed&per_page=1")
        if runs.get("total_count", 0) > 0 and runs.get("workflow_runs"):
            with_ci += 1
            if runs["workflow_runs"][0].get("conclusion") == "success":
                green += 1
    return {
        "user": info.get("login", user),
        "since": int(str(info.get("created_at", "0000"))[:4]),
        "followers": int(info.get("followers", 0)),
        "repos": len(picked),
        "stars": sum(int(r.get("stargazers_count", 0)) for r in picked),
        "releases": releases,
        "ci_green": green,
        "ci_total": with_ci,
        "lang_repos": lang_repos,
        "languages": top_languages(totals),
    }


def _font_face(family, path, weight):
    try:
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("ascii")
    except OSError:
        return ""
    return (f"@font-face{{font-family:{family};font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")


def _num(n):
    return f"{n:,}"


def _pct(share):
    p = share * 100
    return "<0.1%" if 0 < p < 0.1 else f"{p:.1f}%"


def render_svg(s):
    fonts = (_font_face("U", os.path.join(HERE, "src", "unbounded.woff2"), "200 900")
             + _font_face("G", os.path.join(HERE, "src", "golos.woff2"), "400 900"))
    t = escape
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="GitHub stats of {t(s["user"])}">',
        f"<title>GitHub stats of {t(s['user'])}</title>",
        "<style>" + fonts +
        ".k{font:600 15px U,sans-serif;letter-spacing:2.4px;fill:#f5a623}"
        ".n{font:800 48px U,sans-serif;fill:#fff}"
        ".s{font:400 21px G,sans-serif;fill:#d9dcef}"
        ".v{font:700 30px U,sans-serif;fill:#fff}"
        ".l{font:400 15px G,sans-serif;fill:#9aa3d6}"
        ".m{font:400 19px ui-monospace,Consolas,monospace;fill:#c9cdea}"
        ".h{font:400 15px ui-monospace,Consolas,monospace;fill:#7d86c2}"
        ".p{font:400 16px ui-monospace,Consolas,monospace;fill:#ffb84d}"
        "</style>",
        "<defs>"
        '<radialGradient id="bg" cx="0.78" cy="0.5" r="0.75">'
        '<stop offset="0" stop-color="#1a2150"/><stop offset="0.6" stop-color="#0d1124"/>'
        '<stop offset="1" stop-color="#0b0f1f"/></radialGradient>'
        '<pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">'
        '<path d="M32 0H0V32" fill="none" stroke="#ffffff" stroke-opacity="0.04"/></pattern>'
        '<linearGradient id="bar" x1="0" x2="1"><stop offset="0" stop-color="#f5a623"/>'
        '<stop offset="1" stop-color="#f0532f"/></linearGradient>'
        f'<clipPath id="barclip"><rect x="{BAR_X}" y="100" width="{BAR_WIDTH:g}" height="12" rx="6"/></clipPath>'
        "</defs>",
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#grid)"/>',
        f'<rect y="{HEIGHT - 5}" width="{WIDTH}" height="5" fill="url(#bar)"/>',
        '<text class="k" x="64" y="78">GITHUB · PUBLIC NUMBERS</text>',
        f'<text class="n" x="64" y="136">{t(s["user"])}</text>',
        f'<text class="s" x="64" y="174">On GitHub since {s["since"]} · {_num(s["followers"])} followers</text>',
    ]
    tiles = [("Repositories", _num(s["repos"])), ("Stars", _num(s["stars"])),
             ("Releases", _num(s["releases"])), ("Repos with green CI", f'{s["ci_green"]} / {s["ci_total"]}')]
    for i, (label, value) in enumerate(tiles):
        x, y = 64 + (i % 2) * 270, 206 + (i // 2) * 84
        out.append(f'<rect x="{x}" y="{y}" width="254" height="72" rx="12" fill="#141a4a" '
                   f'fill-opacity="0.75" stroke="#2b3570"/>')
        out.append(f'<text class="v" x="{x + 20}" y="{y + 38}">{t(value)}</text>')
        out.append(f'<text class="l" x="{x + 20}" y="{y + 61}">{t(label)}</text>')

    out.append('<rect x="640" y="44" width="560" height="312" rx="14" fill="#141a4a" fill-opacity="0.75" '
               'stroke="#2b3570"/>')
    for i in range(3):
        out.append(f'<circle cx="{670 + i * 22}" cy="70" r="6" fill="#2b3570"/>')
    out.append(f'<text class="h" x="{670 + 3 * 22 + 6}" y="75">languages · bytes in {s["lang_repos"]} '
               f'repositories</text>')

    langs = s["languages"]
    colors, fb = [], iter(FALLBACK * 3)
    for lang in langs:
        colors.append(LANG_COLORS.get(lang["name"]) or next(fb))
    out.append('<g clip-path="url(#barclip)">')
    if langs:
        x = float(BAR_X)
        for i, (lang, color) in enumerate(zip(langs, colors)):
            w = BAR_WIDTH * lang["share"] if i < len(langs) - 1 else BAR_X + BAR_WIDTH - x
            out.append(f'<rect class="seg" x="{x:.6f}" y="100" width="{w:.9f}" height="12" fill="{color}"/>')
            x += w
    else:
        out.append(f'<rect x="{BAR_X}" y="100" width="{BAR_WIDTH:g}" height="12" fill="#2b3570"/>')
    out.append("</g>")
    for i, (lang, color) in enumerate(zip(langs, colors)):
        col, row = i // 4, i % 4
        x, y = BAR_X + col * 268, 154 + row * 40
        out.append(f'<circle cx="{x + 6}" cy="{y - 6}" r="6" fill="{color}"/>')
        out.append(f'<text class="m" x="{x + 22}" y="{y}">{t(lang["name"])}</text>')
        out.append(f'<text class="p" x="{x + 244}" y="{y}" text-anchor="end">{t(_pct(lang["share"]))}</text>')
    out.append(f'<text class="h" x="{BAR_X}" y="334">public GitHub API · refreshed daily</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def write_atomic(path, text):
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".stats-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def main(argv=None, fetch=None):
    ap = argparse.ArgumentParser(description="Build the GitHub profile stats card.")
    ap.add_argument("--user", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--maintained-fork", action="append", default=[],
                    help="a fork that counts as my project (repeatable)")
    args = ap.parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    try:
        s = collect(args.user, fetch or http_fetch, set(args.maintained_fork), token)
        svg = render_svg(s)
    except (ApiError, OSError, ValueError, KeyError) as e:
        print(f"stats: {e}; the card was not changed", file=sys.stderr)
        return 1
    write_atomic(args.out, svg)
    print(f"{args.out}: {s['repos']} repositories, {s['stars']} stars, {s['releases']} releases, "
          f"CI {s['ci_green']}/{s['ci_total']}, {len(s['languages'])} languages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
