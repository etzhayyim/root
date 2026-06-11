# bio-gene wasm components

`etzhayyim-project-researcher-bio-gene` の component scaffold。

## Components
- `bio-gene-mcp-gateway`
- `bio-gene-literature-worker`
- `bio-gene-variant-worker`
- `bio-gene-omics-worker`
- `bio-gene-assay-planner`
- `bio-gene-governance-policy`
- `bio-gene-evidence-store`

## Intended Flow
1. `bio-gene-mcp-gateway` が researcher / agent からの要求を受ける
2. `bio-gene-literature-worker` が source delta を取得し正規化する
3. `bio-gene-variant-worker` と `bio-gene-omics-worker` が evidence を解釈する
4. `bio-gene-assay-planner` が validation plan を作る
5. `bio-gene-governance-policy` が release 判定を行う
6. `bio-gene-evidence-store` が packet を保持・再配布する

各 component は現時点では scaffold。実装時は `sources.jsonld` と `crawler-normalizer-design.jsonld` を契約面の基準にする。
