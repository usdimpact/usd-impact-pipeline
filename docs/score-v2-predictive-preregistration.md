# Score v2 prospective predictive preregistration

Registered: August 25, 2026

First untouched prediction origin: August 28, 2026

Current status: preregistered, not started, no predictive claim authorized

## Question

Does the sign of the as-published USD Impact Score v2 contain directional information about the DXY move from one completed Friday to the next?

This is separate from the Score v3 descriptive study. Score v3 prospectively tests revision immunity, concentration and robustness; it does not test a forecast. This protocol tests one narrow future target and does not change either production model.

Score v2 and the zero-threshold direction rule were selected with knowledge of information available through August 21, 2026. That earlier information is design evidence, not part of the untouched predictive test. Only origins beginning August 28, 2026 can count toward this protocol.

## Frozen prediction and target

- Predictor: the score in the origin week's immutable strict reproduction bundle.
- Rule: score greater than or equal to zero predicts DXY up; score below zero predicts DXY down.
- Target: the log change from the origin bundle's exact DXY weekly level to the immediately following strict bundle's DXY weekly level.
- No abstentions, threshold optimization, substituted outcomes, driver-based exclusions or later-provider recalculations are allowed.

The first origin is August 28, 2026. Its outcome can first be resolved on September 4, 2026. The formal test requires 52 consecutive resolved predictions, which needs 53 weekly bundles and is expected no earlier than August 27, 2027 if no week is missed.

## Decision rule

Meaningful evidence requires every condition below:

1. exactly 52 consecutive, immutable, non-backfilled origin/outcome pairs;
2. directional accuracy of at least 60%;
3. a preregistered circular-shift null-comparison p-value of 0.05 or less, comparing observed accuracy with all 51 non-zero shifts of the locked prediction sequence against the outcome sequence; and
4. accuracy at least five percentage points above the better of the always-up and one-week DXY-momentum comparators.

The 13-, 26- and 39-outcome checkpoints may report integrity only. They may not publish performance values, alter the rule or stop the study because results look favorable or unfavorable.

## Interpretation boundary

A failure means meaningful one-week DXY directional evidence was not established under this protocol. A pass would support only a bounded association in this sample. It would not establish causal power, trading profitability, performance for another asset, probability calibration or durable future accuracy. The evidence remains first-party until independently reproduced or audited.

The complete machine-readable protocol is [`research/score_v2_predictive_preregistration.json`](../research/score_v2_predictive_preregistration.json).
