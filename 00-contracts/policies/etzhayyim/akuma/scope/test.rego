package etzhayyim.akuma.scope

base_scope := {
  "status": "active",
  "targetKind": "ip",
  "targets": ["203.0.113.10", "198.51.100.0/24"],
  "excludedTargets": ["198.51.100.7"],
  "allowedPorts": [80, 443, 8080],
  "allowedPaths": ["/"],
  "intrusivenessTier": "safe-active",
  "validFromMs": 1000,
  "validUntilMs": 9999,
  "rateLimitRps": 5,
}

test_passive_dns_allowed if {
  allow with input as {
    "scope": base_scope,
    "probe": {"tool": "dns", "target": "203.0.113.10", "port": 0, "intrusiveness": "passive"},
    "rate": {"currentRps": 0},
    "nowMs": 5000,
  }
}

test_safe_active_http_head_allowed if {
  allow with input as {
    "scope": base_scope,
    "probe": {"tool": "http-head", "target": "203.0.113.10", "port": 443, "intrusiveness": "safe-active"},
    "rate": {"currentRps": 0},
    "nowMs": 5000,
  }
}

test_intrusive_nuclei_denied_when_scope_safe_active if {
  not allow with input as {
    "scope": base_scope,
    "probe": {"tool": "nuclei", "target": "203.0.113.10", "port": 443, "intrusiveness": "intrusive"},
    "rate": {"currentRps": 0},
    "nowMs": 5000,
  }
}

test_target_outside_scope_denied if {
  not allow with input as {
    "scope": base_scope,
    "probe": {"tool": "dns", "target": "192.0.2.1", "port": 0, "intrusiveness": "passive"},
    "rate": {"currentRps": 0},
    "nowMs": 5000,
  }
}

test_excluded_target_denied if {
  not allow with input as {
    "scope": object.union(base_scope, {"targetKind": "cidr"}),
    "probe": {"tool": "dns", "target": "198.51.100.7", "port": 0, "intrusiveness": "passive"},
    "rate": {"currentRps": 0},
    "nowMs": 5000,
  }
}

test_cidr_member_allowed if {
  allow with input as {
    "scope": object.union(base_scope, {"targetKind": "cidr"}),
    "probe": {"tool": "dns", "target": "198.51.100.42", "port": 0, "intrusiveness": "passive"},
    "rate": {"currentRps": 0},
    "nowMs": 5000,
  }
}

test_outside_window_denied if {
  not allow with input as {
    "scope": base_scope,
    "probe": {"tool": "dns", "target": "203.0.113.10", "port": 0, "intrusiveness": "passive"},
    "rate": {"currentRps": 0},
    "nowMs": 99999,
  }
}

test_revoked_scope_denied if {
  not allow with input as {
    "scope": object.union(base_scope, {"status": "revoked"}),
    "probe": {"tool": "dns", "target": "203.0.113.10", "port": 0, "intrusiveness": "passive"},
    "rate": {"currentRps": 0},
    "nowMs": 5000,
  }
}

test_port_not_allowed_denied if {
  not allow with input as {
    "scope": base_scope,
    "probe": {"tool": "http-head", "target": "203.0.113.10", "port": 22, "intrusiveness": "safe-active"},
    "rate": {"currentRps": 0},
    "nowMs": 5000,
  }
}

test_rate_limit_exceeded_denied if {
  not allow with input as {
    "scope": base_scope,
    "probe": {"tool": "dns", "target": "203.0.113.10", "port": 0, "intrusiveness": "passive"},
    "rate": {"currentRps": 5},
    "nowMs": 5000,
  }
}

test_unauthorized_target_triggers_seed_prune if {
  ob := deny_obligations with input as {
    "scope": base_scope,
    "probe": {"tool": "dns", "target": "192.0.2.1", "port": 0, "intrusiveness": "passive"},
    "rate": {"currentRps": 0},
    "nowMs": 5000,
  }
  "prune_actor_seed_tier" in ob
}

test_unregistered_tool_returns_correct_reason if {
  d := decision with input as {
    "scope": base_scope,
    "probe": {"tool": "metasploit", "target": "203.0.113.10", "port": 443, "intrusiveness": "safe-active"},
    "rate": {"currentRps": 0},
    "nowMs": 5000,
  }
  d.reason == "tool-not-registered"
}

test_unregistered_tool_not_misleading_reason if {
  d := decision with input as {
    "scope": base_scope,
    "probe": {"tool": "metasploit", "target": "203.0.113.10", "port": 443, "intrusiveness": "safe-active"},
    "rate": {"currentRps": 0},
    "nowMs": 5000,
  }
  d.reason != "tool-exceeds-probe-tier"
}
