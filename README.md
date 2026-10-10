<a href="https://itparty.club/about"><img src="assets/header.jpg" width="100%" alt="Anton Vaskov. Digital marketer in Pattaya, Thailand. AI agents for a real community."></a>

<a href="https://itparty.club/about"><img src="https://img.shields.io/badge/itparty.club-141A4A?style=for-the-badge&logo=googlechrome&logoColor=F5A623" alt="Website itparty.club"></a> <a href="https://t.me/passone"><img src="https://img.shields.io/badge/Telegram-@passone-141A4A?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram @passone"></a> <a href="https://t.me/it_networking_pattaya"><img src="https://img.shields.io/badge/Channel-IT--party%20Pattaya-141A4A?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram channel of IT-party Pattaya"></a> <a href="https://www.youtube.com/@IT-party-Pattaya"><img src="https://img.shields.io/badge/YouTube-AI%20meetups-141A4A?style=for-the-badge&logo=youtube&logoColor=white" alt="YouTube: AI meetup recordings"></a> <a href="https://hr24copilot.online"><img src="https://img.shields.io/badge/HR24%20Copilot-141A4A?style=for-the-badge&logoColor=white" alt="HR24 Copilot"></a>

I am a digital marketer, not a software engineer. I run a Russian-speaking IT community in Pattaya, help a recruiting agency with its tools, and keep a family AI agent on my own server. Everything below started as a problem in one of those three places, and each repository is the part that someone else can install and use.

## Hermes Agent skills and plugins

[Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research is the agent I use every day. Three of these four are listed in the official Hermes Plugin Catalog.

### hermes-cron

<a href="https://github.com/itpartypattaya/hermes-cron"><img src="assets/hermes-cron.jpg" width="100%" alt="Abstract illustration of scheduled automation for the Hermes agent"></a>

A skill that teaches Hermes to work with its cron scheduler carefully, plus a read-only doctor script that checks existing jobs.

**Why it exists.** Cron failures in an agent look like success. `30m` written instead of `in 30m`, a message delivered twice, `deliver: origin` pointing to the wrong chat, a half-paused job, a model pinned to a job and forgotten: nothing reports an error, the reminder simply never arrives.

**What it is.** A Hermes skill that can also be installed as a plugin. Python standard library only. The doctor only reads: no network, no API keys, it registers no tools or hooks and writes nothing.

<a href="https://github.com/itpartypattaya/hermes-cron"><img src="https://img.shields.io/badge/Repository-F5A623?style=for-the-badge&logo=github&logoColor=0B0F1F" alt="hermes-cron on GitHub"></a> <a href="https://hermes-agent.nousresearch.com/docs/plugins/hermes-cron"><img src="https://img.shields.io/badge/Listed%20in-Hermes%20Plugin%20Catalog-141A4A?style=for-the-badge" alt="Listed in the Hermes Plugin Catalog"></a>

Install: `hermes skills install itpartypattaya/hermes-cron/skills/hermes-cron`

### hermes-dreaming

<a href="https://github.com/itpartypattaya/hermes-dreaming"><img src="assets/hermes-dreaming.jpg" width="100%" alt="Abstract illustration of the agent's nightly memory consolidation"></a>

Nightly, deterministic memory consolidation for Hermes: the agent "dreams" over the day's conversations and proposes only the memory updates worth keeping.

**Why it exists.** Useful facts never reach long-term memory, while the memory itself fills up with stale entries and hits its character limit. The script does the sorting without an LLM and wakes the agent only when there is something to decide.

**What it is.** A plugin or a plain skill, Python standard library, Hermes 0.21 or later. No network, and the scripts never call a model. The agent makes at most six memory changes a night and nothing is deleted from storage. Secrets and prompt-injection attempts go to quarantine; the README says plainly that this is a regex filter, not a guarantee.

<a href="https://github.com/itpartypattaya/hermes-dreaming"><img src="https://img.shields.io/badge/Repository-F5A623?style=for-the-badge&logo=github&logoColor=0B0F1F" alt="hermes-dreaming on GitHub"></a> <a href="https://hermes-agent.nousresearch.com/docs/plugins/hermes-dreaming"><img src="https://img.shields.io/badge/Listed%20in-Hermes%20Plugin%20Catalog-141A4A?style=for-the-badge" alt="Listed in the Hermes Plugin Catalog"></a>

Install from the catalog: `hermes plugins install hermes-dreaming`

### hermes-field-notes

<a href="https://github.com/itpartypattaya/hermes-field-notes"><img src="assets/field-notes.jpg" width="100%" alt="Abstract illustration of engineering field notes"></a>

Field notes for Hermes: pitfalls recorded with their root cause, plus a registry of local patches to the Hermes core that is checked after every `hermes update`.

**Why it exists.** What an agent learned the hard way is lost with the chat, and `hermes update` silently wipes local fixes to the engine. The registry makes that loss visible the moment it happens.

**What it is.** A skill or plugin, Python 3.11+ standard library. Notes stay on the machine and the core is only read. `--read-only` mode guarantees no writes and no network; otherwise the network is used for an optional Telegram dashboard and a public GitHub API check every 12 hours, which can be switched off.

<a href="https://github.com/itpartypattaya/hermes-field-notes"><img src="https://img.shields.io/badge/Repository-F5A623?style=for-the-badge&logo=github&logoColor=0B0F1F" alt="hermes-field-notes on GitHub"></a> <a href="https://github.com/itpartypattaya/hermes-field-notes/releases/latest"><img src="https://img.shields.io/badge/Latest%20release-141A4A?style=for-the-badge&logo=github&logoColor=white" alt="Latest release"></a> <a href="https://hermes-agent.nousresearch.com/docs/plugins/hermes-field-notes"><img src="https://img.shields.io/badge/Listed%20in-Hermes%20Plugin%20Catalog-141A4A?style=for-the-badge" alt="Listed in the Hermes Plugin Catalog"></a>

Install: `hermes skills install itpartypattaya/hermes-field-notes/skills/hermes-field-notes`

### hermes-dashboard

<a href="https://github.com/itpartypattaya/hermes-dashboard"><img src="assets/hermes-dashboard.jpg" width="100%" alt="Abstract illustration of the Hermes system dashboard"></a>

A static system dashboard for a Hermes installation: host status, security, model routing, honest cost, memory, cron economics and a capability map, rebuilt by cron from the agent's own telemetry.

**Why it exists.** I wanted to see what my agent actually does and costs without trusting numbers typed in by hand. The rule of the project: if a number cannot be collected automatically, it is not on the page.

**What it is.** Python 3.9+, standard library only, English and Russian. The pages are `noindex`, hold only aggregates and no secrets, and have no runtime; the only outside request is Google Fonts, which one setting turns off.

<a href="https://github.com/itpartypattaya/hermes-dashboard"><img src="https://img.shields.io/badge/Repository-F5A623?style=for-the-badge&logo=github&logoColor=0B0F1F" alt="hermes-dashboard on GitHub"></a> <a href="https://github.com/itpartypattaya/hermes-dashboard/releases/latest"><img src="https://img.shields.io/badge/Latest%20release-141A4A?style=for-the-badge&logo=github&logoColor=white" alt="Latest release"></a>

Install: clone into `~/.hermes/hermes-dashboard` and run `bin/hermes-dashboard build`; the README has the config steps.

## Claude Code and Codex tools

### truedev-codex-workflow

<a href="https://github.com/itpartypattaya/truedev-codex-workflow"><img src="assets/truedev-workflow.jpg" width="100%" alt="Abstract illustration of a gated development workflow"></a>

A native Codex plugin for gated, file-backed product and engineering work.

**Why it exists.** On long tasks an agent drifts: it touches files nobody asked about, calls the work done without running anything, commits on its own. Here hooks block the next step until a person approves the current one.

**What it is.** A Codex plugin with two skills, Codex hooks and a Python runner. No telemetry; the only network request is an update check, and only with consent. It ships in two editions: one for a GitHub marketplace, one for the ChatGPT Plugins Directory.

<a href="https://github.com/itpartypattaya/truedev-codex-workflow"><img src="https://img.shields.io/badge/Repository-F5A623?style=for-the-badge&logo=github&logoColor=0B0F1F" alt="truedev-codex-workflow on GitHub"></a> <a href="https://github.com/itpartypattaya/truedev-codex-workflow/releases/latest"><img src="https://img.shields.io/badge/Latest%20release-141A4A?style=for-the-badge&logo=github&logoColor=white" alt="Latest release"></a>

```
codex plugin marketplace add itpartypattaya/truedev-codex-workflow --ref main
codex plugin add truedev-workflow@truedev-workflow
```

### mafia-review-skill

<a href="https://github.com/itpartypattaya/mafia-review-skill"><img src="assets/mafia-review.jpg" width="100%" alt="Abstract illustration of an AI review of a Mafia game"></a>

A Codex skill that reviews a club game of Mafia from two audio transcripts and the host's score sheet: roles, night events, timeline, key moments and ratings.

**Why it exists.** Our city Mafia league at [mafia.itparty.club](https://mafia.itparty.club) publishes a review of every game. This skill produces the same review on an agent subscription instead of a paid API pipeline, in the exact format the site imports.

**What it is.** A `SKILL.md` method plus two standard-library Python scripts that score the review and validate the bundle before import.

<a href="https://github.com/itpartypattaya/mafia-review-skill"><img src="https://img.shields.io/badge/Repository-F5A623?style=for-the-badge&logo=github&logoColor=0B0F1F" alt="mafia-review-skill on GitHub"></a>

### More tools

- **[reels-montage](https://github.com/itpartypattaya/reels-montage)** · Claude Code plugins that edit vertical videos locally: cuts by audio, a virtual camera, word-timed subtitles, branded motion graphics in Remotion. `it-reelsmaker` is [in the Claude plugin directory](https://claude.ai/customize/plugins/id/c1ae3d1a-cbd2-4ee3-be95-a87be163ba1f%40anthropic-plugin-directory).
  `claude plugin marketplace add https://github.com/itpartypattaya/reels-montage.git && claude plugin install it-reelsmaker@itparty`
- **[ui-verify](https://github.com/itpartypattaya/ui-verify)** · checks web layout with numbers instead of screenshots: overflow, real contrast, grids, which CSS rule won, missing glyphs. Every check returns true, false, or null with a reason.
  `claude plugin marketplace add itpartypattaya/ui-verify && claude plugin install ui-verify@ui-verify`
- **[telegram-stories-stat](https://github.com/itpartypattaya/telegram-stories-stat)** · who viewed your Telegram stories and when, statistics tables and opt-in auto-replies by rules. A Hermes skill backed by a small Telethon service, no LLM inside.
  `hermes skills install itpartypattaya/telegram-stories-stat/skills/telegram-stories`
- **[field-notes](https://github.com/itpartypattaya/field-notes)** · the same idea as hermes-field-notes for Claude Code and Codex CLI: one notes store per machine, searched before a fix. No network.

## In production

These tools exist because something real runs on them.

- **[itparty.club](https://itparty.club)** · the site of IT-party Pattaya, a community that started as a Telegram chat on 22 July 2023 and grew into meetups, a city Mafia league, a currency exchange service and beach transfers. Static Astro, no trackers beyond the site's own analytics.
- **[mafia.itparty.club](https://mafia.itparty.club)** · the league: player ratings, game history and AI reviews of every game.
- **[HR24 Copilot](https://hr24copilot.online)** · interview recordings turned into a transcript, an HR analysis and a comparison with the vacancy, for an international recruiting agency.
- **A family agent on Hermes** · runs on my own server; the dashboard above shows its state. Its configuration is private because it holds family data.
- **[subs.itparty.club](https://subs.itparty.club)** · a tiny offline teleprompter for recording videos ([source](https://github.com/itpartypattaya/subs)).

## How the work is checked

Most repositories here ship offline tests that run without network or accounts. Only two run them in GitHub Actions today: truedev-codex-workflow and reels-montage. I would rather say that than show green badges I do not have. CI for the Hermes repositories is the next step, and test counts with dates will go here once it is in place.

## Attribution

My part is the problem, the requirements, the acceptance criteria, the security and privacy decisions, the review, and running the result on real people and real data. The code and most texts are written with AI assistance, mainly Claude Code and Codex.
