package etzhayyim.xrpc.arms_test

import data.etzhayyim.xrpc.arms

# internal service can register firearms when its service-jwt carries the
# registerFirearm scope (issue #1505 — service-jwt is no longer unrestricted)
test_internal_service_register_firearm if {
  arms.allow with input as {
    "auth": {"method": "service-jwt", "scopes": ["rpc?lxm=com.etzhayyim.apps.arms.registerFirearm"], "holderAuthSessionPassed": false},
    "route": {"nsid": "com.etzhayyim.apps.arms.registerFirearm"},
    "permission_sets": ["arms:system"],
    "params": {}
  }
}

# issue #1505: a leaked service-jwt WITHOUT the matching scope MUST be denied
# (this is the regression the fix is meant to prevent)
test_internal_service_wrong_scope_denied if {
  not arms.allow with input as {
    "auth": {"method": "service-jwt", "scopes": ["rpc?lxm=com.etzhayyim.apps.arms.getAuditLog"], "holderAuthSessionPassed": false},
    "route": {"nsid": "com.etzhayyim.apps.arms.registerFirearm"},
    "permission_sets": ["arms:system"],
    "params": {}
  }
}

# issue #1505: a service-jwt with no scopes at all MUST be denied
test_internal_service_no_scope_denied if {
  not arms.allow with input as {
    "auth": {"method": "service-jwt", "scopes": [], "holderAuthSessionPassed": false},
    "route": {"nsid": "com.etzhayyim.apps.arms.getAuditLog"},
    "permission_sets": ["arms:authority"],
    "params": {}
  }
}

# public can request auth challenge
test_public_authenticate_holder if {
  arms.allow with input as {
    "auth": {"method": "public", "scopes": []},
    "route": {"nsid": "com.etzhayyim.apps.arms.authenticateHolder"},
    "permission_sets": [],
    "params": {}
  }
}

# holder with session can check out
test_holder_checkout_with_session if {
  arms.allow with input as {
    "auth": {"method": "did-session", "scopes": ["rpc?lxm=com.etzhayyim.apps.arms.checkOutFirearm"], "holderAuthSessionPassed": true},
    "route": {"nsid": "com.etzhayyim.apps.arms.checkOutFirearm"},
    "permission_sets": ["arms:holder"],
    "params": {}
  }
}

# holder WITHOUT session cannot check out
test_holder_checkout_without_session if {
  not arms.allow with input as {
    "auth": {"method": "did-session", "scopes": ["rpc?lxm=com.etzhayyim.apps.arms.checkOutFirearm"], "holderAuthSessionPassed": false},
    "route": {"nsid": "com.etzhayyim.apps.arms.checkOutFirearm"},
    "permission_sets": ["arms:holder"],
    "params": {}
  }
}

# audit log requires authority or law-enforcement
test_audit_log_authority_allowed if {
  arms.allow with input as {
    "auth": {"method": "did-session", "scopes": ["rpc?lxm=com.etzhayyim.apps.arms.getAuditLog"]},
    "route": {"nsid": "com.etzhayyim.apps.arms.getAuditLog"},
    "permission_sets": ["arms:authority"],
    "params": {}
  }
}

# civilian holder cannot access audit log
test_audit_log_civilian_denied if {
  not arms.allow with input as {
    "auth": {"method": "did-session", "scopes": ["rpc?lxm=*"]},
    "route": {"nsid": "com.etzhayyim.apps.arms.getAuditLog"},
    "permission_sets": ["arms:holder"],
    "params": {}
  }
}

# export to restricted jurisdiction blocks transfer
test_transfer_custody_restricted_jurisdiction_denied if {
  not arms.allow with input as {
    "auth": {"method": "did-session", "scopes": ["rpc?lxm=com.etzhayyim.apps.arms.transferCustody"], "holderAuthSessionPassed": true},
    "route": {"nsid": "com.etzhayyim.apps.arms.transferCustody"},
    "permission_sets": ["arms:authority"],
    "params": {"destinationJurisdiction": "KP"}
  }
}

# transfer to allowed jurisdiction passes
test_transfer_custody_allowed_jurisdiction if {
  arms.allow with input as {
    "auth": {"method": "service-jwt", "scopes": ["rpc?lxm=com.etzhayyim.apps.arms.transferCustody"], "holderAuthSessionPassed": true},
    "route": {"nsid": "com.etzhayyim.apps.arms.transferCustody"},
    "permission_sets": ["arms:authority"],
    "params": {"destinationJurisdiction": "JP"}
  }
}

# unauthenticated getFirearm returns 401 obligation
test_getfirearm_unauthenticated_obligation if {
  "return_401" in arms.deny_obligations with input as {
    "auth": {"method": "public", "scopes": []},
    "route": {"nsid": "com.etzhayyim.apps.arms.getFirearm"},
    "permission_sets": [],
    "params": {}
  }
}

# export control violation returns 451 obligation
test_export_control_obligation if {
  "return_451" in arms.deny_obligations with input as {
    "auth": {"method": "service-jwt", "scopes": ["rpc?lxm=*"], "holderAuthSessionPassed": true},
    "route": {"nsid": "com.etzhayyim.apps.arms.transferCustody"},
    "permission_sets": ["arms:authority"],
    "params": {"destinationJurisdiction": "IR"}
  }
}

# issue #1504: omitting destinationJurisdiction MUST NOT bypass export control
# on transferCustody (previously evaluated as undefined → export_restricted=false)
test_transfer_custody_omitted_jurisdiction_denied if {
  not arms.allow with input as {
    "auth": {"method": "did-session", "scopes": ["rpc?lxm=com.etzhayyim.apps.arms.transferCustody"], "holderAuthSessionPassed": true},
    "route": {"nsid": "com.etzhayyim.apps.arms.transferCustody"},
    "permission_sets": ["arms:authority"],
    "params": {}
  }
}

# issue #1504: omitted jurisdiction on transferCustody returns 451 obligation
test_transfer_custody_omitted_jurisdiction_451 if {
  "return_451" in arms.deny_obligations with input as {
    "auth": {"method": "did-session", "scopes": ["rpc?lxm=com.etzhayyim.apps.arms.transferCustody"], "holderAuthSessionPassed": true},
    "route": {"nsid": "com.etzhayyim.apps.arms.transferCustody"},
    "permission_sets": ["arms:authority"],
    "params": {}
  }
}

# issue #1504: omitting destinationJurisdiction MUST NOT bypass export control
# on reportIncident either
# NOTE: This test is now REMOVED per issue #1515 — reportIncident is NOT
# export-restricted and should be allowed regardless of destinationJurisdiction.
# The test below previously asserted denial; it is replaced by positive tests.

# issue #1515: reportIncident is allowed even without destinationJurisdiction
test_report_incident_omitted_jurisdiction_allowed if {
  arms.allow with input as {
    "auth": {"method": "did-session", "scopes": ["rpc?lxm=com.etzhayyim.apps.arms.reportIncident"], "holderAuthSessionPassed": true},
    "route": {"nsid": "com.etzhayyim.apps.arms.reportIncident"},
    "permission_sets": ["arms:authority"],
    "params": {}
  }
}

# issue #1515: reportIncident is allowed even to restricted jurisdictions (KP, IR)
test_report_incident_restricted_jurisdiction_allowed if {
  arms.allow with input as {
    "auth": {"method": "did-session", "scopes": ["rpc?lxm=com.etzhayyim.apps.arms.reportIncident"], "holderAuthSessionPassed": true},
    "route": {"nsid": "com.etzhayyim.apps.arms.reportIncident"},
    "permission_sets": ["arms:authority"],
    "params": {"destinationJurisdiction": "KP"}
  }
}

# issue #1515: reportIncident is allowed even to restricted jurisdictions (IR)
test_report_incident_iran_jurisdiction_allowed if {
  arms.allow with input as {
    "auth": {"method": "did-session", "scopes": ["rpc?lxm=com.etzhayyim.apps.arms.reportIncident"], "holderAuthSessionPassed": true},
    "route": {"nsid": "com.etzhayyim.apps.arms.reportIncident"},
    "permission_sets": ["arms:authority"],
    "params": {"destinationJurisdiction": "IR"}
  }
}

# issue #1504: an empty params object (not just a missing key) is also denied,
# even for an otherwise-scoped internal service (issue #1505 scope gate + #1504
# jurisdiction gate compose: both must pass for allow)
test_transfer_custody_empty_params_denied if {
  not arms.allow with input as {
    "auth": {"method": "service-jwt", "scopes": ["rpc?lxm=com.etzhayyim.apps.arms.transferCustody"], "holderAuthSessionPassed": true},
    "route": {"nsid": "com.etzhayyim.apps.arms.transferCustody"},
    "permission_sets": ["arms:authority"],
    "params": {}
  }
}
