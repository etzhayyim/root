# actor-dna — code + data, one content-addressed unit (kotoba ⇢ Holochain-iso)

**ADR-2606112000.** Pure-stdlib substrate that binds a kotoba actor's **CODE** (WASM) and
**DATA** (graph) into ONE content-addressed identity — the property Ethereum (bytecode +
storage at one account) and Holochain (a DNA hash wrapping WASM zomes + integrity rules + the
DHT) have and plain kotoba lacked.

## The gap it closes

Before: a kotoba actor was **four** separate content-addresses linked only by references in
`did.json` — the WASM program CID, the data-graph CID, the validation rules, the lexicon — and
the engine was append-only with CACAO auth (who may write) but **no code-defined validation of
what is written**.

After: the **Actor DNA manifest** is one canonical-EDN object whose raw CIDv1 (`dna_cid`) is the
actor's whole identity. `did.json` points at `ipfs://<dna-cid>` and nothing else. Change any part
— recompile the WASM, edit a rule, retarget the graph — and the DNA CID changes: code and data
are fused into one tamper-evident hash.

```
{:dna/spec "kotoba-actor-dna/v0"
 :dna/actor-did   "did:web:etzhayyim.com:actor:ibuki"
 :dna/wasm-cid    "bafkrei…"   ; CODE   (raw CID; ipfs add --raw-leaves)
 :dna/graph       "ibuki"      ; DATA   (the graph this code governs)
 :dna/graph-cid   "bafyrei…"   ; DERIVED = graph_cid(:dna/graph) — the binding is ASSERTED
 :dna/validation-cid "bafkrei…"; the integrity ruleset
 :dna/lexicon-cid "bafkrei…"
 :dna/capability  "datom:transact"}     ; the CACAO leash this actor's writes present (ADR-2606111400)
```

## Modules (stdlib, deterministic)

| file | what |
|---|---|
| `cid.py` | CIDv1 helpers — `cidv1_raw` (0x55, byte-identical to `ipfs add --cid-version=1 --raw-leaves`) + `cidv1_dag_cbor`/`graph_cid` (0x71, `KotobaCid::from_bytes`). Cross-checked byte-identical vs `orgs/etzhayyim/com-etzhayyim-rasen/methods/cid.py`; `graph_cid("ibuki")` matches the live engine's graph CID. |
| `dna.py` | build / `dna_cid` / `verify` the manifest. `verify` recomputes `graph_cid(:dna/graph)` and checks `:dna/graph-cid` (the binding is tamper-evident), and — given the bytes — re-verifies each referenced CID (the trustless re-verify a WASM loader does). |
| `integrity.py` | the **integrity-zome analogue**: a content-addressed ruleset (`validation_cid`) + `validate(datoms, rules)` that **REJECTS** non-conforming datoms before they are pushed (append-only / closed-vocabulary / attr-types / denied-attrs / required-attrs / graph-binding). |
| `deploy.py` | the atomic deploy **descriptor**: an ordered plan (pin code → pin validation → pin lexicon → pin manifest → graph-genesis → did-link) where **every step binds to the one DNA CID** — atomicity-of-identity. |

## Run

```
./run_tests.sh        # 33 tests / 4 hermetic stdlib suites
python3 -c "import dna, integrity as ig, cid; \
  r={':integrity/spec':'kotoba-integrity/v0',':integrity/graph':'ibuki',':integrity/append-only':True}; \
  m=dna.build(actor_did='did:web:etzhayyim.com:actor:ibuki', \
    wasm_cid=cid.cidv1_raw(b'wasm'), graph='ibuki', \
    validation_cid=ig.validation_cid(r), lexicon_cid=cid.cidv1_raw(b'lex')); \
  print('DNA CID =', dna.dna_cid(m))"
```

## Honest scope (what's done vs the gated follow-up)

**Done (this repo owns it):**
- both CODE and DATA content-addressed + re-verifiable (already true; this formalizes it);
- **one DNA CID fuses** code + graph + rules + lexicon (was four linked CIDs);
- **tamper-evidence**: any part change → new DNA CID → a different actor;
- **client/actor-tier code-defined validation** — `integrity.validate()` rejects before
  `kotoba_bridge.push`; the ruleset is content-addressed so it is tamper-evident.

**Gated follow-up (the `40-engine/kotoba` submodule, a separate repo):**
- **engine-tier enforcement** — the kotoba transact path invoking the DNA's `validate` *before
  commit*, so a **peer's** writes are checked too (full Holochain-integrity parity). Today the
  engine is append-only + CACAO; the content-addressed ruleset is the half that makes that
  follow-up trustless.
- **true single-tx atomicity** — execution is still ordered steps; the descriptor gives
  atomicity-of-identity (all steps bind one DNA CID) not one atomic block.

## Pins to kotobase.net

The DNA manifest, the WASM, the rules and the lexicon are ordinary content-addressed blocks —
pinned durably to **kotobase.net** (the canonical remote pin, ADR-2606091500) via the
ipfs-pinner kotobase provider, and retrievable at `https://ipfs.gftd.ai/ipfs/<cid>`.
