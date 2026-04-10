# Weekly Regime Commentary — Operator Guide

Your 30-minute Friday routine for writing the weekly Regime Commentary that accompanies each USD Impact Score release.

This is the scarce layer of the project. The pipeline produces a number automatically; the commentary produces the *read* of what that number means against the specific shape of the current week. Readers subscribe to the commentary, not the number.

---

## The routine (Friday evening or Saturday morning UTC)

**Time budget:** 30 minutes, no more. If you find yourself spending longer, you are overthinking it. The commentary is disciplined, not exhaustive.

**Step 1 (5 min).** Visit your live dashboard at the canonical URL. Read the current score, regime label, and the week-over-week change. Look at the eleven-year chart and ask one question: *is this week a continuation of the previous regime, a transitional week, or the beginning of a shift?* Write that one-sentence answer at the top of a scratch document. This is your anchor.

**Step 2 (5 min).** Open the CSV at `public/data/usd_impact_score_v2.csv` in your repo (just click it on GitHub — it renders as a table). Look at the z-scored components for the most recent week. Which of the eight inputs are pulling the score in the direction it currently sits? Identify the two or three dominant drivers and write them down. This is your *why*.

**Step 3 (15 min).** Open the template below and fill in each section. The template has five short sections and a methodology footer. Do not add sections. Do not remove sections. Consistency of format every week is the product.

**Step 4 (5 min).** Save the file as `commentary/latest.md` in your local clone of the repo (or create it directly via GitHub's web editor). Commit with the message `Regime Commentary — YYYY-MM-DD`. Push. The next scheduled pipeline run — or a manual re-run via Actions — will render it into the dashboard. Done.

---

## The template

Copy this entire block. Replace the bracketed placeholders. Keep the section headings exactly as shown so the dashboard renders them consistently.

```markdown
# Regime Commentary — Week of [Month Day, Year]

**USD Impact Score: [signed score, 2 decimals]  |  [Regime label]**

[Optional one-sentence introduction if the week is unusual. Skip this
paragraph entirely on routine continuation weeks — a commentary that is
short and steady is more valuable than one that is long and performative.]

## What the score is saying

[2-3 sentences. State where the score sits in historical context. Is this
week continuous with the previous weeks, transitional, or a clear shift?
Reference the eleven-year chart if a direct historical analog exists
(mid-2019 pivot, 2020 two-phase, 2022 tightening, etc.). Do not predict.
Describe the regime's position and character.]

## What is driving the reading

[3-4 sentences. Name the 2 or 3 dominant inputs pulling the score. Use
the transmission-channel language from the book: real-yield channel,
liquidity channel, stress channel, opportunity-cost channel, supply
channel. If one input is unusually large in magnitude, call it out.
Readers who have read the book will recognize the channel names.]

## What the score is not saying

[2-3 sentences. The framework does not forecast. State plainly what this
week's reading does and does not imply. This is the via-negativa section
and it is the most important section because it establishes the
commentary's discipline. The absence of a prediction is the product.]

## What to watch over the coming week

[3-4 sentences. Name 2 or 3 specific things to watch: a specific data
release, a specific policy meeting, a specific asset's behavior, a
specific threshold where the score would flip. Tie each watch item to a
transmission channel if possible. Readers should finish this section
knowing what to pay attention to next Friday.]

## Methodology reminder

The USD Impact Score is computed from eight cross-asset inputs — DXY,
WTI, S&P 500, VIX, Bitcoin, gold, 2-year Treasury yield, 10-year
Treasury yield — z-scored against full-sample history, clipped at ±3.5
standard deviations, and combined with fixed transmission-logic weights.
The score runs on the same data and the same weights every week. No
fitting, no parameter tuning, no look-ahead. The eleven-year backtest
published in Chapter 10 of the book produced an aggregate hit rate of
84.5 percent across five anchor regimes, with three of those five
regimes identified at 100 percent accuracy. The backtest is reproducible
by anyone willing to run the open pipeline against the same data
sources.

---

*Regime Commentary is educational and informational. It is not
investment advice, not a trading signal, and not a recommendation to buy
or sell any security, commodity, currency, or digital asset. Historical
results do not indicate future results.*
```

The methodology paragraph and the compliance disclaimer are identical every week. Do not rewrite them. They establish the commentary's regulatory posture and the consistency signals to readers that the framework is not changing underneath them.

---

## Voice rules

- **No hype.** The word "bombshell" and its cousins never appear. The framework is steady; the voice matches.
- **No predictions.** Use "consistent with", "the reading sits in", "the structure suggests" — never "will", "should", or "is likely to".
- **No trade calls.** Never name an asset alongside a buy or sell. Name the channel, not the trade.
- **No emojis, no exclamation points, no all-caps.** This is an investor education product, not a newsletter personality.
- **Present tense for the current reading. Past tense for historical context. Conditional for forward-watching.** "The score sits at −0.80. In 2019 the same level accompanied a Fed pivot. If real yields compress further next week, the reading would deepen."
- **Use the book's vocabulary.** Transmission channels, regime, dollar as infrastructure, hurdle rate, opportunity cost, via negativa when relevant. Readers who have read the book will recognize the through-line.

---

## Length discipline

- **Minimum:** 350 words
- **Target:** 500 words
- **Maximum:** 750 words

If you hit 750 and have more to say, that material is a candidate for a longer monthly essay — not this week's commentary. Weekly commentary is a disciplined format and its value comes from being the same size every week. Readers develop a Friday routine around a predictable thing; the predictability is the product.

---

## Spanish translation policy

**Canonical:** English. You write the commentary in English every week without exception.

**Spanish:** Optional per week. If you have time and want to translate, save the Spanish version as `commentary/latest_es.md`. The dashboard's Spanish page will use it automatically.

**If no Spanish translation exists for a given week**, the dashboard's Spanish page falls back to showing the English commentary rather than leaving a dead zone. This is intentional: Spanish visitors get content rather than emptiness. You can decide each week whether to add Spanish based on time available.

Do not skip English to do Spanish instead. English is the canonical layer.

---

## File location and archive

The current week's commentary lives at `commentary/latest.md` in your repo. The dashboard's render function looks for this exact path.

**Archive policy:** when you write next week's commentary, rename the current `latest.md` to `commentary/YYYY-MM-DD.md` with the Friday date of the week it covered, then create a fresh `latest.md` for the new week. This builds a dated archive over time without special tooling. After 52 weeks you will have 52 dated files, and any reader can browse them directly on GitHub.

**Do not delete** old commentaries. The archive is part of the product's credibility — a skeptic can walk the full record of what the framework read and how you read the framework, week by week. Missing weeks break the chain and damage the audit trail.

---

## Emergency protocol

If the pipeline fails on a Friday and no new score is produced, write the commentary anyway against the *previous* week's score and note the pipeline failure at the top:

> *Note: the USD Impact Score pipeline failed to run on [date] due to [brief cause]. The reading below reflects the previous week ending [previous date]. A rerun is scheduled and this commentary will be updated when fresh data is available.*

Then write the rest of the commentary normally. Silence is the worst possible response to a pipeline failure — readers come to the dashboard expecting content and should find a commentary and an explanation, not an empty page.

If the commentary itself slips (you are traveling, ill, or simply cannot write it that Friday), post a short honest message as `commentary/latest.md` acknowledging the skip and promising the next week's regular commentary. Do not let the dashboard sit with a stale commentary that predates the current score — the inconsistency will confuse readers.

---

## Monthly review (first Saturday of each month)

Once per month, on the first Saturday, walk back through the previous four commentaries and ask yourself one question: **did my reads of the framework match what the score and the market actually did?**

Where your read matched, the framework is serving you well and the commentary voice is calibrated.

Where your read diverged from what subsequently happened, the divergence is the learning signal. It almost always clusters — you will find that you consistently over-read certain channels and under-read others. That clustering is the most valuable thing you can discover about your own use of the framework, because once you see it you can correct it.

Keep a short private note (not published) tracking these divergences. Over a year the note becomes the raw material for Chapter 14 of a future book edition: "What I Learned Reading the Framework in Public."

---

## Why this format exists

Weekly commentary is the scarce layer of the USD Impact project. The pipeline is reproducible by anyone with Python. The book can be read in a weekend. The framework is documented. What cannot be copied is a disciplined weekly practice applied against real data by someone who has done it for dozens or hundreds of weeks.

The commentary is how the project becomes antifragile: it turns the infrastructure from a closed system (pipeline computes a number, displays a number) into an open system (pipeline computes a number, human reads that number against the week's specific events, human publishes the read, history accumulates). Over time the accumulated reads become the product's most defensible asset.

Keep it short. Keep it steady. Keep it every week.
