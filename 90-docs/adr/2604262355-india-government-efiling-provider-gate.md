---
id: adr-2604262355-india-government-efiling-provider-gate
title: "India government e-filing provider gate"
status: accepted
doc_type: adr
date: 2026-04-26
last_verified: 2026-04-26
topic: india-government-efiling
depends_on:
  - adr-0052-epfo-ecr-actor
  - adr-0054-esic-contribution-actor
  - adr-0070-itr1-sahaj-actor
  - adr-0071-gstr3b-actor
---

## Decision

India e-filing is implemented as a provider-gated handoff, not as direct
government portal browser automation.

The common Zeebe task is `ind.efiling.submit`. It may be used by EPFO,
ESIC, ITR-1, and GSTR-3B flows after draft validation and human approval.
It writes every attempt to `vertex_ind_efiling_submission` and exposes
status through `mv_ind_efiling_submission_status`.

Live submission is disabled unless all gates are true:

- `IND_EFILING_LIVE_ENABLED=1`
- provider kind is allowed for the jurisdiction:
  - ITR-1: `eri_type2_api` or `authorized_eri`
  - GSTR-3B: `gsp_api` or `authorized_gsp`
  - EPFO: `authorized_epfo_integrator`
  - ESIC: `authorized_esic_integrator`
- `authorizationRef`, `credentialRef`, and `approvedByDid` are present
- provider endpoint is configured as HTTPS:
  `IND_EFILING_PROVIDER_<KEY>_ENDPOINT`
- provider HMAC secret is configured:
  `IND_EFILING_PROVIDER_<KEY>_HMAC_SECRET`

Without those gates the task returns `dry_run` or `blocked` and still
records an audit row.

## Current official routes

As of 2026-04-26, the Income Tax Department documents ERI types, including
Type 2 ERIs that file through APIs provided by the department. The e-Filing
portal also documents client consent for ERI actions and service request
verification.

GSTR-3B live filing must go through an authorized GST provider/API route
(GSP/ASP), not ad hoc portal automation.

EPFO and ESIC live filing remain provider/integrator-gated. Direct scraping
or automated portal login is not part of this architecture.

## Non-goals

- No CAPTCHA solving.
- No OTP/MFA bypass.
- No credential storage in BPMN variables.
- No direct government portal browser automation from the shared Zeebe worker.
- No live filing from dry-run data.

## Implementation Notes

`ind.efiling.submit` sends only to an operator-configured HTTPS adapter. The
adapter is responsible for using an authorized government/API channel and for
returning one of:

- `submitted` with an external reference such as ACK, ARN, TRRN, or challan
- `requires_user_action` when OTP/MFA/client consent is needed
- `failed`
- `blocked`

The worker records the idempotency key and payload hash so retries do not
create duplicate filing attempts.

## Consequences

This makes the India actors operational up to the compliant e-filing boundary.
For ITR-1 and GSTR-3B, live automation becomes available when ERI/GSP
credentials and adapter endpoints are provisioned. For EPFO and ESIC, live
automation remains blocked until an authorized integrator route exists.
