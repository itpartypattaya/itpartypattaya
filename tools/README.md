# Profile images

The header and the project covers in `../assets/` are drawn in HTML and rendered with headless Chrome, so they keep the fonts and colours of [itparty.club](https://itparty.club) and stay crisp.

- `header.html` — the profile header, 1600×440: photo, name, one line about me.
- `cover.html` — every project cover, 1264×400. The cover is picked by `?id=`; each entry in the `D` object at the bottom holds the kicker, the title, the one-line description, the panel caption and five panel rows `[label, value, pill colour, pill text]`. Pill colours: `ok` green, `bad` red, `nul` amber, `info` blue. A long title shrinks itself to fit.
- `src/` — the fonts and photos the pages use.

Render everything, or only the ids you name:

```bash
sh tools/render.sh
sh tools/render.sh hermes-cron ui-verify
```

It needs Chrome (found automatically, or set `CHROME=/path/to/chrome`) and `ffmpeg`. The values on the panels are illustrations of what each tool reports, not live data.

A new project: add an entry to `D` in `cover.html`, run `sh tools/render.sh <id>`, and reference `assets/<id>.jpg` from the README.

## Stats card

`assets/stats.svg` is built by `stats.py` from the public GitHub API: public repositories that are not archived and not forks (plus the forks named with `--maintained-fork`), their stars, releases, languages by bytes and how many of those with CI are green on the default branch. The workflow `.github/workflows/stats.yml` runs the tests, rebuilds the card once a day and commits it only when a number changed; the card holds no date for that reason. If any API call fails, the run fails and the old card stays.

```bash
python -m unittest discover -s tools/tests
GITHUB_TOKEN=$(gh auth token) python tools/stats.py --user itpartypattaya --out assets/stats.svg --maintained-fork hermes-plugin-holographic
```

The token only raises the rate limit; no scopes are needed.

## Badges

GitHub shows README images through its camo proxy, which answers 504 to a random part of the requests to shields.io, so random badges showed as broken links. Static badges (`img.shields.io/badge/...`) are therefore stored in `../assets/badges/`; only the live star counters still come from shields.io. To add a badge, put its shields.io URL in the README and run:

```bash
python tools/badges.py
```

It downloads every remote static badge, saves it and points the README at the file. If any badge fails to download as an SVG, nothing is changed.

The Codex and Hermes Agent icons come from [Lobe Icons](https://github.com/lobehub/lobe-icons) (MIT), `@lobehub/icons-static-svg@1.100.0`, recoloured white. The Hermes icon is too large for a shields.io URL (HTTP 431), so `hermes-agent-*.svg` was made by hand: a shields.io badge of the same text with a placeholder logo, whose `<image href>` was replaced with the icon.

Fonts: [Unbounded](https://fonts.google.com/specimen/Unbounded) and [Golos Text](https://fonts.google.com/specimen/Golos+Text), both under the SIL Open Font License 1.1 (Latin subsets).
