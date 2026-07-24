package etzhayyim.xrpc.dispatch

test_public_read_allowed if {
  allow with input as {
    "auth": {"method": "public", "scopes": []},
    "permission_sets": [],
    "route": {}
  } with data.etzhayyim.xrpc.dispatch.method_policy as {
    "publicRead": true,
    "requiresAuth": false,
    "allowedScopes": [],
    "allowedPermissionSets": []
  }
}

test_public_write_denied if {
  not allow with input as {
    "auth": {"method": "public", "scopes": []},
    "permission_sets": [],
    "route": {}
  } with data.etzhayyim.xrpc.dispatch.method_policy as {
    "publicRead": true,
    "requiresAuth": true,
    "allowedScopes": [],
    "allowedPermissionSets": []
  }
}

test_scoped_write_allowed if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": ["rpc?lxm=com.atproto.repo.createRecord"]},
    "permission_sets": [],
    "route": {}
  } with data.etzhayyim.xrpc.dispatch.method_policy as {
    "publicRead": true,
    "requiresAuth": true,
    "allowedScopes": ["rpc[?]lxm=com.atproto.repo.createRecord"],
    "allowedPermissionSets": []
  }
}
