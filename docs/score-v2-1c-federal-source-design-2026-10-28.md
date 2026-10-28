# Score v2.1C rights-minimized federal-source alternative — 2026-10-28

Status: **design only / public-evidence rights review only**.

## Objective

Reduce the number of proprietary or Reserve-Bank-copyright dependencies in the zero-budget Score alternative.

This candidate is separate from v2.1B. The v2.1B preregistration remains immutable.

## Rights evidence

### Federal Reserve Board

The Board's website disclaimer states that, unless otherwise indicated, information on its website is in the public domain and may be copied and distributed without permission, with citation requested.

This makes direct Board outputs a materially cleaner starting point than proprietary index feeds.

It does not remove the need to check each series for third-party exceptions.

### EIA

EIA explicitly states that U.S. government publications are public domain and that its data, files, databases and other information products may be used and distributed. EIA requests acknowledgment.

### Office of Financial Research

OFR states that no copyright may be claimed for works created by federal employees in the course of their duties, while separately warning that third-party copyrighted material remains protected.

## Candidate architecture

| Slot | Proposed official source | Candidate transform |
|---|---|---|
| USD | Board H.10 broad dollar index | level |
| Energy | EIA WTI Cushing spot | log level |
| Financial conditions | Board FCI-G | level |
| Financial stress | OFR FSI | level |
| Liquidity | Board WALCL | 13-week log change |
| Real yield | Board DFII10 | level |
| 2Y | Board DGS2 | level |
| 10Y | Board DGS10 | level |

## Why NFCI is removed from this candidate

The Chicago Fed legal notice states that most Bank-created materials are protected by copyright and that uses beyond its noncommercial reproduction permission require written permission.

That does not mean NFCI can never be used. It means NFCI is not the best fit for a **zero-friction rights-minimized** architecture.

## Why STLFSI4 is removed from this candidate

FRED currently labels STLFSI4 as copyrighted/citation-required. FRED terms provide useful commercial-use permissions for some citation-required series, but the exact public derived/machine-readable scope of our intended aggregate Score is less explicit than the federal-source alternatives.

So v2.1C uses OFR FSI instead.

## Important caveat: federal output can still depend on private inputs

FCI-G is a Board-produced index, but its published methodology references several private-source inputs. OFR FSI likewise uses financial-market variables.

The engineering posture is therefore:

- treat the **published federal index output** as the candidate series;
- do not ingest or redistribute the proprietary underlying components;
- verify that no series-specific notice overrides the federal public-domain default;
- keep public Score delivery aggregate-safe;
- do not claim legal approval from this evidence review.

## Frequency consequence

The main tradeoff is FCI-G frequency.

FCI-G is monthly, so a weekly Score would carry forward the latest **published** monthly value, with a maximum age of 45 calendar days.

This creates a slower financial-conditions channel than NFCI and must be evaluated separately before any methodology decision.

## Current disposition

v2.1C is the strongest rights-minimized conceptual candidate so far, but it is not authorized for real-data research.

Next work may document direct official endpoints, release/vintage behavior and series-specific exceptions. No real data should be fetched until separately authorized.
