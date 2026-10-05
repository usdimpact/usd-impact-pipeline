# Dependency environment migration — 2026-10-05

## Status

Phase B candidate only. This document does not authorize merge, deployment, a research reset, or acceptance of residual dependency risk.

## Problem

The repository historically used one root `requirements.lock` for online execution, published-release provenance, and frozen prospective research. Updating `urllib3` fixed the online security audit but correctly broke the frozen Score v3 identity and historical bundle checks.

## Separated identities

### Active online runtime

`runtime/active-environment.json` identifies `runtime/requirements-2026-10-05.lock`. Online workflows use that versioned lock. The candidate contains `urllib3==2.8.0`.

Weekly reproduction bundles are built through `scripts/build_runtime_score_repro_bundle.py`, so the dependency hash recorded in a new bundle is the environment actually used to generate it.

### Historical release provenance

`scripts/verify_release_environment.py` resolves an already-published dated archive to the first Git commit that introduced that archive path. It verifies generator-to-publication-to-current ancestry, exact historical bundle bytes, and the dependency lock at the recorded generator revision. A later runtime upgrade does not rewrite earlier publication evidence.

A brand-new release path is instead bound to the active online runtime. Unknown or mismatched identity fails closed.

### Frozen prospective research

The root `requirements.lock` remains byte-bound to the preregistered research engine. It is not installed into the host runner by the prospective workflows.

`scripts/run_frozen_research.py` downloads binary wheels as inert artifacts, records their SHA-256 hashes, builds from the pinned Python 3.11.15 slim-bookworm image, installs those wheels with build networking disabled, and executes the frozen research with runtime networking disabled, read-only container root, all Linux capabilities dropped, no-new-privileges, resource bounds, and a non-root UID.

Only the preregistered append-only research paths can leave the worker. Wheel hashes are retained as a workflow artifact.

## Security status

The patched online dependency audit and CodeQL are expected to pass.

The frozen root lock remains separately audited. Its known `urllib3 2.7.0` advisories are intentionally visible and merge-blocking until the isolation evidence is reviewed and residual risk is explicitly accepted. No advisory suppression or `continue-on-error` exception is part of this candidate.

## Merge boundary

Before any merge:

1. exact-head Weekly score quality must pass;
2. patched online dependency audit and CodeQL must pass;
3. frozen-research isolation tests must pass;
4. historical and new-release reproduction tests must pass;
5. the frozen residual-risk job is expected to remain RED until separately approved;
6. no published bundle/archive, research protocol, holdout boundary, branch rule, secret, provider configuration, customer state, or commerce state may be changed.

A merge remains a separate protected action.
