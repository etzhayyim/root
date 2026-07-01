package etzhayyim.xrpc.arms

import rego.v1

default allow := false

nsid := input.route.nsid

method_policy := data.method_policy[nsid] if {
  nsid in object.keys(data.method_policy)
}

internal_service if input.auth.method == "service-jwt"

public_read if {
  method_policy.publicRead == true
}

scope_allowed if {
  some scope in input.auth.scopes
  some allowed in method_policy.allowedScopes
  glob.match(allowed, [], scope)
}

permission_set_allowed if {
  some permission_set in input.permission_sets
  permission_set in method_policy.allowedPermissionSets
}

# holder_auth_session_valid: the calling DID has a passed auth session recorded
# Input must carry input.auth.holderAuthSessionPassed == true (set by Worker middleware)
holder_auth_session_valid if {
  input.auth.holderAuthSessionPassed == true
}

# For methods requiring a holder auth session, deny if it's absent
requires_holder_session if {
  method_policy.requiresHolderAuthSession == true
}

# Export control gate: block custody transfers to ATT/Wassenaar restricted
# jurisdictions. destinationJurisdiction is MANDATORY for transferCustody
# and reportIncident — omitting it is treated as restricted (issue #1504:
# otherwise OPA evaluates the missing param as undefined, export_restricted
# stays false, and the transfer is authorised to a potentially restricted
# destination).
export_restricted if {
  nsid in {"com.etzhayyim.apps.arms.transferCustody", "com.etzhayyim.apps.arms.reportIncident"}
  not is_string(object.get(input.params, "destinationJurisdiction", null))
}
export_restricted if {
  nsid in {"com.etzhayyim.apps.arms.transferCustody", "com.etzhayyim.apps.arms.reportIncident"}
  object.get(input.params, "destinationJurisdiction", null) in data.export_restricted_jurisdictions
}

allow if {
  internal_service
  not export_restricted
}

allow if {
  not method_policy.requiresAuth
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

reason := "internal-service" if internal_service
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
