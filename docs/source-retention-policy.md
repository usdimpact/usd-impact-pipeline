# Source retention and evidence policy


Last reviewed: **2026-10-29** (earlier baseline: 2026-08-24).

**Operational status:** **RIGHTS / PUBLICATION HOLD** — [Issue #155](https://github.com/usdimpact/usd-impact-pipeline/issues/155); [Issue #282](https://github.com/usdimpact/usd-impact-pipeline/issues/282). This document defines engineering safeguards, **not** a legal opinion, provider permission, retrospective determination, or authorization to resume provider fetching, release public artifacts, create new real-provider storage, or erase existing evidence.

## Binding current interpretation — supersedes August 24 baseline

### Source owner, delivery service, instrument and right are distinct

A `Public Domain: Citation Requested` tag for a particular Treasury series is **not** a global permission for every act of storage, redistribution or historical research. Treat **DGS2** and **DGS10** at three layers:

- **Originator:** U.S. Treasury for nominal Treasury yields (H.15 attributes the underlying yields to Treasury).
- **Republisher:** Federal Reserve Board H.15, subject to its own notices and source-specific exceptions.
- **Delivery:** Federal Reserve Bank of St. Louis FRED, subject to **FRED Services** terms, separate **FRED API** terms, underlying copyright tags and source attribution.

FRED's 2026-10-29 reply recognizes the described commercial processing of FRED series **specifically tagged public domain**, conditional on citations and compliance with its terms, **with disposal after use**. It expressly does **not** permit retention/storage. The reply is private correspondence and must not be reproduced or attributed to the Federal Reserve in public marketing or GitHub. The [FRED Services terms (verified 2026-10-29)](https://fred.stlouisfed.org/legal/terms/) separately address **Services (p) AI/ML development or training**, **Services (q) storage/caching/archiving**, and **Services (r) modifying/copying/distributing/derivative works**. Additional **FRED API (k) AI/ML development or training** and **API (l) storage/caching/archiving** restrictions apply when the API is used. Clause labels refer to the current online version, not a historical agreement. The FRED API also has applicable non-endorsement notice and attribution requirements; verify scope before any authorized use. A permitted transient processing scenario is **not** a waiver of these other terms or upstream rights.

Yahoo Finance / `yfinance` delivery, ICE-linked DXY, S&P DJI S&P 500, Cboe VIX, CME WTI/Gold futures and any BTC input must be reviewed separately by product/underlying owner, commercial internal calculation, public aggregate, component-derived release, historical retention, and permitted transport. An absence of affirmative permissions is **PENDING/HOLD**, not a finding that any historical use was unlawful.

### What the existing Score actually contains

The August 24 statements below are retained **as historical policy text**, not current assertions that public artifacts contain no derived history.

- No raw provider **HTTP response payloads** are known to have been intentionally committed by the Score release workflow; this does **not** establish that provider **values or transformations** were absent.
- `public/data/usd_impact_score_v2.csv` and `.json` contain multi-year, per-driver **normalized z-score** history (617 weeks in the audited edition). They are public machine-readable derived information.
- `public/data/weekly_input_latest.json` and dated `weekly_input.json` contain driver-level current z-scores, weights, contributions and source metadata.
- `public/data/score_repro_bundle_latest.json` and dated `repro_bundle.json` contain release-week provider-derived levels, normalization moments, z-scores/contributions and provenance. A hash-only **daily fingerprint section** does **not** make the **entire bundle** free of provider-derived numeric content.
- `public/data/research/` includes Class D/E/F aggregate and component-derived diagnostics requiring separate review. Both Git tree and served Pages origins may expose information; access gates on premium HTML do not hide raw Git blobs.
- The 2026-10-29 metadata audit found **27** dated Score archive directories containing **50** dated Class C files plus **four** current Class C artifacts, **15** root `data/weekly_input_*.json` Git-only bridge files and historic EN/ES HTML. These are current-tree path counts, not approval or full historical/cached-copies coverage.
- `usd_impact_score_v2.py` has runner-local matrices/fingerprints, a non-web local parquet cache pathway and web-mode local/stdout logging (including some per-driver normalization statistics). GitHub workflow logs, caches, historical commits and backups require review; a temporary runner file being deleted is not proof of legal disposal of its content across all persistence surfaces.

### Fail-closed handling, with no retrospective purge

1. **Do not fetch fresh Score provider observations or publish new component-level Score artifacts** while `governance/score-publication-rights-gate.json` has `state=hold` or lacks a properly authorized receipt. Eight inventoried rights-controlled workflows now require an explicit `hold == 'false'` before live processing; manually invoked/external paths still require their own audit.
2. **Do not create new retained real-provider datasets, private replicas, caches, backup copies or training sets** based on the synthetic-only Development Storage approval. `governance/score-private-research-migration-contract.json` still denies real evidence, public replacement and Production change.
3. **Classify output by substance**, not filename: original response, daily/weekly level, transformed z-score, normalization moment, contribution, aggregate score/regime, vintage comparison, provider identifier, non-value-bearing receipt. Source/transport-specific rights and non-reversibility must be decided for each class.
4. **No AI/ML training on FRED-delivered content** without a separately reviewed, applicable permission. Do not mistake ordinary Python arithmetic in Score for AI training, but audit any genuine ML systems before use.
5. **Cite both FRED and original source** when/if covered FRED usage is permitted. The exact acceptable citation, retrieval date and series label must reflect the actual source; a citation alone does not authorize retention, redistribution or derivative publication.
6. **Preserve incident/audit metadata without making new unauthorized content copies**. Before any redaction, history rewrite, cache purge, production replacement or provider-data migration, obtain provider/counsel disposition on historical treatment, lawful preservation boundary, consumer compatibility and reversible, legally safe rollback. An existing public copy is not automatically permission to duplicate it.
7. A future approved aggregate-safe public schema may keep week, aggregate Score/regime and aggregate history **only after** provider/counsel and owner release review. Passing synthetic transformer/research tests is technical evidence, **not** a publication license.
8. Check the written decision receipt and source-specific scope (commercial processing, FRED transport, in-memory lifetime, logging, retention, attribution, public derivative fields, backups, termination and historic treatment). **Never infer an ALLOW from silence, earlier public visibility, or missing validation output.**

### Evidence and decision references

- [Issue #155 — rights HOLD](https://github.com/usdimpact/usd-impact-pipeline/issues/155)
- [Issue #282 — FRED retention/source audit](https://github.com/usdimpact/usd-impact-pipeline/issues/282)
- [Current archive metadata/preservation inventory](score-public-archive-metadata-preservation-2026-10-29.md)
- [Provider/counsel decision package](score-provider-counsel-rights-decision-package-2026-10-28.md)
- [FRED terms](https://fred.stlouisfed.org/legal/terms/) and [Treasury XML feed documentation](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed)

## Historical 2026-08-24 baseline (retained for audit; superseded where conflicting)

This is an operational data-governance control, not a legal opinion. It defines what the USD Impact weekly score workflow retains and publishes while provider rights remain source-specific.

### Current provider boundary (August 24 historical claim)

- Yahoo market histories are retrieved through `yfinance`. The [yfinance documentation](https://ranaroussi.github.io/yfinance/) states that it is not affiliated with Yahoo and that the Yahoo Finance API is intended for personal use. The workflow therefore does not retain raw Yahoo response payloads or publish complete Yahoo-derived histories.
- The [FRED API terms](https://fred.stlouisfed.org/docs/api/terms_of_use.html) require users to respect each underlying series owner's restrictions. The production Treasury series [DGS2](https://fred.stlouisfed.org/series/DGS2) and [DGS10](https://fred.stlouisfed.org/series/DGS10) are tagged “Public Domain: Citation Requested.” The mixed-source workflow nevertheless applies one conservative rule and does not archive raw provider responses.

### Evidence retained for strict releases (August 24 historical claim)

Beginning with the 2026-08-28 strict-release boundary, one live provider fetch creates both the score and its evidence bundle. The public bundle contains:

- the release week's exact levels, calculation moments, z-scores, weights and contributions;
- source, series, observation-date and retrieval-mode provenance;
- SHA-256 fingerprints of the complete production weekly input matrix and each driver; and
- SHA-256 fingerprints of the provider-derived daily matrix and each driver, after field selection and numeric parsing, before calendar forward fill, limited to observations eligible for that score week.

The daily receipt contains hashes and metadata only. It does not contain provider-derived values. The exact weekly handoff and hashes-only daily receipt remain outside the public tree during the run; the runner discards them after the bundle is built.

### Explicit limitations (August 24 historical claim)

- Original HTTP response bytes are not hashed.
- Raw Yahoo or FRED response payloads are not archived.
- Complete provider-derived histories are not published.
- A fingerprint can detect that a later reconstruction differs, but cannot recover the earlier values or distinguish every possible cause of the difference.
- These controls are first-party evidence, not an independent audit or a provider attestation.

### Change control before any raw-payload retention (August 24 historical claim)

Raw-payload retention must remain disabled unless a separate review documents all of the following:

1. written rights for the intended commercial, archival and audit use;
2. a private storage location with encryption, least-privilege access and no public route;
3. a defined retention period, deletion process and provider-termination response;
4. access logging and incident handling;
5. automated tests preventing payloads from entering Git, Pages artifacts, logs or pull requests; and
6. explicit owner approval for the storage and cost boundary.

Until those conditions are met, cryptographic provider-derived history receipts are the maximum approved evidence layer.
