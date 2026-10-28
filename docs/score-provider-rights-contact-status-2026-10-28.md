# Score provider-rights contact status — 2026-10-28

Status: **review evidence only / no-send / no Production authorization**.

Related:
- issue #155 — Score v2 public redistribution HOLD;
- PR #156 — rights-safe containment design;
- PR #157 — aggregate-only public artifact prototype;
- PR #158 — ephemeral private-evidence handoff prototype;
- PR #159 — fail-closed publication/research HOLD candidate.

## Read-only evidence review

A read-only review of the connected USD Impact Gmail and Google Drive sources was performed on 2026-10-28 to determine whether any provider or counsel evidence already resolves the Score v2 component-data rights question.

### Current result

No inbound written authorization was located that permits the current public Score v2 component-level redistribution for:

- ICE / DXY;
- Cboe / VIX;
- S&P Dow Jones Indices / S&P 500;
- CME Group / WTI or Gold futures;
- Yahoo / Yahoo Finance transport and downstream component redistribution.

No counsel opinion was located that overrides issue #155 or approves the existing public component schema.

## Existing outreach evidence

### ICE

An outbound licensing inquiry exists for an ICE index-data educational use case. The reviewed mailbox contains the sent inquiry but no inbound written permission.

That inquiry is not specific enough to be treated as approval for Score v2 DXY component publication, and no response was located that grants such rights.

Disposition: **HOLD / no permission evidence found**.

### Cboe

An outbound closure message exists for the earlier VIX licensing inquiry. USD Impact stated that it did not have budget for paid market-data licensing and would not republish restricted data without necessary permission.

The reviewed mailbox did not contain a usable provider authorization for public VIX-derived Score fields.

Disposition: **HOLD / no permission evidence found**.

### S&P Dow Jones Indices

No usable inbound licensing or permission correspondence was located for Score v2.

Disposition: **HOLD / no permission evidence found**.

### CME Group

No usable inbound licensing or permission correspondence was located for Score v2 WTI/Gold component publication.

Disposition: **HOLD / no permission evidence found**.

### Yahoo / Yahoo Finance

No usable commercial redistribution permission was located for the current Yahoo-delivered Score inputs or their public transformations.

Disposition: **HOLD / no permission evidence found**.

## Internal legal-workflow evidence

The existing USD Impact legal/publishing checklist explicitly requires:

- a rights-clearance spreadsheet/process;
- separation of official/public data from protected third-party content;
- permission review for ICE, FRED, index providers and other market-data sources;
- preference for internally recreated outputs only from data whose use rights are permitted.

That document is a lawyer work pack, not legal advice, and does not itself grant rights.

Engineering implication: the current issue #155 containment direction remains consistent with the project's pre-existing legal workflow.

## Engineering conclusion

This review found **no evidence basis to relax the Score HOLD**.

Continue with:

1. aggregate-only public-schema planning;
2. private evidence containment;
3. no expansion of component-level public data;
4. no deletion of historical public artifacts until archive treatment is decided;
5. provider/counsel review before any resume decision;
6. separate Production authorization even after rights are resolved.

Do not treat absence of a reply as permission.

## Privacy boundary

This repository record intentionally omits:

- private message IDs;
- private mail headers;
- personal correspondence metadata;
- credentials;
- attachment contents;
- non-public legal records.

Only the engineering-relevant disposition is recorded.
