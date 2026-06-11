# murakumo (`40-engine/cluster/murakumo`)

Murakumo cluster node/worker CLI.

This package is the new home for Murakumo runtime code under `40-engine/cluster`.
It includes `tailmesh`, a self-hosted tailnet implementation (Tailscale alternative)
based on:

- X25519 key exchange
- XChaCha20-Poly1305 authenticated encryption
- Murakumo control-plane peer registration/list API

## Build

```bash
cargo check --manifest-path 40-engine/cluster/murakumo/Cargo.toml
```

## Tailmesh examples

```bash
# 1) Generate identity
cargo run --manifest-path 40-engine/cluster/murakumo/Cargo.toml -- \
  murakumo-mesh keygen --node-id node-a

# 2) Register peer in control plane
cargo run --manifest-path 40-engine/cluster/murakumo/Cargo.toml -- \
  murakumo-mesh register --node-id node-a --public-key <PUBKEY> --endpoint https://node-a.example

# 3) List peers
cargo run --manifest-path 40-engine/cluster/murakumo/Cargo.toml -- \
  murakumo-mesh peers
```
