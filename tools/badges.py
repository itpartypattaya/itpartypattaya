#!/usr/bin/env python3
"""Keeps the static shields.io badges of the README inside the repository.

    python tools/badges.py            # README.md -> assets/badges/*.svg

GitHub shows README images through its camo proxy, which answers 504 to a random part of the
requests to shields.io, so random badges on the profile show as broken links. A badge whose text
never changes (img.shields.io/badge/...) can be a file in the repo instead. This script downloads
every such badge once, saves it to assets/badges/ and points the README at the file. Live badges
(img.shields.io/github/... such as stars) stay as they are.

All badges are downloaded first; if any of them does not come back as an SVG after a few tries,
nothing is written. Running it again with nothing left to fetch changes nothing. To add a new
static badge, put its shields.io URL in the README and run the script.

Standard library only.
"""

import argparse
import hashlib
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = re.compile(r"https://img\.shields\.io/badge/[^\s\"'()<>]+")


class BadgeError(Exception):
    pass


def http_fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "itpartypattaya-profile-badges"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.headers.get("Content-Type", ""), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, (e.headers or {}).get("Content-Type", ""), e.read()


def find_static(text):
    seen, out = set(), []
    for m in STATIC.finditer(text):
        url = m.group(0)
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


def local_name(url):
    path = urllib.parse.urlsplit(url).path.split("/badge/", 1)[1]
    label = path.rsplit("-", 1)[0] if "-" in path else path
    label = urllib.parse.unquote(label).replace("--", "-").replace("__", "_")
    slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")[:40].strip("-") or "badge"
    return f"{slug}-{hashlib.sha1(url.encode('utf-8')).hexdigest()[:6]}.svg"


def _download(url, fetch, sleep, tries):
    last = ""
    for attempt in range(tries):
        try:
            status, ctype, body = fetch(url)
        except OSError as e:
            status, ctype, body, last = 0, "", b"", str(e)
        if status == 200 and "svg" in (ctype or "") and body.lstrip().startswith(b"<svg"):
            return body
        last = last or f"HTTP {status} {ctype}".strip()
        if attempt < tries - 1:
            sleep(2 * attempt + 1)
    raise BadgeError(f"{url}: {last}")


def _write_atomic(path, data):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".badge-", dir=d)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def localize(readme, out_dir, fetch=http_fetch, sleep=time.sleep, tries=3):
    with open(readme, encoding="utf-8") as f:
        text = f.read()
    urls = find_static(text)
    if not urls:
        return 0
    bodies = {url: _download(url, fetch, sleep, tries) for url in urls}
    base = os.path.dirname(os.path.abspath(readme))
    for url, body in bodies.items():
        _write_atomic(os.path.join(out_dir, local_name(url)), body)
    for url in sorted(urls, key=len, reverse=True):
        rel = os.path.relpath(os.path.join(out_dir, local_name(url)), base).replace(os.sep, "/")
        text = text.replace(url, rel)
    _write_atomic(readme, text.encode("utf-8"))
    return len(urls)


def main(argv=None):
    root = os.path.dirname(HERE)
    ap = argparse.ArgumentParser(description="Store static shields.io badges in the repository.")
    ap.add_argument("--readme", default=os.path.join(root, "README.md"))
    ap.add_argument("--out", default=os.path.join(root, "assets", "badges"))
    args = ap.parse_args(argv)
    try:
        n = localize(args.readme, args.out)
    except BadgeError as e:
        print(f"badges: {e}; nothing was changed", file=sys.stderr)
        return 1
    print(f"{n} badges stored in {os.path.relpath(args.out, root)}" if n else "no remote static badges left")
    return 0


if __name__ == "__main__":
    sys.exit(main())
