# chigiri-legal-comms-guest

Counsel-operated comms **G18 gate** as a kotoba WASM Component — runs INSIDE the
kotoba node (`wasm32-wasip2`, WasmExecutor), not as a Cloudflare Worker.

The guest is the **authorization gate + audit record**, not the transport. It
refuses any legal act lacking a valid `counselActuation` and, on pass, asserts an
`outboundLegalAct` quad into the EAVT graph + publishes an `authorized` event.
Network egress (fax / email / e-filing) happens OUTSIDE the sandboxed guest,
keyed off that event — the guest never performs the act, it only authorizes it.

## G18 (enforced in `evaluate_legal_act`)

Every legal act (court-filing, pleading, formal-notice, demand/representation
letter, appeal) must carry a counselActuation:

1. `counsel_did` present — else refused (no autonomous filing);
2. `counsel_signature_ref` present — the lawyer's OWN credential (the corp holds
   no legal-act signing key, no-server-key ADR-2605231525);
3. `counsel_license_jurisdiction == destination_jurisdiction`.

## Build / deploy

```sh
XDG_CONFIG_HOME=/tmp/xdg-empty cargo component build --release   # ~150 KB
cargo test --release    # native G18 unit tests (4)
python3 scripts/deploy.py   # → invoke.run (wasm-node), operator JWT
```

Live-verified on the local node (2026-05-30):

| input | result |
|---|---|
| court-filing + jpn counsel + own signature | `status=ok assert_count=1` → outboundLegalAct asserted (`authorized`) |
| no actuation | `refused assert_count=0` |
| counsel licensed in wrong jurisdiction | `refused assert_count=0` |
| missing own signature | `refused assert_count=0` |

Host ABI: `kqe.assert-quad`, `kse.publish` (`chigiri/<graph>/legalAct/authorized`),
`auth.current-did`. WIT world `kotoba-node`.

> Supersedes the gate logic of the `50-infra/etzhayyim-legal-comms` Cloudflare
> Worker; egress transport adapters remain the downstream concern.
