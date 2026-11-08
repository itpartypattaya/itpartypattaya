"""Tests for tools/stats.py, the profile stats card.

What the card must do for a reader of the profile:
- count only the repositories that are really mine and public: no archived ones, no forks I only
  cloned, but the fork I maintain (hermes-plugin-holographic) does count; the profile repo itself
  is not a project;
- show stars and releases of exactly those repositories;
- show languages by bytes, the top ones by name and the rest as "Other", with a bar whose parts
  add up to the whole bar;
- say how many of the repositories with CI are green on their default branch; a repository
  without CI is not counted as red, a cancelled or failed run is not green;
- never put a broken or half-filled card on the profile: if any API call fails, the old card
  stays and the run fails loudly;
- give the same file for the same numbers, so the daily job commits only when something changed.

The fixtures follow the shape of real GitHub REST answers, including pagination by Link header,
an empty languages object and a 403 rate-limit answer.
"""

import json
import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import stats  # noqa: E402

API = "https://api.github.com"
USER = "itpartypattaya"


def repo(name, stars=0, fork=False, archived=False, private=False, branch="main"):
    return {
        "name": name,
        "full_name": f"{USER}/{name}",
        "owner": {"login": USER},
        "private": private,
        "fork": fork,
        "archived": archived,
        "stargazers_count": stars,
        "default_branch": branch,
    }


def runs(total, conclusion=None):
    wr = [] if total == 0 else [{"status": "completed", "conclusion": conclusion}]
    return {"total_count": total, "workflow_runs": wr}


class FakeGitHub:
    """Answers GET requests by URL, like urllib would, with status, headers and body."""

    def __init__(self):
        self.routes = {}
        self.calls = []

    def add(self, path, body, status=200, link=None):
        headers = {"Link": link} if link else {}
        self.routes[path if path.startswith("http") else API + path] = (status, headers, body)

    def __call__(self, url, token=None):
        self.calls.append(url)
        if url not in self.routes:
            raise AssertionError(f"unexpected request {url}")
        status, headers, body = self.routes[url]
        return status, headers, json.dumps(body).encode("utf-8")


def full_fixture():
    gh = FakeGitHub()
    gh.add(f"/users/{USER}", {"login": USER, "created_at": "2021-03-05T10:00:00Z", "followers": 7})
    page2 = f"{API}/users/{USER}/repos?per_page=100&type=owner&page=2"
    gh.add(f"/users/{USER}/repos?per_page=100&type=owner", [
        repo(USER, stars=2),                                    # the profile itself
        repo("reels-montage", stars=5),
        repo("hermes-plugin-holographic", stars=34, fork=True),  # maintained fork
        repo("book-distill", stars=1, fork=True),                # cloned fork
    ], link=f'<{page2}>; rel="next", <{page2}>; rel="last"')
    gh.add(page2, [
        repo("old-thing", stars=9, archived=True),
        repo("subs", stars=1, branch="master"),
        repo("secret", stars=3, private=True),
    ])
    gh.add(f"/repos/{USER}/reels-montage/languages", {"Python": 600, "TypeScript": 300, "Shell": 100})
    gh.add(f"/repos/{USER}/hermes-plugin-holographic/languages", {"Python": 1000})
    gh.add(f"/repos/{USER}/subs/languages", {})
    rel2 = f"{API}/repos/{USER}/reels-montage/releases?per_page=100&page=2"
    gh.add(f"/repos/{USER}/reels-montage/releases?per_page=100", [{"id": i} for i in range(100)],
           link=f'<{rel2}>; rel="next"')
    gh.add(rel2, [{"id": i} for i in range(30)])
    gh.add(f"/repos/{USER}/hermes-plugin-holographic/releases?per_page=100", [{"id": 1}, {"id": 2}])
    gh.add(f"/repos/{USER}/subs/releases?per_page=100", [])
    gh.add(f"/repos/{USER}/reels-montage/actions/runs?branch=main&status=completed&per_page=1",
           runs(40, "success"))
    gh.add(f"/repos/{USER}/hermes-plugin-holographic/actions/runs?branch=main&status=completed&per_page=1",
           runs(12, "failure"))
    gh.add(f"/repos/{USER}/subs/actions/runs?branch=master&status=completed&per_page=1", runs(0))
    return gh


class SelectionTest(unittest.TestCase):
    def test_only_my_public_projects_count(self):
        all_repos = [repo(USER), repo("a"), repo("b", fork=True), repo("hermes-plugin-holographic", fork=True),
                     repo("c", archived=True), repo("d", private=True)]
        picked = stats.select_repos(all_repos, USER, {"hermes-plugin-holographic"})
        self.assertEqual([r["name"] for r in picked], ["a", "hermes-plugin-holographic"])


class CollectTest(unittest.TestCase):
    def setUp(self):
        self.s = stats.collect(USER, full_fixture(), maintained_forks={"hermes-plugin-holographic"})

    def test_counts_and_stars_of_selected_repositories_only(self):
        self.assertEqual(self.s["repos"], 3)
        self.assertEqual(self.s["stars"], 5 + 34 + 1)

    def test_releases_follow_pagination(self):
        self.assertEqual(self.s["releases"], 130 + 2 + 0)

    def test_ci_counts_green_and_ignores_repos_without_ci(self):
        self.assertEqual((self.s["ci_green"], self.s["ci_total"]), (1, 2))

    def test_languages_by_bytes_and_empty_repo_is_harmless(self):
        names = [l["name"] for l in self.s["languages"]]
        self.assertEqual(names, ["Python", "TypeScript", "Shell"])
        self.assertAlmostEqual(sum(l["share"] for l in self.s["languages"]), 1.0, places=9)
        self.assertAlmostEqual(self.s["languages"][0]["share"], 1600 / 2000)

    def test_profile_header_data(self):
        self.assertEqual(self.s["since"], 2021)
        self.assertEqual(self.s["followers"], 7)


class CiConclusionTest(unittest.TestCase):
    def test_cancelled_is_not_green(self):
        gh = FakeGitHub()
        gh.add(f"/users/{USER}", {"login": USER, "created_at": "2021-03-05T10:00:00Z", "followers": 0})
        gh.add(f"/users/{USER}/repos?per_page=100&type=owner", [repo("x")])
        gh.add(f"/repos/{USER}/x/languages", {"Python": 1})
        gh.add(f"/repos/{USER}/x/releases?per_page=100", [])
        gh.add(f"/repos/{USER}/x/actions/runs?branch=main&status=completed&per_page=1", runs(3, "cancelled"))
        s = stats.collect(USER, gh, maintained_forks=set())
        self.assertEqual((s["ci_green"], s["ci_total"]), (0, 1))


class LanguagesTest(unittest.TestCase):
    def test_tail_goes_to_other(self):
        totals = {f"L{i}": 100 - i for i in range(9)}
        langs = stats.top_languages(totals, keep=6)
        self.assertEqual(len(langs), 7)
        self.assertEqual(langs[-1]["name"], "Other")
        self.assertEqual(langs[-1]["bytes"], sum(100 - i for i in range(6, 9)))
        self.assertAlmostEqual(sum(l["share"] for l in langs), 1.0, places=9)

    def test_no_languages_at_all(self):
        self.assertEqual(stats.top_languages({}, keep=6), [])


def sample_stats(**over):
    s = {"user": USER, "since": 2021, "followers": 7, "repos": 17, "stars": 81, "releases": 120,
         "ci_green": 11, "ci_total": 12, "lang_repos": 16,
         "languages": stats.top_languages({"Python": 7000, "JavaScript": 2000, "Shell": 600,
                                           "HTML": 300, "TypeScript": 60, "CSS": 30, "Lua": 10}, keep=6)}
    s.update(over)
    return s


class RenderTest(unittest.TestCase):
    def test_svg_parses_and_shows_the_numbers(self):
        svg = stats.render_svg(sample_stats())
        root = ET.fromstring(svg)
        text = " ".join(t for t in root.itertext())
        for part in ("17", "81", "120", "11 / 12", "Python", "Other", USER):
            self.assertIn(part, text)

    def test_bar_parts_fill_the_bar_exactly(self):
        svg = stats.render_svg(sample_stats())
        root = ET.fromstring(svg)
        ns = "{http://www.w3.org/2000/svg}"
        parts = [r for r in root.iter(ns + "rect") if r.get("class") == "seg"]
        self.assertEqual(len(parts), 7)
        total = sum(float(r.get("width")) for r in parts)
        self.assertAlmostEqual(total, stats.BAR_WIDTH, places=6)

    def test_language_name_is_escaped(self):
        s = sample_stats(languages=stats.top_languages({"C<&>": 5, "Python": 5}, keep=6))
        root = ET.fromstring(stats.render_svg(s))
        self.assertIn("C<&>", " ".join(root.itertext()))

    def test_tiny_language_share_keeps_the_svg_valid(self):
        # Real data: a few hundred bytes of Batchfile among megabytes of Python gives "<0.1%".
        s = sample_stats(languages=stats.top_languages({"Python": 5_000_000, "Batchfile": 300}, keep=6))
        root = ET.fromstring(stats.render_svg(s))
        self.assertIn("<0.1%", " ".join(root.itertext()))

    def test_same_numbers_same_file(self):
        self.assertEqual(stats.render_svg(sample_stats()), stats.render_svg(sample_stats()))

    def test_thousands_are_grouped(self):
        root = ET.fromstring(stats.render_svg(sample_stats(stars=12345)))
        self.assertIn("12,345", " ".join(root.itertext()))


class MainTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.out = os.path.join(self.dir, "stats.svg")

    def test_writes_card(self):
        rc = stats.main(["--user", USER, "--out", self.out, "--maintained-fork", "hermes-plugin-holographic"],
                        fetch=full_fixture())
        self.assertEqual(rc, 0)
        with open(self.out, encoding="utf-8") as f:
            ET.fromstring(f.read())

    def test_api_failure_keeps_old_card(self):
        with open(self.out, "w", encoding="utf-8") as f:
            f.write("OLD")
        gh = full_fixture()
        gh.add(f"/repos/{USER}/subs/languages", {"message": "API rate limit exceeded"}, status=403)
        rc = stats.main(["--user", USER, "--out", self.out, "--maintained-fork", "hermes-plugin-holographic"],
                        fetch=gh)
        self.assertNotEqual(rc, 0)
        with open(self.out, encoding="utf-8") as f:
            self.assertEqual(f.read(), "OLD")
        self.assertEqual(os.listdir(self.dir), ["stats.svg"])

    def test_network_error_keeps_old_card(self):
        with open(self.out, "w", encoding="utf-8") as f:
            f.write("OLD")

        def broken(url, token=None):
            raise OSError("connection reset")

        rc = stats.main(["--user", USER, "--out", self.out], fetch=broken)
        self.assertNotEqual(rc, 0)
        with open(self.out, encoding="utf-8") as f:
            self.assertEqual(f.read(), "OLD")


if __name__ == "__main__":
    unittest.main()
