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
