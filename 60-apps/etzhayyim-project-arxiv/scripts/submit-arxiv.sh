#!/usr/bin/env bash
# submit-arxiv.sh — arXiv 投稿用 tarball を生成する
# Usage: bash scripts/submit-arxiv.sh papers/moex-distributed-webgpu
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <paper-dir>"
  echo "  paper-dir: papers/ 内の論文ディレクトリ (例: papers/moex-distributed-webgpu)"
  exit 1
fi

PAPER_DIR="$PROJECT_ROOT/$1"
PAPER_NAME="$(basename "$1")"
DATE_TAG="$(date +%Y%m%d)"
DIST_DIR="$PROJECT_ROOT/dist"

if [[ ! -d "$PAPER_DIR" ]]; then
  echo "ERROR: $PAPER_DIR not found"
  exit 1
fi

# main.tex を探す
MAIN_TEX=""
if [[ -f "$PAPER_DIR/main.tex" ]]; then
  MAIN_TEX="main.tex"
else
  # .tex ファイルを自動検出
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

echo "=== arXiv Submission Packager ==="
echo "Paper directory: $PAPER_DIR"
echo "Main TeX file:   $MAIN_TEX"

# Step 1: pdflatex コンパイル検証
echo ""
echo "--- Step 1: Compiling LaTeX (validation) ---"
cd "$PAPER_DIR"

# 一時ディレクトリでコンパイル（元ディレクトリを汚さない）
BUILD_TMPDIR="$(mktemp -d)"
trap 'rm -rf "$BUILD_TMPDIR"' EXIT

cp -a "$PAPER_DIR"/. "$BUILD_TMPDIR"/
cd "$BUILD_TMPDIR"

# pdflatex 2-pass
pdflatex -interaction=nonstopmode -halt-on-error "$MAIN_TEX" > /dev/null 2>&1 || {
  echo "ERROR: First pdflatex pass failed. Running verbose:"
  pdflatex -interaction=nonstopmode "$MAIN_TEX"
  exit 1
}
pdflatex -interaction=nonstopmode -halt-on-error "$MAIN_TEX" > /dev/null 2>&1 || {
  echo "ERROR: Second pdflatex pass failed"
  exit 1
}

PDF_FILE="${MAIN_TEX%.tex}.pdf"
if [[ ! -f "$PDF_FILE" ]]; then
  echo "ERROR: PDF not generated"
  exit 1
fi

PAGE_COUNT=$(strings "$PDF_FILE" | grep -c '/Type /Page' || echo "?")
echo "OK: PDF generated ($PAGE_COUNT pages)"

# Step 2: arXiv 用 tarball 生成
echo ""
echo "--- Step 2: Creating arXiv tarball ---"
cd "$PAPER_DIR"
mkdir -p "$DIST_DIR"

TARBALL="$DIST_DIR/${PAPER_NAME}-arxiv-${DATE_TAG}.tar.gz"

# arXiv に含めるファイルを収集
FILES_TO_INCLUDE=()

# .tex ファイル
while IFS= read -r f; do
  FILES_TO_INCLUDE+=("$f")
done < <(find . -maxdepth 1 -name '*.tex' -printf '%P\n' 2>/dev/null || find . -maxdepth 1 -name '*.tex' | sed 's|^\./||')

# .bib ファイル (存在すれば)
while IFS= read -r f; do
  FILES_TO_INCLUDE+=("$f")
done < <(find . -maxdepth 1 -name '*.bib' -printf '%P\n' 2>/dev/null || find . -maxdepth 1 -name '*.bib' | sed 's|^\./||')

# .bst ファイル (存在すれば)
while IFS= read -r f; do
  FILES_TO_INCLUDE+=("$f")
done < <(find . -maxdepth 1 -name '*.bst' -printf '%P\n' 2>/dev/null || find . -maxdepth 1 -name '*.bst' | sed 's|^\./||')

# .sty ファイル (存在すれば)
while IFS= read -r f; do
  FILES_TO_INCLUDE+=("$f")
done < <(find . -maxdepth 1 -name '*.sty' -printf '%P\n' 2>/dev/null || find . -maxdepth 1 -name '*.sty' | sed 's|^\./||')

# .cls ファイル (存在すれば)
while IFS= read -r f; do
  FILES_TO_INCLUDE+=("$f")
done < <(find . -maxdepth 1 -name '*.cls' -printf '%P\n' 2>/dev/null || find . -maxdepth 1 -name '*.cls' | sed 's|^\./||')

# 画像ファイル (figures/, images/, fig/ ディレクトリ)
for dir in figures images fig; do
  if [[ -d "$dir" ]]; then
    while IFS= read -r f; do
      FILES_TO_INCLUDE+=("$f")
    done < <(find "$dir" -type f \( -name '*.pdf' -o -name '*.png' -o -name '*.jpg' -o -name '*.eps' -o -name '*.svg' \) -printf '%P\n' 2>/dev/null || find "$dir" -type f \( -name '*.pdf' -o -name '*.png' -o -name '*.jpg' -o -name '*.eps' -o -name '*.svg' \) | sed "s|^\./||")
  fi
done

# .bbl ファイル (bibtex 生成済みの場合は同梱 — arXiv 推奨)
BBL_FILE="${MAIN_TEX%.tex}.bbl"
if [[ -f "$BUILD_TMPDIR/$BBL_FILE" ]]; then
  cp "$BUILD_TMPDIR/$BBL_FILE" "$PAPER_DIR/$BBL_FILE"
  FILES_TO_INCLUDE+=("$BBL_FILE")
  echo "Included generated .bbl file"
fi

if [[ ${#FILES_TO_INCLUDE[@]} -eq 0 ]]; then
  echo "ERROR: No files to include in tarball"
  exit 1
fi

echo "Files to include:"
printf '  %s\n' "${FILES_TO_INCLUDE[@]}"

tar czf "$TARBALL" "${FILES_TO_INCLUDE[@]}"
TARBALL_SIZE=$(du -h "$TARBALL" | cut -f1)

echo ""
echo "=== Done ==="
echo "Tarball:  $TARBALL"
echo "Size:     $TARBALL_SIZE"
echo ""
echo "Contents:"
tar tzf "$TARBALL" | sed 's/^/  /'
echo ""
echo "--- Next steps ---"
echo "1. Go to https://arxiv.org/submit"
echo "2. Upload: $TARBALL"
echo "3. Select category: cs.DC (Distributed Computing) or cs.LG (Machine Learning)"
echo "4. Fill in metadata (title, authors, abstract)"
echo "5. Submit"
