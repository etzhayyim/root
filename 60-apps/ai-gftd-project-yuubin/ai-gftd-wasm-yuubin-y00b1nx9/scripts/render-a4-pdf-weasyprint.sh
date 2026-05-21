#!/bin/bash
# render-a4-pdf-weasyprint.sh — markdown → A4 PDF with embedded CJK fonts via WeasyPrint
#
# Prereq (local Mac):
#   brew install pandoc pango pipx
#   pipx install weasyprint
#   export PATH="$HOME/.local/bin:$PATH"
#
# Usage:
#   scripts/render-a4-pdf-weasyprint.sh INPUT.md OUTPUT.pdf [title]

set -euo pipefail

SRC=${1:?input markdown path required}
DST=${2:?output pdf path required}
TITLE=${3:-$(basename "$SRC" .md)}

export PATH="$HOME/.local/bin:$PATH"

for tool in pandoc weasyprint; do
  command -v "$tool" >/dev/null || { echo "$tool not installed" >&2; exit 1; }
done

TMPHTML=$(mktemp -t saikoku.XXXXXX.html)
trap "rm -f $TMPHTML" EXIT

# Inline CSS — A4, 25mm margins, Hiragino Mincho (macOS system CJK font).
# WeasyPrint embeds fonts by default, passes Web ゆうびん validator.
pandoc "$SRC" --metadata title="$TITLE" --standalone --output "$TMPHTML" -H /dev/stdin <<'HEADEOF'
<style>
@page { size: A4; margin: 25mm 20mm; }
html, body { font-family: "Hiragino Mincho ProN", "YuMincho", "MS Mincho", serif; font-size: 11pt; line-height: 1.85; color: #000; }
h1 { font-size: 16pt; text-align: center; margin: 0 0 24pt; letter-spacing: 0.4em; font-weight: normal; border-bottom: 1px solid #000; padding-bottom: 8pt; page-break-after: avoid; }
h2 { font-size: 13pt; margin: 16pt 0 6pt; }
p, li { text-align: justify; word-break: keep-all; line-break: strict; }
pre { font-family: inherit; white-space: pre-wrap; word-break: keep-all; margin: 0; font-size: 10.5pt; line-height: 1.9; }
.footer { margin-top: 24pt; font-size: 9pt; color: #555; text-align: right; }
</style>
HEADEOF

weasyprint "$TMPHTML" "$DST"

echo "✓ rendered: $DST"
ls -la "$DST"
