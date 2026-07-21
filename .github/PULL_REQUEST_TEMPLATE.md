## Summary

<!-- 1-3 sentences. What does this PR do, and why? -->

## Scope

<!--
Tick the boxes that apply. If multiple, consider whether the PR
should be split — single-scope PRs are easier to review + revert.
-->

- [ ] New feature / new substrate / new actor
- [ ] Bug fix / regression fix
- [ ] Refactor / cleanup (no behavior change)
- [ ] Documentation (ADR, README, CLAUDE.md, comment-only)
- [ ] Infrastructure (CI, lefthook, dependabot, audit scripts)
- [ ] Subrepo pull (kotoba / kami-engine-sdk / etc.) — list the upstream commit SHA

## ADR references

<!--
List the ADR(s) this PR implements or amends. ADR IDs are
YYMMDDhhmm under 90-docs/adr/. New ADRs should be in the PR diff.
-->

- ADR-

## Charter Rider compliance (first-party packages only)

<!--
Skip this section if the PR doesn't touch first-party Apache-2.0
code retained by this repository. Standalone packages are checked in their
own repositories. For first-party packages, confirm:
-->

- [ ] CHARTER-RIDER.md present in package root (real file or symlink within the same repo boundary; see ADR-2605192200 + the iter-24/iter-31 subrepo-symlink notes)
- [ ] NOTICE updated if the package's attribution surface changed
- [ ] No third-party-vendored-code introduced under `lib/` / `vendor/` / `*-fork/` (those paths are gitignored from the Rider applicator)
- [ ] No Stripe / PayPal / centralized DB ORM dependencies added (substrate-boundary lint catches these; verify the lint passes locally)

## Test plan

<!--
Bulleted list of how this PR has been verified. Mark `[x]` for items
already done; leave `[ ]` for items the reviewer should re-run.
-->

- [ ] `lefthook run pre-commit` passes (lint + e7m verify + secret scan + …)
- [ ] `lefthook run pre-push --all-files` passes if SDK / cyber-drill paths touched
- [ ] `bash 70-tools/scripts/audit/all.sh` total findings ≤ 25 (current baseline; see audit/README.md)
- [ ] Manual verification: <!-- describe what you ran + what you observed -->

## Out of scope

<!--
Anything deliberately deferred to a follow-up PR. Linking the
follow-up issue / PR is appreciated but not required.
-->

---

<!--
Reminder: religious-corp PRs default to small + reversible. Big PRs
get split. Multi-ADR PRs cite each ADR explicitly. Charter Rider §2
prohibits commercial sponsorship discussions; route those questions
to the Council via the council-bootstrap-* issue templates instead.
-->
