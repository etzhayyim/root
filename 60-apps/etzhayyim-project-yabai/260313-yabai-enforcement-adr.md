# ADR: YABAI Enforcement Decisions

## Status

Accepted on 2026-03-13.

## Context

`yabai` already scores risky entities in Tonbo/LanceDB REST, but cluster-wide blocking needs a separate enforcement-ready projection. Raw `yabai_risks`, `yabai_evidences`, and `yabai_watchlist_signals` are useful for analysis, not direct policy distribution.

We need one compiled table that can be consumed by:

- HTTP egress controls for suspicious domains
- mailer and adapter-side rejects for risky email addresses or patterns
- telephony/provider-side rejects for risky phone indicators
- IP egress controls for risky addresses or CIDRs

## Decision

Add `yabai_enforcement_decisions` as the enforcement projection table.

Primary fields:

- `decision_id`
- `entity_id`
- `entity_name`
- `entity_type`
- `indicator_type`
- `normalized_value`
- `match_mode`
- `scope`
- `action`
- `score`
- `source_count`
- `reason`
- `categories_json`
- `sources_json`
- `expires_at`
- `updated_at`

Initial compiler inputs:

- `yabai_risks`
- `yabai_evidences`
- `yabai_watchlist_signals`
- `yabai_entities`

Initial scopes:

- `mailer`
- `egress_http`
- `egress_ip`
- `telephony`

Initial action thresholds:

- `SanctionHit` => `deny`
- `score >= 95` => `deny`
- `85 <= score < 95` => `challenge`
- `70 <= score < 85` => `monitor`

## Consequences

- `yabai` remains the source of truth for score and evidence.
- Enforcement consumers read a stable, normalized projection instead of reimplementing risk logic.
- `domain`, `ip`, `email`, and `phone` indicators can be distributed independently.
- `email` and `phone` remain application-layer enforcement concerns, not cluster firewall concerns.

## Rollout

1. Compile and expose `yabai_enforcement_decisions`.
2. Integrate `scope=mailer` and `scope=egress_http` consumers first.
3. Add controller-based projection into ConfigMaps, CRDs, or adapter APIs.
4. Extend to `egress_ip` and telephony adapters after audit logging is in place.
