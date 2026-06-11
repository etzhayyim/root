# etzhayyim-project-app-reviewer

App review platform for Kotodama app publication.

## Goal
- Evaluate app submissions before publish for bugs, runtime errors, abuse, policy violations, and security risk.
- Provide deterministic decision flow similar to an app store reviewer process.

## Core workflow
1. Submission intake
2. Automated checks (policy/security/runtime)
3. Human review (functional/safety/compliance)
4. Decision (approve/request_changes/reject)
5. Post-release monitoring and emergency revoke

## Review status model
- `submitted`
- `auto_checking`
- `auto_failed`
- `auto_passed`
- `in_review`
- `request_changes`
- `rejected`
- `approved`
- `published`
- `revoked`

## Primary entities
- `ReviewSubmission`
- `AutomatedCheck`
- `ReviewFinding`
- `ReviewDecision`
- `CapabilityProfile`

## API surface (design)
- `ReviewService.CreateSubmission`
- `ReviewService.RunAutomatedChecks`
- `ReviewService.ListPendingReviews`
- `ReviewService.SubmitFinding`
- `ReviewService.SubmitDecision`
- `ReviewService.RevokePublishedApp`

Detailed process and role matrix are in `design/review-process.md`.
