package etzhayyim.xrpc.dispatch

default allow := false

internal_service if input.auth.method == "service-jwt"

public_read if {
  not input.route.requiresAuth
  data.etzhayyim.xrpc.dispatch.method_policy.publicRead
}

scope_allowed if {
  some scope in input.auth.scopes
  some allowed in data.etzhayyim.xrpc.dispatch.method_policy.allowedScopes
  glob.match(allowed, [], scope)
}

permission_set_allowed if {
  some permission_set in input.permission_sets
  permission_set in data.etzhayyim.xrpc.dispatch.method_policy.allowedPermissionSets
}

allow if internal_service
allow if public_read
allow if {
  input.auth.method != "public"
  scope_allowed
}
allow if {
  input.auth.method != "public"
  permission_set_allowed
}

reason := "internal-service" if internal_service
reason := "public-read" if {
  not internal_service
  public_read
}
reason := "scope-or-permission-set" if {
  not internal_service
  not public_read
  input.auth.method != "public"
  allow
}
reason := "authentication-required" if {
  not allow
  input.auth.method == "public"
}
reason := "insufficient-scope" if {
  not allow
  input.auth.method != "public"
}

deny_obligations contains "return_401" if {
  not allow
  input.auth.method == "public"
}
deny_obligations contains "return_403" if {
  not allow
  input.auth.method != "public"
}
deny_obligations contains "audit_authz_denied" if not allow

decision := {
  "allow": allow,
  "reason": reason,
  "deny_obligations": deny_obligations,
}
