# Score private-evidence migration pattern — 2026-10-27

Status: **review-only design; no private storage provider selected**.

## Constraint

The frozen Score v2 predictive and Score v3 shadow engines were preregistered against strict reproduction bundles at legacy paths such as:

- `public/data/score_repro_bundle_latest.json`;
- `public/archive/YYYY-MM-DD/repro_bundle.json`.

Changing those engine paths directly would alter frozen research code and its engine-lock hashes.

## Preferred migration

Keep the frozen engine code unchanged and change the **runner filesystem**, not the research algorithm:

1. checkout current research code into a temporary worktree;
2. obtain the authorized strict evidence through a future approved private evidence channel;
3. stage the exact evidence bytes into the legacy paths inside the temporary, non-serving worktree;
4. execute the unchanged locked research engine;
5. verify expected research outputs / engine lock;
6. hash-guard cleanup of staged evidence;
7. destroy the temporary worktree.

Prototype: draft PR #158.

## Why this preserves research integrity

- no path constant in the frozen engine changes;
- no computation rule changes;
- no source value is reconstructed after outcomes are visible;
- original strict bundle hashes can remain the source identity;
- prior predictive records can still validate exact historic bundle hashes;
- public website paths no longer need to carry the strict evidence.

## Remaining unsolved dependency

A real implementation still needs an approved place from which the CI runner obtains historic strict evidence. That mechanism must define:

- access control;
- service identity;
- encryption at rest/in transit;
- retention;
- immutable versioning;
- deletion/legal-hold behavior;
- audit logging;
- cost/operational ownership;
- how old research weeks remain retrievable without putting values back in Git/public web.

No storage vendor, bucket, database, secret, credential or billing change is selected by this design.

## Historical Git evidence

Moving future strict evidence private does not erase existing public Git history or already published archives.

Historical treatment remains a separate decision:
- retain under documented permission; or
- withdraw current web routes while preserving audit history; or
- replace served artifacts with aggregate-only records plus a dated transparency notice.

Do not rewrite Git history as a substitute for a rights decision.
