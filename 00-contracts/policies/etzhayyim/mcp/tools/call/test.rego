package etzhayyim.mcp.tools.call

# Public access denied for all tools
test_public_denied_read_only if {
  not allow with input as {
    "auth": {"method": "public", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "list"
  }
}

test_public_denied_write if {
  not allow with input as {
    "auth": {"method": "public", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "create"
  }
}

# Read-only tools: only require authentication (not public)
test_read_only_allowed_with_auth if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "list"
  }
}

test_read_only_allowed_get if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "get"
  }
}

test_read_only_allowed_search if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "search"
  }
}

test_read_only_allowed_query if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "query"
  }
}

test_read_only_allowed_read if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "read"
  }
}

test_read_only_allowed_describe if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "describe"
  }
}

test_read_only_allowed_find if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "find"
  }
}

test_read_only_allowed_lookup if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "lookup"
  }
}

test_read_only_allowed_info if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "info"
  }
}

test_read_only_allowed_status if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "status"
  }
}

test_read_only_allowed_health if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "health"
  }
}

test_read_only_allowed_version if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "version"
  }
}

test_read_only_allowed_schema if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "schema"
  }
}

test_read_only_allowed_manifest if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "manifest"
  }
}

test_read_only_allowed_capabilities if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "capabilities"
  }
}

test_read_only_allowed_list_tools if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "list_tools"
  }
}

test_read_only_allowed_list_resources if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "list_resources"
  }
}

test_read_only_allowed_get_resource if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "get_resource"
  }
}

test_read_only_allowed_read_resource if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "read_resource"
  }
}

# Write tools: require scope or permission set
test_write_allowed_with_scope if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": ["rpc?lxm=com.etzhayyim.mcp.*"]},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "create"
  }
}

test_write_allowed_with_permission_set if {
  allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": ["com.etzhayyim.actor.authActorManagement"],
    "route": {"requiresAuth": true},
    "tool": "create"
  }
}

test_write_denied_without_scope_or_permission if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "create"
  }
}

test_write_denied_update if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "update"
  }
}

test_write_denied_delete if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "delete"
  }
}

test_write_denied_invoke if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "invoke"
  }
}

test_write_denied_execute if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "execute"
  }
}

test_write_denied_call if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "call"
  }
}

test_write_denied_write if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "write"
  }
}

test_write_denied_patch if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "patch"
  }
}

test_write_denied_replace if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "replace"
  }
}

test_write_denied_remove if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "remove"
  }
}

test_write_denied_destroy if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "destroy"
  }
}

test_write_denied_submit if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "submit"
  }
}

test_write_denied_publish if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "publish"
  }
}

test_write_denied_send if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "send"
  }
}

test_write_denied_trigger if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "trigger"
  }
}

test_write_denied_run if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "run"
  }
}

test_write_denied_start if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "start"
  }
}

test_write_denied_stop if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "stop"
  }
}

test_write_denied_restart if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "restart"
  }
}

test_write_denied_deploy if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "deploy"
  }
}

test_write_denied_rollback if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "rollback"
  }
}

test_write_denied_approve if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "approve"
  }
}

test_write_denied_reject if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "reject"
  }
}

test_write_denied_confirm if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "confirm"
  }
}

test_write_denied_cancel if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "cancel"
  }
}

test_write_denied_execute_tool if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "execute_tool"
  }
}

test_write_denied_write_resource if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "write_resource"
  }
}

# Unclassified tools default to write behavior (more restrictive)
test_unclassified_defaults_to_write if {
  not allow with input as {
    "auth": {"method": "oauth", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "unknown_tool"
  }
}

# Internal service always allowed
test_internal_service_allowed_read_only if {
  allow with input as {
    "auth": {"method": "service-jwt", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "list"
  }
}

test_internal_service_allowed_write if {
  allow with input as {
    "auth": {"method": "service-jwt", "scopes": []},
    "permission_sets": [],
    "route": {"requiresAuth": true},
    "tool": "create"
  }
}

# Existing tests for scope/permission set allowed
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
