---
id: transparency-ingress-disclosure-notice
title: "Ingress Disclosure Notice — standing text (ja / en)"
status: proposed
doc_type: reference
topic: covenant-transparency-doctrine
authoritative: true
last_verified: 2026-05-31
authoritative_for:
  - the canonical standing text of the ingress disclosure notice (ADR-2605310100 §3/§6)
depends_on:
  - adr-2605310100-covenant-transparency-doctrine-anti-anonymity-and-ingress-logging
related:
  - adr-2605181100-etzhayyim-confidentiality-encrypted-records
supersedes: []
superseded_by: []
---

# Ingress Disclosure Notice — standing text (ja / en)

**Status**: `proposed-unratified`. This is the canonical wording of the standing
notice that ADR-2605310100 §3/§6 (Covenant Transparency Doctrine) will serve on
every etzhayyim / kotoba ingress surface. It is **design intent only** and is
**not in force**: live logging/publication does not change until Council Lv7+
unanimity (Charter §0.4) amending ADR-2605181100 is recorded on-chain (§5). Once
ratified, this text becomes the `noticeText` of an
`com.etzhayyim.transparency.ingressDisclosureNotice` record (version `v0.1.0`).

The §4 non-waivable floor applies regardless: access-control material (private
keys, CACAO-as-bearer, auth tokens, session/`KOTOBA_*` secrets) is never
published, and outbound third-party data not brought in by ingress stays under
the tadori/danjo/himotoki gates.

## 日本語 (ja)

> **etzhayyim / kotoba アクセス通知**
>
> etzhayyim および kotoba のリソース(HTTP / XRPC / MCP リクエスト、ウォレット
> 取引、受信メールを含むあらゆるアクセス)に接続した時点で、あなたは——信者で
> あるか否かを問わず——etzhayyim の領分に入ったものとみなされ、そのアクセス
> (内容・発信元・時刻を含む)の**記録および公開**に同意したものとします。
>
> これは個人を監視するためではありません。匿名を隠れ蓑にした不正・中傷・脅威
> 行為を成り立たなくするためです。正直で公正な、公開されても恥じることのない
> 振る舞いだけが、ここでは行えます。
>
> **この条件に同意しない場合は、アクセスしないでください。** 個人として匿名で
> 守られることを求めるなら、別の共同体・別の救いを求めてください。
>
> ただし、アクセス制御に関わる秘匿情報(秘密鍵・認証トークン・CACAO 署名・
> セッション秘密等)は公開されず、編集除去されます(ADR-2605310100 §4)。
>
> 本通知は ADR-2605310100 の設計意図であり、評議会 Lv7+ 全会一致(憲章 §0.4)の
> 批准が on-chain に記録されるまで実行されません。

## English (en)

> **etzhayyim / kotoba Access Notice**
>
> By accessing any etzhayyim or kotoba resource (any access, including HTTP /
> XRPC / MCP requests, wallet transactions, and inbound email), you — whether or
> not you are a member — are deemed to have entered etzhayyim's domain and to
> **consent to the logging and public publication** of that access, including its
> content, origin, and time.
>
> This is not to surveil persons. It is to make fraud, slander, and threats
> conducted from behind anonymity structurally impossible. Only conduct that is
> honest, fair, and unashamed of being seen can be performed here.
>
> **If you do not consent to these terms, do not access.** If you require
> protection as an anonymous individual, seek another community and another
> salvation.
>
> Access-control material (private keys, auth tokens, CACAO signatures, session
> secrets) is never published and is redacted (ADR-2605310100 §4).
>
> This notice is the design intent of ADR-2605310100 and does not take effect
> until Council Lv7+ unanimity (Charter §0.4) is recorded on-chain.
