# Score private evidence handoff prototype — 2026-10-27

Status: **review-only / not wired into Production or weekly research workflows**.

Related: issue #155, design PR #156, public-safe prototype #157.

## Goal

Preserve the frozen Score v2 predictive and Score v3 shadow research contracts while allowing a future public Score schema to remove uncleared provider-derived component values.

The frozen research engines currently expect strict reproduction evidence at paths such as:

- `public/data/score_repro_bundle_latest.json`;
- `public/archive/YYYY-MM-DD/repro_bundle.json`.

Changing those engine paths directly would alter frozen/preregistered research code. This prototype instead preserves their file contract inside an **ephemeral, non-serving worktree**.

## Proposed runner sequence

1. Weekly calculation creates full strict evidence in a private runner location outside the repository/public output tree.
2. The public release emits only the reviewed aggregate-safe artifact.
3. A downstream research job creates a fresh temporary git worktree outside the repository root.
4. The job places the reviewed marker `.private-score-evidence-worktree` in that temporary worktree.
5. `materialize_private_score_evidence.py stage` validates the private strict bundles and stages exact bytes into the legacy paths **inside that temporary worktree only**.
6. The unchanged frozen research ingestion runs against that worktree.
7. The helper's hash-only receipt is retained outside the worktree.
8. `cleanup` verifies every staged file hash before deleting only the receipted evidence.
9. The temporary worktree is destroyed.

## Safety properties

The helper fails closed when:

- private evidence is inside the repository;
- the worktree is the repository or nested under it;
- the worktree lacks an explicit ephemeral marker;
- evidence and worktree are nested;
- latest/archive bytes differ;
- any bundle fails reproduction verification;
- any bundle has the wrong driver set/week;
- a destination evidence file already exists;
- a staged file changes before cleanup;
- the receipt is placed inside repository/worktree/evidence paths;
- receipt writing fails after staging — staged evidence is hash-guard rolled back;
- receipt structure, file hashes, archive count, latest-week archive, or approved destination paths are tampered;
- cleanup is given an arbitrary `public/data/*` path rather than the exact reviewed latest/archive bundle paths.

The receipt contains only paths, SHA-256 hashes, latest week, archive count and contract metadata. It intentionally contains no component values. Cleanup validates the full closed receipt contract before considering any deletion, so a modified receipt cannot expand the deletion surface beyond the exact reviewed Score evidence paths.

## Why archive history is staged

Score v2 predictive validation rechecks prior immutable bundle hashes, not just the latest bundle. Therefore a safe private evidence boundary must preserve every archived strict bundle required by the frozen study, byte-for-byte.

## Non-goals

This prototype does not:

- decide where private evidence is stored;
- create a new cloud bucket/database/secret;
- migrate historical provider-derived Git records;
- modify the frozen research engines;
- modify Score v2 calculation;
- modify public routes;
- modify weekly workflows;
- deploy or delete anything.

A real implementation still requires provider/counsel treatment, an approved private storage/access/retention design, exact-head CI, frozen-research equivalence tests and explicit Production authorization.
