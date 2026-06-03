#!/bin/bash
# normalize-a4-docx.sh — inject A4 page size into pandoc-generated (or other) .docx
#
# Problem: pandoc --to=docx defaults to US Letter. Web ゆうびん requires A4 (210x297mm).
# Solution: unzip .docx → edit word/document.xml sectPr → re-zip.
#
# Usage:
#   scripts/normalize-a4-docx.sh INPUT.docx OUTPUT.docx

set -euo pipefail

SRC=${1:?input docx path required}
DST=${2:?output docx path required}

if [[ ! -f "$SRC" ]]; then echo "not found: $SRC" >&2; exit 1; fi

WORK=$(mktemp -d)
trap "rm -rf $WORK" EXIT

cd "$WORK"
unzip -q "$SRC"

# Inject A4 page size into empty <w:sectPr>, or replace existing pgSz.
# A4 portrait: w=11906 (210mm in twips), h=16838 (297mm)
# Margins: top/bottom 1440 (25.4mm), left/right 1134 (20mm)
PG='<w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1134" w:bottom="1440" w:left="1134" w:header="720" w:footer="720" w:gutter="0"/>'

# Remove any existing pgSz/pgMar, then inject ours
# Strategy 1: empty sectPr → inject
sed -i '' "s|<w:sectPr></w:sectPr>|<w:sectPr>${PG}</w:sectPr>|g" word/document.xml
sed -i '' "s|<w:sectPr/>|<w:sectPr>${PG}</w:sectPr>|g" word/document.xml

# Strategy 2: sectPr has body but no pgSz — inject before </w:sectPr>
# Only touch sectPr that doesn't already have pgSz
python3 <<'PYEOF'
import re, sys
path = 'word/document.xml'
with open(path) as f: xml = f.read()

PG = '<w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1134" w:bottom="1440" w:left="1134" w:header="720" w:footer="720" w:gutter="0"/>'

# Replace existing pgSz/pgMar (non-A4 → A4)
xml = re.sub(r'<w:pgSz[^/]*/>', '', xml)
xml = re.sub(r'<w:pgMar[^/]*/>', '', xml)

# Inject into every <w:sectPr> that is non-empty but lacks pgSz now
def inject(m):
    inner = m.group(1)
    if '<w:pgSz' in inner: return m.group(0)
    return f'<w:sectPr>{PG}{inner}</w:sectPr>'
xml = re.sub(r'<w:sectPr>(.*?)</w:sectPr>', inject, xml, flags=re.DOTALL)
# empty sectPr
xml = xml.replace('<w:sectPr></w:sectPr>', f'<w:sectPr>{PG}</w:sectPr>')
xml = xml.replace('<w:sectPr/>', f'<w:sectPr>{PG}</w:sectPr>')

with open(path,'w') as f: f.write(xml)
PYEOF

# Verify
if ! grep -q 'w:w="11906"' word/document.xml; then
  echo "WARN: A4 injection may have failed" >&2
fi

# Repack preserving original order/compression
DST_ABS=$(realpath "$DST" 2>/dev/null || (cd "$(dirname "$DST")" && echo "$PWD/$(basename "$DST")"))
rm -f "$DST_ABS"
zip -qr "$DST_ABS" . -x '.*'

echo "✓ normalized → $DST_ABS"
ls -la "$DST_ABS"
