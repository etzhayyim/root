package etzhayyim.mcp.tools.call

test_public_denied if {
  not allow with input as {
    "auth": {"method": "public", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true}
  }
}

test_scope_allowed if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": ["rpc?lxm=com.etzhayyim.mcp.*"]},
    "permission_sets": [],
    "route": {"requiresAuth": true}
  }
}

test_permission_set_allowed if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": ["com.etzhayyim.actor.authActorManagement"],
    "route": {"requiresAuth": true}
  }
}
