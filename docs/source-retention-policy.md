# Source retention and evidence policy

Last reviewed: 2026-08-24

This is an operational data-governance control, not a legal opinion. It defines what the USD Impact weekly score workflow retains and publishes while provider rights remain source-specific.

## Current provider boundary

- Yahoo market histories are retrieved through `yfinance`. The [yfinance documentation](https://ranaroussi.github.io/yfinance/) states that it is not affiliated with Yahoo and that the Yahoo Finance API is intended for personal use. The workflow therefore does not retain raw Yahoo response payloads or publish complete Yahoo-derived histories.
- The [FRED API terms](https://fred.stlouisfed.org/docs/api/terms_of_use.html) require users to respect each underlying series owner's restrictions. The production Treasury series [DGS2](https://fred.stlouisfed.org/series/DGS2) and [DGS10](https://fred.stlouisfed.org/series/DGS10) are tagged “Public Domain: Citation Requested.” The mixed-source workflow nevertheless applies one conservative rule and does not archive raw provider responses.

## Evidence retained for strict releases

Beginning with the 2026-08-28 strict-release boundary, one live provider fetch creates both the score and its evidence bundle. The public bundle contains:

- the release week's exact levels, calculation moments, z-scores, weights and contributions;
- source, series, observation-date and retrieval-mode provenance;
- SHA-256 fingerprints of the complete production weekly input matrix and each driver; and
- SHA-256 fingerprints of the provider-derived daily matrix and each driver, after field selection and numeric parsing, before calendar forward fill, limited to observations eligible for that score week.

The daily receipt contains hashes and metadata only. It does not contain provider-derived values. The exact weekly handoff and hashes-only daily receipt remain outside the public tree during the run; the runner discards them after the bundle is built.

## Explicit limitations

- Original HTTP response bytes are not hashed.
- Raw Yahoo or FRED response payloads are not archived.
- Complete provider-derived histories are not published.
- A fingerprint can detect that a later reconstruction differs, but cannot recover the earlier values or distinguish every possible cause of the difference.
- These controls are first-party evidence, not an independent audit or a provider attestation.

## Change control before any raw-payload retention

Raw-payload retention must remain disabled unless a separate review documents all of the following:

1. written rights for the intended commercial, archival and audit use;
2. a private storage location with encryption, least-privilege access and no public route;
3. a defined retention period, deletion process and provider-termination response;
4. access logging and incident handling;
5. automated tests preventing payloads from entering Git, Pages artifacts, logs or pull requests; and
6. explicit owner approval for the storage and cost boundary.

Until those conditions are met, cryptographic provider-derived history receipts are the maximum approved evidence layer.
