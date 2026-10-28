# Score rights outreach handoff — 2026-10-28

Status: **provider outreach sent / HOLD remains active / no Production authorization**.

## Current repository state

- main: `d3568ddae2426942e914ab4f66a6396df985677a`
- controlling issue: #155 — HOLD
- decision receipt: not completed
- provider/counsel decision: not yet received
- Production authorization: false
- public replacement authorization: false
- real provider evidence authorization: false

## Engineering state already proven

The technical migration path has been demonstrated without changing Production:

- private Development evidence boundary created and rehearsed;
- GitHub OIDC broker write/read path proven;
- aggregate-safe Score transformer proven;
- aggregate-safe research transformers proven;
- broker-downloaded synthetic private bundle accepted by the research adapter;
- locked Score v2 predictive reader compatibility proven;
- locked Score v3 shadow reader compatibility proven;
- both locked readers completed first-week logic with `write=False`;
- frozen research/engine boundaries remained green;
- exactly one synthetic rehearsal object remains in the Development private bucket.

Do not repeat these rehearsals unless a new code change requires it.

## Provider outreach sent

Four provider-specific emails were sent as separate Gmail threads on 2026-10-28.

### S&P Dow Jones Indices

- recipient: `index_services@spglobal.com`
- subject: `USD Impact Score — request for data/derived-output licensing clarification`
- Gmail message/thread: `1a1806f0320cbf6e`

Requested clarification:
- commercial internal use;
- aggregate Score/regime as derived data;
- transformed component values;
- attribution / delayed / historical / redistribution conditions;
- machine-readable vs human-readable treatment.

### Cboe Market Data Services

- recipient: `marketdata@cboe.com`
- subject: `USD Impact Score — VIX-derived output and redistribution licensing clarification`
- Gmail message/thread: `1a1806f08b4ec756`

Requested clarification:
- governing agreement/license;
- aggregate Score/regime publication;
- normalized VIX-derived values and diagnostics;
- machine-readable vs chart/narrative treatment;
- attribution/reporting/distribution requirements.

### CME Group Derived Data

- recipient: `CMEGroupDerivedData@CMEGroup.com`
- subject: `USD Impact Score — derived-data licensing clarification for WTI and Gold inputs`
- Gmail message/thread: `1a1806f1176f6010`

Requested clarification:
- whether the Score is a CME-derived work;
- aggregate Score/regime publication;
- normalized WTI/Gold values and diagnostics;
- machine-readable vs non-machine-readable treatment;
- attribution/licensing/reporting conditions.

### FRED

- recipient: `stlsFRED@stls.frb.org`
- subject: `USD Impact Score — DGS2/DGS10 commercial and derived-output usage clarification`
- Gmail message/thread: `1a1806f193b0a5b3`

Requested clarification:
- ownership/rights status of DGS2 and DGS10;
- commercial internal use;
- transformed values;
- aggregate Score/regime publication;
- machine-readable history/archive restrictions.

## Immediate S&P acknowledgment

An automated S&P DJI response arrived shortly after send.

- message: `1a1806f3f91ec24b`
- subject: `Regarding 01036004 USD Impact Score — request for data/derived-output licensing clarification`
- case/reference: `01036004`
- sender: `no-replyspdjisfdc@spglobal.com`

Treatment:
- **do not record this as rights approval**;
- it states full data services are subscription-based;
- it repeats that Index Data must not be modified, used to create derivative works/derived indices, reproduced or redistributed without prior written consent;
- it directs other inquiries to S&P DJI regional/contact channels;
- sender is a no-reply address, so do not reply to that mailbox.

Next step for S&P:
- wait for a substantive case response if one follows, or route through the official regional/contact channel with reference `01036004`;
- any substantive answer must still be scoped into the decision receipt.

## Yahoo / yfinance status

No Yahoo/yfinance inquiry was sent.

Reason:
- the exact Yahoo service and upstream rights owner governing each yfinance-delivered instrument remain unresolved;
- the accepted routing rule requires that mapping before outreach;
- yfinance documentation itself must not be treated as a license.

Still unresolved:
- DX-Y.NYB;
- CL=F;
- ^GSPC;
- ^VIX;
- BTC-USD;
- GC=F.

Do not send a generic Yahoo inquiry until the exact governing route is identified.

## Response handling protocol

When a provider reply arrives:

1. read the entire thread, including attachments if any;
2. identify the exact responding authority and whether they are authorized to answer licensing questions;
3. record:
   - provider/authority;
   - response date;
   - exact products/series/fields covered;
   - permitted internal use;
   - permitted public use;
   - derived-data treatment;
   - machine-readable treatment;
   - attribution/reporting conditions;
   - historical/archive treatment;
   - agreement/reference number or link;
4. do not generalize permission from one provider to another;
5. do not treat a partial answer as full approval;
6. update the decision matrix and decision receipt only to the scope explicitly supported;
7. keep `production_authorized=false`;
8. keep issue #155 on HOLD until all required provider/counsel dispositions and public-schema approvals are complete.

If a reply is ambiguous, ask a narrow follow-up in the same thread instead of interpreting it optimistically.

## Immediate next-session checks

Start with these checks, in this order:

1. verify current `main` and issue #155 state;
2. search Gmail for replies to the four exact threads above;
3. check for delivery failures/bounces;
4. read any new provider response fully;
5. update #155 with the factual response state;
6. only then decide whether a follow-up question is needed.

## Explicit do-not-cross boundaries

Until a valid decision receipt is completed:

- do not upload real/provider-derived evidence into the private Development bucket;
- do not migrate live research readers to private evidence;
- do not redact or replace current public Score artifacts;
- do not remove historical public archives;
- do not change Score methodology/formula;
- do not close issue #155;
- do not authorize or deploy Production changes;
- do not infer Yahoo/upstream permissions from yfinance.

## Current accepted governance files

- `governance/score-publication-rights-gate.json`
- `governance/score-public-rights-surface.json`
- `governance/score-private-research-migration-contract.json`
- `governance/score-rights-decision-matrix.json`
- `governance/score-rights-decision-receipt.schema.json`
- `governance/score-rights-decision-receipt.template.json`
- `docs/score-provider-counsel-rights-decision-package-2026-10-28.md`
- `docs/score-rights-provider-contact-routing-2026-10-28.md`

## Completion condition for this handoff

This handoff is complete once it is merged to current main with Cloudflare Pages skipped and issue #155 remains HOLD.
