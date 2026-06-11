# e7m-sim scene — `giemon-factory-r0/`

**Status**: R0 design. The **factory that manufactures the giemon robot line**
(arm6 + kabitori), designed end-to-end in **kami-engine** (geometry +
kami-genesis physics) and **kotoba Datomic** (建材 + 建築手順 as EAVT datoms).

## Binding

- **ADR**: ADR-2606010030 — giemon factory R0 (kami-engine + kotoba 4D BIM).
- **Sim consumer**: `40-engine/kami-engine/kami-app-giemon-factory/`.
- **Depends on**: ADR-2605311800 (kami-genesis 3-D solver + contact),
  ADR-2605311900 (shibuya scene→world pattern), ADR-2605312300 (kabitori
  part-ledger → SBOM → kotoba pilot), ADR-2605312345 (kotoba Datom = first-class
  canonical state), ADR-2605262130 (kotoba substrate).

## Modeled layers — all in kami-engine + kotoba, nothing outside

| Layer | 中身 | File(s) | kami-engine | kotoba |
|---|---|---|---|---|
| 1. Building shell (建材) | foundation · steel frame · roof · cladding | `building.edn` A-D | walls / columns / beams as `Obstacle::Aabb` + CAD geometry | `kg/claim/part/*` datoms |
| 2. MEP utilities, **routed** (電気/給排水/ガス/圧空/通信/消防) | 受電→配電→配線 · 給水/排水/雨水 · ガス · 圧空 · データ · 消火栓 — each a **routed network** | `building.edn` E,G-J + scene `service_nodes`/`utilities`/`fixtures` | colour-coded conduit/pipe ribbons along the route + service-node boxes + 照明/誘導灯 fixtures | `kg/claim/part/*` datoms |
| 3. Production hardware (設備) | CNC · lathe · CMM · benches · conveyor · racks · **giemon arm6 cells** · AGVs | `building.edn` F | CAD geometry + `Articulation3d` (arm6) + 4-DOF AGV agents | `kg/claim/part/*` datoms |
| 4. External site / 外部動線 (外構) | access road · truck apron · parking · service drive · walkway · fence · gate · 外灯 · bollard · landscape · sign | `building.edn` K + scene `site_*` | pavements/greens/fences/poles outside the bay | `kg/claim/part/*` datoms |
| 5. Raw materials (原材料) | 生コン · アスコン · 砕石 · 塗料 · シーリング | `building.edn` L | (bulk inputs, no geometry) | `kg/claim/part/*` datoms |
| 6. Construction procedure (建築手順) | **23-step** 4D施工シーケンス (引込→埋設→基礎→鉄骨→屋根→外装→配線→照明→床→衛生→消防→機械→ロボット→外構→試運転) | `construction.edn` | `run_giemon_factory_build_v1` reveals geometry in `:step/seq` order | `kg/claim/step/*` datoms (depends-on/consumes = entity refs → VAET) |

## Files

| File | Role |
|---|---|
| `scene.yaml` | e7m-sim scene descriptor (foundry-yard style; indoor carve-out) |
| `factory.scene.json` | **runtime scene** (hand-authored): walls / columns / beams / zones / machines / conveyors / cells / agvs — `include_str!`'d by the crate |
| `building.edn` | **SSoT** 建材 + 設備 + MEP + 外構 + 原材料 Datomic ledger (72 parts, groups A-L) |
| `construction.edn` | **SSoT** 建築手順 4D sequence (23 steps, full MEP + 外構) |
| `procurement.py` | manufacturer(企業名) → 調達もと(商社/代理店)/原産国/リードタイム/channel join table |
| `engineering.py` | クラッシュ検出 + サイジング(電気/給水/排水) + 法規チェック → `engineering.json` + `clashes.json` |
| `ifc_export.py` | scene → `factory.ifc` (IFC4 STEP, BlenderBIM 等で開ける) |
| `kotoba_gen.py` | **orchestrator** — EDN → SBOM + ingest + order + engineering + IFC (+ cross-checks) |
| `factory.cdx.json` | generated CycloneDX 1.5 SBOM (74 components, 企業名+機器名+調達もと付き) |
| `kotoba_ingest.json` | generated `kg.ingest_batch` body (**117 entities** = 74 parts + 23 steps + 12 clash + 3 sizing + 5 code) |
| `construction.order.json` | generated flat 4D order — consumed by the build viewer |
| `engineering.json` | クラッシュ/サイジング/法規チェック レポート |
| `clashes.json` | 干渉リスト — 完成ビューアが赤(構造貫通)/橙(設備調整)マーカー描画 |
| `factory.ifc` | IFC4 (ISO-10303-21) 970行 — IfcColumn/Beam/Wall/Slab/Proxy/FlowSegment + Pset(企業名/機器名/調達もと) |

## Robotic construction — 全工程を robotics 手順に (tatekata 建方)

The plant is designed to be **built by robotics**, and every process is an
executable robot task graph (not just a 4D reveal):

| File | 中身 |
|---|---|
| `robots.edn` | 施工ロボット registry (7種: 自動建機/配筋/コンクリ3Dプリンタ/ボルト溶接/パネル/MEP/内装AGV) + reach/cycle/`:robot/process`/**正直な実用成熟度** |
| `process_gen.py` | 各工程 → **robot op 列** (調達→搬入→搬送→建方/据付/敷設/打設→締結/溶接→検査) = **125 ops / 23 steps** → `process.json` + `op/*` datom |

`construction.edn` の各 `:step` に `:step/robot`。`kami-app-tatekata`
(`run_tatekata_v1`) が各工程で割当ロボに op 列を実行させ、黄カートが材料を
受入→work-zone に搬送、据付/締結の間だけ geometry が成長(コンクリ=堆積field,
鉄骨=溶接field 赤熱)。`engineering.py` の **buildability** が各工程のロボ到達/
段取り回数/必要台数を算定 (`build/*` datom)。

| op action | 工程 | robot | material process |
|---|---|---|---|
| procure 調達 | 調達もと(商社) から発注 + リードタイム | (発注) | — |
| deliver 搬入 | 自律トラックで工場ゲート→受入 | robot:doboku | — |
| stage 搬送 | AGV で受入→work-zone 仮置き | robot:fitout | — |
| build 建方/据付/敷設/打設 | 工程ロボが施工 | step robot | deposition/weld |
| fasten 締結/溶接/養生 | ボルト/溶接/養生 | step robot | thermal-weld |
| inspect 検査 | scan-to-BIM 出来形照合 | robot:fitout | — |

**Honest**: R0 robotic process PLAN (task graph) + 簡略化 material-process field
(堆積height-grid / 移動熱源拡散) — 検証済み motion plan / cycle study / safety
case ではなく、material-process は granular/MPM/thermal-FEM ではない。

## Engineering passes (R0 — 簡略化モデル)

`engineering.py` turns "代表値の箱" into "式で計算・干渉検出・法規照合" — a real step up,
but **NOT** a licensed engineer's 構造/設備計算書・確認申請・消防同意.

| Pass | 中身 | 例 (現状) |
|---|---|---|
| クラッシュ検出 | utility 経路 vs 構造 AABB 干渉 + 設備同士の近接(<0.30m)交差 | 12件 (hard=4 壁貫通=要スリーブ, coord=8 x36埋設管交差=要上下調整) |
| 電気サイジング | 負荷集計→需要率0.65→幹線電流→電圧降下% | 需要73.8kVA / VD 1.49%<3% → **OK** |
| 給水サイジング | 器具給水負荷→設計流量→必要管径 | 必要32mm<PPR50A → **OK** |
| 排水サイジング | 横主管長×最小勾配1/100→必要落差 vs 確保落差 | 必要1.23m>0.6m → **NG**(要 中継ポンプ/深さ) |
| 法規チェック | 建ぺい率/容積率/避難距離/消火栓半径/駐車台数 | 消火栓 包含40m>25m → **要 複数栓** / 他OK |

→ 結果は kotoba datom (`clash/*`, `sizing/*`, `code/*`) として ingest され、`engineering.json`
にレポート、`clashes.json` で 3-D 可視化されます。**実際に設計上の不備を2件検出**(排水落差・単栓カバー)。

## Pipeline

```
building.edn + construction.edn  (EDN SSoT)
        │  python3 kotoba_gen.py
        ▼
factory.cdx.json   kotoba_ingest.json   construction.order.json
   (SBOM)          (kotoba EAVT body)    (Rust 4D build viewer)
```

`kotoba_gen.py` validates: step `:seq` is contiguous 1..N, `:depends-on` is
acyclic and references real steps, every `:consumes` is a real building part,
and every `:reveals` is a real render-element id in `factory.scene.json`
(`ground` + `floor` are synthetic render elements built by the renderer).

## Regenerate

```bash
python3 70-tools/e7m-sim/scenes/giemon-factory-r0/kotoba_gen.py
# building parts=74  cots=59  custom-fab=15  groups=[A-foundation..L-raw-materials]
# construction steps=23  nominal_programme_days=179
# clashes=12 (hard=4 coord=8)  sizing={電気:OK 給水:OK 排水:NG}  code_NG=[屋内消火栓 包含半径]
# wrote factory.cdx.json (74) + kotoba_ingest.json (117) + construction.order.json
#     + engineering.json + clashes.json + factory.ifc (956 STEP entities, 70 elements)
```

Standalone runs: `python3 engineering.py` (干渉/サイジング/法規), `python3 ifc_export.py`
(IFC), `python3 procurement.py` (調達もと一覧).

## kotoba queries (after `kg.ingest_batch`)

Mirrors the kabitori pilot (run `kotoba serve` with `KOTOBA_IPFS=off`, POST
`kotoba_ingest.json` to `.../kg.ingest_batch`):

| Question | Index | Query shape |
|---|---|---|
| 全建材点数 / total parts | AEVT | scan `part/bom = giemon-factory-r0` |
| F-equipment だけ | AVET | `part/group = F-equipment` |
| 施工手順 全ステップ | AEVT | `step/proc = giemon-factory-r0` |
| あるステップの先行作業 | EAVT | entity-frame of `step:NN`, read `step/dependsOn` |
| **逆**: このステップを待つ後続 | VAET | reverse-ref of `step:NN` via `step/dependsOn` |
| ある建材を使う工程 | VAET | reverse-ref of `bld:XX` via `step/consumes` |
| ゾーン別 機械 | AVET | `part/simFeature` ∈ zone machines |

## Constitutional non-goals (see ADR-2606010030)

- No mega-press / ≥7500 t HPDC clamping (N1, ADR-2605261200) — light-assembly only.
- No FEM/structural analysis — frame is rigid AABB geometry + a ledger, not solved.
- No MEP/HVAC/electrical simulation — MEP is a 建材 line item + schedule step only.
- `:sourcing :representative` — manufacturers/MPNs are R0 design examples, NOT a
  procurement or 建築確認申請 decision.
