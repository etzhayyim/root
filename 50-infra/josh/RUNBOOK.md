# josh-proxy — per-actor public mirror runbook (ADR-2606231200, A-axis)

Bidirectional `monorepo ⇄ com-etzhayyim-<name>` code distribution. josh serves
*virtual* filtered git views; a clone of a view is a normal repo and pushes flow
back into the right `20-actors/<name>` subtree. Chosen over submodule (pointer
sync blows up at 59→1245 actors) and over plain `git subtree` (one-way only).

## Run the proxy

```bash
# container (recommended) — serves on :8002
docker run -d --name josh -p 8002:8002 \
  -v "$PWD/josh-data:/data/git" \
  joshproject/josh-proxy:latest \
  --remote https://github.com/etzhayyim

# or cargo install josh-proxy && josh-proxy --local ./josh-data \
#      --remote https://github.com/etzhayyim --port 8002
```

## Clone one actor's view (read, or PR-write back)

```bash
git clone "http://localhost:8002/etzhayyim/root.git:/20-actors/cargo.git" \
          com-etzhayyim-cargo
# edit, commit, push -> lands in etzhayyim/root under 20-actors/cargo
```

## Publish a public mirror repo

`bb actor:publish cargo --apply` does the rest: it ensures the public
`etzhayyim/com-etzhayyim-cargo` repo exists (`gh repo create`) and seeds the
mirror branch (`git subtree split` for the first push; josh keeps it in sync
thereafter). Run josh-proxy as the durable two-way path; `subtree split` is the
one-time seed / CI fallback when the proxy is down.

## Filter spec

`workspace.josh` lists the per-actor prefixes. Each `:/20-actors/<name>` is the
subdir filter that becomes one public repo. Add a line per actor as it
graduates from the cargo/vessel/port pilot.

## Why not the alternatives (full comparison: ADR-2606231200)

submodule (pointer-sync hell) · subtree (one-way) · Copybara (Java/Bazel-heavy,
for >1000 repos) · DataLad (git-annex overhead, for data not code) · Radicle
(sovereignty — handled separately by kotoba-rad, the B-axis).
