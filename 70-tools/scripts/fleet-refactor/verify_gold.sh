#!/usr/bin/env bash
# verify_gold — gold-corpus の各 .clj を clj-kondo + bb (require ns) で検証する。
# CPT/SFT に入れる前に「実際にロードできる」ことを保証する (Fable 実装の自己検証)。
set -uo pipefail
DIR="$(cd "$(dirname "$0")/gold-corpus" && pwd)"
pass=0; fail=0
# bb のクラスパス用に ns→パス構造を temp に展開
work="$(mktemp -d)"; trap 'rm -rf "$work"' EXIT
# langgraph/langchain-clj を使う gold のため、依存のクラスパスを前置する
DEPCP="$(bb --config "$DIR/deps-bb.edn" -e '(println (System/getProperty "java.class.path"))' 2>/dev/null | tail -1)"
[ -n "$DEPCP" ] && CP="$work:$DEPCP" || CP="$work"
for f in "$DIR"/*.clj; do
  [ -e "$f" ] || continue
  ns=$(grep -m1 -oE '\(ns [a-zA-Z0-9._-]+' "$f" | sed 's/(ns //')
  [ -z "$ns" ] && { echo "NO-NS  $(basename "$f")"; fail=$((fail+1)); continue; }
  rel=$(echo "$ns" | tr '.' '/' | tr '-' '_')
  mkdir -p "$work/$(dirname "$rel")"; cp "$f" "$work/$rel.clj"
done
for f in "$DIR"/*.clj; do
  [ -e "$f" ] || continue
  ns=$(grep -m1 -oE '\(ns [a-zA-Z0-9._-]+' "$f" | sed 's/(ns //')
  base=$(basename "$f")
  k=$(clj-kondo --lint "$f" --fail-level error \
        --config '{:linters {:namespace-name-mismatch {:level :off}}}' \
        >/dev/null 2>&1 && echo ok || echo LINT)
  b=$(bb -cp "$CP" -e "(require '$ns)" >/dev/null 2>&1 && echo ok || echo BB)
  if [ "$k" = ok ] && [ "$b" = ok ]; then echo "PASS  $base"; pass=$((pass+1))
  else echo "FAIL  $base  [kondo:$k bb:$b]"; fail=$((fail+1)); fi
done
echo "---"; echo "gold-corpus: $pass pass / $fail fail"
[ "$fail" -eq 0 ]
