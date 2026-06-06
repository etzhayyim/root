#!/usr/bin/env python3
"""tsumugi 紡ぎ — DRY-RUN mirror social-post projector for the influence-history graph.
ADR-2606061500 (entity-as-actor mirror ADR-2606042330 + feed-post membrane ADR-2605231902).

Generates `app.bsky.feed.post`-shaped OBSERVATIONS about documented historical influence —
NEVER the figure speaking. Two structural guarantees (N2 mirror, never impersonation):

  * :post/voice is LOCKED to :observer. There is no first-person template and no code path
    that emits a figure's words. project_post() refuses any node lacking :mirror/is-mirror.
  * every post text OPENS with the node's :mirror/disclaimer.

All posts are :post/published false (DRY-RUN, G7 outward-gated). Live publish to the firehose
needs Council + operator. Narration here is deterministic/templated; live narration routes
through Murakumo (G6, ADR-2605215000) — never a vendor LLM.

stdlib only. Usage:
    python3 project_influence_posts.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
from analyze_influence import read_edn, load  # reuse the EDN reader + loader

KIND_VERB = {
    ":influences": "shaped", ":transmits": "was transmitted into", ":cites": "is cited by",
    ":reinterprets": "was reinterpreted by", ":synthesizes": "was synthesized into",
    ":translates": "was carried across language into", ":opposes": "was defined against by",
}

class ImpersonationError(Exception):
    """Raised if a post would be authored AS a figure rather than ABOUT one (N2)."""

def project_post(node: dict, flow: dict | None, nodes: dict, tick: int) -> dict:
    # N2 GUARD: only mirrors may be projected, and only in observer voice.
    if not node.get(":mirror/is-mirror"):
        raise ImpersonationError(f"{node.get(':organism/id')} is not a mirror — refuse (N2)")
    disclaimer = node.get(":mirror/disclaimer", "観察像 — 本人ではない (observational mirror)")
    label = node.get(":organism/label", node.get(":organism/id"))
    if flow is not None:
        frm = nodes[flow[":flow/from"]].get(":organism/label", flow[":flow/from"])
        to = nodes[flow[":flow/to"]].get(":organism/label", flow[":flow/to"])
        verb = KIND_VERB.get(flow.get(":flow/kind"), "influenced")
        w = float(flow.get(":flow/signed-weight", 0.0))
        body = (f"観察: 「{frm}」 {verb} 「{to}」 "
                f"(documented influence, weight {w:+.2f}). "
                f"An information channel across history, not an endorsement.")
        pid = f"post.{flow[':flow/id'][3:]}"
        about_flow = flow[":flow/id"]
    else:
        trad = ",".join(t[1:] for t in node.get(":hist/tradition", []))
        body = (f"観察: 「{label}」 — public influence-bearing node "
                f"({node.get(':hist/subkind','?')[1:]}; {trad}). "
                f"Mapped for its documented influence on later thought, never adjudicated for truth.")
        pid = f"post.node.{node[':organism/id']}"
        about_flow = None
    # voice is structurally :observer — there is NO branch that emits first-person text.
    post = {
        ":post/id": pid,
        ":post/about-node": node[":organism/id"],
        ":post/voice": ":observer",          # LOCKED (N2)
        ":post/text": f"{disclaimer}\n{body}",
        ":post/tick": tick,
        ":post/published": False,            # DRY-RUN (G7)
        ":post/sourcing": ":representative",
    }
    if about_flow:
        post[":post/about-flow"] = about_flow
    return post

def edn_str(p: dict) -> str:
    parts = []
    for k, v in p.items():
        if isinstance(v, bool):
            parts.append(f"{k} {'true' if v else 'false'}")
        elif isinstance(v, str) and v.startswith(":"):
            parts.append(f"{k} {v}")
        elif isinstance(v, str):
            esc = v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
            parts.append(f'{k} "{esc}"')
        else:
            parts.append(f"{k} {v}")
    return "{" + " ".join(parts) + "}"

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = args[0] if args else str(here / "data" / "seed-influence-history.kotoba.edn")
    outdir = pathlib.Path(sys.argv[sys.argv.index('--out') + 1]) if '--out' in sys.argv else here / "out"
    outdir.mkdir(parents=True, exist_ok=True)

    nodes, flows = load(seed)
    tick = 0
    posts = []
    # one observation per influence edge (the most informative), plus one per node summary
    for f in flows:
        if f[":flow/from"] in nodes and f[":flow/to"] in nodes:
            posts.append(project_post(nodes[f[":flow/to"]], f, nodes, tick))
    for k, nd in nodes.items():
        posts.append(project_post(nd, None, nodes, tick))

    assert all(p[":post/voice"] == ":observer" for p in posts), "N2: all posts must be observer voice"
    assert all(p[":post/published"] is False for p in posts), "G7: all posts must be dry-run"

    out = outdir / "influence-posts.dryrun.kotoba.edn"
    lines = [";; tsumugi 紡ぎ — GENERATED dry-run mirror posts (ADR-2606061500). DO NOT hand-edit.",
             ";; N2 mirror-only: every post is OBSERVER voice ABOUT a node — never the figure speaking.",
             ";; G7 outward-gated: every :post/published is false. Live firehose = Council + operator.",
             "["]
    lines += [edn_str(p) for p in posts]
    lines.append("]")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"✓ {len(posts)} dry-run mirror posts (observer voice, published=false)")
    print(f"✓ wrote {out}")

if __name__ == "__main__":
    main()
