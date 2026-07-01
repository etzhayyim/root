package etzhayyim.xrpc.arms

import rego.v1

default allow := false

nsid := input.route.nsid

method_policy_item := data.etzhayyim.xrpc.arms.method_policy[nsid] if {
  nsid in object.keys(data.etzhayyim.xrpc.arms.method_policy)
}

internal_service if input.auth.method == "service-jwt"

public_read if {
  method_policy_item.publicRead == true
}

scope_allowed if {
  some scope in input.auth.scopes
  some allowed in method_policy_item.allowedScopes
  glob.match(allowed, [], scope)
}

permission_set_allowed if {
  some permission_set in input.permission_sets
  permission_set in method_policy_item.allowedPermissionSets
}

# holder_auth_session_valid: the calling DID has a passed auth session recorded
# Input must carry input.auth.holderAuthSessionPassed == true (set by Worker middleware)
holder_auth_session_valid if {
  input.auth.holderAuthSessionPassed == true
}

# For methods requiring a holder auth session, deny if it's absent
requires_holder_session if {
  method_policy_item.requiresHolderAuthSession == true
}

# Export control gate: block custody transfers to ATT/Wassenaar restricted jurisdictions
export_restricted if {
  nsid in {"com.etzhayyim.apps.arms.transferCustody", "com.etzhayyim.apps.arms.reportIncident"}
  some jur in data.etzhayyim.xrpc.arms.export_restricted_jurisdictions
  input.params.destinationJurisdiction == jur
}

# Internal services authenticate with a service-jwt. They are NOT exempt from
# authorization: the token MUST carry a scope matching the method's
# allowedScopes (issue #1505 — a leaked service-jwt must not grant unrestricted
# access to registerFirearm / issuePermit / transferCustody / getAuditLog / …).
# Services act on their own authority (not as a holder), so the holder-auth-
# session gate (requiresHolderAuthSession) does not apply to them.
allow if {
  internal_service
  scope_allowed
  not export_restricted
}

allow if {
  not method_policy_item.requiresAuth
  public_read
  not export_restricted
}

allow if {
  not internal_service
  not public_read
  input.auth.method != "public"
  scope_allowed
  not requires_holder_session
  not export_restricted
}

allow if {
  not internal_service
  not public_read
  input.auth.method != "public"
  permission_set_allowed
  not requires_holder_session
  not export_restricted
}

allow if {
  not internal_service
  not public_read
  input.auth.method != "public"
  scope_allowed
  requires_holder_session
  holder_auth_session_valid
  not export_restricted
}

allow if {
  not internal_service
  not public_read
  input.auth.method != "public"
  permission_set_allowed
  requires_holder_session
  holder_auth_session_valid
  not export_restricted
}

reason := "internal-service" if {
  internal_service
  allow
}
reason := "public-read" if {
  not internal_service
  public_read
}
reason := "scope-allowed" if {
  not internal_service
  not public_read
  input.auth.method != "public"
  scope_allowed
  not requires_holder_session
}
reason := "permission-set-allowed" if {
  not internal_service
  not public_read
  input.auth.method != "public"
  not scope_allowed
  permission_set_allowed
  not requires_holder_session
}
reason := "holder-auth-session-required" if {
  not allow
  requires_holder_session
  not holder_auth_session_valid
  input.auth.method != "public"
}
reason := "export-control-blocked" if {
  not allow
  export_restricted
}
reason := "authentication-required" if {
  not allow
  input.auth.method == "public"
  not export_restricted
}
reason := "insufficient-scope" if {
  not allow
  input.auth.method != "public"
  not export_restricted
  not requires_holder_session
}

deny_obligations contains "return_401" if {
  not allow
  input.auth.method == "public"
}
deny_obligations contains "return_403" if {
  not allow
  input.auth.method != "public"
}
deny_obligations contains "return_451" if {
  not allow
  export_restricted
}
deny_obligations contains "audit_authz_denied" if not allow
deny_obligations contains "audit_export_control" if {
  export_restricted
}

decision := {
  "allow": allow,
  "reason": reason,
  "deny_obligations": deny_obligations,
}
