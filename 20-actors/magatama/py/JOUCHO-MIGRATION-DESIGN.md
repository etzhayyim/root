<!-- ⚠️  DESIGN DOCUMENT — MDN FOR JOUCHO RELIGIOUS-CORP VARIANT ⚠️  -->

# JOUCHO-MIGRATION-DESIGN.md

Authoritative ADR: **ADR-2605215200** (`90-docs/adr/2605215200-etzhayyim-shinka-pregel-mst-rewrite.md`)

Design date: 2026-05-21  
Status: **PAPER DESIGN (no impl)** — deliverable is this doc + new lexicon file  
Intended reviewer: religiousAI / adherent governance

---

## Vendor Mechanism (Research Findings)

**Source:** Vendor `ai-gftd-apps-gftdcojp/20-actors/magatama/py/src/pymagatama/shinka/__init__.py` (495 LOC)

**Architecture:** Vendor does NOT write `vertex_joucho` table — reads only. The joucho mood axes (5-axis: joy/calm/stress/gratitude/focus, each int 0–100) originate from an unidentified upstream source (likely MagatamaApp event scoring or pre-computed in RW). The shinka heartbeat loop consumes the latest joucho row via:

```python
row = fetch_one(
    "SELECT mood, joy, calm, stress, gratitude, focus FROM vertex_joucho "
    "WHERE owner_did = %s ORDER BY created_at DESC LIMIT 1",
    (did,),
)
```

**Mood classification** (pure function, no side effects):
- stress >= 70 → stressed (inhibits post/engage; triggers recovery drill)
- joy >= 60 → joyful (expressive, post + engage enabled)
- calm >= 60 → calm (introspective, validate + analyze enabled)
- gratitude >= 60 → grateful (social, short engage cadence)
- focus >= 60 → focused (concentrated, kyumei-koji priority)
- else → neutral (balanced thresholds across all)

**Cadence table** (mood × elapsed-since-last-heartbeat determines flags: should_post/engage/drill/validate/analyze). New actor defaults: axes={joy:40, calm:40, stress:20, gratitude:30, focus:40} → neutral mood.

**Use:** Cadence drives 5 action flags that gate heartbeat behavior (publish, social engagement, self-repair, governance validation, analysis).

---

## Religious-Corp Variant: Design Decision

### Chosen Option: **Aggregation Cell (Option A)** + On-Demand Fallback (Hybrid A+B)

**Verdict:** Deploy **JouchoAggregationCell** as primary persistent joucho source (MST write path), with on-demand recomputation gated by fresh-data needs (optional, Phase C).

**Reasoning:**

1. **Cost efficiency (primary):** Single scheduled aggregation (1h cron) beats per-caller recomputation across 18k adherents. O(1) read per heartbeat << O(N) per-adherent scan of kyumeiSignal.

2. **Substrate alignment:** Religious-corp substrate (ADR-2605172000) forbids RisingWave-only writes. MST + optional IPFS pins is the law. Aggregation cell writes to MST, shinka heartbeat reads from MST (not RW). Zero RW dependency.

3. **Freshness trade-off acceptable:** Joucho mood is psychological state — 1h aggregation latency (max) is acceptable. Real-time emotion tracking is neither user-facing nor guaranteed (vendor itself uses 15m cron). Adherents with high-recency signal needs can opt-in to on-demand (Phase C) via capability flag.

4. **Simplicity:** Single cell, single write path, single lexicon record type. ShinkaHeartbeatCell reads one MST joucho record per adherent per tick. No branching logic.

### Rejected options:
- **Option B (On-Demand):** Would require every agent (shinka, yoro, kyumei) calling aggregation independently. 18k adherents × 4-8 calls/day = 100k+ daily calls. LLM cost and latency unacceptable without caching.
- **Option C (Pure Hybrid):** Scheduled writes + on-demand recompute branches adds complexity for marginal freshness gain (1h → ~5min). Not justified until Phase C use-case surfaces.

---

## Cell Design

### JouchoAggregationCell

**Placement:** levi (etzhayyim Murakumo node, per `50-infra/murakumo/fleet.toml`)  
**Port:** 13027 (reserved in fleet.toml; next free after shinka heartbeat 13026)

**Trigger:** 
- **Primary:** Cron `0 * * * *` (every hour, UTC) — bulk recomputation
- **Secondary:** MST listener on `app.etzhayyim.shinka.kyumeiSignal` (mst.onCommit) — within-hour freshness for active adherents (optional, Phase C, off in M5)

**Write path:**
1. Query MST for recent `app.etzhayyim.shinka.kyumeiSignal` records (last 7 days)
2. Group by `adherentDid` → aggregate weights per signal kind
3. Compute 5-axis joucho via signal-kind mapping (see Aggregation Algorithm)
4. Write/upsert to MST: `app.etzhayyim.joucho.joucho` record (1 per adherent)
5. Log result and latency

**Error handling:** 
- Missing kyumeiSignal → use new-adherent defaults (joy:40, calm:40, stress:20, gratitude:30, focus:40)
- MST write failure → log and retry next cron (no alert cascade; resilience via periodic re-run)

**Latency SLO:** <2s per 100 adherents (typical: 18k adherents ≈ 360s total per hour)

---

## New Lexicon Spec

**NSID:** `app.etzhayyim.joucho.joucho`  
**Kind:** Record (keyable by adherent DID path, indexed by MST)  
**Purpose:** Store aggregated joucho emotional axes (5-axis mood state + computation metadata)

### Schema (AT Protocol Lexicon v1)

```json
{
  "lexicon": 1,
  "id": "app.etzhayyim.joucho.joucho",
  "defs": {
    "main": {
      "type": "record",
      "description": "Joucho (情報) aggregated 5-axis emotional state derived from kyumeiSignal records. Consumed by ShinkaHeartbeatCell and other mood-aware agents per ADR-2605215200 §3.",
      "key": "did",
      "record": {
        "type": "object",
        "required": [
          "adherentDid",
          "joy",
          "calm",
          "stress",
          "gratitude",
          "focus",
          "computed_at",
          "from_signal_count"
        ],
        "properties": {
          "adherentDid": {
            "type": "string",
            "format": "did",
            "description": "DID of the adherent whose joucho this record represents."
          },
          "joy": {
            "type": "integer",
            "minimum": 0,
            "maximum": 1000,
            "description": "Joy axis in permille (0–1000). Driven by ritual + kuniUmi-witness signals."
          },
          "calm": {
            "type": "integer",
            "minimum": 0,
            "maximum": 1000,
            "description": "Calm axis in permille (0–1000). Driven by oath + governance-participation signals."
          },
          "stress": {
            "type": "integer",
            "minimum": 0,
            "maximum": 1000,
            "description": "Stress axis in permille (0–1000, inverted semantics). High = distressed. No direct positive signal kind; derived from absence of positive signals or governance blockers."
          },
          "gratitude": {
            "type": "integer",
            "minimum": 0,
            "maximum": 1000,
            "description": "Gratitude axis in permille (0–1000). Driven by contribution signals."
          },
          "focus": {
            "type": "integer",
            "minimum": 0,
            "maximum": 1000,
            "description": "Focus axis in permille (0–1000). Driven by oath + contribution signals (deep practice)."
          },
          "computed_at": {
            "type": "string",
            "format": "datetime",
            "description": "ISO 8601 timestamp when this joucho was computed by JouchoAggregationCell."
          },
          "from_signal_count": {
            "type": "integer",
            "minimum": 0,
            "description": "Count of kyumeiSignal records aggregated into this joucho. 0 = new-adherent defaults applied."
          },
          "from_signal_days": {
            "type": "integer",
            "minimum": 1,
            "maximum": 7,
            "description": "Recency window in days for included signals (default 7). Allows temporal decay strategies in Phase C."
          }
        }
      }
    }
  }
}
```

### Encoding Notes

- **Axes in permille (0–1000)** instead of percentage — AT Protocol Lexicon forbids float type. 1000 = 100%, 500 = 50%, etc. Vendor used int 0–100; religious-corp scales to permille for precision (e.g., 567 permille = 56.7%).
- **No nested array.** kyumeiSignal breakdown would be `{kind: "ritual", weight: 800}` array — forbidden by AT Lexicon inline-object rules. Aggregated axes are sufficient; breakdown lives in IPFS provenance record if needed (Phase C).
- **DID as key:** MST indexing by adherent DID path is canonical (one joucho record per adherent, updated hourly).

---

## Aggregation Algorithm

### Signal-Kind Mapping

| kyumeiSignal.signalKind | Target Axes | Aggregation Rule |
|---|---|---|
| `ritual` | joy, focus | weight × 0.8 → joy; weight × 0.3 → focus |
| `oath` | calm, focus | weight × 0.9 → calm; weight × 0.7 → focus |
| `contribution` | gratitude, focus | weight × 1.0 → gratitude; weight × 0.5 → focus |
| `governance-participation` | calm | weight × 0.8 → calm |
| `kuniUmi-witness` | joy | weight × 0.6 → joy |

### Pseudocode

```
input: adherentDid, kyumeiSignal records (last 7 days)
output: JouchoAxes (joy, calm, stress, gratitude, focus)

if signals.empty():
  return new_adherent_defaults()

// Accumulate weighted signals
joy_acc = 0, calm_acc = 0, gratitude_acc = 0, focus_acc = 0

for each signal in signals:
  if signal.recordedAt < now - 7 days:
    skip  // recency window
  
  match signal.signalKind:
    case "ritual":
      joy_acc += signal.weight * 0.8
      focus_acc += signal.weight * 0.3
    case "oath":
      calm_acc += signal.weight * 0.9
      focus_acc += signal.weight * 0.7
    case "contribution":
      gratitude_acc += signal.weight * 1.0
      focus_acc += signal.weight * 0.5
    case "governance-participation":
      calm_acc += signal.weight * 0.8
    case "kuniUmi-witness":
      joy_acc += signal.weight * 0.6

// Normalize to 0–1000 (permille)
signal_count = count(signals)
joy = clamp(0, 1000, joy_acc / signal_count)
calm = clamp(0, 1000, calm_acc / signal_count)
gratitude = clamp(0, 1000, gratitude_acc / signal_count)
focus = clamp(0, 1000, focus_acc / signal_count)

// Stress as absence of positive mood (inhibitor)
positive_mood = (joy + calm + gratitude + focus) / 4
stress = clamp(0, 1000, 1000 - positive_mood)

return JouchoAxes(joy, calm, stress, gratitude, focus)
```

### Recency Filter

**Default:** Include signals from last 7 days (configurable per Phase C). Signals older than window are discarded.

**Rationale:** Joucho mood should reflect recent activity (last week of practice). Stale signals (>7d) indicate dormancy; 7d window balances freshness with noise tolerance.

**Future (Phase C):** Exponential decay (e.g., weight *= exp(-days_old / 3.5)) can smooth temporal dynamics without hard cutoff.

---

## Open Questions for Review

1. **Signal weight interpretation:** Should weight be normalized per signal kind (e.g., divide by signal count per kind), or use raw weight sums? Current algorithm uses raw sum / total count — risk of one-signal-kind domination. Suggest review by adherent governance.

2. **Stress computation:** Stress = 1000 - average(positive axes) is synthetic (not directly signaled). Should stress have direct positive signal kinds (e.g., `recovery` / `healing`)? Or keep stress as inhibitor-only?

3. **MST update cadence fallback:** If kyumeiSignal sources are unreliable, should JouchoAggregationCell fall back to vendor joucho snapshot (read from historical RW export)? Or assume kyumeiSignal is primary source of truth?

4. **Cron time:** 1h cron at `0 * * * *` (top of hour) may cause stampede if other cells also run then. Should phase-shift to `0 2,5,8,11,14,17,20,23 * * *` (3-hourly) for scalability? Trade-off: 3h max latency vs. 1h latency.

5. **Per-adherent opt-out:** Should cell respect a capability flag (e.g., `joucho.aggregation.disable`) to skip aggregation for specific adherents (e.g., those running local aggregation)? Complicates logic but respects autonomy.

6. **Lexicon versioning:** Should `app.etzhayyim.joucho.joucho` have a version suffix (e.g., `v1` / `v2`)? Follows AT Proto convention for breaking changes.

---

## Phase Roadmap (ADR-2605215200)

| Phase | Deliverable | Status |
|---|---|---|
| **M2** | shinka_murakumo.py skeleton + JouchoAxes / CadencePolicy classes | ✅ 2026-05-21 (this session) |
| **M3** | JouchoAggregationCell impl + etzhayyim-sdk-py MST client | ⏳ post-review |
| **M4** | 6 new lexicons (observe / validate / emit / heartbeat / joucho / ???) | ⏳ post-M3 |
| **M5** | End-to-end test: 1 adherent tick, MST joucho + shinka heartbeat visible | ⏳ post-M4 |
| **Phase C (optional)** | On-demand recomputation + exponential decay + capability flags | future |

---

**Next step:** Deploy design to governance for review (2–3 days), then proceed to M3 impl.
