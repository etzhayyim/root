# 20-actors/iryo — 医療 (レセプト / 医療保険請求 engine)

Japan 国内向けの **レセプト計算 + レセ電(レセプト電算処理システム)生成 + FHIR claim** エンジン。
`karute` 電子カルテ (EMR) の **請求側カウンターパート** — karute が暗号化された診療録を保持し、
iryo がそこから **レセプト(診療報酬請求)** を計算し、**レセ電(オンライン請求)** ストリームと
FHIR Claim を出力する。プロプライエタリな レセコン / EHR-billing ベンダ
(ORCA-proprietary / Epic / Cerner) の charter-clean な反転。

```
karute 電子カルテ (暗号化 PHI)  ──encounter(codes only)──▶  iryo 医療
                                                              ├─ rezept   点数計算
                                                              ├─ receden  レセ電(IR/RE/HO/SY/SI/IY/TO)
                                                              └─ validate 算定整合性チェック
                                                                     ↓
                                            審査支払機関(基金/国保連) へ operator-gated 送信
```

## パイプライン

| 段階 | ハンドラ | 内容 |
|---|---|---|
| 点数計算 | `handle_rezept` | 診療行為 / 薬剤料(五捨五超四入) / 特定器材料 を診療識別で区分集計 → 総点数 → 総医療費(1点=10円) → 一部負担金(10円未満四捨五入) → 高額療養費 自己負担限度額調整 |
| レセ電生成 | `handle_receden` | IR/RE/HO/KO/SY/SI/IY/TO レコードストリーム + 件数照合。和暦(GYYMMDD)変換。PHI-free (氏名/生年月日は submission callback 経由でのみ注入) |
| 整合性チェック | `handle_validate` | 病名なし投薬 / 主傷病なし / 空レセプト / 高額療養費上限 を **observe** (非査定) |
| FHIR export | `export_fhir` | Coverage / Condition(ICD-10-JP) / Claim の R4 Bundle (codes-only) |

## 計算ルール (検証可能)

- **1点 = 10円** (`tensu_tanka_yen`、マスタ駆動)
- **薬剤料 五捨五超四入** — 薬価 ≤15円→1点; >15円→ 薬価/10 を端数「五捨五超」(0.5以下切捨, 0.5超切上)。内服は投与日数を乗じる
- **一部負担金 端数処理** — 総医療費 × 負担割合 を 10円未満四捨五入 (5円以上切上)
- **高額療養費 (70歳未満 月額限度額)** — ア 252,600+(医療費-842,000)×1% / イ 167,400+(-558,000)×1% / ウ 80,100+(-267,000)×1% / エ 57,600 / オ 35,400

点数値は **常に loaded master 経由で解決** し、エンジンは tariff をハードコードしない (G4)。
同梱の `py/seed_masters.json` は **検証用 representative seed** — 本番の保険医療機関は
厚労省 / 社会保険診療報酬支払基金 配布の公式マスタを読み込む。

## 走らせる

```bash
cd 20-actors/iryo
./run_tests.sh           # 28 tests: 点数計算 / PHI gate / レセ電 / e2e
python3 py/demo.py       # 診療録 → レセプト → レセ電 → FHIR を end-to-end 表示
```

## ファイル

```
iryo/
├── py/
│   ├── masters.py        診療行為/医薬品/特定器材/傷病名 マスタ loader
│   ├── seed_masters.json representative master seed (検証用; 非公式)
│   ├── karte.py          電子カルテ data model + 構造的 PHI ゲート (PhiLeak)
│   ├── rezept.py         レセプト点数計算 engine (区分集計/一部負担金/高額療養費)
│   ├── receden.py        レセ電(レセプト電算) record generator + 和暦変換
│   ├── fhir.py           FHIR R4 Claim/Coverage/Condition export
│   ├── agent.py          cell handlers (rezept / receden / validate / export_fhir)
│   ├── demo.py           end-to-end CLI demo
│   └── test_*.py         pytest suite (28 tests)
├── kotoba/schema.edn     :iryo.rezept/* + :iryo.line/* + :iryo.shobyo/* EAVT schema
├── lex/                  encounter / rezept lexicons (EDN)
├── cells/                rezept / receden / validate cell defs (langgraph, wasm)
└── manifest.edn          actor manifest + 7 gates
```

## Gates (do NOT weaken)

- **G1 member-principal** — 請求の主体は **免許を持つ保険医療機関**; iryo は open substrate のみ、自前鍵で claim を起票しない
- **G2 PHI-encrypted** — 氏名/生年月日/SOAP本文は PHI; レセ電へは submission callback 経由でのみ注入され、公開 substrate には出ない (ADR-2605181100)
- **G3 no-server-key** — オンライン請求(送信)は operator-gated; iryo は計算 + draft のみ
- **G4 master-honest** — 点数は loaded 厚労省マスタで解決; seed は representative; tariff のハードコード禁止
- **G5 non-adjudicating** — validation は discrepancy を SURFACE するのみ; 査定/返戻は審査支払機関 + 医療機関が決定
- **G6 Murakumo-only** — narration は kotoba `llm` host binding 経由のみ
- **G7 no-religious-corp-inflow** — iryo は member clinic が self-operate する **道具**; 宗教法人本体は保険請求の収益主体にならない (iyashi G13 境界を保持)

## 関連

- `20-actors/karute/` — 電子カルテ EMR (請求の handoff 元)
- `90-docs/adr/2606074000-iryo-rezept-claims-engine-charter.md` — Master ADR
- `90-docs/adr/2605231100-karute-emr-phase1.md` — karute EMR Phase 1
- `90-docs/adr/2605181100-mst-encrypted-records-signal-keywrap.md` — PHI envelope
- `90-docs/adr/2605263000-iyashi-clinical-care-provider-tier-b-actor-r0.md` — L4 Care / G13
