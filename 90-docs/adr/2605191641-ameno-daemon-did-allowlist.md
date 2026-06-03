---
id: 2605191641-ameno-daemon-did-allowlist
title: Ameno daemon — DID auth allowlist (AMENO_ALLOWED_DIDS)
status: proposed
doc_type: adr
topic: ameno-auth
authoritative: true
last_verified: 2026-05-19
depends_on:
  - 2605191657-ameno-daemon-did-auth
related:
V05191407-ameno-browser-viewer-mode
V05191346-etzhayyim-vultr-free-murakumo-control-plane
---

# ADR 2605191641: Ameno daemon — DID auth allowlist (AMENO_ALLOWED_DIDS)

## Context

ADR-2605191657 が did:key Ed25519 challenge-response 認証を導入した。
仕様上 **well-formed な did:key + 有効署名** ならば誰でも認証通る:

```
verifyDidSig:
  parse  → did:key
  decode → 32-byte pubkey
  fetch  → nonce
  verify → Ed25519.verify(sig, nonceBody, pubkey)
  → 通過
```

これは「daemon を起動した = 全世界に LLM サービス提供」を意味する。
production の Mac-mini fleet で `ameno-daemon.etzhayyim.com` を晒した
瞬間、認証は通るが誰でも使える状態になる。

## Decision

**`AMENO_ALLOWED_DIDS` 環境変数で許可 did:key のホワイトリストを
強制する。**

```
AMENO_ALLOWED_DIDS=did:key:zA1B2…,did:key:zX9Y8…
```

- カンマ区切り、 trim 後 `did:key:z` で始まるもののみ採用
- **未設定 / 空文字列** → 制限なし(loopback dev / 単一オペレータ)
- **設定あり** → 厳格な whitelist、`verifyDidSig()` で `did not in allowlist` を返して 401

### Path A (TS daemon)

`60-apps/etzhayyim-project-ameno/daemon/src/did-auth.ts`:

```ts
const ALLOWED_DIDS = new Set(
  (process.env.AMENO_ALLOWED_DIDS ?? "")
    .split(",").map((s) => s.trim())
    .filter((s) => s.startsWith("did:key:z")),
);

function isDidAllowed(did: string): boolean {
  return ALLOWED_DIDS.size === 0 || ALLOWED_DIDS.has(did);
}
```

`verifyDidSig()` の最初の検査で `isDidAllowed(did)` を確認、 NG なら
`{ ok: false, error: "did not in allowlist" }` を返す(nonce 消費前)。

### Path B (Python daemon)

同形:`pymagatama/projects/ameno/did_auth.py` で `_load_allowlist()`
+ `is_did_allowed()`。

### Browser (viewer-mode.ts)

`invokeAmenoRemote()` のエラー分岐で **`did not in allowlist`** を
含む 401 を区別、ユーザに具体的アクションを示す:

> daemon rejected DIDSig: this browser's did:key is not in the daemon's
> AMENO_ALLOWED_DIDS allowlist

新規 user の onboarding 体験:
1. browser 開いて `getAuthDid()` で表示された `did:key:z…` をコピー
2. daemon オペレータに連絡(slack, email, GitHub issue 等)
3. オペレータが `AMENO_ALLOWED_DIDS` env に追加 → daemon restart
4. browser から再アクセスで通過

### K8s 設定

`50-infra/k8s/lg-ameno/deployment.yaml` には未追加 — production deploy
時に kustomize overlay か `kubectl set env` で投入:

```sh
kubectl -n etzhayyim-langserver set env deploy/lg-ameno \
  AMENO_ALLOWED_DIDS="did:key:zABC,did:key:zXYZ"
```

### 関連 ADR-2605191346(Vultr-free)との整合

production daemon が公開 ingress を持つ場合、 allowlist 未設定運用は
**抑止すべきデフォルト**(本 ADR で確定)。 dev / loopback 単独運用は
従来通り無設定で動かせる。

## Consequences

- ameno daemon が **per-actor 認可** を獲得。 bearer token と異なり
  鍵 rotation で全 client 切断しなくて済む(allowlist に追加削除)
- 認証拒否時のエラーメッセージで user が次の手順を理解できる
- ADR-2605191657 の DIDSig flow に check 1 行追加だけで impl 完了
- 大規模 multi-tenant では allowlist が膨らむ。OAuth / Capability
  token への発展は別 ADR(`ameno-capability-token`)で

## Alternatives Considered

1. **denylist(blacklist)** — 拒否したい DID を列挙。明示的 onboarding
  には逆効果、reject
2. **public open**(allowlist なしを default に)— production 公開で
  抑止が無い、 reject
3. **roles / scopes**(`AMENO_DID_SCOPES={did:key:zA=read,did:key:zB=write}`)
   — capability token 導入と等価、現状はシンプルな allowlist で十分

## References

- ADR-2605191657(did:key Ed25519 daemon auth、本 ADR の前提)
- ADR-2605191407(viewer mode、エラー UI 影響)
- ADR-2605191346(Vultr-free、 production 公開の前提)
