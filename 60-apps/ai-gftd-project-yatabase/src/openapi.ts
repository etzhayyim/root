// openapi.ts — machine-readable spec at GET /openapi.json.
//
// OpenAPI 3.1.0. Covers every documented public + authenticated surface.
// Operator-only paths (/_agents/*, /api/leads/*) are deliberately
// excluded — they are admin-internal and not for SDK consumers.
//
// Goals:
//   - Postman / Swagger UI / openapi-typescript can import directly
//   - Cursor / Continue.dev / other LLM-coding tools can call the spec
//     to autogenerate type-safe clients
//   - Operator can `curl yatabase.etzhayyim.com/openapi.json` as a "did the
//     API contract change?" diff source

const SPEC = {
  openapi: "3.1.0",
  info: {
    title: "Yatabase",
    version: "0.1.0",
    summary: "Real-time graph database + S3-style object storage + MCP tool surface.",
    description: [
      "Single-host BaaS combining a Cypher-subset graph DB on RisingWave,",
      "Supabase-shape storage REST + AWS SigV4 compat, an MCP JSON-RPC tool",
      "surface, and AT Protocol XRPC pass-through. One bearer token across",
      "every surface. See https://yatabase.etzhayyim.com/docs for narrative docs.",
    ].join(" "),
    termsOfService: "https://yatabase.etzhayyim.com/terms",
    contact: {
      name: "Yatabase support",
      url: "https://yatabase.etzhayyim.com/team",
      email: "support@etzhayyim.com",
    },
    license: {
      name: "Yatabase Terms of Service",
      url: "https://yatabase.etzhayyim.com/terms",
    },
  },
  servers: [
    { url: "https://yatabase.etzhayyim.com", description: "Production (Cloudflare Workers + RisingWave Vultr LAX)" },
  ],
  externalDocs: {
    description: "Narrative documentation",
    url: "https://yatabase.etzhayyim.com/docs",
  },
  security: [{ bearerAuth: [] }],
  tags: [
    { name: "auth", description: "Signup / upgrade / member management" },
    { name: "graph", description: "Cypher + SPARQL" },
    { name: "storage", description: "Object storage (Supabase REST + AWS SigV4)" },
    { name: "mcp", description: "Model Context Protocol JSON-RPC" },
    { name: "xrpc", description: "AT Protocol XRPC pass-through" },
    { name: "billing", description: "Plan / usage / invoices / Stripe webhook" },
    { name: "privacy", description: "Data rights — export / delete" },
    { name: "observability", description: "Health / meta / audit / outbox" },
  ],
  components: {
    securitySchemes: {
      bearerAuth: {
        type: "http",
        scheme: "bearer",
        bearerFormat: "sk_live_yata_*",
        description:
          "Tenant API key minted via POST /auth/v1/signup. Same shape as `sk_live_*` keys minted via PDS `ai.gftd.auth.createApiKey`. AT Protocol session JWTs (ES256) are also accepted.",
      },
    },
    schemas: {
      Error: {
        type: "object",
        required: ["error"],
        properties: {
          error: { type: "string", examples: ["Unauthorized", "Forbidden", "NotFound", "QuotaExceeded", "PreconditionFailed"] },
          message: { type: "string" },
        },
      },
      SignupRequest: {
        type: "object",
        properties: {
          email: { type: "string", format: "email", description: "Optional. If provided, a welcome email is queued in the outbox." },
          name: { type: "string", maxLength: 128 },
        },
      },
      SignupResponse: {
        type: "object",
        required: ["ok", "apiKey", "keyId", "orgDid", "tenantName"],
        properties: {
          ok: { type: "boolean" },
          apiKey: { type: "string", description: "sk_live_yata_* — shown ONCE. Persist it; we keep only the SHA-256 hash." },
          keyId: { type: "string", examples: ["apikey:abc123..."] },
          orgDid: { type: "string", examples: ["did:web:t-xxxxx-yata-tenant.etzhayyim.com"] },
          tenantName: { type: "string" },
          awsAccessKeyId: { type: "string", description: "For S3 SigV4 access via /s3/{bucket}/{key}" },
          emailStatus: { type: "string", examples: ["sent", "queued-no-recipient", "skipped-no-email"] },
          welcome: { type: "string" },
          next: { type: "string" },
          pricing: { type: "string" },
        },
      },
      CypherRequest: {
        oneOf: [
          {
            type: "object",
            required: ["query"],
            description: "Yatabase quickstart shape — single statement.",
            properties: {
              query: { type: "string", examples: ["MATCH (n:Demo) RETURN n LIMIT 10"] },
              parameters: { type: "object", additionalProperties: true },
            },
          },
          {
            type: "object",
            required: ["statement"],
            description: "Bare statement shape (alias of {query}).",
            properties: {
              statement: { type: "string" },
              parameters: { type: "object", additionalProperties: true },
            },
          },
          {
            type: "object",
            required: ["statements"],
            description: "Neo4j HTTP API shape — multi-statement.",
            properties: {
              statements: {
                type: "array",
                items: {
                  type: "object",
                  required: ["statement"],
                  properties: {
                    statement: { type: "string" },
                    parameters: { type: "object", additionalProperties: true },
                  },
                },
              },
            },
          },
        ],
      },
      CypherResponse: {
        type: "object",
        properties: {
          results: {
            type: "array",
            items: {
              type: "object",
              properties: {
                columns: { type: "array", items: { type: "string" } },
                data: { type: "array", items: { type: "array" } },
                stats: {
                  type: "object",
                  properties: {
                    contains_updates: { type: "boolean" },
                    nodes_created: { type: "integer" },
                    nodes_deleted: { type: "integer" },
                    relationships_created: { type: "integer" },
                    relationships_deleted: { type: "integer" },
                    properties_set: { type: "integer" },
                    labels_added: { type: "integer" },
                  },
                },
              },
            },
          },
          errors: { type: "array", items: { type: "object" } },
        },
      },
      QuotaStatus: {
        type: "object",
        properties: {
          plan: { type: "string", enum: ["free", "starter", "developer", "business", "enterprise"] },
          apiRequestPerDay: { type: "integer", nullable: true },
          apiRequestUsedToday: { type: "integer" },
          apiRequestRemaining: { type: "integer", nullable: true },
          exceeded: { type: "boolean" },
          windowStart: { type: "string", format: "date-time" },
        },
      },
      UsageReport: {
        type: "object",
        properties: {
          orgDid: { type: "string" },
          windowHours: { type: "integer" },
          byMetric: {
            type: "array",
            items: {
              type: "object",
              properties: {
                metric: { type: "string", examples: ["api_request", "yata_query_cu_ms", "storage_gb_hour"] },
                qty: { type: "integer" },
                billedJpy: { type: "number" },
              },
            },
          },
          totalBilledJpy: { type: "number" },
        },
      },
      OutboxEvent: {
        type: "object",
        properties: {
          kind: { type: "string", examples: ["signup-welcome", "plan-upgrade", "member-invite", "quota-warning", "invoice-ready"] },
          subject: { type: "string" },
          recipient: { type: "string" },
          status: { type: "string", enum: ["pending", "queued-no-recipient", "sent", "failed"] },
          createdAt: { type: "string", format: "date-time" },
          sentAt: { type: "string", format: "date-time" },
        },
      },
      McpJsonRpcRequest: {
        type: "object",
        required: ["jsonrpc", "method", "id"],
        properties: {
          jsonrpc: { type: "string", const: "2.0" },
          method: { type: "string", examples: ["initialize", "ping", "tools/list", "tools/call"] },
          params: { type: "object" },
          id: { oneOf: [{ type: "integer" }, { type: "string" }] },
        },
      },
      AppMeta: {
        type: "object",
        properties: {
          app: { type: "string" },
          did: { type: "string" },
          version: { type: "string" },
          layer: { type: "string", const: "L3-dispatcher" },
          codename: { type: "string", const: "io-yatabase" },
          surfaces: { type: "array", items: { type: "string" } },
        },
      },
    },
    responses: {
      Unauthorized: {
        description: "Missing or invalid bearer token.",
        content: { "application/json": { schema: { $ref: "#/components/schemas/Error" }, example: { error: "Unauthorized" } } },
      },
      QuotaExceeded: {
        description: "Daily plan limit exceeded. `Retry-After` header set to the next-day boundary.",
        headers: { "Retry-After": { schema: { type: "string", format: "date-time" } } },
        content: { "application/json": { schema: { $ref: "#/components/schemas/Error" }, example: { error: "QuotaExceeded" } } },
      },
      ServerError: {
        description: "Unexpected error.",
        content: { "application/json": { schema: { $ref: "#/components/schemas/Error" } } },
      },
    },
  },
  paths: {
    "/health": {
      get: {
        summary: "Worker liveness probe",
        description: "Always returns `{ok:true}`. Public, no auth. Edge-served — does not exercise downstream RW / dispatcher.",
        operationId: "getHealth",
        tags: ["observability"],
        security: [],
        responses: {
          "200": {
            description: "OK",
            content: { "application/json": { schema: { type: "object", properties: { ok: { type: "boolean" }, app: { type: "string" }, ts: { type: "string", format: "date-time" } } } } },
          },
        },
      },
    },
    "/_app/meta": {
      get: {
        summary: "App metadata + surface listing",
        description: "Lists every public path on the Worker plus the codename, layer, ADR refs.",
        operationId: "getAppMeta",
        tags: ["observability"],
        security: [],
        responses: {
          "200": {
            description: "OK",
            content: { "application/json": { schema: { $ref: "#/components/schemas/AppMeta" } } },
          },
        },
      },
    },
    "/auth/v1/signup": {
      post: {
        summary: "Mint a new tenant + API key",
        description: "Anonymous. Returns `sk_live_yata_*` + `orgDid` + AWS access keys for S3 SigV4. The `apiKey` is shown ONCE; persist it on the client side (we store only the SHA-256 hash).",
        operationId: "signup",
        tags: ["auth"],
        security: [],
        requestBody: { content: { "application/json": { schema: { $ref: "#/components/schemas/SignupRequest" } } } },
        responses: {
          "200": { description: "Created", content: { "application/json": { schema: { $ref: "#/components/schemas/SignupResponse" } } } },
          "503": { description: "Hyperdrive unavailable", content: { "application/json": { schema: { $ref: "#/components/schemas/Error" } } } },
        },
      },
    },
    "/auth/v1/upgrade": {
      post: {
        summary: "Upgrade plan tier",
        description: "Returns either a stub-mode confirmation (no Stripe configured) or a Stripe Checkout `checkoutUrl`.",
        operationId: "upgradePlan",
        tags: ["auth", "billing"],
        requestBody: {
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["plan"],
                properties: {
                  plan: { type: "string", enum: ["starter", "developer", "business"] },
                  successUrl: { type: "string", format: "uri" },
                  cancelUrl: { type: "string", format: "uri" },
                },
              },
            },
          },
        },
        responses: {
          "200": {
            description: "Stub or Checkout URL",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    ok: { type: "boolean" },
                    mode: { type: "string", enum: ["stub", "stripe"] },
                    plan: { type: "string" },
                    checkoutUrl: { type: "string", nullable: true },
                    sessionId: { type: "string", nullable: true },
                  },
                },
              },
            },
          },
          "401": { $ref: "#/components/responses/Unauthorized" },
        },
      },
    },
    "/auth/v1/portal": {
      post: {
        summary: "Stripe Customer Portal session (self-serve billing)",
        description: "Returns a hosted-page URL where the customer can change card, cancel, or view invoices. Requires the org has completed Stripe Checkout previously (i.e. a `cus_*` ID is cached).",
        operationId: "openPortal",
        tags: ["auth", "billing"],
        requestBody: {
          content: {
            "application/json": {
              schema: {
                type: "object",
                properties: {
                  returnUrl: { type: "string", format: "uri", description: "Where Stripe returns the customer after they close the portal. Default: https://yatabase.etzhayyim.com/dashboard" },
                },
              },
            },
          },
        },
        responses: {
          "200": {
            description: "Portal URL",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    ok: { type: "boolean" },
                    portalUrl: { type: "string" },
                    sessionId: { type: "string" },
                    customerId: { type: "string" },
                  },
                },
              },
            },
          },
          "400": { description: "Org has no Stripe customer yet (still on free / stub-upgraded)", content: { "application/json": { schema: { $ref: "#/components/schemas/Error" } } } },
          "401": { $ref: "#/components/responses/Unauthorized" },
          "502": { description: "Stripe API error", content: { "application/json": { schema: { $ref: "#/components/schemas/Error" } } } },
          "503": { description: "STRIPE_SECRET_KEY not configured", content: { "application/json": { schema: { $ref: "#/components/schemas/Error" } } } },
        },
      },
    },
    "/auth/v1/whoami": {
      get: {
        summary: "Current bearer's tenant identity",
        description: "Returns the orgDid, active plan, attached recovery email (if any), and Stripe customer linkage for the bearer. Useful for client-side bootstrap and dashboard rendering.",
        operationId: "getWhoami",
        tags: ["auth"],
        responses: {
          "200": {
            description: "Identity snapshot",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  required: ["orgDid", "actorDid", "productScope", "plan", "canOpenPortal"],
                  properties: {
                    orgDid: { type: "string" },
                    actorDid: { type: "string" },
                    productScope: { type: "string" },
                    plan: { type: "string", enum: ["free", "starter", "developer", "business", "enterprise"] },
                    attachedEmail: { type: "string", nullable: true, format: "email" },
                    attachedEmailVerified: { type: "boolean" },
                    stripeCustomerId: { type: "string", nullable: true },
                    canOpenPortal: { type: "boolean" },
                  },
                },
              },
            },
          },
          "401": { $ref: "#/components/responses/Unauthorized" },
        },
      },
    },
    "/auth/v1/attach-email": {
      post: {
        summary: "Attach a recovery email (verification required for recovery)",
        description: "Stores `email` for the current tenant and emails a verification link (24h TTL). The email is NOT added to the recovery reverse index until the owner clicks the link and POST /auth/v1/verify-email succeeds. This prevents an attacker from attaching a victim's email + triggering /auth/v1/recover to send spam-like recovery emails to people who never signed up. Idempotent: re-attaching the same email preserves verified status.",
        operationId: "attachEmail",
        tags: ["auth"],
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["email"],
                properties: {
                  email: { type: "string", format: "email", maxLength: 254 },
                },
              },
            },
          },
        },
        responses: {
          "200": {
            description: "Attached",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    ok: { type: "boolean" },
                    orgDid: { type: "string" },
                    attachedEmail: { type: "string", format: "email" },
                    attachedEmailVerified: { type: "boolean", description: "True only after the owner clicks the verification link." },
                    attachedAt: { type: "string", format: "date-time" },
                  },
                },
              },
            },
          },
          "400": { description: "Invalid email", content: { "application/json": { schema: { $ref: "#/components/schemas/Error" } } } },
          "401": { $ref: "#/components/responses/Unauthorized" },
          "503": { description: "auth-cache KV not bound", content: { "application/json": { schema: { $ref: "#/components/schemas/Error" } } } },
        },
      },
    },
    "/auth/v1/verify-email": {
      post: {
        summary: "Verify an attached email (anonymous, single-use)",
        description: "Redeems the 48-hex token sent to the email by /auth/v1/attach-email. On success, marks the email verified for the tenant and adds the SHA-256 hash to the recovery reverse index. Also available via GET with `?token=` so customers can click directly from the verification email.",
        operationId: "verifyEmail",
        tags: ["auth"],
        requestBody: {
          required: true,
          content: { "application/json": { schema: { type: "object", required: ["token"], properties: { token: { type: "string", pattern: "^[0-9a-f]{48}$" } } } } },
        },
        responses: {
          "200": {
            description: "Verified",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    ok: { type: "boolean" },
                    orgDid: { type: "string" },
                    verifiedEmail: { type: "string", format: "email" },
                  },
                },
              },
            },
          },
          "400": { description: "Token expired / corrupt / invalid", content: { "application/json": { schema: { $ref: "#/components/schemas/Error" } } } },
        },
      },
      get: {
        summary: "Verify email via link click (mirrors POST)",
        operationId: "verifyEmailGet",
        tags: ["auth"],
        parameters: [{ name: "token", in: "query", required: true, schema: { type: "string", pattern: "^[0-9a-f]{48}$" } }],
        responses: {
          "200": { description: "Verified (same body as POST)" },
          "400": { description: "Token expired / corrupt / invalid" },
        },
      },
    },
    "/auth/v1/recover": {
      post: {
        summary: "Email-based API key recovery (anonymous)",
        description: "Sends a recovery link to the attached email if any tenant matches. ALWAYS returns 200 with a neutral message — there is no signal whether the email is registered, to prevent enumeration. Recovery link contains a 48-hex token with a 15-minute TTL and resolves via POST /auth/v1/redeem.",
        operationId: "recoverKey",
        tags: ["auth"],
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["email"],
                properties: {
                  email: { type: "string", format: "email", maxLength: 254 },
                },
              },
            },
          },
        },
        responses: {
          "200": {
            description: "Neutral ack (no enumeration signal)",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    ok: { type: "boolean" },
                    message: { type: "string" },
                  },
                },
              },
            },
          },
          "400": { description: "Invalid email", content: { "application/json": { schema: { $ref: "#/components/schemas/Error" } } } },
        },
      },
    },
    "/auth/v1/redeem": {
      post: {
        summary: "Exchange recovery token for new API key (anonymous)",
        description: "Validates a 48-hex recovery token obtained via /auth/v1/recover email. Mints a fresh apiKey per matching orgDid via the pod's invite forwarder (KV fallback on pod miss). Single-use: token is deleted before processing.",
        operationId: "redeemRecoverToken",
        tags: ["auth"],
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["token"],
                properties: {
                  token: { type: "string", pattern: "^[0-9a-f]{48}$" },
                },
              },
            },
          },
        },
        responses: {
          "200": {
            description: "Newly-minted keys",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    ok: { type: "boolean" },
                    redeemedAt: { type: "string", format: "date-time" },
                    email: { type: "string", format: "email" },
                    minted: {
                      type: "array",
                      items: {
                        type: "object",
                        properties: {
                          orgDid: { type: "string" },
                          apiKey: { type: "string", description: "Save this — yatabase does not show it again." },
                          keyId: { type: "string" },
                          error: { type: "string" },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
          "400": { description: "Invalid or expired token", content: { "application/json": { schema: { $ref: "#/components/schemas/Error" } } } },
          "503": { description: "auth-cache KV not bound", content: { "application/json": { schema: { $ref: "#/components/schemas/Error" } } } },
        },
      },
    },
    "/auth/v1/invite": {
      post: {
        summary: "Mint a teammate API key under your org",
        operationId: "inviteMember",
        tags: ["auth"],
        requestBody: {
          content: {
            "application/json": {
              schema: {
                type: "object",
                properties: {
                  name: { type: "string" },
                  email: { type: "string", format: "email" },
                },
              },
            },
          },
        },
        responses: {
          "200": { description: "Created" },
          "401": { $ref: "#/components/responses/Unauthorized" },
        },
      },
    },
    "/auth/v1/revoke": {
      post: {
        summary: "Revoke a member's API key",
        operationId: "revokeMember",
        tags: ["auth"],
        requestBody: {
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["vertex_id"],
                properties: { vertex_id: { type: "string", examples: ["apikey:abc123..."] } },
              },
            },
          },
        },
        responses: {
          "200": { description: "Revoked" },
          "401": { $ref: "#/components/responses/Unauthorized" },
        },
      },
    },
    "/cypher": {
      post: {
        summary: "Run a Cypher query",
        description: "Cypher subset on RisingWave. Supports MATCH/CREATE/SET/DELETE on vertices and edges. Forbidden: DETACH DELETE, FOREACH, CALL{} writes.",
        operationId: "runCypher",
        tags: ["graph"],
        requestBody: { required: true, content: { "application/json": { schema: { $ref: "#/components/schemas/CypherRequest" } } } },
        responses: {
          "200": { description: "OK", content: { "application/json": { schema: { $ref: "#/components/schemas/CypherResponse" } } } },
          "400": { description: "Forbidden Cypher keyword (DETACH/FOREACH)", content: { "application/json": { schema: { $ref: "#/components/schemas/Error" } } } },
          "401": { $ref: "#/components/responses/Unauthorized" },
          "429": { $ref: "#/components/responses/QuotaExceeded" },
          "500": { $ref: "#/components/responses/ServerError" },
        },
      },
    },
    "/sparql": {
      post: {
        summary: "Run a SPARQL 1.1 query",
        operationId: "runSparql",
        tags: ["graph"],
        requestBody: {
          required: true,
          content: {
            "application/sparql-query": { schema: { type: "string" } },
            "application/json": { schema: { type: "object", required: ["query"], properties: { query: { type: "string" } } } },
          },
        },
        responses: {
          "200": { description: "OK", content: { "application/sparql-results+json": { schema: { type: "object" } } } },
          "401": { $ref: "#/components/responses/Unauthorized" },
        },
      },
    },
    "/storage/v1/object/{bucket}/{key}": {
      parameters: [
        { name: "bucket", in: "path", required: true, schema: { type: "string" } },
        { name: "key", in: "path", required: true, schema: { type: "string" } },
      ],
      put: {
        summary: "Upload an object",
        operationId: "putObject",
        tags: ["storage"],
        requestBody: { required: true, content: { "application/octet-stream": { schema: { type: "string", format: "binary" } } } },
        responses: { "200": { description: "OK" }, "401": { $ref: "#/components/responses/Unauthorized" } },
      },
      get: {
        summary: "Download an object",
        operationId: "getObject",
        tags: ["storage"],
        responses: {
          "200": { description: "OK", content: { "application/octet-stream": { schema: { type: "string", format: "binary" } } } },
          "404": { description: "Not found" },
        },
      },
      head: {
        summary: "Object metadata",
        operationId: "headObject",
        tags: ["storage"],
        responses: { "200": { description: "OK" }, "404": { description: "Not found" } },
      },
      delete: {
        summary: "Delete an object",
        operationId: "deleteObject",
        tags: ["storage"],
        responses: { "200": { description: "OK" } },
      },
    },
    "/storage/v1/object/list/{bucket}": {
      get: {
        summary: "List objects in a bucket",
        operationId: "listObjects",
        tags: ["storage"],
        parameters: [{ name: "bucket", in: "path", required: true, schema: { type: "string" } }],
        responses: { "200": { description: "OK", content: { "application/json": { schema: { type: "object" } } } } },
      },
    },
    "/storage/v1/bucket": {
      get: {
        summary: "List buckets",
        operationId: "listBuckets",
        tags: ["storage"],
        responses: { "200": { description: "OK" } },
      },
    },
    "/storage/v1/object/sign/{bucket}/{key}": {
      post: {
        summary: "Mint a presigned URL",
        operationId: "presignObject",
        tags: ["storage"],
        parameters: [
          { name: "bucket", in: "path", required: true, schema: { type: "string" } },
          { name: "key", in: "path", required: true, schema: { type: "string" } },
        ],
        responses: { "200": { description: "OK" } },
      },
    },
    "/storage/v1/object/public/{bucket}/{key}": {
      get: {
        summary: "Public download (no auth)",
        description: "Only succeeds if the bucket has `public_read=true` AND the ACL grants public.",
        operationId: "publicObject",
        tags: ["storage"],
        security: [],
        parameters: [
          { name: "bucket", in: "path", required: true, schema: { type: "string" } },
          { name: "key", in: "path", required: true, schema: { type: "string" } },
        ],
        responses: { "200": { description: "OK" }, "403": { description: "Forbidden — public ACL not set" }, "404": { description: "Not found" } },
      },
    },
    "/s3/{bucket}/{key}": {
      put: { summary: "S3 SigV4 PUT", operationId: "s3Put", tags: ["storage"], parameters: [{ name: "bucket", in: "path", required: true, schema: { type: "string" } }, { name: "key", in: "path", required: true, schema: { type: "string" } }], security: [], responses: { "200": { description: "OK" } }, description: "Use awsAccessKeyId + awsSecretAccessKey from /auth/v1/signup. Standard AWS SDK works against `--endpoint-url https://yatabase.etzhayyim.com/s3`." },
      get: { summary: "S3 SigV4 GET", operationId: "s3Get", tags: ["storage"], parameters: [{ name: "bucket", in: "path", required: true, schema: { type: "string" } }, { name: "key", in: "path", required: true, schema: { type: "string" } }], security: [], responses: { "200": { description: "OK" } } },
    },
    "/mcp": {
      post: {
        summary: "MCP JSON-RPC 2.0 dispatch",
        description: "Public methods (initialize, ping, tools/list, resources/list, prompts/list) require no auth. tools/call and resources/read require Bearer auth.",
        operationId: "mcpDispatch",
        tags: ["mcp"],
        security: [],
        requestBody: { required: true, content: { "application/json": { schema: { $ref: "#/components/schemas/McpJsonRpcRequest" } } } },
        responses: { "200": { description: "JSON-RPC response" } },
      },
    },
    "/xrpc/{nsid}": {
      parameters: [{ name: "nsid", in: "path", required: true, schema: { type: "string" }, description: "AT Protocol NSID, e.g. ai.gftd.apps.yata.runCypher", examples: { yata: { value: "ai.gftd.apps.yata.runCypher" }, billing: { value: "ai.gftd.apps.billing.getInvoice" } } }],
      get: { summary: "XRPC query", operationId: "xrpcQuery", tags: ["xrpc"], responses: { "200": { description: "OK" } } },
      post: { summary: "XRPC procedure", operationId: "xrpcProcedure", tags: ["xrpc"], responses: { "200": { description: "OK" } } },
    },
    "/api/usage": {
      get: { summary: "Read your tenant's recent usage", operationId: "getUsage", tags: ["billing", "observability"], responses: { "200": { description: "OK", content: { "application/json": { schema: { $ref: "#/components/schemas/UsageReport" } } } }, "401": { $ref: "#/components/responses/Unauthorized" } } },
    },
    "/api/plan": {
      get: { summary: "Read your tenant's current plan + quota status", operationId: "getPlan", tags: ["billing"], responses: { "200": { description: "OK", content: { "application/json": { schema: { $ref: "#/components/schemas/QuotaStatus" } } } }, "401": { $ref: "#/components/responses/Unauthorized" } } },
    },
    "/api/schema": {
      get: { summary: "Describe your tenant graph schema (label list + counts)", operationId: "getSchema", tags: ["graph", "observability"], responses: { "200": { description: "OK" }, "401": { $ref: "#/components/responses/Unauthorized" } } },
    },
    "/api/webhooks": {
      get: {
        summary: "List registered outbound webhooks (secrets redacted)",
        description: "Returns this org's webhook subscriptions. The full secret is only returned once at POST time; subsequent GETs only carry `secretPrefix` (first 8 chars + ellipsis).",
        operationId: "listWebhooks",
        tags: ["webhooks"],
        responses: {
          "200": {
            description: "OK",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    orgDid: { type: "string" },
                    webhooks: {
                      type: "array",
                      items: {
                        type: "object",
                        properties: {
                          id: { type: "string", pattern: "^whk_[0-9a-f]+$" },
                          url: { type: "string", format: "uri" },
                          label: { type: "string", nullable: true },
                          types: { type: "array", items: { type: "string" } },
                          createdAt: { type: "string", format: "date-time" },
                          secretPrefix: { type: "string", description: "First 8 chars + ellipsis. Full secret only at POST." },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
          "401": { $ref: "#/components/responses/Unauthorized" },
          "503": { description: "auth-cache KV not bound" },
        },
      },
      post: {
        summary: "Register an outbound webhook for graph-mutation events",
        description: "Per-org cap: 10 webhooks. Events: cypher.create, cypher.set, cypher.delete, cypher.create_edge, cypher.delete_edge. Optional `label` filter — only fires when the payload label matches. Each delivery POSTs JSON with X-Yatabase-Event, X-Yatabase-Signature (hex hmac-sha256 over body), X-Yatabase-Delivery headers. HTTPS only. Fire-and-forget; no retries in v1.",
        operationId: "registerWebhook",
        tags: ["webhooks"],
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["url"],
                properties: {
                  url: { type: "string", format: "uri", description: "Must be https://" },
                  secret: { type: "string", minLength: 8, description: "Custom HMAC secret. If omitted, server generates a 32-hex secret." },
                  label: { type: "string", description: "Optional: only fire for this label." },
                  types: {
                    type: "array",
                    description: "Defaults to all events.",
                    items: { type: "string", enum: ["cypher.create", "cypher.set", "cypher.delete", "cypher.create_edge", "cypher.delete_edge"] },
                  },
                },
              },
            },
          },
        },
        responses: {
          "200": {
            description: "Registered. Save the secret — only returned here.",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    ok: { type: "boolean" },
                    webhook: {
                      type: "object",
                      properties: {
                        id: { type: "string" },
                        url: { type: "string" },
                        secret: { type: "string", description: "Full secret — save it. Subsequent GETs only return secretPrefix." },
                        label: { type: "string", nullable: true },
                        types: { type: "array", items: { type: "string" } },
                        createdAt: { type: "string", format: "date-time" },
                      },
                    },
                    message: { type: "string" },
                  },
                },
              },
            },
          },
          "400": { description: "Invalid url or unsupported types" },
          "401": { $ref: "#/components/responses/Unauthorized" },
          "409": { description: "Per-org webhook cap (10) exceeded" },
          "503": { description: "auth-cache KV not bound" },
        },
      },
    },
    "/api/webhooks/{id}": {
      parameters: [{ name: "id", in: "path", required: true, schema: { type: "string", pattern: "^whk_[0-9a-f]+$" } }],
      delete: {
        summary: "Remove an outbound webhook",
        operationId: "deleteWebhook",
        tags: ["webhooks"],
        responses: {
          "200": { description: "Deleted (idempotent — also returns 200 for unknown ids)" },
          "400": { description: "Invalid id shape" },
          "401": { $ref: "#/components/responses/Unauthorized" },
        },
      },
    },
    "/api/members": {
      get: { summary: "List API keys minted under your org", operationId: "listMembers", tags: ["auth"], responses: { "200": { description: "OK" }, "401": { $ref: "#/components/responses/Unauthorized" } } },
    },
    "/api/audit": {
      get: { summary: "Last 90d of authenticated requests for your org", operationId: "getAudit", tags: ["observability", "privacy"], responses: { "200": { description: "OK" }, "401": { $ref: "#/components/responses/Unauthorized" } } },
    },
    "/api/outbox": {
      get: {
        summary: "Email outbox for your org",
        operationId: "getOutbox",
        tags: ["observability"],
        parameters: [{ name: "limit", in: "query", schema: { type: "integer", minimum: 1, maximum: 200, default: 50 } }],
        responses: { "200": { description: "OK", content: { "application/json": { schema: { type: "object", properties: { events: { type: "array", items: { $ref: "#/components/schemas/OutboxEvent" } } } } } } }, "401": { $ref: "#/components/responses/Unauthorized" } },
      },
    },
    "/api/invoices": {
      get: { summary: "List invoice months for your org", operationId: "listInvoices", tags: ["billing"], responses: { "200": { description: "OK" }, "401": { $ref: "#/components/responses/Unauthorized" } } },
    },
    "/api/invoice": {
      get: {
        summary: "HTML invoice for a given month (適格請求書 T9007028460042)",
        operationId: "getInvoice",
        tags: ["billing"],
        parameters: [{ name: "month", in: "query", required: true, schema: { type: "string", pattern: "^\\d{4}-\\d{2}$" }, examples: { example: { value: "2026-05" } } }],
        responses: { "200": { description: "OK", content: { "text/html": { schema: { type: "string" } } } }, "401": { $ref: "#/components/responses/Unauthorized" } },
      },
    },
    "/api/export": {
      get: { summary: "Right-to-know full data export (CCPA §1798.100, GDPR Art 15+20, 改正個人情報保護法 §33)", operationId: "exportData", tags: ["privacy"], responses: { "200": { description: "OK", content: { "application/json": { schema: { type: "object" } } } }, "401": { $ref: "#/components/responses/Unauthorized" } } },
    },
    "/api/account/delete": {
      post: {
        summary: "Right-to-erasure account deletion (irreversible) (CCPA §1798.105, GDPR Art 17, 改正個人情報保護法 §34-36)",
        description: "Physically purges every per-org row in the Worker-side authoritative stores: KV (auth, plan, usage, cypher graph, storage meta, attached email, reverse index) and R2 (`yata/{orgDid}/*`). Also writes `erased:v1:{orgDid}` so resolveAuthContext returns 401 immediately even if the legacy pod-side `vertex_api_key` row still resolves. The bearer used to delete is invalidated on the next request.",
        operationId: "deleteAccount",
        tags: ["privacy"],
        requestBody: {
          required: true,
          content: { "application/json": { schema: { type: "object", required: ["confirm"], properties: { confirm: { type: "string", const: "DELETE" } } } } },
        },
        responses: {
          "200": {
            description: "Deleted",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                  properties: {
                    ok: { type: "boolean" },
                    orgDid: { type: "string" },
                    mode: { type: "string", enum: ["kv-r2-purge"] },
                    erasedAt: { type: "string", format: "date-time" },
                    counters: {
                      type: "object",
                      properties: {
                        auth_keys: { type: "integer" },
                        plan: { type: "integer" },
                        usage_days: { type: "integer" },
                        cypher_nodes: { type: "integer" },
                        cypher_labels: { type: "integer" },
                        storage_kv_objects: { type: "integer" },
                        r2_objects: { type: "integer" },
                        attached_email_index: { type: "integer" },
                      },
                    },
                  },
                },
              },
            },
          },
          "400": { description: "Missing confirm:DELETE" },
          "401": { $ref: "#/components/responses/Unauthorized" },
        },
      },
    },
    "/webhook/stripe": {
      post: {
        summary: "Stripe webhook (signature-verified, no auth)",
        description: "Used by Stripe Live to flip vertex_org_plan after a customer completes Checkout. Requires `Stripe-Signature` header + `STRIPE_WEBHOOK_SECRET` env. Internal — listed for transparency only.",
        operationId: "stripeWebhook",
        tags: ["billing"],
        security: [],
        responses: { "200": { description: "OK" }, "400": { description: "BadSignature / BadJson" }, "503": { description: "STRIPE_WEBHOOK_SECRET not configured" } },
      },
    },
  },
} as const;

export function openapiResponse(): Response {
  return new Response(JSON.stringify(SPEC, null, 2), {
    status: 200,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "x-yatabase-surface": "openapi",
      "cache-control": "public, max-age=300, s-maxage=600",
      "access-control-allow-origin": "*",
      "access-control-allow-methods": "GET, OPTIONS",
    },
  });
}
