---
id: adr-2606231200-kotoba-rad-sovereign-actor-identity
title: "ADR-2606231200: kotoba-rad — sovereign per-actor repo identity on the kotoba substrate"
status: proposed
doc_type: adr
topic: kotoba-rad-sovereign-actor-identity
authoritative: true
last_verified: 2026-06-23
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Substrate for splitting 20-actors/* into per-actor public repos + DID + aozora(yoro) actor registration."
authoritative_for:
  - per-actor-repo-identity
  - kotoba-rad
depends_on:
  - adr-2605231525  # did:web multi-controller / no-server-key
  - adr-2605312345  # kotoba member-signed block CAS / Datom-first-class state
  - adr-2605203000  # kotoba write-target Option B (PDS XRPC e.write)
related: []
supersedes: []
superseded_by: []
---

# ADR-2606231200: kotoba-rad — sovereign per-actor repo identity on the kotoba substrate

**Status**: proposed
**Date**: 2026-06-23
**Deciders**: Jun Kawasaki

## Addendum 2026-06-24 — actor did.json は静的・github.io path 型（動的配信しない）

per-actor repo + per-actor DID にした時点で、**actor の did.json に動的配信は不要**。
オペレータ指示で、各 actor は**独自ドメインを使わず GitHub Pages のデフォルト
`etzhayyim.github.io` のまま**運用する。よって本 ADR の did:web を下記に確定する:

- **DID** = `did:web:etzhayyim.github.io:com-etzhayyim-<name>`（path 型）
- **解決先** = `https://etzhayyim.github.io/com-etzhayyim-<name>/.well-known/did.json`
- **配信** = repo に**静的コミットした did.json を GitHub Pages がそのまま配信**（github.io
  自身の TLS）。`.nojekyll` を repo ルートに同梱し、`/.well-known/` と `*.wasm` を生配信。
- **CF Worker / wildcard TLS / 動的 KV-DID は actor には不要**。apex Worker（ADR-2606013800
  / 2606112100 の動的 did.json）は **組織自身の `did:web:etzhayyim.com` + IPFS gateway +
  XRPC + donation 専用**に縮小。「apex は did:web を 1 ホストからしか解決できない」という
  Pages 却下理由（2606112100）は path 型 = 1 actor = 1 静的ファイルには当てはまらない。

**根拠（なぜ動的が消えるか）**: 旧 `did:web:etzhayyim.com:actor:<h>` は apex 単一ホストに
多数 actor を相乗りさせる前提で、apex が KV/kotoba から did.json を**動的生成**していた。
本 ADR の per-subdomain/per-repo モデルでは 1 actor = 1 ホスト = 1 静的ファイルなので、
多重化も生成ロジックも不要。静的 did.json の更新は **commit/PR** で、これは no-server-key
（鍵 rotation = KV write ではなく署名コミット）と PR ベース自己進化により整合する。

**副産物**: did.json が静的になるので、**GitHub Pages が wasm + did.json + edn を一体ホスト**
できる（Pages 却下の唯一の理由＝動的 DID エンドポイントが path 型には不在）。
1 repo = Pages(コード/wasm/did.json) + IPFS(content-address) + kotoba(状態) + PR(進化)。

**主権の担保**: controller ドメインが `github.io`（非所有）になるが、主権同一性は
`kotoba-rad RID + did:key`（kotoba log 上）で、did:web は `alsoKnownAs` の1ポインタに過ぎない
— GitHub が消えても RID/did:key で actor 同一性は残る（本 ADR の元設計どおり）。

**AT ハンドル**: `at://<name>.etzhayyim.com` ハンドルは DNS TXT `_atproto.<name>.etzhayyim.com`
で解決でき、Web ホスト（Pages/サブドメイン）を必要としない。よって did:web を github.io に
置いても at:// ハンドルは etzhayyim.com 名前空間に維持できる（別 id・別解決経路、矛盾なし）。

**実装差分（本追補と同 PR）**: `manifest->genesis` の `:did-web` を path 型に変更・
`did-web-doc` の既定 DID を path 型に・`step-did-web` に `.nojekyll` 同梱を追加
（`70-tools/src/etzhayyim/{actor_publish,kotoba_rad}.cljc`）。

# Context

`orgs/etzhayyim/root/20-actors/<name>/` の各 actor を

1. monorepo 内に保ちつつ、個別 **public GitHub repo `com-etzhayyim-<name>`** として公開し、
2. それぞれに **DID** を持たせ、
3. **aozora.app（= `gftdcojp/app-aozora` の yoro AppView）の actor** として登録する、

ことが目標。調査で確定した前提:

- aozora.app の actor 登録は専用 API ではなく、**(i) DID = `did:web:<name>.etzhayyim.com`（controller）+ 権限チェーン `…:<recordtype>:{id}`、(ii) PDS への profile レコード書込み（`@etzhayyim/sdk` の `e.write`, Option B / ADR-2605203000）、(iii) `mst-projector` による index** の3点が揃うこと。`kotoba-appview` README が SSoT。
- kotoba（`40-engine/kotoba`, `70-tools/src/etzhayyim/kotoba/*`）は **content-addressed Datalog DB**：Datom[CID/T]・CAR・IPFS・CACAO・AT Protocol を備える。
- `50-infra/etzhayyim-did-web/cljs/src/did_web/kotoba.cljs` が既に **member-signed CAS** を実装：member が Datom log root CID を **ed25519 署名**、server は**検証のみ（root を mint 不可）**、content-addressed delta block を保存し **CAS で head を前進（衝突は 409）**。`did:key:z<hex pubkey>` 形式を採用。

コード配布レイヤ（A 軸）は **josh-proxy**（monorepo ⇄ `com-etzhayyim-<name>` の双方向 view）で決定済み。可変状態レイヤ（C 軸）は **ATProto MST/PDS + IPFS pin** で既存充足（CRDT/DeltaDB は不要 — ATProto が署名付き追記ログを既に提供）。

残る論点は **B 軸 = アイデンティティ主権**。「各 repo に DID」を、Cloudflare/`etzhayyim.com` 依存の did:web だけに委ねるか、プラットフォーム独立な主権同一性も持たせるか。Radicle（repo=RID, identity=did:key, signed sigrefs, COB）はこの主権モデルの代表だが、本物の `radicle-node` を併置すると **ATProto(可変state) ⊕ Radicle(別DAG) の二重台帳**になる。

# Decision

**Radicle を併置せず、Radicle 型の主権同一性モデルを kotoba 上に薄く実装する（"kotoba-rad", 案 R2）。** kotoba は Radicle のコア要素の約8割を既に持つため、新規はトランスポート（gossip）だけで、当面それも IPFS + CAS head + `70-tools/kotoba-webrtc-poc` で段階導入する。

## Radicle → kotoba 能力対応

| Radicle 構成要素 | kotoba の既存資産 | 状態 |
|---|---|---|
| did:key (Ed25519) peer identity | `kotoba.cljs`: `did:key:z<hex>` + ed25519 verify | ✅ |
| RID (repo id = genesis hash) | `cid.cljc`: `cid-of-edn` → genesis identity block の CID | ✅ |
| signed refs (`rad/sigrefs`) | member が Datom log root を署名・server は検証のみ・**CAS head** | ✅ ほぼ同型 |
| Merkle DAG storage | Datom[CID/T] + IPFS pinner + CAR | ✅ |
| COB (issues/patches = op-DAG) | EAVT/Datalog 追記 Datom collection | ✅ モデル一致 |
| Heartwood gossip (p2p 複製) | **無し**。現状 CF KV + IPFS（準中央）。種: `kotoba-webrtc-poc` | ⚠️ 唯一のギャップ |

## kotoba-rad 同一性スキーマ（Datom 形）

actor 1体の主権同一性を、kotoba Datom log に追記する。genesis identity block（下記）を `cid/cid-of-edn` で content-address した値が **RID**（Radicle の Repository Identity に対応）。entity は `rad:<RID>`。

```clojure
;; genesis identity block（これ自体の CID = RID）
{:rad/type        :identity
 :rad/name        "cargo"
 :rad/did-web     "did:web:cargo.etzhayyim.com"     ; aozora/yoro controller DID（B軸 GitHub/did:web）
 :rad/delegates   ["did:key:z<hex pubkey>"]          ; 署名権限を持つ鍵（kotoba.cljs 互換 hex 形）
 :rad/threshold   1                                   ; m-of-n（pilot は 1）
 :rad/repo        "github.com/etzhayyim/com-etzhayyim-cargo"
 :rad/aozora      {:pds "https://pds.etzhayyim.com"
                   :collection "com.etzhayyim.apps.cargo"}}
```

同一性更新（delegate 追加・rotation）は **新しい identity Datom + 旧 head 参照**として追記し、`log/head-cid` が signed head（sigref 相当）になる。sigref（署名 head）の Datom:

```clojure
{:rad/type :sigref
 :rad/rid  "<genesis CID>"
 :rad/head "<head-cid log>"        ; log/head-cid
 :rad/by   "did:key:z<hex>"
 :rad/sig  "<ed25519(head-cid bytes)>"}  ; server 検証のみ・mint 不可（kotoba.cljs と同規約）
```

## did:key 規約

**標準 W3C did:key（`z` + base58btc(0xed01‖pubkey)）ではなく、既存 `kotoba.cljs` の `did:key:z<hex pubkey>` 形を踏襲する。** 理由: 既存検証器（`kotoba.cljs` verify）との相互運用を、外部 did:key resolver 互換より優先。標準形が要る時点で可逆変換関数を1本足す（差分は prefix とエンコードのみ）。

## レイヤ責務（最終形）

```
A コード配布 : josh-proxy   monorepo ⇄ com-etzhayyim-<name>（双方向 view・PR 受け可）
B 同一性(web): did:web:etzhayyim.github.io:com-etzhayyim-<name>   静的・Pages 直（追補2606-24）
B 同一性(主権): kotoba-rad   RID(genesis CID)+did:key  alsoKnownAs に併記（本 ADR）
C 状態       : ATProto MST/PDS（e.write Option B）+ IPFS pin   既存・DeltaDB 不要
登録         : PDS に profile write → mst-projector index → yoro searchActors に出現
配信         : repo の /.well-known/did.json を GitHub Pages が STATIC 配信（github.io TLS）
              — CF Worker / wildcard TLS / 動的生成は actor には不要（追補 2026-06-24）
```

`alsoKnownAs` で3つの同一性を相互リンク（at:// ハンドルは DNS TXT `_atproto` で解決、Web ホスト不要）:

```
did:web の did.json:  alsoKnownAs = [ "at://<name>.etzhayyim.com",
                                      "rad:<RID>",
                                      "https://github.com/etzhayyim/com-etzhayyim-<name>" ]
```

## 実装（本 ADR と同 PR）

- `70-tools/src/etzhayyim/kotoba_rad.cljc` — genesis-block / RID / did:key / sigref / identity-log（`cid`+`datom`+`log` を再利用）。**no-server-key**：署名は member 鍵（Keychain/1Password）でのみ、関数は `sign-fn` を注入する seam。署名鍵不在なら unsigned identity（`:rad/sig nil`）+ warn で fail-open（pilot 用）。
- `70-tools/src/etzhayyim/actor_publish.cljc` — `bb actor:publish <name>` 冪等オーケストレータ。**dry-run 既定**、`--apply` で副作用。段: josh split → `gh repo create` → did.json 生成 → kotoba-rad RID 発行 → PDS profile write。
- `50-infra/josh/` — workspace.josh フィルタ + RUNBOOK。
- bb.edn に `actor:publish` / `actor:rid` / `actor:didweb` タスク。

# Consequences

**正**
- 鍵・CID・CAR・IPFS・Datom を**単一基盤で共有** — ATProto repo/did/Datom と did:key/RID/COB が同じ log 上で相互運用。
- GitHub / Cloudflare が失われても RID + did:key で actor 同一性が残る（主権）。
- gossip 以外に新規依存ゼロ。pilot は IPFS + CAS head で動く。
- 既存 §"Operational code = clj/bb over the kotoba Datom log" 規約に準拠（clj/bb・no-server-key）。

**負 / リスク**
- 当面は **"Radicle のデータモデルを Radicle のネットワーク無しで"** 実現するもので、radicle.xyz ネットワークとの**ワイヤ相互接続は別マイルストーン**。"Radicle 互換" を対外的に名乗らない。
- did:key を非標準 hex 形にするため、外部 did:key resolver からは直接引けない（変換関数で緩和）。
- gossip 不在の間は複製が準中央（CF KV/IPFS）。p2p 主権は `kotoba-webrtc-poc` 統合後。

# Alternatives Considered

- **R1. 本物の Radicle 併置**: `radicle-node` を別運用。工数最小だが別データモデル・二重台帳。却下。
- **R3. アンカーのみ**: RID/did:key を計算して `alsoKnownAs` に記録するだけ（ネットワーク無し）。pilot の最小形として R2 の degenerate case に含む（`--no-network`）。
- **C 軸に CRDT/DeltaDB(Zed/Automerge/dolt)**: ATProto MST が署名付き追記ログを既に提供。二重台帳になるため不採用。
- **submodule / subtree（A 軸）**: submodule は多数化で pointer 同期が破綻、subtree は片方向。PR 受けのため josh を採用。

# References

- `50-infra/etzhayyim-did-web/cljs/src/did_web/kotoba.cljs` — member-signed CAS（ADR-2605312345）
- `70-tools/src/etzhayyim/kotoba/{cid,datom,log}.cljc` — RID/sigref の再利用 API
- `gftdcojp/app-aozora` `60-apps/etzhayyim-project-yoro/kotoba-appview/README.md` — Option B 登録モデル
- 実装: `70-tools/src/etzhayyim/kotoba_rad.cljc`, `70-tools/src/etzhayyim/actor_publish.cljc`, `50-infra/josh/`
