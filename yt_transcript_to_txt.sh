#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <youtube_url | file_with_urls>"
  exit 1
fi

INPUT="$1"
DEFAULT_LOCALE_LANG="${LANG:-en}"
DEFAULT_LOCALE_LANG="${DEFAULT_LOCALE_LANG%%_*}"
DEFAULT_LOCALE_LANG="${DEFAULT_LOCALE_LANG%%.*}"
SUB_LANG="${SUB_LANG:-$DEFAULT_LOCALE_LANG}"
OUTDIR="${OUTDIR:-$(pwd)/transcripts}"
TMPDIR="$(mktemp -d)"

mkdir -p "$OUTDIR"

cleanup() { rm -rf "$TMPDIR"; }
trap cleanup EXIT

download_subs() {
  local url="$1"

  yt-dlp \
    --ignore-errors \
    --skip-download \
    --write-info-json \
    --write-subs \
    --write-auto-subs \
    --sub-lang "$SUB_LANG" \
    --sub-format vtt \
    --output "$TMPDIR/%(id)s.%(ext)s" \
    "$url"
}

vtt_to_txt() {
  local vtt="$1"
  local fname id lang infojson title safe out

  fname="$(basename "$vtt")"

  # Extract YouTube video id from filenames like:
  #   <id>.vtt
  #   <id>.<lang>.vtt
  #   <id>.<lang>.<something>.vtt
  id="${fname%%.*}"

  # Try to infer language tag (purely informational)
  lang=""
  if [[ "$fname" =~ ^${id}\.([a-zA-Z-]+)\.vtt$ ]]; then
    lang="${BASH_REMATCH[1]}"
  fi

  infojson="$TMPDIR/${id}.info.json"

  # Read title from infojson; fall back to id if missing.
  title="$(python3 - "$infojson" <<'PY'
import sys, json, pathlib
p = pathlib.Path(sys.argv[1])
if p.exists():
  try:
    d = json.loads(p.read_text(encoding='utf-8', errors='replace'))
    print(d.get('title') or d.get('fulltitle') or "")
  except Exception:
    print("")
else:
  print("")
PY
)"

  # Sanitize title for macOS filenames.
  safe="$(python3 - "$id" "$title" <<'PY'
import sys, re
id = sys.argv[1]
title = sys.argv[2]
s = title or id
# Replace path separators and other annoying characters
s = s.replace('/', '-').replace('\\', '-').replace(':', ' - ')
# Collapse whitespace
s = re.sub(r"\s+", " ", s).strip()
# Remove characters that commonly cause issues
s = re.sub(r"[\000-\037]", "", s)
# Keep it reasonably short
s = s[:200].rstrip()
print(s)
PY
 )"

  if [[ -n "$safe" ]]; then
    out="$OUTDIR/${safe} [${id}].txt"
  else
    out="$OUTDIR/${id}.txt"
  fi

  awk -f - "$vtt" > "$out" <<'AWK'
function trim(s){ sub(/^[ \t]+/, "", s); sub(/[ \t]+$/, "", s); return s }
BEGIN { in_header=1; prev="" }

{ sub(/\r$/, "", $0) }

in_header {
  if ($0=="") in_header=0
  next
}

/^WEBVTT/ { next }
/^Kind: / { next }
/^Language: / { next }
/^NOTE/ { next }
/^STYLE/ { next }
/^REGION/ { next }

/^[0-9]+$/ { next }
/^[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3} --> / { next }
/^[0-9]{1,2}:[0-9]{2}\.[0-9]{3} --> / { next }

$0=="" { next }

{
  # Strip tags
  gsub(/<[^>]+>/, "", $0)

  # Decode/clean common HTML entities (cheap but effective)
  gsub(/&nbsp;|&#160;/, " ", $0)
  gsub(/&amp;/, "&", $0)
  gsub(/&quot;/, "\"", $0)
  gsub(/&#39;/, "'", $0)

  line = trim($0)
  if (line=="") next

  # Remove non-speech markers at the start; keep remaining text if any
  if (tolower(line) ~ /^\[(music|applause|laughter)\][[:space:]]*/) {
    sub(/^\[[^]]+\][[:space:]]*/, "", line)
    line = trim(line)
    if (line=="") next
  }

  # Remove consecutive duplicates
  if (line == prev) next
  prev = line

  print line
}
AWK
}

process_all_vtt() {
  while IFS= read -r -d '' vtt; do
    vtt_to_txt "$vtt"
  done < <(find "$TMPDIR" -type f -name "*.vtt" -print0)
}

# ---- main ----
if [[ -f "$INPUT" ]]; then
  while IFS= read -r url; do
    [[ -z "$url" ]] && continue
    [[ "$url" =~ ^[[:space:]]*# ]] && continue
    download_subs "$url"
  done < "$INPUT"
else
  download_subs "$INPUT"
fi

process_all_vtt
echo "Done. Output: $OUTDIR"
