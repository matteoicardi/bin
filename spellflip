#!/usr/bin/env bash
set -euo pipefail

# spellflip.sh
#
# Replace American spellings with British spellings, or vice versa,
# using a user-editable mapping file.
#
# Default direction:
#   American -> British
#
# Usage:
#   ./spellflip.sh [options] <target-file>
#
# Options:
#   -m, --map FILE         Mapping file (default: ./spelling_map.tsv)
#   -d, --direction DIR    Direction: us2uk | uk2us   (default: us2uk)
#   -i, --in-place         Edit file in place
#   -o, --output FILE      Write result to FILE
#   -h, --help             Show help
#
# Examples:
#   ./spellflip.sh notes.txt
#   ./spellflip.sh -d uk2us thesis.md
#   ./spellflip.sh -i report.txt
#   ./spellflip.sh -m custom_map.tsv -o fixed.txt draft.tex
#
# Mapping file format:
#   One pair per line, tab-separated:
#       american<TAB>british
#
# Example:
#   color   colour
#   organize        organise
#   center  centre
#
# Notes:
# - Preserves simple case variants:
#     color   -> colour
#     Color   -> Colour
#     COLOR   -> COLOUR
# - Replaces whole words only.
# - Best for plain text / text-based files.
# - Not safe for arbitrary binary files.

usage() {
  sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

MAP_FILE="./spelling_map.tsv"
DIRECTION="us2uk"
IN_PLACE=0
OUTPUT_FILE=""
TARGET_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -m|--map)
      [[ $# -ge 2 ]] || { echo "Missing argument for $1" >&2; exit 1; }
      MAP_FILE="$2"
      shift 2
      ;;
    -d|--direction)
      [[ $# -ge 2 ]] || { echo "Missing argument for $1" >&2; exit 1; }
      DIRECTION="$2"
      shift 2
      ;;
    -i|--in-place)
      IN_PLACE=1
      shift
      ;;
    -o|--output)
      [[ $# -ge 2 ]] || { echo "Missing argument for $1" >&2; exit 1; }
      OUTPUT_FILE="$2"
      shift 2
      ;;
    -h|--help)
      usage 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage 1
      ;;
    *)
      if [[ -n "$TARGET_FILE" ]]; then
        echo "Only one target file is allowed." >&2
        exit 1
      fi
      TARGET_FILE="$1"
      shift
      ;;
  esac
done

if [[ -z "$TARGET_FILE" ]]; then
  echo "Missing target file." >&2
  usage 1
fi

if [[ ! -f "$TARGET_FILE" ]]; then
  echo "Target file not found: $TARGET_FILE" >&2
  exit 1
fi

if [[ ! -f "$MAP_FILE" ]]; then
  echo "Mapping file not found: $MAP_FILE" >&2
  exit 1
fi

if [[ "$DIRECTION" != "us2uk" && "$DIRECTION" != "uk2us" ]]; then
  echo "Direction must be 'us2uk' or 'uk2us'." >&2
  exit 1
fi

if [[ $IN_PLACE -eq 1 && -n "$OUTPUT_FILE" ]]; then
  echo "Use either --in-place or --output, not both." >&2
  exit 1
fi

tmp_out="$(mktemp)"
trap 'rm -f "$tmp_out"' EXIT

perl -CS -Mutf8 -e '
use strict;
use warnings;

my ($map_file, $direction, $target_file) = @ARGV;

open my $mf, "<:encoding(UTF-8)", $map_file
  or die "Cannot open mapping file: $map_file\n";

my @pairs;
while (my $line = <$mf>) {
    chomp $line;
    $line =~ s/\r$//;
    next if $line =~ /^\s*$/;
    next if $line =~ /^\s*#/;

    my ($us, $uk) = split /\t/, $line, 2;
    die "Bad mapping line (must be tab-separated): $line\n"
      unless defined $us && defined $uk;

    for ($us, $uk) {
        s/^\s+//;
        s/\s+$//;
    }

    push @pairs, ($direction eq "us2uk") ? [$us, $uk] : [$uk, $us];
}
close $mf;

# Longest first avoids partial collisions such as:
# "organize" before shorter fragments in more complex lists.
@pairs = sort { length($b->[0]) <=> length($a->[0]) } @pairs;

open my $fh, "<:encoding(UTF-8)", $target_file
  or die "Cannot open target file: $target_file\n";

local $/;
my $text = <$fh>;
close $fh;

sub match_case {
    my ($from, $to) = @_;

    return uc($to) if $from eq uc($from);
    return ucfirst(lc($to)) if $from eq ucfirst(lc($from));
    return lc($to) if $from eq lc($from);

    # Mixed case fallback: leave replacement in its base form
    return $to;
}

for my $pair (@pairs) {
    my ($src, $dst) = @$pair;
    my $quoted = quotemeta($src);

    # Whole-word replacement.
    # Works reasonably for normal alphabetic spellings.
    $text =~ s/\b($quoted)\b/match_case($1, $dst)/gei;
}

binmode STDOUT, ":encoding(UTF-8)";
print $text;
' "$MAP_FILE" "$DIRECTION" "$TARGET_FILE" > "$tmp_out"

if [[ $IN_PLACE -eq 1 ]]; then
  cp "$tmp_out" "$TARGET_FILE"
elif [[ -n "$OUTPUT_FILE" ]]; then
  cp "$tmp_out" "$OUTPUT_FILE"
else
  cat "$tmp_out"
fi