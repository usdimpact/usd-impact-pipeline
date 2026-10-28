# Score v2.1E real-data research authorization packet — 2026-10-28

Status: **HOLD / preparation only**.

## Purpose

The v2.1E methodology and preregistration are complete enough that the next meaningful technical step would involve real Board/BLS observations.

This packet defines the approval boundary before that happens.

It does **not** authorize the run.

## Exact frozen research candidate

The future one-off study, if separately approved, is limited to the eight direct series already frozen by v2.1E:

- H10/H10/JRXWTFB_N.B
- WPU0561
- H8/H8/B1001NCBA
- H41/H41/RESPPALDP_N.WW
- H41/H41/RESPPA_N.WW
- H15/H15/RIFLGFCY10_XII_N.B
- H15/H15/RIFLGFCY02_N.B
- H15/H15/RIFLGFCY10_N.B

No substitute, proxy or ninth source can enter the study under the same authorization.

## What a future approval would authorize

Only a **one-off private research run**.

It may:
- fetch the eight exact public federal series from direct official Board/BLS endpoints;
- reconstruct historical release/vintage eligibility;
- apply the already-preregistered transformations and point-in-time normalization;
- compute the already-preregistered diagnostics and acceptance gates.

It may not:
- purchase data;
- accept provider contracts;
- use paid APIs or credentials;
- mutate the public Score;
- write component/source values to the public repository;
- mutate existing research ledgers;
- activate a methodology;
- deploy to Production.

## Storage rule

The default first-run authorization is deliberately strict:

- source values: ephemeral only;
- raw responses: ephemeral only;
- temporary workspace: isolated and non-public;
- durable private storage: not authorized.

Persistent outputs are restricted to aggregate diagnostics, gate results, coverage statistics, correlation/redundancy statistics, release-vintage identifiers, and non-value-bearing hashes.

This allows a first research decision without creating another durable data-rights surface.

## Approval receipt

The repository currently contains only a **HOLD template**.

The active receipt path is reserved as:

`governance/score-v2-1e-real-data-research-authorization.json`

That file does not exist in the authorized state today.

A later owner decision must create it through a separate reviewed change. The receipt must bind:
- exact methodology version;
- design merge commit;
- preregistration merge commit;
- exact eight series;
- explicit research date window;
- private one-off scope;
- storage/output restrictions;
- owner identity and approval timestamp.

Production remains hard-coded false even in an approved research receipt.

## Fail-closed execution contract

Any future runner must stop if:
- the active receipt is absent;
- the receipt does not validate;
- the data window is missing;
- a source is paid or credentialed;
- a source resolves outside Board/BLS official endpoints;
- historical BLS/H.8 vintage reconstruction is not conservative and reproducible;
- release timing cannot be established;
- a ninth/replacement series is introduced;
- raw/component data persistence is requested.

## Current state

- Real-data fetch: **not authorized**
- Real-data research: **not authorized**
- Paid data: **not authorized**
- Public replacement: **not authorized**
- Research-ledger mutation: **not authorized**
- Production: **not authorized**

Issue #155 remains HOLD.
