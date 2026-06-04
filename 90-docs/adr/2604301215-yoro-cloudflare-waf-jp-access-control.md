---
id: adr-2604301215-yoro-cloudflare-waf-jp-access-control
title: "Yoro JP Access Control Lives in Cloudflare WAF"
status: active
doc_type: adr
topic: edge-access-control
authoritative: true
last_verified: 2026-04-30
authoritative_for:
  - yoro-jp-access-control
  - yoro-edge-geo-blocking
  - yoro-cloudflare-waf-rule
related:
  - adr-2604241038-yoro-pds-ideal-topology
  - adr-2604282300
  - adr-2604231828-appview-domain-separation-bsky-etzhayyim-ai
supersedes: []
superseded_by: []
---

# Context

`yoro.etzhayyim.com` is served by the `magatama-yoro` Cloudflare Worker with
Workers Assets. A first implementation put Japan geo blocking inside the
Worker request handler. That caused legitimate operator access to receive
`403 Forbidden` when Cloudflare observed the request over an IPv6 address
rather than the IPv4 address initially allowlisted.

Access control at the application Worker layer is the wrong ownership boundary
for this case:

- Cloudflare already has the authoritative client IP and country signal before
  Worker execution.
- The Worker should remain focused on yoro routing, discovery metadata, asset
  serving, and app shell behavior.
- Geo/IP policy should be visible in Cloudflare security controls and auditable
  without changing application code.

# Decision

Yoro country/IP access control is enforced in Cloudflare WAF custom rules, not
in `60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/src/app.ts`.

Live rule:

| Field | Value |
|---|---|
| Zone | `etzhayyim.com` |
| Zone ID | `63132931facb26812993527da9f85186` |
| Ruleset | `etzhayyim.com yoro access control` |
| Ruleset ID | `67eee63e3ec24916be3ffdb556dec05d` |
| Phase | `http_request_firewall_custom` |
| Rule ID | `e3e04e28ef7944eca3475da894883daf` |
| Action | `block` |
| Enabled | `true` |

Rule expression:

```txt
(http.host eq "yoro.etzhayyim.com"
 and ip.geoip.country eq "JP"
 and not ip.src in {219.104.136.140 240d:f:88c:8100::/64})
```

This blocks Japan-origin requests to `yoro.etzhayyim.com` except the current operator
IPv4 and the operator IPv6 `/64` observed by Cloudflare.

# Consequences

- `yoro.etzhayyim.com` application code must not contain ad hoc JP/IP block logic.
- Operator access remains available from the currently observed IPv4 and IPv6
  prefix.
- Non-operator JP access is blocked before Worker execution.
- Changes to allowlisted IPs must be made in Cloudflare WAF/rulesets and then
  reflected in this ADR and `50-infra/deps.toml`.
- The live ruleset is currently managed through the Cloudflare API. Terraform
  should adopt it in `50-infra/prod/main.tf` before the next broad production
  infrastructure apply, to avoid unmanaged drift.

# Alternatives Considered

## Worker-level block

Rejected. It coupled access policy to application deploys and failed for the
operator when the effective Cloudflare source IP was IPv6.

## Cloudflare Access application

Deferred. Access is stronger but changes the user experience and auth flow.
The current requirement is a geo/IP block for public yoro traffic, not an
identity-gated private app.

# References

- Cloudflare ruleset created 2026-04-30 with `http_request_firewall_custom`.
- Operator verification: `https://www.cloudflare.com/cdn-cgi/trace` reported
  `loc=JP` and `ip=240d:f:88c:8100:7837:7b14:d01d:cb11`.
- Worker-side block removal commit: `857ba4e61dd`.
