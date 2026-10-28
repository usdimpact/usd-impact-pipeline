# Score public containment current-main integration — 2026-10-28

Status: **review-only / no public-route, workflow, archive, deployment or Production change**.

Related:
- issue #155 — rights / redistribution HOLD;
- merged #159 — fail-closed publication/research HOLD on `main`;
- draft #161 — current private-evidence source integration candidate;
- historical drafts #156 and #157.

## Purpose

Refresh the public-containment work onto current HOLD-enabled `main` without carrying forward the older private-evidence prototype that #161 has superseded.

This branch combines:

1. the rights evidence, public-surface inventory, provider-contact/question pack, consumer impact and historical-archive treatment work from accepted #156 head `596043c89efb3154a4db017fc3092bc3f8ccf9f4`;
2. the aggregate-only public Score artifact and aggregate-only research publication transformers/tests from accepted #157 head `d209b6feeda697acfb65de575af550122061bf41`.

## Deliberately omitted from #157

The following #157 files are **not** carried into this branch:

- `scripts/score_private_evidence_source.py`;
- `tests/test_score_private_evidence_source.py`;
- `scripts/rehearse_score_rights_containment.py`;
- `tests/test_score_rights_containment_rehearsal.py`;
- `docs/score-private-evidence-consumer-map-2026-10-27.md`.

Reason: #161 is now the reviewed current-main private-evidence boundary. Keeping the older adapter here would create two competing private-evidence implementations.

## Public-safe artifact layer

Carried unchanged from #157:

- `schemas/score_public_safe.schema.json`;
- `scripts/build_score_public_safe_artifact.py`;
- `tests/test_score_public_safe_artifact.py`.

The transformer preserves aggregate Score/regime publication while rejecting public output containing:
- provider source/provenance;
- provider tickers/URLs;
- weekly source levels;
- per-driver z-scores;
- contributions;
- normalization moments.

It is not wired into weekly publication.

## Public-safe research layer

Carried unchanged from #157:

- `scripts/build_score_public_safe_research.py`;
- `tests/test_score_public_safe_research.py`;
- public-safe research prototype/migration documentation.

The intended future architecture remains:

1. full/frozen research calculations operate against approved private evidence;
2. existing full research contract is validated privately;
3. aggregate-safe publication views are generated only after validation;
4. only approved safe publication paths are committed publicly.

It is not wired into `research-validation.yml`.

## Current main safety state

Merged #159 is already active on `main`:

- Score publication rights gate state: `hold`;
- new weekly component-level publication is stopped before provider retrieval/generation;
- research publication is stopped before live generation;
- recovery is held;
- health recognizes the governance HOLD rather than creating false stale incidents.

This branch does not alter that gate.

## Source preservation

The copied #156/#157 files should retain their source Git blob SHAs. A review mismatch is a defect.

No historical research branch, archive, public artifact or evidence hash is rewritten by this integration.

## Required order before any public migration

1. Keep issue #155 open until rights treatment is documented.
2. Complete the separately authorized #161 Development private-evidence rehearsal if the internal-retention path is approved.
3. Confirm counsel/provider treatment for aggregate Score/research publication.
4. Choose the public URL migration strategy:
   - same URL with narrower schema, or
   - new versioned aggregate-safe URLs.
5. Update `usd-impact-site` methodology/About/Score/replication consumers in a separate site PR.
6. Update pipeline public allowlist and research publication workflow in a separate reviewed PR.
7. Run exact-head CI, anonymous-origin checks and non-Production Preview.
8. Obtain separate Production authorization.

## Manual decision gates

No manual action is needed to review or test this branch.

Manual/owner action becomes mandatory only for:
- provider/counsel rights disposition;
- provisioning the #161 Development private-evidence infrastructure/rehearsal;
- any merge that changes public serving or Production behavior.

Record the rights decision on issue #155 so the gate has an auditable source of truth.

## No-action record

This integration does **not**:
- change Score v2 calculations;
- change public Score/research files;
- change Cloudflare/Pages routing;
- change the public allowlist;
- change the website;
- provision private storage;
- deploy an Edge Function;
- add a secret;
- enable OIDC;
- alter signup, billing, newsletter sending or Production.
