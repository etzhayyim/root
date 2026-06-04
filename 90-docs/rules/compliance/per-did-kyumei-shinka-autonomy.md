# Per-DID Kyumei/Shinka Autonomy Rules

Last updated: 2026-04-13

## Principle

`shinka`、`koji`、`kyumei`、domain knowledge の実行主体は app ではなく DID。  
親DIDとsub-DIDを同じ app に属させても、運用状態と知識更新は DID ごとに独立させる。

## Mandatory Rules

1. `liveData.status` は DID 単位で記録し、`actorDid` を必須とする。
2. sub-DID を持つ app は、各 sub-DID ごとに `completed` status を生成できなければならない。
3. readiness 集計は app 合算だけでなく DID 内訳を保持しなければならない。
4. monitor は app 健康度に加えて DID freshness (`last_updated`) を警告できなければならない。
5. 親DIDによる代理更新だけで sub-DID を「更新済み」と見なしてはならない。
6. すべての actor/app DID は `/_heartbeat` を持ち、joucho cadence から `shouldDrill`, `shouldValidate`, `shouldAnalyze`, `shouldEngage` を解決しなければならない。
7. すべての actor/app DID は `shinkaEvolution` と `shinkaKnowledge` の少なくとも 2 系統の進化記録面を持たなければならない。
8. すべての actor/app DID は domain knowledge の正本として `convoSystemPrompt`, `description`, `capabilities` の 3 点を欠いてはならない。
9. `koji` と `kyumei` は親DIDだけの総称タスクではなく、対象 DID ごとに freshness と knowledge write を持たなければならない。
10. custom Worker を持たない actor でも、中央 shinka executor から見て上記 6-9 の要件を満たす manifest/metadata を備えなければならない。

## Standard Rule

全 actor に適用する標準要件は次の 4 軸。

1. `shinka`: cadence-driven heartbeat と進化ログ
2. `koji`: freshness を持つ self-repair / validation ループ
3. `kyumei`: self-information gathering と knowledge write
4. `domain knowledge`: prompt, capabilities, description, sub-DID knowledge surface

`standard compliant` と見なす最小条件:

1. source に `resolveHeartbeatCadence`
2. source に `shouldDrill`, `shouldValidate`, `shouldAnalyze`, `shouldEngage`
3. source または manifest に `shinkaEvolution`, `shinkaKnowledge`
4. manifest に `convoSystemPrompt`, `description`, `capabilities`

## Transitional Allowance

- 既存 app では `gatherSubDID` のような親DID経由コマンドを暫定許可する。
- ただし生成される status は必ず対象 DID を `actorDid` で明示する。
- 中央 shinka worker が代理実行する場合でも、対象 actor 側 metadata が空なら non-compliant とみなす。

## Verification

```bash
go run ./70-tools/etzhayyim/etzhayyim apps kyumei-koji -nanoid <nanoid> -dir ./60-apps -json
go run ./70-tools/etzhayyim/etzhayyim monitor shinka -nanoid <nanoid> -dir ./60-apps --freshness-hours 24 --json
go run ./70-tools/etzhayyim/etzhayyim code-quality -check magatama_lint
```
