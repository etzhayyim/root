# etzhayyim-project-ekyc

eKYC (electronic Know Your Customer) project — Clerk-integrated identity verification with MCP integration for APQC 12.4.5 KYC workflows.

## Architecture (DoDAF v2)

### Capability (CV-1)
**eKYC Verification** — Electronic identity verification capability integrating Clerk authentication with KYC document validation and MCP-enabled workflow automation (APQC 12.4.5).

### Activities (OV-5b)
- Identity document upload and validation (OCR, authenticity checks)
- Face liveness detection (gesture-based)
- Clerk user authentication and org-scoped verification
- MCP-enabled APQC workflow integration
- Verification status tracking and reporting

### Performers (OV-2)
- **ekyc-service** (`legacy-runtime/ekyc-service-ephj2jf6/`) — XRPC MCP service (Tier 2, Scale-to-Zero)
- **ekyc-ui** (`cdn/ekyc-ui-hzaooy0f/`) — SvelteKit static UI (Tier 3)
- **APQC 12.4.5 KYC performer** — MCP integration target (`etzhayyim-performer-sys-etzhayyim-actors-pba7d22f-svc-apqc-12-4-5-kyc-v2`)

### Services (SvcV-1)
| Service | Type | Protocol | URL |
|---|---|---|---|
| ekyc-service | XRPC MCP | XRPC (HTTP/2) | `ekyc.etzhayyim.com` |
| ekyc-ui | Static UI | HTTP/1.1 | `ekyc.etzhayyim.com` |

### Resource Flows (OV-2)
```
User (Browser) → Clerk Auth → ekyc-ui (SvelteKit)
                                    ↓ XRPC (Connect-gRPC Bridge)
                              ekyc-service (App runtime)
                                    ↓ App state store
                              PostgreSQL (org-statestore)
                                    ↓ MCP CallTool
                              APQC 12.4.5 KYC performer
```

## Components

### legacy-runtime/ekyc-service-ephj2jf6

gRPC eKYC service with Clerk JWT validation and MCP integration.

**Features:**
- Clerk JWKS-based JWT authentication
- Document upload and validation (OCR placeholder)
- Face liveness check (gesture-based)
- App state store integration (PostgreSQL)
- MCP service implementation (Initialize, ListTools, CallTool, ListResources, ReadResource)
- APQC 12.4.5 KYC workflow integration via MCP CallTool

**Proto:** `proto/v1/ekyc.proto`
- `EKYCService` — SubmitVerification, GetVerificationStatus, ListVerifications, UpdateVerificationStatus, InitiateLivenessCheck, SubmitLivenessCheck
- `MCPService` — Initialize, ListTools, CallTool, ListResources, ReadResource

**Environment:**
```bash
CLERK_JWKS_URL=https://clerk.etzhayyim.com/.well-known/jwks.json
POSTGRES_STATE_STORE=org-statestore
MCP_APQC_KYC_ENDPOINT=etzhayyim-performer-sys-etzhayyim-actors-pba7d22f-svc-apqc-12-4-5-kyc-v2:8080
APP_GRPC_ENDPOINT=http://shared-ekyc-service-legacy-runtime:50001
```

**Ports:**
- 8080: XRPC server
- 9090: Prometheus `/metrics`

### cdn/ekyc-ui-hzaooy0f

SvelteKit eKYC frontend with Clerk authentication.

**Features:**
- Clerk JS SDK authentication
- Document upload UI (front/back images)
- Liveness check UI (face image + gestures)
- Verification status tracking
- MCP workflow status display

**Tech Stack:**
- SvelteKit (SSG mode, adapter-static)
- Clerk JS SDK
- Connect-gRPC web client (placeholder, uses fetch for now)

**URL:** `https://ekyc.etzhayyim.com`

## Deployment

### Deploy ekyc-service (XRPC backend)

```bash
cd 60-apps/etzhayyim-project-ekyc/legacy-runtime/ekyc-service-ephj2jf6/

# Generate proto code (Go + TypeScript)
buf generate

# Deploy to K8s via current mage flow
mage Deploy
```

**Generated Resources:**
- Deployment: `ekyc-service`
- Service: `ekyc-service` (ClusterIP)
- GRPCRoute: `ekyc.etzhayyim.com` → `ekyc-service:8080`
- KEDA ScaledObject: HTTP trigger, 0-5 replicas
- App runtime Pulumi Application: `shared-ekyc-service`

### Deploy ekyc-ui (Static frontend)

```bash
cd 60-apps/etzhayyim-project-ekyc/wasm/ekyc-ui-hzaooy0f/svelte/

# Install dependencies
pnpm install

# Build SvelteKit SSG
pnpm build

# Deploy to K8s via current mage flow
mage Deploy
```

**Generated Resources:**
- Deployment: `ekyc-ui` (nginx)
- Service: `ekyc-ui` (ClusterIP)
- HTTPRoute: `ekyc.etzhayyim.com` → `ekyc-ui:80`
- KEDA HTTPScaledObject: 0-3 replicas

## MCP Integration with APQC 12.4.5 KYC

ekyc-service integrates with APQC 12.4.5 KYC performer via MCP:

1. **Submit Verification** → Calls APQC KYC performer's `CallTool` RPC
   - Tool: `submit_kyc_verification`
   - Arguments: `{ verification_id, user_id, org_id, document_info }`
   - Returns: `{ workflow_id }`

2. **Get Workflow Status** → Calls APQC KYC performer's `ReadResource` RPC
   - Resource: `apqc://kyc/workflows/{workflow_id}`
   - Returns: `{ status, steps, last_updated }`

3. **List Verifications** → Exposes as MCP Resource
   - Resource: `ekyc://verifications`
   - Consumers: APQC performers, monitoring tools

## Authentication Flow

1. User signs in via Clerk (`ekyc-ui` → `clerk.etzhayyim.com`)
2. Clerk issues JWT with claims: `{ sub, org_id, org_slug, org_role, email }`
3. ekyc-ui sends XRPC requests with `Authorization: Bearer <jwt>`
4. ekyc-service validates JWT via JWKS (`clerk.etzhayyim.com/.well-known/jwks.json`)
5. ekyc-service extracts `user_id` and `org_id` from JWT claims
6. All operations are org-scoped (user can only view their org's verifications)

## Verification Flow

1. **Document Upload** (UI)
   - User selects document type (Passport, Driver's License, etc.)
   - Uploads front + back images (base64)
   - Enters document number, issuing country, expiry date

2. **Liveness Check** (UI)
   - UI calls `InitiateLivenessCheck` → receives `session_id`
   - User performs gestures (nod, smile, turn head)
   - UI captures face image + gesture sequence
   - UI calls `SubmitLivenessCheck` → receives liveness result

3. **Submit Verification** (Backend)
   - ekyc-service receives `SubmitVerificationRequest`
   - Saves to App state store (`ekyc:verification:{id}`)
   - Starts background verification:
     - Check 1: Image quality
     - Check 2: Document authenticity (placeholder)
     - Check 3: OCR extraction (placeholder)
     - Check 4: Expiry validation
   - Triggers APQC KYC workflow via MCP
   - Returns `verification_id` + `mcp_workflow_id`

4. **Status Tracking** (UI)
   - UI polls `GetVerificationStatus` with `verification_id`
   - Backend returns:
     - Verification status (PENDING, PROCESSING, APPROVED, REJECTED, REQUIRES_REVIEW)
     - Check results
     - MCP workflow status

## State Store Schema

### Verification Record

```json
{
  "verification_id": "abc123",
  "user_id": "user_xyz",
  "org_id": "org_abc",
  "status": "VERIFICATION_STATUS_PROCESSING",
  "message": "Processing verification",
  "document_info": {
    "document_type": "DOCUMENT_TYPE_PASSPORT",
    "document_number": "AB123456",
    "issuing_country": "JP",
    "expiry_date": "2030-12-31T00:00:00Z"
  },
  "liveness_result": {
    "status": "LIVENESS_STATUS_PASS",
    "confidence_score": 0.92,
    "message": "Liveness check passed",
    "checked_at": "2026-02-17T10:00:00Z"
  },
  "checks": [
    {
      "check_name": "image_quality",
      "status": "CHECK_STATUS_PASS",
      "message": "Image quality verification",
      "checked_at": "2026-02-17T10:00:00Z"
    }
  ],
  "created_at": "2026-02-17T09:00:00Z",
  "updated_at": "2026-02-17T10:00:00Z",
  "metadata": {},
  "mcp_workflow_id": "kyc-wf-abc123",
  "admin_notes": ""
}
```

**State Key:** `ekyc:verification:{verification_id}`

### Liveness Session

```json
{
  "session_id": "sess_abc",
  "user_id": "user_xyz",
  "org_id": "org_abc",
  "session_token": "token_xyz",
  "expires_at": "2026-02-17T10:05:00Z",
  "created_at": "2026-02-17T10:00:00Z"
}
```

**State Key:** `ekyc:liveness:{session_id}`

## Measures (StdV-1)

- Verification success rate (target: >95%)
- Processing time (target: <30s for auto-approval)
- KEDA scale-to-zero efficiency (target: <5s cold start)
- MCP workflow completion rate (target: >99%)

## Security

- **Clerk JWT authentication** — All XRPC requests require valid Clerk JWT
- **Org-scoped access** — Users can only view verifications for their org
- **Admin role check** — UpdateVerificationStatus requires `org:admin` role
- **JWKS rotation** — JWKS keys refreshed every hour
- **service mesh mTLS** — All legacy runtime component communication encrypted
- **KEDA scale-to-zero** — Reduces attack surface when idle

## Next Steps

1. Integrate real OCR service (Google Vision API, AWS Textract)
2. Integrate real liveness detection (FaceTec, iProov)
3. Implement document authenticity checks (hologram detection)
4. Complete APQC KYC performer integration (real MCP CallTool)
5. Add admin dashboard for manual review
6. Add audit logging for compliance
7. Add webhook notifications for status updates
