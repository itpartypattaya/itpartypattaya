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

Fonts: [Unbounded](https://fonts.google.com/specimen/Unbounded) and [Golos Text](https://fonts.google.com/specimen/Golos+Text), both under the SIL Open Font License 1.1 (Latin subsets).
