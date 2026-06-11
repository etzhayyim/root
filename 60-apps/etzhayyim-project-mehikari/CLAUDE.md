# etzhayyim-project-mehikari

`mehikari.etzhayyim.com` — 監視カメラ シーン/人物検索 + 警察向け B2G 営業 LangGraph。共通ルールは `60-apps/CLAUDE.md`、設計詳細は `_working/mehikari/DESIGN.md`、法令ガードは `_working/mehikari/COMPLIANCE-MEMO.md`。

## Components

| Component | Folder | Domain | Role |
|---|---|---|---|
| **mehikari** (mhk7r2vq) | `appview/etzhayyim-wasm-mehikari-mhk7r2vq` | `mehikari.etzhayyim.com` | T3 TS Native L3 dispatcher — `com.etzhayyim.apps.mehikari.{registerCamera,ingestClip,queryScene,queryPerson,reviewMatches,exportEvidence,registerProspect,draftSalesEmail,reviewSalesEmail,sendSalesEmail,handleInboundReply,unsubscribe,listQueries,getAuditTrail,listOutreach}` XRPC + MCP |

## CRITICAL — Domestic inference invariant

**顔特徴量 (face template) + raw frame は murakumo on-prem (国内 GPU) のみで処理。RunPod (US) / Cloudflare AI / 外部 LLM への送信は protocol レベルで禁止。** 詳細: `_working/mehikari/MURAKUMO-DOMESTIC-CONSTRAINT.md`。

| データ | 経路 |
|---|---|
| Face detection / arcface embedding / ReID embedding | murakumo on-prem (JP) のみ |
| Scene CLIP encoding | murakumo on-prem (JP) のみ (frame に顔が映る可能性) |
| Sales draft 生成 / safety_review LLM / scene query 自然言語パース | RunPod (US) OK — PII を含まない text のみ送信 |

CF Worker (this dir) は edge L3 dispatcher。直接 face / frame を扱わない (env.HYPERDRIVE 無し、murakumo URL も無し)。全推論は bpmn-dispatcher → LangGraph pod 経由。

## CRITICAL — Operating entity boundary

- **運営法人 = etzhayyim** (CLAUDE.md root rule)
- **Vendor (実装受託) = etzhayyim Japan株式会社**
- 警察との契約当事者 = etzhayyim。etzhayyim Japan は再委託先として開示
- 個人情報取扱事業者の届出主体 = etzhayyim
- 顔特徴量管理責任者 = etzhayyim CLO

## CRITICAL — Sales outreach gate

`com.etzhayyim.apps.mehikari.{registerProspect, draftSalesEmail, reviewSalesEmail, sendSalesEmail}` は以下を hard-block:

| Gate | 違反時の挙動 |
|---|---|
| opt-in source whitelist (展示会名簿 / 講演主催者経由 / 紹介 / inbound 問合せ) 外 | `registerProspect` が `rejectedOptInSource` |
| `reviewSalesEmail` 未承認 | `sendSalesEmail` が `rejectedNotApproved` |
| 09:00-17:00 JST 平日外 | `sendSalesEmail` が `rejectedOutsideHours` + 次営業日 09:00 JST に queue |
| SAFETY_GATES 11 種 violation | `draftSalesEmail` / `sendSalesEmail` が `rejectedSafety` |

詳細: `_working/mehikari/COMPLIANCE-MEMO.md` §6 + `_working/mehikari/langgraph_sales_outreach.py` (prototype)。

## CRITICAL — Person query gate

`com.etzhayyim.apps.mehikari.queryPerson` は以下 required (Lexicon enforced):

- `legalBasis.warrantRef` (令状) OR `legalBasis.enquiryRef` (捜査関係事項照会書) のいずれか非空
- `requesterDid` = `mehikari:investigator` role
- `supervisorDid` 承認 (consent helper)
- `reviewMatches` 記録なしには `exportEvidence` 不可

`queryScene` (人物特定なし) は令状不要、ただし `mehikari:operator` role + 監査ログは必須。

## Lexicon SSoT

`00-contracts/lexicons/com/etzhayyim/apps/mehikari/` 配下 15 本:

| 検索系 (8) | 営業系 (7) |
|---|---|
| registerCamera | registerProspect |
| ingestClip | draftSalesEmail |
| queryScene | reviewSalesEmail |
| queryPerson | sendSalesEmail |
| reviewMatches | handleInboundReply |
| exportEvidence | unsubscribe |
| listQueries | listOutreach |
| getAuditTrail | |

新規 NSID 追加時は root CLAUDE.md `LLM Coding Guardrails` を遵守:
1. JSON 作成 (camelCase, integer-only, ref-pattern)
2. `node 70-tools/scripts/contract/gen-lexicon-nsid-types.mjs`
3. `node 50-infra/cloudflare/workers/atproto/scripts/bundle-lexicons.mjs`
4. `node 70-tools/scripts/contract/gen-pds-lexicon-registry.mjs`
5. `cd 50-infra/cloudflare/workers/atproto && npx wrangler deploy`

## Deploy pre-reqs

1. Secrets Store に `mehikari_vault_master_key` (face-template 暗号化用 AES-256), `mehikari_ms_client_secret` (営業送信用 microsoft.etzhayyim.com 共有 secret 経路) を登録
2. DNS: `mehikari.etzhayyim.com` + `reply.mehikari.etzhayyim.com` (inbound email worker) の CNAME を `etzhayyim dns-sync` 経由
3. R2 bucket `etzhayyim-mehikari-clips` (police-only ACL, lifecycle 90日)
4. bpmn-dispatcher に `com.etzhayyim.apps.mehikari.*` の routing 登録 (LangGraph pod を pointers)
5. murakumo on-prem pod `mehikari-inference` を JP DC に常駐 (`_working/mehikari/MURAKUMO-DOMESTIC-CONSTRAINT.md` Phase 2)
6. `etzhayyim deploy` を `appview/etzhayyim-wasm-mehikari-mhk7r2vq/` で実行

## Phase gate (mid-deploy)

**Phase 0 (法務 / プロトタイプ)** 中は本 Worker を deploy しない。`_working/mehikari/COMPLIANCE-MEMO.md` の CLO triage + 外部弁護士 BAR-JP items クリア後にのみ Phase 1 へ。

## Related

- `_working/mehikari/DESIGN.md` — 全体設計
- `_working/mehikari/COMPLIANCE-MEMO.md` — 法令ガード + Kunal triage
- `_working/mehikari/LEAD-PIPELINE-SEED.md` — 47 県警 + JC3 + 警察庁の優先順
- `_working/mehikari/MURAKUMO-DOMESTIC-CONSTRAINT.md` — 国内拘束構成
- `_working/mehikari/langgraph_sales_outreach.py` — 営業 LangGraph mock prototype
- `60-apps/etzhayyim-project-microsoft/` — 送信経路 (`com.etzhayyim.apps.microsoft.sendMail`)
- `60-apps/etzhayyim-project-kaisya/` — consent helper (approval gate)
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/malak/langgraph/police_report.py` — evidence export base pattern
