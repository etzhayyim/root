package etzhayyim.xrpc.dispatch

test_public_read_allowed if {
  data.etzhayyim.xrpc.dispatch.allow with input as {
    "auth": {"method": "public", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": false}
  }
}

test_public_write_denied if {
  not data.etzhayyim.xrpc.dispatch.allow with input as {
    "auth": {"method": "public", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true}
  }
}

test_scoped_write_allowed if {
  data.etzhayyim.xrpc.dispatch.allow with input as {
    "auth": {"method": "oauth", "scopes": ["rpc?lxm=com.atproto.repo.createRecord"]},
    "permission_sets": [],
    "route": {"requiresAuth": true}
  }
}
