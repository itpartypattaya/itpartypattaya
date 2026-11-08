"""Tests for tools/badges.py, which keeps the static shields.io badges inside the repository.

Why: GitHub shows README images through its camo proxy, and camo answers 504 to a random part of
the shields.io requests, so random badges on the profile show as broken links. A badge whose text
never changes can be an SVG file in the repo instead. What the tool must do:
- find every static shields.io badge (img.shields.io/badge/...) in the README, in both HTML
  <img src> and Markdown image forms, and leave the live ones (stars) alone;
- give each distinct badge its own file and the same file for the same badge;
- download everything first and change nothing unless every badge came back as a real SVG,
  so a half-converted README never lands; a 504 is retried a couple of times first;
- be safe to run again: nothing left to fetch means nothing changes.
"""

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import badges  # noqa: E402

A = "https://img.shields.io/badge/Claude%20Code-D97757?style=flat&logo=claude&logoColor=white"
B = "https://img.shields.io/badge/Repository-F5A623?style=for-the-badge&logo=github&logoColor=0B0F1F"
B2 = "https://img.shields.io/badge/Repository-141A4A?style=for-the-badge"
C = "https://img.shields.io/badge/OVH%20VPS%20%C2%B7%204%20vCPU%20%C2%B7%208%20GB-123F6D?style=flat&logo=ovh&logoColor=white"
LIVE = "https://img.shields.io/github/stars/itpartypattaya/ui-verify?style=for-the-badge&logo=github&label=Stars"
MD = "https://img.shields.io/badge/tests-passing-green"

README = f"""<img src="{A}" alt="Claude Code"> <img src="{C}" alt="OVH">

<a href="x"><img src="{B}" alt="repo one"></a> <a href="y"><img src="{B}" alt="repo two"></a>
<img src="{B2}" alt="other colour"> <img src="{LIVE}" alt="stars">

| x | [![tests]({MD})](https://example.com) |
"""


def svg(text):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="80" height="20"><text>{text}</text></svg>').encode()


class Fake:
    def __init__(self, answers=None, default=None):
        self.answers = {k: list(v) for k, v in (answers or {}).items()}
        self.default = default
        self.calls = []

    def __call__(self, url):
        self.calls.append(url)
        queue = self.answers.get(url)
        if queue:
            return queue.pop(0)
        if self.default:
            return self.default(url)
        return 200, "image/svg+xml;charset=utf-8", svg(url[-12:])


class FindTest(unittest.TestCase):
    def test_finds_static_badges_once_and_skips_live_ones(self):
        self.assertEqual(badges.find_static(README), [A, C, B, B2, MD])


class NameTest(unittest.TestCase):
    def test_same_badge_same_file_other_colour_other_file(self):
        self.assertEqual(badges.local_name(B), badges.local_name(B))
        self.assertNotEqual(badges.local_name(B), badges.local_name(B2))

    def test_names_are_plain_ascii_files(self):
        name = badges.local_name(C)
        self.assertTrue(name.startswith("ovh-vps-4-vcpu-8-gb-"), name)
        self.assertTrue(name.endswith(".svg"))
        self.assertTrue(name.isascii())


class LocalizeTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.readme = os.path.join(self.root, "README.md")
        with open(self.readme, "w", encoding="utf-8", newline="\n") as f:
            f.write(README)
        self.out = os.path.join(self.root, "assets", "badges")

    def read(self):
        with open(self.readme, encoding="utf-8") as f:
            return f.read()

    def test_rewrites_static_badges_and_keeps_live_ones(self):
        n = badges.localize(self.readme, self.out, Fake(), sleep=lambda s: None)
        self.assertEqual(n, 5)
        text = self.read()
        self.assertNotIn("img.shields.io/badge/", text)
        self.assertIn(LIVE, text)
        self.assertEqual(text.count(f'src="assets/badges/{badges.local_name(B)}"'), 2)
        self.assertIn(f"![tests](assets/badges/{badges.local_name(MD)})", text)
        self.assertEqual(len(os.listdir(self.out)), 5)

    def test_one_failure_changes_nothing(self):
        fake = Fake(answers={C: [(504, "text/plain", b"Gateway Timeout")] * 5})
        with self.assertRaises(badges.BadgeError):
            badges.localize(self.readme, self.out, fake, sleep=lambda s: None)
        self.assertEqual(self.read(), README)
        self.assertFalse(os.path.exists(self.out) and os.listdir(self.out))

    def test_html_error_page_is_not_a_badge(self):
        fake = Fake(answers={A: [(200, "text/html", b"<html>rate limited</html>")] * 5})
        with self.assertRaises(badges.BadgeError):
            badges.localize(self.readme, self.out, fake, sleep=lambda s: None)
        self.assertEqual(self.read(), README)

    def test_a_504_is_retried(self):
        fake = Fake(answers={A: [(504, "text/plain", b"timeout")]})
        badges.localize(self.readme, self.out, fake, sleep=lambda s: None)
        self.assertEqual(fake.calls.count(A), 2)
        self.assertNotIn(A, self.read())

    def test_second_run_fetches_nothing(self):
        badges.localize(self.readme, self.out, Fake(), sleep=lambda s: None)
        before = self.read()
        fake = Fake()
        self.assertEqual(badges.localize(self.readme, self.out, fake, sleep=lambda s: None), 0)
        self.assertEqual(fake.calls, [])
        self.assertEqual(self.read(), before)


if __name__ == "__main__":
    unittest.main()
