---
id: adr-2606122000-tate-kaiyaku-worldwide-r2-status
title: "ADR-2606122000: tate 盾 R2 status — 34-wave coverage loop の到達点 (kaiyaku compose 含む)"
status: active
doc_type: adr
topic: tate-r2-status
authoritative: true
last_verified: 2026-06-12
priority: 4.0
axis: architecture
weight: 0.40
priority_note: "status snapshot — declares tate R2 and fixes the invariant system the 34-wave loop built"
authoritative_for:
  - tate-r2-status
depends_on:
  - adr-2606112300
  - adr-2606112400
related:
  - adr-2606112200
supersedes: []
superseded_by: []
---

# ADR-2606122000: tate 盾 R2 status — 34-wave coverage loop の到達点

**Status**: active
**Date**: 2026-06-12
**Deciders**: Jun Kawasaki (loop 指示: 「coverage, 成熟度を上げて」×33 iterations)

# Context

ADR-2606112300 (R0 JP) と ADR-2606112400 (R1 worldwide layer) の後、30分周期の
/loop が 33 iterations 走り、coverage と成熟度を毎 wave 交互に積んだ。本 ADR は
その到達点を固定し、tate を **R2 (registry maturity)** と宣言する。

# Decision — R2 の内容 (到達点)

**Coverage** (全数値は registry/テストに機械照合 — wave 25):
- 30 法域 (jp us eu uk de kr fr au ca it es nl br tw sg in cn pl se at pt ie ch dk
  fi no mx be ar nz) + **米国全50州** (small-claims 上限 + answer 期限 + ARL)
- 手続き 114 (civil 36 / labor 29 / housing 16 / enforcement 14 / insolvency 9 /
  family 10) · 条項 76 パターン · critical 失権期限 census 25+ · protective 88
- 解雇通知は**全30法域**で専門応答を持つ (civil-only 0, wave 28)

**Invariant system** (parametric — 新規手続きに自動適用; CLAUDE.md に一覧表):
全手続き: anchored rules + refer-when + verify-service-date + UPL self-submit ·
非civil: ≥1 :opt/protective · housing: no-self-help · enforcement: 法定差押え保護の
開示 · insolvency: kaiyaku 縁-ledger 突合 · family: kokoro 心 routing ·
:dl/critical 三層 (census/先頭/⚠) · fake-guard: 全 trigger 語彙が自動 trip-wire,
SMS/email は宣言なき限り偽疑い (NZ Tribunal 等の宣言例外も実証)

**手動同期の構造的封殺** (3系統): manifest⇔registry (w16) · fake-guard 語彙の
registry 導出 (w17) · CLAUDE.md counts 照合 (w25 — 導入即 family 数の手書き誤りを
検出)。computed gaps (worklist 自動消込 / civil-only / track depth / 州 50/50) が
人手リストの漏れ (:at, MI) を2度検出した。

**Actor compose** (機械間配線3本): tate→kaiyaku handoff EDN (w23) ⇄ kaiyaku
handoff_ingest (w26, round-trip test) · response-plans.json + clause-flags.json
(yoro UI 向け, w30/32)。unknown-jurisdiction fixture lineage :br→:mx→:ar→:cl。

# Consequences

- R3 候補: 改正追跡の機械化 (:verify-current-law の sources whitelist — suimin G1
  方式), DC/準州, さらなる track depth (insolvency/family), 新法域 (:cl :za :tr
  :th :id …), Murakumo 通知分類 (G9), 暗号化ライブ ingest (G7)。
- 法令 registry の保守は 30 法域分に拡大 — :verify-current-law true 全件 +
  「改正時は現行条文を引く」規約が生命線。
- G1-G10 のゲート (非裁定・期限正直・管轄正直・UPL・偽通知ガード) は全 wave を
  通じ不変— 拡大はすべて registry データであり、ゲートの緩和は一度もない。

# References

ADR-2606112200 (kaiyaku) · 2606112300 (tate R0) · 2606112400 (R1) · PR #1624
(wave-by-wave の全コミットログが詳細記録)
