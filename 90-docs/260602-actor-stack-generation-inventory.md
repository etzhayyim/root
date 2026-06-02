---
doc_type: inventory
topic: actor-stack-generation
authoritative: false
last_verified: 2026-06-02
related:
  - 90-docs/adr/2605262130-kotoba-storage-substrate-unification.md
  - 90-docs/adr/2605312345-kotoba-datom-first-class-canonical-state.md
  - 90-docs/adr/2605214000-etzhayyim-murakumo-mesh-no-vke-and-lexicon-port-rules.md
  - 90-docs/adr/2606021139-tsukuru-actor-namespace-disambiguation.md
  - 90-docs/260602-tsukuru-kotoba-native-migration-plan.md
---

# Actor Stack-Generation Inventory (2026-06-02)

棚卸しの目的: どの `20-actors/*` actor が **現行 canonical 設計**（kotoba-EAVT-native
+ `manifest.edn` + cells/lex + Murakumo-only）に乗っていて、どれが **旧 gftd / RisingWave
世代** に取り残されているかを構造マーカーで機械判定する。

## 判定基準（構造シグナル）

| 世代 | マーカー | 意味 |
|---|---|---|
| **Gen-3 (canonical)** | `manifest.edn` + `kotoba/` + `cells/` + `lex/` | kotoba-EAVT-native の現行標準形（okaimono がリファレンス） |
| **Gen-2 (cells, pre-kotoba)** | `actor-manifest.jsonld` + `cells/`、`kotoba/` 無し | Pregel cell はあるが manifest が旧 JSON-LD、canonical state 未配線 |
| **Gen-1 (legacy)** | `actor-manifest.jsonld` のみ（cells 無し） | スキャフォルド段階。R0 manifest のみ |

> 注: `graph.query` / `graph.write` / `RisingWave` の grep は **負マーカー（"no RisingWave" の禁止注記）にも当たる**ため信頼できない。構造マーカー（`manifest.edn` + `kotoba/` の有無）が唯一の確実なシグナル。下表はそれで分類。

## Gen-3 — 現行 canonical 設計に統合済み（2 actors）

| Actor | ADR | 状態 |
|---|---|---|
| **okaimono** 御買物 | 2606012100 | 🟢 R0+R1+R2+R3（リファレンス実装） |
| **haraedo** 祓戸 | 2606010200 | 🟡 R0 |

この2つだけが `manifest.edn` + `kotoba/`（schema/seed/ingest）+ `cells/` + `lex/` を完備。

## Gen-2 — Pregel cells あり / 旧 JSON-LD manifest（18 actors）

kotoba 配線が未完。`cells/` はあるが `manifest.edn` と `kotoba/` ディレクトリが無く、
canonical state が kotoba Datom に乗っていない。Gen-3 化のコストは中。

funadaiku · futawa · gov-municipality · hagukumi · hikari · hodoki ·
infra-utility-connect · kanayama · kuni-umi · makura · manabi · mitsuho ·
sarutahiko · tatekata · wadachi · yakushi · yamabiko · yoro-supply

> **更新 2026-06-02**: **tsukuru** が Gen-1 → このカテゴリ（cells+lex+manifest.edn 完備、`kotoba/`
> 未配線）に昇格。Phase 2 scaffold landed（移行プラン参照）。**silicon** も `manifest.edn`+cells+lex
> を取得し Gen-2 相当（ADR-2606021139 で tsukuru namespace から分離）。残り Gen-3 化は両者とも `kotoba/` 配線。

> 部分世代: **warifu** / **yobel** は `cells/`（+warifu は `lex/`）を持つが JSON-LD manifest が無い変則形。

## Gen-1 — legacy JSON-LD only（残り ~80 actors）

スキャフォルド段階（R0 manifest のみ、cells 無し）。Tier-B roster の大半はここ。
chigiri · iyashi · igata · junkan · kataribe · kawase-yui · kazaori · kizashi ·
kokoro · mitate · mizuho · musubi · ossekai · shidemori · suki · toritate ·
tsumugi · tsutae · wakai · watatsuna … ほか各種 intel/oil/gov 系。

## gftd 命名残渣サブセット（cutover 対象）

旧 `gftd:` 識別子がコードに残る actor。ADR-2605214000 §3 + ADR-2605215000 §4 の
**atomic rename wave（法人登記後の単一 PR）対象**で、個別に触ってはいけないもの（magatama 系）を含む。

| Actor | gftd: ファイル数 | 備考 |
|---|---|---|
| **magatama** | 33 | フレームワーク本体。Step 8 cutover の中核、**partial rename 禁止**（CLAUDE.md §Do Not） |
| abuse / intel / ipaddress / isco / isekai / joucho / kami-sabiotoshi / media-gamers / os / **tsukuru** / vin / yabai / yotei | 各 1 | manifest/CLAUDE 内の WIT パッケージ参照（`gftd:<name>@x.y.z`） |

## ハイライト

- **現行設計に「本当に乗っている」のは okaimono と haraedo の 2 actor のみ。** root CLAUDE.md
  Tier-B roster の 🟡 R0 表示の多くは Gen-1/Gen-2 のスキャフォルドであり、kotoba canonical
  state には未配線。
- **tsukuru** は Gen-1（cells すら無い）かつ gftd 残渣ありで、二重に取り残されている。さらに
  名前衝突あり（→ ADR-2606021139）。移行プランは `260602-tsukuru-kotoba-native-migration-plan.md`。
- 大量移行の前提として **magatama の gftd→etzhayyim atomic cutover**（法人登記ゲート）が
  ボトルネック。個別 actor の Gen-3 化はこれと干渉しない範囲（manifest/cells/kotoba 追加）なら先行可能。
