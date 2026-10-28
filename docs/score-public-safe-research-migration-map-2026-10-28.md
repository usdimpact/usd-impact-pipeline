# Score public-safe research migration map — 2026-10-28

Status: **design/review only; no workflow or public-route change authorized**.

## Current workflow fact

The current `research-validation.yml` writes full research results directly into `public/data/research` before validation and PR creation.

Current full-output generation includes:
- robustness JSON;
- point-in-time JSON;
- vintage-comparison JSON/CSV/HTML.

The same workflow validates provider provenance and component-specific robustness sections, then commits all changed files under `public/data/research` to an automation branch.

Therefore a safe rights migration cannot be implemented by editing only the Pages allowlist. Full component-derived research would still be placed in the public Git worktree/PR.

## Safe insertion boundary

Keep the frozen/reviewed research calculations unchanged, but split **calculation evidence** from **public publication views**.

Future approved sequence:

1. Generate full research results into a runner-private directory such as `$RUNNER_TEMP/score-research-full`.
2. Validate the existing full research contract against those private files, including provenance and component-specific diagnostic checks.
3. Run `scripts/build_score_public_safe_research.py` against the validated full outputs.
4. Validate aggregate-safe outputs independently.
5. Place only the safe outputs under `public/data/research`.
6. Commit only those safe publication views to the protected research PR.
7. Keep or migrate the full research evidence to the approved private evidence boundary if retention is required.
8. Destroy runner-temporary full outputs.

This preserves calculation/research semantics while changing only the publication layer.

## Required workflow refactor if rights treatment is approved

### Generation

Change generator output targets from public paths to runner-private full-result paths.

Do **not** change:
- `score_robustness_battery` calculations;
- point-in-time normalization logic;
- vintage comparison calculations;
- study metadata or preregistration semantics.

### Full-result validation

Move the existing validation assertions to the runner-private full files.

Those validations should continue checking:
- expected week;
- methodology unchanged flags;
- predictive/as-published classifications;
- source freshness/provenance;
- all component robustness sections;
- full vintage row/count consistency.

### Public-safe transformation

After the full contract passes, build:
- aggregate-safe point-in-time JSON;
- aggregate-safe robustness JSON;
- aggregate-safe vintage JSON;
- aggregate-safe vintage CSV;
- aggregate-safe vintage HTML.

### Public-safe validation

Add fail-closed checks for:
- no source provenance/provider/source URL keys;
- no per-driver z/contribution/weekly-level fields;
- no component correlation/contribution sections;
- no per-driver vintage revision structures;
- row counts and aggregate Score/regime values equal the full validated output;
- no unexpected public files.

### PR creation

Change the publication commit step from broad `git add public/data/research` to an explicit allowlist of reviewed safe output paths.

This prevents a future full-result file or debug artifact from being committed merely because it appeared in the directory.

## Vintage dependency

The vintage calculation currently reads public archived `score.json` files.

If historical component JSON is later redacted from the public tree, vintage research must first switch its **input evidence** to the approved private historical boundary while preserving the same as-published bytes/hashes.

Do not recalculate historical vintages from replacement aggregate-only archives and call that equivalent evidence.

## Point-in-time / robustness dependency

The current research readiness step reads `public/data/usd_impact_score_v2.json` to decide whether the weekly upstream is current.

Under a future aggregate-only main Score artifact, readiness may continue to use only the aggregate latest week if that field remains available.

The actual research calculations, however, require the full component history. That input must come from the approved private evidence boundary before public component history is removed.

## Public path transition

Do not remove old allowlisted paths until replacement behavior is explicit.

Two safe migration shapes exist:

**Same URL / narrower payload**
- keep existing public research URLs;
- replace their content with the aggregate-safe views;
- update schemas/tests/documentation to the narrower contract.

**New versioned safe URL**
- publish new aggregate-safe paths;
- update consumer links;
- deprecate/remove old component-derived paths only after verification.

Same-URL replacement minimizes link breakage but is a schema-breaking change. Versioned paths provide clearer contract separation. The final choice requires API/consumer review.

## Health/readiness consumers

Repository search shows current research filenames are referenced by:
- `security/score-public-paths.mjs`;
- README/public-contract documentation;
- `research-validation.yml`;
- branded-domain readiness checks;
- Pages public-only tests;
- vintage HTML tests;
- security/preview documentation.

A production migration must update these references intentionally rather than relying on redirects or compatibility fallbacks.

## No-action record

This map records the future insertion point only. No workflow, generator, research engine, public allowlist, Pages route, archive, deployment or Production configuration was changed.
