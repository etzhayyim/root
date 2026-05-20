#!/usr/bin/env bash
# validate-tex.sh — LaTeX コンパイル検証 (pdflatex 2-pass)
# Usage: bash scripts/validate-tex.sh papers/moex-distributed-webgpu
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <paper-dir>"
  echo "  paper-dir: papers/ 内の論文ディレクトリ (例: papers/moex-distributed-webgpu)"
  exit 1
fi

PAPER_DIR="$PROJECT_ROOT/$1"

if [[ ! -d "$PAPER_DIR" ]]; then
  echo "ERROR: $PAPER_DIR not found"
  exit 1
fi

# main.tex を探す
MAIN_TEX=""
if [[ -f "$PAPER_DIR/main.tex" ]]; then
  MAIN_TEX="main.tex"
else
  TEX_COUNT=$(find "$PAPER_DIR" -maxdepth 1 -name '*.tex' | wc -l | tr -d ' ')
  if [[ "$TEX_COUNT" -eq 0 ]]; then
    echo "ERROR: No .tex files found in $PAPER_DIR"
    exit 1
  elif [[ "$TEX_COUNT" -eq 1 ]]; then
    MAIN_TEX="$(basename "$(find "$PAPER_DIR" -maxdepth 1 -name '*.tex')")"
  else
    echo "ERROR: Multiple .tex files found. Rename the primary file to main.tex"
    exit 1
  fi
fi

# pdflatex の存在確認
if ! command -v pdflatex &>/dev/null; then
  echo "ERROR: pdflatex not found. Install TeX Live:"
  echo "  macOS:  brew install --cask mactex"
  echo "  Ubuntu: sudo apt-get install texlive-full"
  exit 1
fi

echo "=== LaTeX Validation ==="
echo "Paper directory: $PAPER_DIR"
echo "Main TeX file:   $MAIN_TEX"

# 一時ディレクトリでコンパイル
BUILD_TMPDIR="$(mktemp -d)"
trap 'rm -rf "$BUILD_TMPDIR"' EXIT

cp -a "$PAPER_DIR"/. "$BUILD_TMPDIR"/
cd "$BUILD_TMPDIR"

LOG_FILE="${MAIN_TEX%.tex}.log"
PDF_FILE="${MAIN_TEX%.tex}.pdf"

# Pass 1
echo ""
echo "--- Pass 1/2 ---"
if pdflatex -interaction=nonstopmode "$MAIN_TEX" > /dev/null 2>&1; then
  echo "OK: Pass 1 succeeded"
else
  echo "WARN: Pass 1 had issues (may be resolved in pass 2)"
fi

# bibtex (必要な場合)
AUX_FILE="${MAIN_TEX%.tex}.aux"
if grep -q '\\citation' "$AUX_FILE" 2>/dev/null && [[ -f "$(find . -maxdepth 1 -name '*.bib' | head -1)" ]]; then
  echo ""
  echo "--- Running bibtex ---"
  bibtex "${MAIN_TEX%.tex}" > /dev/null 2>&1 || echo "WARN: bibtex had issues"
fi

# Pass 2
echo ""
echo "--- Pass 2/2 ---"
if pdflatex -interaction=nonstopmode "$MAIN_TEX" > /dev/null 2>&1; then
  echo "OK: Pass 2 succeeded"
else
  echo "ERROR: Pass 2 failed"
fi

# 結果確認
echo ""
echo "=== Results ==="

if [[ -f "$PDF_FILE" ]]; then
  PDF_SIZE=$(du -h "$PDF_FILE" | cut -f1)
  PAGE_COUNT=$(strings "$PDF_FILE" | grep -c '/Type /Page' || echo "?")
  echo "PDF:   OK ($PDF_SIZE, $PAGE_COUNT pages)"
else
  echo "PDF:   FAILED (not generated)"
fi

# 警告・エラー抽出
echo ""
echo "--- Warnings ---"
WARNINGS=$(grep -c '^LaTeX Warning\|^Package .* Warning' "$LOG_FILE" 2>/dev/null || echo "0")
echo "Count: $WARNINGS"
if [[ "$WARNINGS" -gt 0 ]]; then
  grep '^LaTeX Warning\|^Package .* Warning' "$LOG_FILE" | head -20
fi

echo ""
echo "--- Errors ---"
ERRORS=$(grep -c '^!' "$LOG_FILE" 2>/dev/null || echo "0")
echo "Count: $ERRORS"
if [[ "$ERRORS" -gt 0 ]]; then
  grep '^!' "$LOG_FILE" | head -20
fi

# Overfull/Underfull boxes
echo ""
echo "--- Overfull/Underfull boxes ---"
BOXES=$(grep -c 'Overfull\|Underfull' "$LOG_FILE" 2>/dev/null || echo "0")
echo "Count: $BOXES"

# arXiv サイズ制限チェック (10MB)
if [[ -f "$PDF_FILE" ]]; then
  PDF_BYTES=$(wc -c < "$PDF_FILE")
  if [[ "$PDF_BYTES" -gt 10485760 ]]; then
    echo ""
    echo "WARN: PDF exceeds arXiv 10MB limit ($PDF_SIZE)"
  fi
fi

echo ""
if [[ "$ERRORS" -eq 0 && -f "$PDF_FILE" ]]; then
  echo "=== PASS: Ready for arXiv submission ==="
else
  echo "=== FAIL: Fix errors before submission ==="
  exit 1
fi
