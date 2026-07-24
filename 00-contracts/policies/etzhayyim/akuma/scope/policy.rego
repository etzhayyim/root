package etzhayyim.akuma.scope

# Authorize a single com.etzhayyim.apps.akuma.runProbe call against a scope
# contract row. ADR-2605151400.
#
# Inputs:
#   input.scope.status                 string ("draft"|"active"|"revoked")
#   input.scope.targetKind             string ("ip"|"cidr"|"hostname"|"url")
#   input.scope.targets                []string
#   input.scope.excludedTargets        []string
#   input.scope.allowedPorts           []int
#   input.scope.allowedPaths           []string
#   input.scope.intrusivenessTier      string ("passive"|"safe-active"|"intrusive")
#   input.scope.validFromMs            int
#   input.scope.validUntilMs           int
#   input.scope.rateLimitRps           int
#   input.probe.tool                   string
#   input.probe.target                 string
#   input.probe.port                   int (optional, 0 = unset)
#   input.probe.intrusiveness          string
#   input.rate.currentRps              int (rate budget consumed this second)
#   input.nowMs                        int

default allow := false

tier_rank := {"passive": 1, "safe-active": 2, "intrusive": 3}

tool_tier := {
  "dns": 1,
  "whois": 1,
  "tls": 1,
  "http-head": 2,
  "nmap": 3,
  "nuclei": 3,
  "zap": 3,
  "sqlmap": 3,
}

scope_active if input.scope.status == "active"

within_window if {
  input.nowMs >= input.scope.validFromMs
  input.nowMs < input.scope.validUntilMs
}

target_listed if {
  some t in input.scope.targets
  t == input.probe.target
}

target_in_cidr if {
  input.scope.targetKind == "cidr"
  some cidr in input.scope.targets
  net.cidr_contains(cidr, input.probe.target)
}

# Also allow CIDR matching when targetKind == "ip" for backward compatibility
# and convenience (CIDR notation in targets array should work regardless of mode)
target_in_cidr_if_ip_mode if {
  input.scope.targetKind == "ip"
  some cidr in input.scope.targets
  net.cidr_contains(cidr, input.probe.target)
}

target_in_scope if target_listed
target_in_scope if target_in_cidr
target_in_scope if target_in_cidr_if_ip_mode

target_excluded if {
  some t in input.scope.excludedTargets
  t == input.probe.target
}

probe_tier_within_scope if {
  pt := tier_rank[input.probe.intrusiveness]
  st := tier_rank[input.scope.intrusivenessTier]
  pt <= st
}

tool_tier_matches_probe if {
  tt := tool_tier[input.probe.tool]
  pt := tier_rank[input.probe.intrusiveness]
  tt <= pt
}

port_ok if input.probe.port == 0
port_ok if {
  some p in input.scope.allowedPorts
  p == input.probe.port
}

rate_budget_ok if input.rate.currentRps < input.scope.rateLimitRps

allow if {
  scope_active
  within_window
  target_in_scope
  not target_excluded
  probe_tier_within_scope
  tool_tier_matches_probe
  port_ok
  rate_budget_ok
}

reason := "scope-not-active" if not scope_active
reason := "outside-window" if {
  scope_active
  not within_window
}
reason := "target-not-in-scope" if {
  scope_active
  within_window
  not target_in_scope
}
reason := "target-excluded" if {
  scope_active
  within_window
  target_in_scope
  target_excluded
}
reason := "intrusiveness-exceeds-scope" if {
  scope_active
  within_window
  target_in_scope
  not target_excluded
  not probe_tier_within_scope
}
reason := "tool-exceeds-probe-tier" if {
  scope_active
  within_window
  target_in_scope
  not target_excluded
  probe_tier_within_scope
  not tool_tier_matches_probe
}
reason := "port-not-allowed" if {
  scope_active
  within_window
  target_in_scope
  not target_excluded
  probe_tier_within_scope
  tool_tier_matches_probe
  not port_ok
}
reason := "rate-limit-exceeded" if {
  scope_active
  within_window
  target_in_scope
  not target_excluded
  probe_tier_within_scope
  tool_tier_matches_probe
  port_ok
  not rate_budget_ok
}
reason := "allowed" if allow

deny_obligations contains "return_403" if not allow
deny_obligations contains "audit_authz_denied" if not allow

# Unauthorized probe attempts trigger Bonsai seed-tier prune (ADR-2605091800).
deny_obligations contains "prune_actor_seed_tier" if {
  not allow
  reason == "target-not-in-scope"
}
deny_obligations contains "prune_actor_seed_tier" if {
  not allow
  reason == "scope-not-active"
}

allow_obligations contains "record_probe_attempt" if allow
allow_obligations contains "bind_to_finding" if allow

decision := {
  "allow": allow,
  "reason": reason,
  "deny_obligations": deny_obligations,
  "allow_obligations": allow_obligations,
}
