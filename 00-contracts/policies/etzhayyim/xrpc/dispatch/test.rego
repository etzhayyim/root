package etzhayyim.xrpc.dispatch

test_public_read_allowed if {
  data.etzhayyim.xrpc.dispatch.allow with input as {
    "auth": {"method": "public", "scopes": []},
    "permission_sets": [],
    "route": {"nsid": "com.atproto.repo.getRecord"}
  }
}

# Uses the real data bundle: the write NSID can never select the public-read
# policy, even when the caller is unauthenticated.
test_public_write_denied if {
  not data.etzhayyim.xrpc.dispatch.allow with input as {
    "auth": {"method": "public", "scopes": []},
    "permission_sets": [],
    "route": {"nsid": "com.atproto.repo.createRecord"}
  }
}

test_scoped_write_allowed if {
  data.etzhayyim.xrpc.dispatch.allow with input as {
    "auth": {"method": "oauth", "scopes": ["rpc?lxm=com.atproto.repo.createRecord"]},
    "permission_sets": [],
    "route": {"nsid": "com.atproto.repo.createRecord"}
  }
}

test_unknown_route_fails_closed if {
  not data.etzhayyim.xrpc.dispatch.allow with input as {
    "auth": {"method": "public", "scopes": []},
    "permission_sets": [],
    "route": {"nsid": "com.example.unknown"}
  }
}
