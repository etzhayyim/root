# murakumo-netd

Small Go helper for the murakumo Mac mini k3s GPU fleet overlay.

It replaces the Tailscale dependency for this specific LAN-local use case by
managing a full-mesh WireGuard interface:

```text
wg0: 10.77.0.x/24
k3s --node-ip 10.77.0.x --flannel-iface wg0
```

It does not implement NAT traversal, DNS, ACLs, relays, or device approval.

## Build

```bash
go build ./...
```

## Example

```bash
sudo murakumo-netd ensure-key
murakumo-netd inventory-template --out nodes.json

# Fill each node's public_key in nodes.json, then render:
sudo murakumo-netd render \
  --node jacob \
  --inventory nodes.json \
  --out /etc/wireguard/wg0.conf

sudo murakumo-netd apply
murakumo-netd status
murakumo-netd k3s-args --node jacob --inventory nodes.json --server
```
