## Objective

Describe the user-visible or safety outcome.

## Evidence

- Baseline:
- Tests and checks actually run:
- Checks not run:
- Expected artifacts:

## Safety and scope

- [ ] The change is typed, capability-scoped, auditable, time-bounded, and reversible.
- [ ] Runtime behavior remains simulation-only unless a separate human approval path is documented.
- [ ] No model-produced free-form shell executes on the host.
- [ ] No secret, credential, personal data, or hidden test is included.
- [ ] Rollback and failure behavior are explicit.
- [ ] New or changed dependencies are pinned or constrained and their licenses were reviewed.

## Protected files

- [ ] This PR does not modify the TCB, safety constitution, foundational policies, audit, rollback, or security workflows.
- [ ] If it does, a human owner reviewed the full diff and applied the human-reviewed-protected-change label.

## Independent verification

Name the verifier or explain why verification is still pending. The mutation producer cannot be its sole verifier.
