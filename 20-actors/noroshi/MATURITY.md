# noroshi (烽) — Maturity Ledger

`/loop` 進捗台帳。各イテレーションで **1項目** だけ成熟度を上げ、ここに記録する。
honest framing: できていないことは「未」と明記する。

- Actor: `did:web:etzhayyim.com:actor:noroshi` · ADR-2606051600 · Tier-B · **R0+R1 (offline)**
- 光電融合 (photonics-electronics convergence) comms chip + ISAC (integrated sensing &
  communication) + packaging robotics。link-budget/CPO + OFDM-radar JCAS + active-alignment。
- 不変条件(厳守): **civilian-only**(兵器/軍事 RF-seeker は表現不能) · **object-not-person**
  (ISAC センシングは物体のみ、人物追跡なし) · **active-alignment under laser-safety**
  (IEC 60825) · **open-EDA**(プロプライエタリ EDA を SoR にしない) · **Murakumo-only**
  inference(ADR-2605215000) · **no-server-key**(ADR-2605231525) · live actuation は G8-gated
  (`.solve()` は R0 で RuntimeError)。

## 成熟度チェックリスト

| # | 項目 | 状態 | 完了 |
|---|---|---|---|
| 1 | ADR-2606051600 (master) + dividend coupling (2606032130) | ✅ | init |
| 2 | manifest + CLAUDE.md + 5 Lexicons (`com.etzhayyim.noroshi.*` — photonicDevice/opticalLinkBudget/isacWaveform/senseEstimate/packagingJob) | ✅ | init |
| 3 | **7 method impl を cljc に移行** (active_alignment / cable_endpoint / fibre_loop / isac_sim / kami_isac_bridge / link_budget / pic_layout) — substrate-native, py pruned | ✅ | port-wave |
| 4 | **11 cljc テストスイート green** — `run_tests.sh` で **163 tests / 552 assertions / 0 fail**(active-alignment / cable-endpoint / **charter-invariants** / consistency / fibre-loop / governance / isac-sim / kami-isac-bridge / lexicons / link-budget / pic-layout) | ✅ | port-wave |
| 5 | charter-invariants テストが civilian / object-not-person / laser-safety / open-EDA ゲートを assert | ✅ | port-wave |
| 6 | run_tests.sh が fleet green-check に wired(全 cljc ns を bb で実行) | ✅ | port-wave |
| 7 | kami-engine ISAC bridge(`kami_isac_bridge.cljc` — OFDM-radar JCAS を kami-genesis 物理で検証) | ✅ | port-wave |
| 8 | **本台帳 (MATURITY.md)** を新設 — 成熟度の honest 追跡を開始 | ✅ | **iter (this)** |
| 9 | R1 live legs (実 PIC レイアウト→fab handoff / 実 fibre 整列 actuation) — G8 Council Lv6+ + operator gated | 未(R1+) | — |
| 10 | Murakumo-fleet autorun heartbeat(他 observatory actor の shionome パターン parity) | 未 | — |
| 11 | 実 link-budget/ISAC データの kotoba Datom log 投影 + commit-DAG | 未 | — |

## イテレーション記録

### iter (this) — 2026-06-18
**上げた項目: #8 — MATURITY.md を新設。** noroshi は既に実質的に成熟(7 cljc method impl + 5
Lexicons + 11 テストスイート **163 tests / 552 assertions green**、ISAC sim + kami-engine bridge)
だが成熟度台帳が無かった。fleet-wide な `run_tests.sh` reflex sweep で noroshi の reflex が green
であること(163/552、0 fail)を確認した上で、現状を honest に記録(✅ 済み項目と R1 以降の「未」を
明記)。ゲートは一切触れず — charter-invariants テストが civilian/object-not-person/laser-safety/
open-EDA を assert 済みであることを台帳に記録しただけ。`.solve()` は R0 で RuntimeError のまま
(live actuation は G8-gated、未)。
