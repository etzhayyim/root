#!/bin/bash
# render-a4-pdf.sh — markdown → A4 PDF with embedded CJK fonts (for Web ゆうびん / e内容証明)
#
# Prereq (local Mac):
#   brew install pandoc
#   brew install --cask basictex        # ~100MB
#   eval "$(/usr/libexec/path_helper)"
#   sudo tlmgr update --self
#   sudo tlmgr install collection-langjapanese haranoaji
#
# Usage:
#   scripts/render-a4-pdf.sh INPUT.md OUTPUT.pdf [title]
#
# Web ゆうびん accepts:
#   * PDF with embedded fonts + A4 page size (210x297mm)
#   * .docx with A4 page size (use scripts/normalize-a4-docx.sh)

set -euo pipefail

SRC=${1:?input markdown path required}
DST=${2:?output pdf path required}
TITLE=${3:-$(basename "$SRC" .md)}

if ! command -v pandoc >/dev/null; then echo "pandoc not installed. brew install pandoc" >&2; exit 1; fi
if ! command -v xelatex >/dev/null; then
  echo "xelatex not found. run:" >&2
  echo "  brew install --cask basictex && eval \"\$(/usr/libexec/path_helper)\" && sudo tlmgr install collection-langjapanese haranoaji" >&2
  exit 1
fi

pandoc "$SRC" \
  --pdf-engine=xelatex \
  -V papersize=a4 \
  -V geometry:margin=25mm \
  -V CJKmainfont="Hiragino Mincho ProN" \
  -V CJKsansfont="Hiragino Sans" \
  -V CJKmonofont="Hiragino Mincho ProN" \
  -V mainfont="Hiragino Mincho ProN" \
  -V fontsize=11pt \
  -V linestretch=1.6 \
  --metadata title="$TITLE" \
  -o "$DST"

echo "✓ rendered: $DST"
ls -la "$DST"
