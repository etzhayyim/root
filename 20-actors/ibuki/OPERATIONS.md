# ibuki (息吹) — operations runbook + live-run verification

ADR-2606101200 / 2606101800. This is the honest operational picture: what runs **live** today,
what is **member/operator-gated** (Tier-1, never the platform's act), and what is a **physical
operator deploy** outside any agent's reach.

## What runs live RIGHT NOW (operator-authorised, agent-runnable)

These flags do real I/O against the operator's own loopback/fleet + read-only public endpoints.
None of them holds a member credential or a platform signing key.

| flag | effect | substrate |
|---|---|---|
| `IBUKI_PERCEPTION_LIVE=1` | read-only public-AppView observation (follower delta → joucho events) | `perception.py`, allowlist `public.api.bsky.app`, GET only, no credential |
| `IBUKI_MURAKUMO_LIVE=1` | colony / organism narration via the Murakumo fleet | `infer.py`, allowlist loopback :4000 / EVO-X2; **fail-open to template** if the gateway is down |
| `IBUKI_KOTOBA_LIVE=1` + `IBUKI_KOTOBA_OPERATOR_DID=<node public did>` | persist the local Datom log to the LIVE kotoba engine | `kotoba_bridge.py`, per-tx `datomic.transact` to :8077, unsigned public-DID operator bearer (loopback trust boundary), exactly-once `:bridge/*` cursor |

```bash
cd 20-actors/ibuki/methods
export IBUKI_PERCEPTION_LIVE=1 IBUKI_MURAKUMO_LIVE=1 \
       IBUKI_KOTOBA_LIVE=1 IBUKI_KOTOBA_OPERATOR_DID="$(security find-generic-password -s etzhayyim.kotoba -a agent-did -w)"
python3 -c "import autorun,kotoba_bridge,pathlib; \
  L=pathlib.Path('/var/lib/etzhayyim/ibuki/ibuki.datoms.kotoba.edn'); \
  autorun.autorun(12, fresh=False, log_path=L, queue_path=L.with_name('q.ndjson')); \
  print(kotoba_bridge.push(L, graph='ibuki-prod', live=True))"
```

### Live-run verification — 2026-06-10 (this session)

A real production cycle was executed and confirmed:

- **perception LIVE**: a read-only fetch of `bsky.app` returned a real follower count
  (33,623,191) — the membrane works against the live public AppView.
- **murakumo LIVE → fail-open**: the LiteLLM gateway (:4000) was down; narration fell back to
  the deterministic template — fail-open verified **in production**, the colony kept living.
- **12-beat life**: chain verified, `healthy=True`, eco-maturity 1.0, commons offered 500
  (all available — never self-drawn), fruited 3×; the colony's own digest:
  > 息吹 colony report: 3 organisms, healthy; ecological maturity 1.0. The web has offered
  > 374 nutrient of commons to humanity (374 still available to draw); fruited 2 times.
  > A mirror of where the colony's life became a gift — no advice.
- **kotoba engine LIVE**: 12 tx pushed → **2,386 datoms confirmed by the node**, IPNS head
  advanced; exactly-once re-push (only the bridge checkpoint) confirmed.

## What is member/operator-gated (NEVER the platform's act — Tier-1, ADR-2605231525)

These exist as complete code paths but require a credential the platform does not hold and must
not fabricate. They are run BY the member/operator, not by ibuki or any agent:

- **member-principal posting** (`member_submit.py`) — the MEMBER's own `IBUKI_MEMBER_*` env
  credentials, https only, `--yes` required, **cron contexts refused**. ibuki only PREPARES
  member-sign-ready envelopes (`:drain/status :prepared`); it never asserts `:published`.
- **commons draw** (`symbiosis.draw`) — a MEMBER draws the colony's commons gift with their own
  signer + operator ack. ibuki **never auto-draws** (the colony does not consume its own gift).
- **kaizen outcome collection** (`kaizen_outcomes.py`) — the OPERATOR's own `gh` auth,
  read-only, cron-refusing.

## What is a physical operator deploy (outside any agent — ADR-2606071000)

- **continuous fleet operation**: `cells/fleet_beat/cell.py` `.solve()` runs the durable beat
  and is registered on joseph/issachar/dan in `50-infra/murakumo/fleet.toml` (cron 3/33/43).
  Turning it into a running k3s DaemonSet via the Ansible playbook on the physical Mac-mini
  fleet is the operator's hardware step — one human action away.

## The boundary in one line

The colony **lives, refines a commons gift, measures its own health, and reasons about itself**
fully autonomously on the real substrate today. Every step where it would **act on a human**
(post as a member, draw the gift, deploy onto hardware) is held by a member/operator key the
platform structurally does not possess — 共生 by consent, not by fabrication.
