#!/usr/bin/env bash
set -euo pipefail

TEMPLATE_DIR="appview/etzhayyim-wasm-unispsc-seg-43-it-s43t7k2m"
CSV_FILE="segments.csv"

if [[ ! -d "$TEMPLATE_DIR" ]]; then
  echo "Template directory not found: $TEMPLATE_DIR" >&2
  exit 1
fi

if [[ ! -f "$CSV_FILE" ]]; then
  echo "CSV file not found: $CSV_FILE" >&2
  exit 1
fi

is_skipped_code() {
  case "$1" in
    25|42|43|50|78|84) return 0 ;;
    *) return 1 ;;
  esac
}

escape_sed_replacement() {
  printf '%s' "$1" | sed 's/[\\/&]/\\\\&/g'
}

short_name_from_full() {
  # Use first two meaningful words (excluding conjunction "and").
  printf '%s\n' "$1" | awk '
    {
      c = 0
      out = ""
      for (i = 1; i <= NF; i++) {
        w = $i
        if (tolower(w) == "and") continue
        out = (out == "" ? w : out " " w)
        c++
        if (c == 2) break
      }
      print out
    }
  '
}

generate_nanoid() {
  local code2="$1"
  local rand=""
  while [[ ${#rand} -lt 5 ]]; do
    rand+="$(openssl rand -hex 8 | tr -dc 'a-z0-9')"
    rand="${rand:0:5}"
  done
  printf 's%s%s' "$code2" "$rand"
}

rewrite_file_common() {
  local file="$1"
  local code="$2"
  local name="$3"
  local slug="$4"
  local nanoid="$5"
  local short_name="$6"

  local esc_code esc_name esc_slug esc_nanoid esc_short_name
  esc_code="$(escape_sed_replacement "$code")"
  esc_name="$(escape_sed_replacement "$name")"
  esc_slug="$(escape_sed_replacement "$slug")"
  esc_nanoid="$(escape_sed_replacement "$nanoid")"
  esc_short_name="$(escape_sed_replacement "$short_name")"

  sed \
    -e "s/s43t7k2m/${esc_nanoid}/g" \
    -e "s/UNSPSC Seg 43 — IT\\/Telecom/UNSPSC Seg ${esc_code} — ${esc_short_name}/g" \
    -e "s/UNSPSC Segment 43 — Information Technology Broadcasting and Telecommunications/UNSPSC Segment ${esc_code} — ${esc_name}/g" \
    -e "s/IT\\/Broadcasting\\/Telecommunications/${esc_short_name}/g" \
    -e "s/IT\\/telecom/${esc_short_name}/g" \
    -e "s/Information Technology Broadcasting and Telecommunications/${esc_name}/g" \
    -e "s/etzhayyim:unispsc-seg-43/etzhayyim:unispsc-seg-${esc_code}/g" \
    -e "s/it-telecom/${esc_slug}/g" \
    -e "s/unispsc-it-telecom/unispsc-${esc_slug}/g" \
    -e "s/unispsc\\.seg43\\./unispsc.seg${esc_code}./g" \
    -e "s/unispsc-seg43/unispsc-seg${esc_code}/g" \
    -e "s/seg-43/seg-${esc_code}/g" \
    -e "s/Segment 43/Segment ${esc_code}/g" \
    -e "s/UNSPSC Segment 43/UNSPSC Segment ${esc_code}/g" \
    -e "s/UNSPSC Seg 43/UNSPSC Seg ${esc_code}/g" \
    -e "s/segment 43/segment ${esc_code}/g" \
    "$file" > "${file}.tmp"
  mv "${file}.tmp" "$file"
}

created=0

while IFS=, read -r raw_code raw_slug raw_name; do
  code="$(printf '%s' "$raw_code" | xargs)"
  slug="$(printf '%s' "$raw_slug" | xargs)"
  name="$(printf '%s' "$raw_name" | sed 's/^ *//; s/ *$//')"

  [[ -z "$code" ]] && continue
  is_skipped_code "$code" && continue

  code2="$(printf '%02d' "$code")"
  nanoid="$(generate_nanoid "$code2")"
  short_name="$(short_name_from_full "$name")"

  dir_name="etzhayyim-wasm-unispsc-seg-${code}-${slug}-${nanoid}"
  target_dir="appview/${dir_name}"

  if [[ -e "$target_dir" ]]; then
    echo "Skipping existing directory: $target_dir"
    continue
  fi

  mkdir -p "$target_dir/wit"

  cp "$TEMPLATE_DIR/main.go" "$target_dir/main.go"
  cp "$TEMPLATE_DIR/kotodama.jsonld" "$target_dir/kotodama.jsonld"
  cp "$TEMPLATE_DIR/go.mod" "$target_dir/go.mod"
  cp "$TEMPLATE_DIR/wit/world.wit" "$target_dir/wit/world.wit"
  cp "$TEMPLATE_DIR/wit/package.wit" "$target_dir/wit/package.wit"

  rewrite_file_common "$target_dir/main.go" "$code" "$name" "$slug" "$nanoid" "$short_name"
  rewrite_file_common "$target_dir/kotodama.jsonld" "$code" "$name" "$slug" "$nanoid" "$short_name"
  rewrite_file_common "$target_dir/go.mod" "$code" "$name" "$slug" "$nanoid" "$short_name"
  rewrite_file_common "$target_dir/wit/world.wit" "$code" "$name" "$slug" "$nanoid" "$short_name"
  rewrite_file_common "$target_dir/wit/package.wit" "$code" "$name" "$slug" "$nanoid" "$short_name"

  sed \
    -e "s/^\([[:space:]]*segmentCode[[:space:]]*=[[:space:]]*\)\"43\"/\1\"${code}\"/" \
    -e '/FollowCandidates: \[\]string{/,/},/c\
		FollowCandidates: []string{},' \
    "$target_dir/main.go" > "$target_dir/main.go.tmp"
  mv "$target_dir/main.go.tmp" "$target_dir/main.go"

  sed \
    -e "s/^module .*/module ${dir_name}/" \
    "$target_dir/go.mod" > "$target_dir/go.mod.tmp"
  mv "$target_dir/go.mod.tmp" "$target_dir/go.mod"

  sed \
    -e "s/\"avatar\": \"43\"/\"avatar\": \"${code}\"/" \
    "$target_dir/kotodama.jsonld" > "$target_dir/kotodama.jsonld.tmp"
  mv "$target_dir/kotodama.jsonld.tmp" "$target_dir/kotodama.jsonld"

  created=$((created + 1))
done < <(tail -n +2 "$CSV_FILE")

echo "created ${created} segment directories"
