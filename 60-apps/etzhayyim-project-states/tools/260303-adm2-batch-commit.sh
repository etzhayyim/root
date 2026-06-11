#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

TARGETS_FILE="${1:-projects/etzhayyim-project-states/tmp/260303-adm2-batch-50-targets.jsonl}"
TEMPLATE_DIR="60-apps/etzhayyim-project-states/appview/etzhayyim-performer-sys-etzhayyim-actors-pba7d22f-org-gov-usa-state-generic-u1s2s3g4"

if [[ ! -f "$TARGETS_FILE" ]]; then
  echo "targets file not found: $TARGETS_FILE" >&2
  exit 1
fi

nanoid() {
  python3 - <<'PY'
import random,string
print(''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8)))
PY
}

count=0
while IFS= read -r line; do
  [[ -z "$line" ]] && continue

  slug="$(jq -r '.suggested_slug' <<<"$line")"
  iso="$(jq -r '.iso' <<<"$line")"
  country="$(jq -r '.country' <<<"$line")"
  shape_name="$(jq -r '.pilot_shape_name' <<<"$line")"

  iso_l="$(echo "$iso" | tr 'A-Z' 'a-z')"
  id8="$(nanoid)"

  dst_dir="60-apps/etzhayyim-project-states/appview/etzhayyim-performer-sys-etzhayyim-actors-pba7d22f-${slug}"
  if [[ -d "$dst_dir" ]]; then
    echo "skip existing: $slug"
    continue
  fi

  cp -R "$TEMPLATE_DIR" "$dst_dir"

  SLUG="$slug" ISO_L="$iso_l" ISO_U="$iso" COUNTRY="$country" SHAPE_NAME="$shape_name" NANOID="$id8" DST_DIR="$dst_dir" python3 - <<'PY'
import os
import re
from pathlib import Path

slug = os.environ["SLUG"]
iso_l = os.environ["ISO_L"]
iso_u = os.environ["ISO_U"]
country = os.environ["COUNTRY"]
shape_name = os.environ["SHAPE_NAME"]
nanoid = os.environ["NANOID"]

d = Path(os.environ["DST_DIR"])
old_jsonld = d / 'usa-state-government-generic.jsonld'
new_jsonld = d / f'{slug}.jsonld'
old_jsonld.rename(new_jsonld)

safe_slug = re.sub(r'-dst-([0-9]+)', lambda m: f'-dst-n{m.group(1)}', slug)
comp_id = f'{safe_slug}-component'
wasm_name = f"build/{comp_id.replace('-', '_')}_s.wasm"

repls = [
    ('gov-usa-state-generic-u1s2s3g4-component', f'{slug}-component'),
    ('gov_usa_state_generic_u1s2s3g4_component_s.wasm', f'{slug.replace('-', '_')}_component_s.wasm'),
    ('gov-usa-state-generic-u1s2s3g4-spin', f'{slug}-spin'),
    ('gov-usa-state-generic-component', f'{slug}-component'),
    ('State Government (Generic)', f'{shape_name} Municipal Government'),
    ('United States', country),
    ('usa', iso_l),
    ('USA', iso_u),
    ('u1s2s3g4', nanoid),
    ('government-state-generic', 'government-adm2-district'),
    ('state governments, providing access to state-level administrative services and policies',
     'municipal administrations with district-level local public services and governance'),
]

for f in [d/'go.mod', d/'main.go', d/'spin.toml', d/'k8s'/'spinapp.yaml', new_jsonld, d/'wit'/'world.wit']:
    txt = f.read_text(encoding='utf-8')
    for a,b in repls:
        txt = txt.replace(a,b)
    txt = txt.replace('if path == "/api/mcp" && r.Method == http.MethodPost {',
                      'if path == "/api/grpc" && r.Method == http.MethodPost {')
    txt = txt.replace('"endpoint":    "https://etzhayyim.com/" + componentNanoID + "/api/mcp",',
                      '"endpoint":    "https://" + componentNanoID + ".etzhayyim.com/api/grpc",')
    txt = txt.replace('/api/mcp', '/api/grpc')
    f.write_text(txt, encoding='utf-8')

# enforce go module path and wit package
(d/'go.mod').write_text(
    (d/'go.mod').read_text(encoding='utf-8').replace(
        re.search(r'^module\s+.*$', (d/'go.mod').read_text(encoding='utf-8'), re.M).group(0),
        f'module github.com/etzhayyim-ai/performer-sys-etzhayyim-actors-pba7d22f-{slug}'
    ),
    encoding='utf-8'
)

wit = d/'wit'/'world.wit'
wit_txt = wit.read_text(encoding='utf-8')
wit_txt = re.sub(r'^package\s+[^;]+;', f'package etzhayyim:{slug};', wit_txt, flags=re.M)
wit.write_text(wit_txt, encoding='utf-8')

# rewrite spin.toml with TOML-safe component id
spin = d/'spin.toml'
spin_txt = spin.read_text(encoding='utf-8')
cmd = re.search(r'^command\s*=\s*"([^"]+)"', spin_txt, re.M).group(1)
cmd = re.sub(r'-o\s+build/[^\s"]+', f'-o {wasm_name}', cmd)
spin_new = f'''spin_manifest_version = 2

[application]
name = "{comp_id}"
version = "0.1.0"

[[trigger.http]]
component = "{comp_id}"
route = "/..."

[component."{comp_id}"]
source = "{wasm_name}"
allowed_outbound_hosts = ["http://*", "https://*"]
key_value_stores = ["default"]

[component."{comp_id}".build]
command = "{cmd}"
watch = ["**/*.go", "go.mod"]
'''
spin.write_text(spin_new, encoding='utf-8')

# enforce KV-backed runtime in generated main.go
main_go = d / 'main.go'
main_txt = main_go.read_text(encoding='utf-8')
if '"github.com/spinframework/spin-go-sdk/v2/kv"' not in main_txt:
    m = re.search(r'import\s*\((.*?)\n\)', main_txt, flags=re.S)
    if m:
        body = m.group(1).rstrip() + '\n\t"github.com/spinframework/spin-go-sdk/v2/kv"\n'
        main_txt = main_txt[:m.start(1)] + body + main_txt[m.end(1):]

kv_helper = '''
func ensureKVStore() error {
\ts, err := kv.OpenStore("default")
\tif err != nil {
\t\treturn err
\t}
\ts.Close()
\treturn nil
}
'''

if 'func ensureKVStore() error {' not in main_txt:
    m_main = re.search(r'\nfunc main\(\) \{\}', main_txt)
    if m_main:
        main_txt = main_txt[:m_main.start()] + '\n' + kv_helper + '\n' + main_txt[m_main.start():]
    else:
        main_txt += '\n' + kv_helper + '\n'

if '_ = ensureKVStore()' not in main_txt:
    m_init = re.search(r'func init\(\) \{', main_txt)
    if m_init:
        ins = m_init.end()
        main_txt = main_txt[:ins] + '\n\t_ = ensureKVStore()' + main_txt[ins:]
    else:
        m_main = re.search(r'\nfunc main\(', main_txt)
        if m_main:
            main_txt = main_txt[:m_main.start()] + '\nfunc init() {\n\t_ = ensureKVStore()\n}\n' + main_txt[m_main.start():]
        else:
            main_txt += '\nfunc init() {\n\t_ = ensureKVStore()\n}\n'

main_go.write_text(main_txt, encoding='utf-8')
PY

  (cd "$dst_dir" && go mod tidy >/dev/null)

  scripts/260303-check-wasm-manifests.sh "$dst_dir/main.go" >/dev/null
  rg -q 'key_value_stores = \["default"\]' "$dst_dir/spin.toml"
  rg -q 'keyValueStores:' "$dst_dir/k8s/spinapp.yaml"
  rg -q 'spin-go-sdk/v2/kv|kv.OpenStore\(' "$dst_dir/main.go"

  git add "$dst_dir"
  git commit -m "feat(states): add ${iso} ADM2 ${slug#org-gov-${iso_l}-dst-}"
  git push

  count=$((count+1))
  echo "done ${count}: ${slug}"
done < "$TARGETS_FILE"

echo "completed=${count}"
