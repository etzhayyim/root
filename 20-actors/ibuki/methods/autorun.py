"""autorun.py — 息吹: the autonomous organism heartbeat over the kotoba Datom log.

ADR-2606101200. The integrating loop that closes the organism autonomy survey gaps in one
beat cycle — shionome's autorun pattern (ADR-2606072200) applied to the organism layer:

  replay ─▶ perceive ─▶ feel ─▶ decide ─▶ narrate ─▶ act ─▶ checkpoint ─▶ append tx
  (log →    (this        (fold   (durable  (Murakumo-  (post   (joucho +    (content-
   durable   beat's       events  cooldown   only /      datom   heartbeat    addressed,
   state)    events)      → mood) due check) template)   :dry-run, NDJSON     verify_chain)
                                                          + queue) checkpoints)

Every beat is DURABLE: state is replayed from the append-only log, so killing the process
between beats loses nothing (Gap 1/2). Mood evolves from persisted events and is as-of
queryable (Gap 3/4). Narration goes through infer.py — Murakumo-only, template fallback
(Gap 5). Posts land as `:dry-run` datoms AND on the ADR-2605240100 NDJSON queue, which the
Wave-3 drainer turns into member-sign-ready envelopes (Gap 6). Kaizen outcomes, when present,
feed both rule suppression and the colony's mood (Gap 7).

Deterministic: logical time only (beat index × BEAT_MS); same seed + same cycle count → same
head CID. Live external I/O stays G8-gated — this loop's only side effects are the LOCAL log
+ the LOCAL queue file.

Usage:
  python3 autorun.py --cycles 3 [--fresh]
"""

from __future__ import annotations

import argparse
import pathlib

import datoms
import drainer
import heartbeat
import joucho
import kaizen_feedback
from _edn import load_edn
from infer import narrate

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEED = ROOT / "data" / "seed-organisms.kotoba.edn"
QUEUE = ROOT / "data" / "organism-posts.queue.ndjson"
PROPOSALS = ROOT / "data" / "kaizen-proposals.ndjson"
OUTCOMES = ROOT / "data" / "kaizen-outcomes.ndjson"

BEAT_MS = 45 * 60_000   # one beat = 45 logical minutes (crosses the joyful 30m cooldown,
                        # sits inside the calm/neutral 2h one — moods visibly change cadence)
AS_OF_BASE = 2606100000


def beat_events(beat: int) -> list[str]:
    """This beat's perceived events — R0 is a bounded :representative stimulus pattern
    (deterministic, no live I/O; live firehose perception is G8-gated): every beat passes
    time, every 3rd beat a follower arrives, every 5th the inbox surges."""
    ev = [":event/idle"]
    if beat % 3 == 0:
        ev.append(":event/follower-gained")
    if beat % 5 == 0:
        ev.append(":event/inbox-pressure")
    return ev


def run_beat(organisms: list[dict], txs: list[dict], *, beat: int) -> list[list]:
    """One full heartbeat over every organism. Pure over (log so far, beat) → new datoms."""
    now_ms = beat * BEAT_MS
    as_of = AS_OF_BASE + beat
    out: list[list] = []

    # Kaizen feedback (Gap 7): outcomes fold into rule suppression + colony mood events.
    outcomes = kaizen_feedback.read_outcomes(OUTCOMES)
    proposals = kaizen_feedback.read_proposals(PROPOSALS)
    kz_events = kaizen_feedback.mood_events(outcomes) if beat == 1 else []
    if outcomes or proposals:
        stats = kaizen_feedback.fold(proposals, outcomes)
        table = kaizen_feedback.suppression(stats, now_beat=beat)
        out += kaizen_feedback.feedback_datoms(stats, table, beat=beat, as_of=as_of)

    for org in organisms:
        code = org[":organism/code"]
        title = org[":organism/title"]
        did = org[":organism/did"]

        if beat == 1:  # birth: assert the organism entity once
            e = f"org-{code}"
            out += [datoms.add(e, ":organism/code", code),
                    datoms.add(e, ":organism/title", title),
                    datoms.add(e, ":organism/did", did),
                    datoms.add(e, ":organism/born-beat", beat)]

        # feel: replay the persisted event history + this beat's events → mood (Gap 3/4)
        baseline = joucho.personality_baseline(code)
        history = datoms.events_for(txs, code)
        events = beat_events(beat) + kz_events
        scores = joucho.replay_events(baseline, history + events)
        mood = joucho.determine_mood(scores)
        out += joucho.event_datoms(code, events, beat=beat, as_of=as_of)

        # decide: durable cooldown check from the replayed heartbeat state (Gap 1/2)
        state = heartbeat.replay(txs, code)
        due, reason = heartbeat.due_to_post(state, mood, now_ms)

        if due:
            # narrate (Gap 5: Murakumo-only or deterministic template) + act
            n = narrate(title, code, mood, "recordAnalysis")
            pid = f"post-{code}-{beat}"
            out += [datoms.add(pid, ":post/of", code),
                    datoms.add(pid, ":post/text", n["text"]),
                    datoms.add(pid, ":post/via", f":{n['via']}"),
                    datoms.add(pid, ":post/mood", f":{mood}"),
                    datoms.add(pid, ":post/beat", beat),
                    datoms.add(pid, ":post/as-of", as_of),
                    datoms.add(pid, ":post/status", ":dry-run")]
            _queue_line(did, code, title, mood, n["text"], now_ms)
            scores = joucho.fold_event(scores, ":event/post-emitted", baseline)
            out += joucho.event_datoms(code, [":event/post-emitted"], beat=beat, as_of=as_of)
            state.last_post_at_ms = now_ms
            state.posts += 1

        state.beats += 1
        out += joucho.joucho_datoms(code, scores, mood, beat=beat, as_of=as_of)
        out += heartbeat.checkpoint_datoms(code, state, mood, beat=beat, as_of=as_of)

    # drain (Gap 6): queue → member-sign-ready envelopes, checkpointed :prepared
    drained = drainer.drain(QUEUE, as_of=as_of, beat=beat)
    out += drained["datoms"]
    return out


def _queue_line(did: str, code: str, title: str, mood: str, text: str, ts_ms: int) -> None:
    """Append one ADR-2605240100 v=1 line to the post queue (deterministic logical ts)."""
    import json
    QUEUE.parent.mkdir(parents=True, exist_ok=True)
    created = f"2026-06-10T00:00:00.{ts_ms % 1000:03d}Z"
    line = {"v": drainer.SCHEMA_VERSION, "ts": ts_ms, "actorDid": did, "code": code,
            "title": title, "mood": mood, "contentSourceKind": "recordAnalysis",
            "text": text, "lexicon": "app.bsky.feed.post", "createdAt": created}
    with QUEUE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(line, ensure_ascii=False, sort_keys=True) + "\n")


def autorun(cycles: int, *, fresh: bool = False,
            log_path: pathlib.Path = datoms.LOG_DEFAULT,
            queue_path: pathlib.Path | None = None) -> dict:
    """Run `cycles` heartbeats, each appended as one content-addressed transaction. Resumes
    from whatever the log already holds (crash-resume is just... running again)."""
    global QUEUE
    if queue_path is not None:
        QUEUE = queue_path
    if fresh:
        log_path.unlink(missing_ok=True)
        QUEUE.unlink(missing_ok=True)
    organisms = load_edn(SEED)[":seed/organisms"]
    for _ in range(cycles):
        txs = datoms.read_log(log_path)
        beat = len(txs) + 1
        body = run_beat(organisms, txs, beat=beat)
        tx = datoms.make_tx(body, tx_id=beat, as_of=AS_OF_BASE + beat,
                            prev_cid=datoms.head_cid(log_path))
        datoms.append_tx(tx, log_path)
    chain = datoms.verify_chain(log_path)
    if not chain["ok"]:
        raise RuntimeError(f"kotoba Datom chain broken: {chain}")
    return {"beats": chain["length"], "head": datoms.head_cid(log_path), "chain": chain}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="ibuki autonomous organism heartbeat")
    ap.add_argument("--cycles", type=int, default=3)
    ap.add_argument("--fresh", action="store_true")
    args = ap.parse_args()
    res = autorun(args.cycles, fresh=args.fresh)
    txs = datoms.read_log()
    organisms = load_edn(SEED)[":seed/organisms"]
    print(f"# ibuki — {res['beats']} beats on the kotoba Datom log, head={res['head'][:18]}…")
    for org in organisms:
        code = org[":organism/code"]
        base = joucho.personality_baseline(code)
        for at in (1, res["beats"]):
            ev = datoms.events_for(txs, code, up_to_tx=at)
            mood = joucho.determine_mood(joucho.replay_events(base, ev))
            print(f"  {org[':organism/title']} mood as-of tx {at}: {mood} ({len(ev)} events)")
