---
id: 2605211910-murakumo-fleet-lan-ip-rebaseline
title: Murakumo Mac-Mini Fleet LAN IP Rebaseline (Ethernet Side)
status: active
doc_type: adr
topic: murakumo-fleet-lan
authoritative: true
last_verified: 2026-05-21
priority: 4.5
axis: infrastructure
weight: 0.40
priority_note: "operational SSoT for cell-runner LAN connectivity within etzhayyim scope"
authoritative_for:
  - 50-infra/murakumo/fleet.toml
related:
  - "ADR-2605182312 (Local Bring-up of Artificial Organism on Murakumo Fleet)"
  - "ADR-2605191346 (etzhayyim Vultr-Free Murakumo Control Plane)"
  - "ADR-2605192415 (etzhayyim Religious-Corp Daemon Architecture)"
  - "ADR-2605202345 (evo-x2 GPU Pod Fleet Integration)"
  - "vendor: ADR-2605111400 (Murakumo Fleet LAN — Dual-Router + dnsmasq SSoT)"
depends_on: []
supersedes: []
superseded_by: []
---

# ADR-2605211910: Murakumo Mac-Mini Fleet LAN IP Rebaseline (Ethernet Side)

**Status**: active
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki

## Context

`50-infra/murakumo/fleet.toml` records 10 Mac-mini cell-runner nodes
(naphtali / simeon / judah / zebulun / levi / joseph / issachar / dan /
benjamin / asher) by `name` + `hostname` only. Per the vendor-side
ADR-2605111400 (Murakumo fleet LAN — dual-router + dnsmasq SSoT), the
fleet was migrated from a WiFi-side broadcom router (192.168.1.0/24) to
the NTT HGW Ethernet side of the same subnet so the two L2 segments
unify. The migration changed LAN IP assignments.

Verification on 2026-05-21 from jacob (192.168.1.9, `en0
100baseTX <full-duplex>`):

- mDNS `<name>nomac-mini.local` resolved 8 of 10 tribes; benjamin and
  asher were silent on mDNS, which the pre-existing
  `status = "pending_wol_2026_05_18"` flag in `fleet.toml` had
  attributed to power state. Cross-checking the jacob dnsmasq SSoT
  (`/opt/homebrew/etc/dnsmasq.d/murakumo-fleet.conf`) showed both
  nodes are actually wired and responsive on `:11434` and `:8000`;
  only their mDNS responder is silent. The WoL flag was therefore
  stale, not a real outage.
- ARP shows each resolved IP on `en0 ifscope [ethernet]` with an Apple
  OUI (`1c:f6:4c:*`) and sub-millisecond ICMP RTT, confirming each node
  is wired into the same L2 Ethernet segment as jacob.
- Service probe: LangGraph (`:8000`) and Ollama (`:11434`) both
  return 200 on all 10 tribes after fixing naphtali's Ollama bind
  (see Consequences); LiteLLM (`:4000`) responds only on judah, as
  designed.

The Ethernet-side IPs (`.11–.19` with `.14` unused) do not match the
WiFi-side IPs (`.49 / .51 / .52 / .54 / .59 / .60 / .61 / .64 / .65 /
.67`) still recorded in:

- vendor repo project doc
  `60-apps/etzhayyim-project-murakumo/CLAUDE.md` §Fleet Topology table
- vendor repo ansible inventory
  `60-apps/etzhayyim-project-murakumo/ansible/inventory/hosts.yml`
- vendor-rendered local config `~/litellm.yaml` on jacob
  (LiteLLM proxy backend list)

This drift means LiteLLM's `simple-shuffle` router currently has 11
unreachable LAN backends out of 12; only the `127.0.0.1` entry hits a
live Ollama. Cell-runners on the live tribes still operate via mDNS, so
the runtime impact is concentrated on LiteLLM-routed inference.

## Decision

1. **`50-infra/murakumo/fleet.toml` is the etzhayyim-scope SSoT for the
   `(name, hostname, ip_lan)` triple of every Mac-mini cell-runner.**
   Each `[[nodes]]` block now carries an explicit `ip_lan` field
   alongside `hostname`. Benjamin and asher use a commented `ip_lan`
   placeholder until WoL recovery confirms their DHCP-reserved
   addresses.

2. **Recorded mapping (verified 2026-05-21):**

   | Node | hostname | `ip_lan` | Notes |
   |---|---|---|---|
   | naphtali | naphtalinomac-mini.local | `192.168.1.18` | |
   | simeon | simeonnomac-mini.local | `192.168.1.19` | |
   | judah | judahnomac-mini.local | `192.168.1.17` | also hosts LiteLLM gateway `:4000` |
   | zebulun | zebulunnomac-mini.local | `192.168.1.11` | |
   | levi | levinomac-mini.local | `192.168.1.16` | |
   | joseph | josephnomac-mini.local | `192.168.1.15` | |
   | issachar | issacharnomac-mini.local | `192.168.1.12` | |
   | dan | dannomac-mini.local | `192.168.1.13` | |
   | benjamin | benjaminomac-mini.local | `192.168.1.14` | mDNS silent; L2 + Ollama + LangGraph active. `pending_wol_2026_05_18` flag cleared. |
   | asher | ashernomac-mini.local | `192.168.1.21` | mDNS silent; L2 + Ollama + LangGraph active. `pending_wol_2026_05_18` flag cleared. |

3. **`~/litellm.yaml` on jacob is rewritten in place to point at the
   Ethernet IPs above** (127.0.0.1 + 7 reachable tribes; naphtali
   excluded until Ollama is restored; benjamin/asher excluded until
   WoL). The file's header notes that the vendor-side ansible role
   (`60-apps/etzhayyim-project-murakumo/ansible/roles/litellm/templates/litellm.yaml.j2`)
   still emits WiFi-side IPs, so this hand-edit is treated as a
   one-shot drift fix and will be overwritten on the next ansible run
   until the vendor inventory is reconciled.

4. **Vendor-repo reconciliation is out of scope for this ADR.** The
   vendor docs and ansible inventory live under
   `github.com/etzhayyim/etzhayyim-root` and are governed by that
   repo's own change process; this ADR records that the Ethernet
   rebaseline supersedes their values within the etzhayyim scope and
   that reconciliation is an open item.

## Consequences

- `fleet.toml` now carries the LAN IP ground truth used by
  `kotodama-cell-runner` under `com.etzhayyim.kotodama-cell-runner.plist`
  and by any future on-host tooling that needs deterministic
  node-to-IP mapping without mDNS round-trips.
- LiteLLM `simple-shuffle` regains 7 live LAN backends on jacob,
  restoring fleet-wide inference fan-out for `gemma3:1b`,
  `gemma4:e4b`, and `qwen3.5:9b` until the next ansible run.
- Naphtali initially had Ollama bound to `127.0.0.1:11434` because
  its `@reboot` crontab line lacked `OLLAMA_HOST=0.0.0.0:11434`; the
  crontab and the running process were updated on 2026-05-21 to add
  the env var, restoring LAN reachability across reboots. All 8
  active tribes now respond on `:11434`.
- Benjamin (`192.168.1.14`) and asher (`192.168.1.21`) are confirmed
  online (Ollama + LangGraph 200) despite mDNS silence; the
  pre-existing `status = "pending_wol_2026_05_18"` flag has been
  removed from both `[[nodes]]` entries. Their mDNS responder
  configuration is a separate (low-priority) follow-up.
- Cross-repo cross-check: the jacob-side dnsmasq SSoT
  (`/opt/homebrew/etc/dnsmasq.d/murakumo-fleet.conf` per vendor
  ADR-2605111400) matches `fleet.toml` for all 10 tribes. The
  dnsmasq file additionally registers an auxiliary `main.murakumo.lan`
  (`192.168.1.66`, WiFi-only, role TBD) which is intentionally not in
  the etzhayyim fleet.toml.
- Cross-repo drift remains between this file and the vendor repo's
  inventory; resolving it requires either updating the vendor ansible
  inventory to the Ethernet rebaseline or refactoring the litellm
  role to read `fleet.toml` directly. Decision deferred.

## Alternatives Considered

1. **Continue relying on `*.local` mDNS only, no IP in `fleet.toml`.**
   Rejected because mDNS lookups race with reboots, are cache-sensitive,
   and cannot be consumed idempotently by ansible / launchd / TOML-only
   consumers without an additional resolver hop. Recording the IP in
   version control makes the SSoT auditable.

2. **Store IPs only in the vendor repo ansible inventory and have
   etzhayyim cell-runners read it through a cross-repo include.**
   Rejected because etzhayyim/root is intentionally substrate-bounded
   (ADR-2605172000 + 2605172100): cell-runtime operational data should
   live inside the religious-corp repo, not be pulled from a vendor
   inventory at runtime. Vendor inventory and `fleet.toml` are
   permitted to diverge as long as etzhayyim cell-runners only read
   `fleet.toml`.

3. **Defer to dnsmasq on jacob as the runtime SSoT** (per vendor
   ADR-2605111400's `.murakumo.lan` zone). Rejected as the *sole*
   record because dnsmasq config is not in etzhayyim/root and would
   create a runtime dependency on a vendor-side service. dnsmasq
   remains useful as a stub resolver in addition to, not in place of,
   `fleet.toml`'s `ip_lan`.

## References

- `50-infra/murakumo/fleet.toml` (this repo, updated by this ADR)
- ADR-2605182312 (Local Bring-up of Artificial Organism on Murakumo Fleet)
- ADR-2605191346 (etzhayyim Vultr-Free Murakumo Control Plane)
- ADR-2605192415 (etzhayyim Religious-Corp Daemon Architecture)
- ADR-2605202345 (evo-x2 GPU Pod Fleet Integration)
- Vendor: ADR-2605111400 (Murakumo Fleet LAN — Dual-Router + dnsmasq SSoT)
- Verification artifacts (transient, not committed):
  `dscacheutil -q host -a name <tribe>nomac-mini.local`,
  `arp -an | grep en0`, `ping -c1 -W500 <ip>`,
  `curl http://<ip>:{8000,11434,4000}/...`.
