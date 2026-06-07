# Domain Ingest Runbook

**Status**: active — 2026-04-23
**Design source-of-truth**: [ADR-0057](/Users/junkawasaki/github/etzhayyim-root/90-docs/adr/0057-common-crawl-domain-ingest-coverage-topology.md:1)

## Purpose

`domain-ingest` の運用手順を固定する。責務境界は次の 3 つ。

- `etzhayyim common-crawler`: acquisition / graph extraction / intel generation
- `etzhayyim domain-ingest`: normalization / enrichment / canonical PDS writes
- `etzhayyim coverage domain`: `mv_domain_coverage_live` を使う read-only reconciliation

この runbook は `domain-ingest` 実行と、その直後の strict health check までを扱う。

## Preconditions

### Required secrets

`local`

```bash
export etzhayyim_TOKEN='sk_live_...'
export MURAKUMO_API_KEY='...'
export etzhayyim_DATABASE_URL='postgres://root@127.0.0.1:14566/dev?sslmode=disable'
```

`common-crawl import only`

```bash
export etzhayyim_DATABASE_URL='postgres://root@127.0.0.1:14566/dev?sslmode=disable'
# phase5_inject.py 側の write auth / PDS auth 前提も別途満たすこと
```

### Runtime prerequisites

- `npx` が使えること (`domain-ingest local` 用)
- `70-tools/scripts/ingest-domain-data.ts` が見えること
- `CC_DATA_DIR` 配下に Common Crawl artifacts があること (`domain-ingest common-crawl` 用)
- `etzhayyim coverage domain --strict` が到達できる DB DSN を持つこと

## Command map

| Task | Command |
|---|---|
| local dataset の dry run | `etzhayyim domain-ingest --domain <slug> --limit <N> --dry-run` |
| local dataset の本投入 | `etzhayyim domain-ingest local --domain <slug> --limit <N>` |
| local dataset 投入 (LLM skip) | `etzhayyim domain-ingest local --domain <slug> --skip-llm` |
| CC intel import dry run | `etzhayyim domain-ingest common-crawl --source intel --dry-run` |
| CC graph import dry run | `etzhayyim domain-ingest common-crawl --source graph --dry-run` |
| live reconciliation health | `etzhayyim coverage domain --format json --strict` |
| runbook shortcut | `bash 70-tools/scripts/domain-coverage-strict-health.sh` |

## Standard procedure

### 1. Build CLI

```bash
cd /Users/junkawasaki/github/etzhayyim-root/70-tools/etzhayyim/etzhayyim
go build -o ../../../etzhayyim .
cd /Users/junkawasaki/github/etzhayyim-root
```

### 2. Dry run first

`local`

```bash
./etzhayyim domain-ingest --domain gtin --limit 500 --dry-run
```

`common crawl`

```bash
./etzhayyim domain-ingest common-crawl --source intel --dry-run
./etzhayyim domain-ingest common-crawl --source graph --dry-run
```

確認ポイント:

- domain filter が意図通りか
- record count が異常に多すぎないか / 0 でないか
- deprecation path (`common-crawler inject`) を使っていないか

### 3. Execute write path

`local`

```bash
./etzhayyim domain-ingest local --domain gtin --limit 500
```

`LLM queue を止めたい場合`

```bash
./etzhayyim domain-ingest local --domain hanrei --skip-llm
```

`common crawl`

```bash
./etzhayyim domain-ingest common-crawl --source intel --batch-size 200
./etzhayyim domain-ingest common-crawl --source graph --batch-size 200
```

## Post-write verification

write の直後に strict health check を流す。

```bash
./etzhayyim coverage domain --format json --strict > /tmp/domain-coverage.json
jq '.liveReadModel, (.reconciliation | length)' /tmp/domain-coverage.json
```

または shortcut:

```bash
etzhayyim_BIN=./etzhayyim bash 70-tools/scripts/domain-coverage-strict-health.sh
```

成功条件:

- `mv_domain_coverage_live` が読める
- `reconciliation` が 1 行以上返る
- `reconcileError` が空

## Failure triage

### `domain-ingest local` fails before write

確認順:

- `etzhayyim_TOKEN` が入っているか
- `MURAKUMO_API_KEY` が必要なモードなのに未設定でないか
- `npx` / `tsx` 実行環境が壊れていないか
- 入力ファイルが `/Volumes/251220/domain-data` に存在するか

### `domain-ingest common-crawl` fails

確認順:

- `CC_DATA_DIR` が正しいか
- `phase5_inject.py` が project copy か fallback copy で解決できているか
- `domain_intel.jsonl.gz` または `did_batch_*.sql` が存在するか
- PDS write auth 条件を満たしているか

### `coverage domain --strict` fails

まず次を確認:

```bash
echo "${etzhayyim_DATABASE_URL:-${DATABASE_URL:-}}"
./etzhayyim coverage domain --format json --no-reconcile | jq '.authorityModel, .liveReadModel'
```

切り分け:

- `--no-reconcile` は通るが `--strict` が落ちる
  `mv_domain_coverage_live` 参照または DB connectivity の問題
- `--no-reconcile` も落ちる
  CLI / DSN / runtime の問題

## CI / scheduled health check

GitHub Actions:

- [domain-coverage-health.yml](/Users/junkawasaki/github/etzhayyim-root/.github/workflows/domain-coverage-health.yml:1)

この workflow は次を行う。

- `etzhayyim` build
- `bash 70-tools/scripts/domain-coverage-strict-health.sh`
- JSON evidence artifact upload

必要 secret:

- `etzhayyim_DATABASE_URL` 推奨
- fallback として `DATABASE_URL`

## Notes

- `etzhayyim common-crawler inject` は互換 alias であり、新規運用では使わない
- `domain-ingest` は mutating command、`coverage domain` は read-only command
- strict health check は write path 後の最小確認として固定する
