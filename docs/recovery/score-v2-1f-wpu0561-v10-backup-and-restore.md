# Score v2.1F / WPU0561: backup and restore playbook (design-only)

**HOLD. Defensive engineering only. Not Production or provider-data backup authorization.**

Research: https://github.com/usdimpact/usd-impact-pipeline/issues/258
Rights: https://github.com/usdimpact/usd-impact-pipeline/issues/155
Draft: https://github.com/usdimpact/usd-impact-pipeline/pull/286

## 1. Verified repository recovery snapshots

Both branches were created from exact commits and compare-verified identical, ahead=0, behind=0.

| Recovery point | Commit (authoritative pin) | Branch (mutable pointer) |
| --- | --- | --- |
| v9 pre-v10 HOLD | 0c420f495e6196d34d195d441edf7b707da4f35a | [v9 backup](https://github.com/usdimpact/usd-impact-pipeline/tree/backup/score-v2-1f-v9-hold-2026-10-29) |
| Initial v10 review draft | 698fb0c0d069c598909cc10e875a28cb711d1ea5 | [v10 backup](https://github.com/usdimpact/usd-impact-pipeline/tree/backup/score-v2-1f-v10-review-2026-10-29) |

These branches reference full committed Git trees. They are not protected immutable tags or off-platform copies. Use commit SHAs as authoritative recovery targets and compare branch pointers to the SHAs before use. They do not back up GitHub repository deletion, external infrastructure, database rows, secrets, email or provider data.

See governance/score-v2-1f-wpu0561-v10-recovery-manifest.json for pinned references and the six exact v9 governance blob hashes.

## 2. Required safeguards

- v9 holds continue to govern until a distinct source-methodology approval.
- Consumed v8 run 40901086765 cannot be repeated; authorization receipt and dispatch marker absent.
- Frozen design v9 and execution contract v21 unchanged; authorization flags all false.
- Previous BLS workflow has an always-false job and no push trigger.
- Publication-rights Issue #155 remains HOLD with no legal disposition.
- No PDF fetch, BLS data request, numeric identifier read, economic-value read, Score computation, source substitution, research-ledger/public write, or Production change.

Any breach means STOP, not automatically retry.

## 3. Safe recovery drill workflow

The new read-only action is .github/workflows/score-v2-1f-wpu0561-recovery-drill.yml.

- Runs on relevant pull-request changes, plus manual workflow_dispatch once available on the default branch.
- GitHub token scope: contents read only. Checkout credential persistence disabled.
- Offline guard checks pinned v9 blob SHA identity, authorizations, consumed receipt, inert workflow, rights HOLD and allowed changed paths.
- Synthetic Git restoration is done inside a throwaway temporary repository only. It proves restoring a broken HOLD file on a *new branch* while retaining unrelated changes.
- Never modifies the checked-out repository, GitHub main, BLS, Vercel, Cloudflare, Supabase, Render or Production.

Run locally or in reviewed CI:

    python3 -m unittest discover -s tests -p 'test_score_v2_1f_wpu0561_recovery.py' -v
    python3 scripts/validate_score_v2_1f_wpu0561_recovery.py --verify-git --drill

A GREEN drill is not proof of a provider-backup or Production restore.

## 4. Restore scenarios and decisions

### A. Draft PR #286 contains an error

Do not merge. Preserve its SHA, read failing checks and source diff. If appropriate, create a new reviewed branch from pinned v10 review SHA and carry over only verified design changes, then open a new PR. Protected main stays at v9. Do not trigger BLS to diagnose a failed design check.

Draft: https://github.com/usdimpact/usd-impact-pipeline/pull/286

### B. An unintended change reaches protected main

Do not force-push/reset main, and do not blindly revert unrelated merges. Record current SHA, affected files, active workflows, receipts/dispatch, and rights state. Create a *new* recovery branch from CURRENT main, restore ONLY the affected v9 governance files from immutable v9 SHA, review the exact diff, then open a restore PR. Verify no legitimate later changes are overwritten.

Illustrative human-run commands for restoring one specific rights file, **not authorized to execute now**:

    git fetch origin main
    git switch -c restore/score-v2-1f-INCIDENT origin/main
    git restore --source=0c420f495e6196d34d195d441edf7b707da4f35a -- governance/score-publication-rights-gate.json
    git diff -- governance/score-publication-rights-gate.json
    git add governance/score-publication-rights-gate.json
    git commit -m "restore(score): reviewed rights HOLD"
    git push -u origin restore/score-v2-1f-INCIDENT

Require a new PR, owner approval, exact-head validate-release, offline recovery drill, CodeQL/security checks and independent rights gate review. Never silently cherry-pick broad commits.

### C. Unauthorized live BLS workflow activates

Stop further work; preserve run logs and commit evidence. Disable the affected workflow in GitHub Actions if necessary. Inspect in-progress runs and stop unsafe outstanding dispatches per incident policy. Disabling a workflow does NOT undo requests already sent.

Through a reviewed recovery PR, restore the inert workflow, remove unauthorized receipt/dispatch files, and verify all authorization flags false. Investigate logs and artifacts separately for any retained economic values. Do not reuse the consumed v8 permission or rerun live tests.

### D. An actual website/Vercel incident occurs

The Score pipeline repository is NOT the site deployment repository. A read-only check on October 29, 2026 observed the usd-impact-site project under team usd-impact with a READY Production deployment:

- Deployment ID: dpl_4n1dptumsQM544KnVSkUHRUCpkmV
- Commit: 06e185d39b4768e1f2ab8aeabccd63b531bf1435
- Inspector: https://vercel.com/usd-impact/usd-impact-site/4n1dptumsQM544KnVSkUHRUCpkmV

This is an observed historical deployment, **NOT an approved rollback target** and NOT proof it still serves the domain. Before any restoration, recheck the team/project, current deployment and candidate, consider any changes since that commit, test impact, and obtain separate Production approval. Vercel rollback can disable automatic domain assignment; restore promotion/assignment deliberately only after QA.

Cloudflare Worker versions, Supabase backups/PITR, Resend email sends, Render and external provider data have NOT been backed up or restored here. Those require their own provider-specific inventory, retention, permissions and independent restoration tests. No automatic infrastructure rollback is configured.

## 5. Failure handling and restore acceptance

When the offline recovery job fails, keep the methodology PR in draft and no live authorizations. Compare the exact current diff against v9, verify the two backup refs and protected files, and review whether rights, auth receipts, BLS workflow or gate flags drifted. Never weaken or remove a guard simply to pass CI.

For real off-platform disaster recovery, independently archive a verified, access-controlled Git bundle or clone and provider-native backups. **This work creates two GitHub snapshot branches, not an off-platform backup.**

## 6. Approval scope

Owner approved methodology **design only**, scoped to the official April 2026 archived BLS PDF candidate, plus defensive recovery preparation. This does not authorize fetching the PDF, reading identifier or economic data, modifying Score or public artifacts, approving Issue #155 rights, merging the current PR, or rolling back a provider. A new separate authorization is required at each subsequent gate.

## 7. v11 PDF preflight abort and restore (future design only)

A new **inert design** lives at governance/score-v2-1f-bls-wpu0561-pdf-structural-preflight-v11-design.json. A separate synthetic-only validator and 34 refusal/contract tests are included in the PR recovery workflow. This does not grant any live data access.

### Before any future activation (not currently authorized)

1. Verify both pinned recovery branches against their immutable commit hashes; preserve the current protected-main SHA and exact reviewed PR SHA.
2. Verify Issue #155 rights HOLD, previous v8 consumption, v9 frozen blob hashes, and that there is no active receipt/dispatch.
3. Separately resolve the BLS April 2026 PDF first-release provenance, same-series WPU0561 label and index schema, parser dependency pin and whether parser exposure to raw economic bytes is permitted.
4. Register exact one-off BLS GET permission in an explicit new reviewed versioned contract. Do not treat the v11 proposal's planned **one GET** as current authorization.
5. Before a future dispatch, validate hard network limits, logging boundaries, request stop conditions, secure runner and mandatory irreversible consumption semantics.
6. No runtime is created by this PR. The published PDF itself was not fetched; no hash, page count or index observation has been verified.

### If a hypothetical future live preflight fails

- **STOP** without retries, redirect following, alternate sources, page-limit widening or replacement of the target series.
- Disable dispatch and preserve the immutable commit/run audit trail.
- Treat authorization as consumed even if transport or parsing fails; never rerun the same permission.
- Remove any active receipt/dispatch through a reviewed cleanup PR and leave v9 authoritative.
- Inspect GitHub logs/artifact leakage separately. Deleting an artifact later does not negate previous access or transfer.
- Any economic-value exposure requires a separate documented incident review; restoring Git cannot recall downloaded data.
- The rollback procedure restores only reviewed repository files through a new PR. It does not reverse external HTTP requests, fix downstream provider data, or roll back Production.
- Revalidate recovery guard, synthetic PDF refusal tests, CodeQL, dependencies and validate-release on exact corrective-PR head.

**Execution gate still closed:** no numeric identifier/economic-value reads, PDF GET, Score v2.1F, research ledger or public writes. The recovery branch/manifest protect the Git state but are not independent offsite snapshots.
