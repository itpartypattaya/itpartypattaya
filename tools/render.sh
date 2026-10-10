#!/usr/bin/env sh
# Renders the profile header and the project covers into ../assets/*.jpg
# with headless Chrome. Needs Chrome and ffmpeg.
#   sh tools/render.sh                 # everything
#   sh tools/render.sh hermes-cron     # one cover (an id from COVERS in cover.html)
set -eu

here=$(cd "$(dirname "$0")" && pwd)
assets="$here/../assets"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

if [ -z "${CHROME:-}" ]; then
  for c in "/c/Program Files/Google/Chrome/Application/chrome.exe" \
           "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
           "$(command -v google-chrome 2>/dev/null || true)" \
           "$(command -v chromium 2>/dev/null || true)"; do
    [ -n "$c" ] && [ -x "$c" ] && CHROME=$c && break
  done
fi
[ -n "${CHROME:-}" ] || { echo "Chrome not found; set CHROME=/path/to/chrome" >&2; exit 1; }

# file:// URL of this folder; on Git Bash turn /c/Users/... into C:/Users/...
dir=$here
case "$dir" in /[a-z]/*) dir=$(printf '%s' "$dir" | sed 's#^/\([a-z]\)/#\1:/#') ;; esac

shot() { # $1 page with query, $2 width, $3 height, $4 output name
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --allow-file-access-from-files \
    --virtual-time-budget=3000 --user-data-dir="$tmp/profile" \
    --window-size="$2,$3" --screenshot="$tmp/$4.png" "file:///$dir/$1" >/dev/null 2>&1
  ffmpeg -v error -y -i "$tmp/$4.png" -q:v 3 "$assets/$4.jpg"
  echo "assets/$4.jpg"
}

ids=${*:-"header ui-verify reels-montage truedev-workflow field-notes-cc mafia-review hermes-cron hermes-dreaming field-notes hermes-dashboard"}
for id in $ids; do
  if [ "$id" = header ]; then shot header.html 1600 440 header
  else shot "cover.html?id=$id" 1264 400 "$id"
  fi
done
