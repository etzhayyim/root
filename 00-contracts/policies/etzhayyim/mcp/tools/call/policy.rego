package etzhayyim.mcp.tools.call

default allow := false

internal_service if input.auth.method == "service-jwt"

# Tool classification: read_only vs write
# input.tool can be a string or array of strings
tool_name := input.tool if is_string(input.tool)
tool_name := input.tool[0] if {
  is_array(input.tool)
  count(input.tool) > 0
}

tool_is_read_only if {
  tool_name
  tool_name in data.method_policy.tools.read_only
}

tool_is_write if {
  tool_name
  tool_name in data.method_policy.tools.write
}

# Default to write (more restrictive) if tool not classified or not provided
tool_classification := "read_only" if tool_is_read_only
tool_classification := "write" if not tool_is_read_only

scope_allowed if {
  some scope in input.auth.scopes
  some allowed in data.method_policy.allowedScopes
  glob.match(allowed, [], scope)
}

permission_set_allowed if {
  some permission_set in input.permission_sets
  permission_set in data.method_policy.allowedPermissionSets
}

# Read-only tools: only require authentication (not public)
allow if internal_service
allow if {
  tool_classification == "read_only"
  input.auth.method != "public"
}
# Write tools: require scope or permission set
allow if {
  tool_classification == "write"
  input.auth.method != "public"
  scope_allowed
}
allow if {
  tool_classification == "write"
  input.auth.method != "public"
  permission_set_allowed
}

reason := "internal-service" if internal_service
reason := "read-only-tool-authenticated" if {
  tool_classification == "read_only"
  input.auth.method != "public"
  allow
}
reason := "write-tool-scope-or-permission" if {
  tool_classification == "write"
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
