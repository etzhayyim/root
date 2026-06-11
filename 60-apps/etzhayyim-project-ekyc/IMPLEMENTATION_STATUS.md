# eKYC Implementation Status

## ✅ Completed Tasks

### 1. Self-Hosted OCR Engine (`internal/ocr/engine.go`)

**Implementation:**
- Tesseract OCR integration (`gosseract/v2`)
- Multi-language support (English + Japanese)
- Document-specific parsers:
  - Passport (MRZ parsing)
  - Driver's License
  - National ID
  - Residence Card
- Image quality validation (minimum 800x600, file size checks)
- OCR confidence scoring
- Data comparison (OCR results vs user-provided data)
- Date normalization for expiry validation

**Features:**
- `ExtractText()` — Raw OCR text extraction
- `ExtractDocumentInfo()` — Structured data extraction
- `ValidateImageQuality()` — Pre-check before OCR
- `CompareDocumentData()` — Cross-validation
- `PreprocessImage()` — Image enhancement (placeholder for grayscale, denoise, deskew)

**Dependencies:**
```go
github.com/otiai10/gosseract/v2 v2.4.1
```

**System Requirements:**
- Tesseract OCR 4.x+ (`/usr/share/tesseract-ocr/4.00/tessdata`)
- Language data: `eng.traineddata`, `jpn.traineddata`

### 2. Self-Hosted Liveness Detection (`internal/liveness/detector.go`)

**Implementation:**
- OpenCV-based face/eye detection (`gocv`)
- Haar Cascade classifiers
- Anti-spoofing checks:
  - Print attack detection (texture analysis via Laplacian variance)
  - Screen replay detection (Moiré pattern detection via FFT)
  - Mask/3D face detection (depth analysis via edge density)
- Gesture verification (nod, shake, smile, blink, turn)
- Device fingerprinting (bot detection)
- Confidence scoring (6-factor weighted average)

**Features:**
- `DetectLiveness()` — Comprehensive liveness check
- `performAntiSpoofing()` — Multi-layer spoofing detection
- `analyzeTexture()` — Laplacian variance for sharpness
- `detectMoirePattern()` — FFT-based screen detection
- `analyzeDepth()` — Canny edge density for 2D/3D
- `verifyGestures()` — Gesture sequence validation
- `verifyDeviceInfo()` — Bot detection via browser fingerprinting

**Dependencies:**
```go
gocv.io/x/gocv v0.35.0
```

**System Requirements:**
- OpenCV 4.x+
- Haar Cascade files:
  - `/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml`
  - `/usr/share/opencv4/haarcascades/haarcascade_eye.xml`

### 3. Integrated Verification Engine (`internal/verification/verifier.go`)

**Updated to use OCR + Liveness:**
- `NewVerifier()` — Initializes OCR engine + liveness detector
- `VerifyDocuments()` — 6 comprehensive checks:
  1. Front image quality
  2. Back image quality
  3. OCR extraction + confidence
  4. Data comparison (OCR vs user input)
  5. Expiry validation
  6. Authenticity placeholder
- `VerifyLiveness()` — Face + gesture + anti-spoofing + device checks

## 🚧 In Progress

### 3. APQC KYC MCP Integration

**Status:** Partially implemented in `internal/server/mcp_client.go`

**TODO:**
- Implement real XRPC calls to APQC 12.4.5 KYC performer
- Pass verification data as MCP CallTool arguments
- Poll workflow status via ReadResource
- Handle workflow completion callbacks

**Target Endpoint:**
```
etzhayyim-performer-sys-etzhayyim-actors-pba7d22f-svc-apqc-12-4-5-kyc-v2:8080
```

**MCP Tools:**
- `submit_kyc_verification` — Start APQC workflow
- `get_kyc_workflow_status` — Poll workflow state
- `approve_kyc` — Admin approval action
- `reject_kyc` — Admin rejection action

## 📝 Pending Tasks

### 4. eKYC Admin Dashboard

**Plan:**
- Create `cdn/ekyc-admin-ui-<nanoid>/`
- Admin-only access (Clerk `org:admin` role)
- Features:
  - List all org verifications (pending, approved, rejected)
  - View verification details (images, OCR results, liveness scores)
  - Manual review actions (approve, reject, request more info)
  - Audit log viewer
  - Statistics dashboard (approval rate, processing time, etc.)

**Tech Stack:**
- SvelteKit (SSG)
- Clerk admin role check
- XRPC client to ekyc-service `UpdateVerificationStatus`

### 5. Audit Logging System

**Plan:**
- Create `internal/audit/logger.go`
- Log all critical actions:
  - Verification submissions
  - Status changes (pending → approved/rejected)
  - Admin actions (manual review, override)
  - API access (who accessed what verification)
- Storage: PostgreSQL (`org-statestore`) or separate audit table
- Tamper-proof: Append-only, cryptographic hash chain
- Retention: 7 years (regulatory compliance)

**Schema:**
```json
{
  "audit_id": "uuid",
  "timestamp": "2026-02-17T10:00:00Z",
  "event_type": "verification_status_change",
  "actor_id": "user_xyz",
  "org_id": "org_abc",
  "resource_id": "verification_id",
  "action": "approved",
  "metadata": {},
  "ip_address": "1.2.3.4",
  "user_agent": "...",
  "previous_hash": "sha256(...)",
  "current_hash": "sha256(...)"
}
```

### 6. Webhook Notification System

**Plan:**
- Create `internal/webhooks/sender.go`
- Send HTTP POST to user-configured webhook URLs
- Events:
  - `verification.submitted`
  - `verification.processing`
  - `verification.approved`
  - `verification.rejected`
  - `verification.expired`
  - `liveness.failed`
- Retry logic: Exponential backoff (3 retries)
- Signature: HMAC-SHA256 for webhook authenticity

**Webhook Payload:**
```json
{
  "event": "verification.approved",
  "timestamp": "2026-02-17T10:00:00Z",
  "data": {
    "verification_id": "abc123",
    "user_id": "user_xyz",
    "org_id": "org_abc",
    "status": "approved",
    "confidence": 0.92
  },
  "signature": "sha256=..."
}
```

**Storage:**
- Webhook URLs stored in App state store per org
- Admin UI to configure webhooks

### 7. etzhayyim-project-amlctf (AML/CTF Integration)

**Plan:**
- Create new project: `60-apps/etzhayyim-project-amlctf/`
- Services:
  - `legacy-runtime/amlctf-screening-<nanoid>/` — Risk screening service
  - `legacy-runtime/amlctf-transaction-monitor-<nanoid>/` — Transaction monitoring
  - `cdn/amlctf-ui-<nanoid>/` — AML/CTF compliance dashboard
- Features:
  - Sanctions screening (OFAC, EU, UN lists)
  - PEP (Politically Exposed Person) checks
  - Adverse media screening
  - Transaction monitoring (velocity, thresholds)
  - Risk scoring (low/medium/high)
  - Case management (SAR filing)

**Integration with eKYC:**
- eKYC verification approved → Trigger AML/CTF screening
- MCP CallTool: `amlctf-screening` service
- Workflow:
  1. eKYC completes → Extract user data
  2. Call `amlctf-screening:ScreenEntity` RPC
  3. Check sanctions, PEP, adverse media
  4. Calculate risk score
  5. Auto-approve low risk, flag high risk for review
  6. Store screening results in App state store

**Data Sources:**
- OFAC SDN list (https://sanctionssearch.ofac.treas.gov/)
- EU sanctions list
- UN consolidated list
- PEP databases (commercial or open-source)
- Adverse media (news API)

### 8. eKYC ↔ AML/CTF Integration

**MCP Workflow:**
```
eKYC SubmitVerification
  ↓
OCR + Liveness Check
  ↓
APQC KYC Workflow (MCP)
  ↓
[APPROVED] → AML/CTF Screening (MCP CallTool)
  ↓
Sanctions/PEP/Adverse Media Check
  ↓
Risk Score (low/medium/high)
  ↓
[LOW RISK] → Auto-approve onboarding
[MEDIUM/HIGH RISK] → Flag for compliance review
  ↓
Webhook Notification → Customer (approved/review-pending)
```

**State Transitions:**
```
PENDING → PROCESSING (OCR + Liveness)
  ↓
PROCESSING → APQC_WORKFLOW (MCP KYC)
  ↓
APQC_WORKFLOW → AMLCTF_SCREENING (if approved)
  ↓
AMLCTF_SCREENING → APPROVED (low risk)
AMLCTF_SCREENING → REQUIRES_REVIEW (medium/high risk)
AMLCTF_SCREENING → REJECTED (sanctions match)
```

## Dependencies to Add

### Dockerfile (Bazel `rules_oci`)
```dockerfile
FROM debian:bookworm-slim

# Install Tesseract OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-jpn \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Install OpenCV
RUN apt-get update && apt-get install -y \
    libopencv-dev \
    opencv-data \
    && rm -rf /var/lib/apt/lists/*

# Copy binary
COPY ekyc-service /usr/local/bin/

ENTRYPOINT ["/usr/local/bin/ekyc-service"]
```

### BUILD.bazel Updates
- Add `@rules_foreign_cc` for native library builds
- Add system dependencies for Tesseract + OpenCV

## Next Immediate Steps

1. ✅ Complete APQC MCP integration (real XRPC calls)
2. Create admin dashboard UI
3. Implement audit logging
4. Add webhook system
5. Plan and create `etzhayyim-project-amlctf`
6. Integrate eKYC → AML/CTF workflow

## Performance Targets

| Metric | Target | Current |
|---|---|---|
| OCR processing time | <3s | TBD |
| Liveness detection time | <2s | TBD |
| End-to-end verification | <30s | TBD |
| KEDA cold start | <5s | TBD |
| Success rate | >95% | TBD |

## Security Checklist

- [x] Clerk JWT authentication
- [x] Org-scoped access control
- [x] Admin role verification
- [x] JWKS rotation (1 hour)
- [x] service mesh mTLS
- [ ] Audit logging (pending)
- [ ] Webhook HMAC signatures (pending)
- [ ] Rate limiting (pending)
- [ ] DDoS protection (pending)

## Compliance Checklist (for production)

- [ ] GDPR compliance (data retention, right to erasure)
- [ ] eIDAS compliance (EU digital identity)
- [ ] KYC/AML regulations (varies by country)
- [ ] FATF recommendations
- [ ] ISO 27001 (information security)
- [ ] SOC 2 Type II (audit)
- [ ] Penetration testing
- [ ] Bug bounty program
