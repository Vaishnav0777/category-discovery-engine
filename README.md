# Category Discovery Engine

**An AI pipeline that reads 3,000 app-store reviews to find out why quick-commerce users
never leave their aisle — and then proves that app-store reviews cannot answer that question.**

[Live demo](https://zepto-discovery-engine.netlify.app) ·
[Research appendix](https://docs.google.com/document/d/1UOKiCVZJJFBArk32fbHKr4IS8YMwVuk8/edit?usp=sharing) ·
[Deck](deck/NL%20Zepto.pdf)

---

## The problem

Zepto's DRHP discloses a cohort curve most people skim past: a new user buys from **2.6 categories
in month one and 18.0 by month 23**.

Read that carefully, because it kills the obvious answer. The obvious answer — the one most analyses
give — is *"users are stuck in a habit loop, so surface more categories."* Zepto users already add
15 categories in two years. They are not stuck.

The business goal isn't lifetime breadth. It's the **share of monthly actives who buy from at least
one new category each month** — a recurring rate, not a cumulative total. And a cumulative curve
that flattens is a rate that has collapsed:

| Period | New categories / month |
|---|---|
| Months 1–12 | **0.78** |
| Months 12–23 | **0.55** |

A 30% collapse. That's arithmetic on disclosed figures, not inference. So the question isn't why
users won't broaden. It's what's different about the categories still left after month 12.

## The headline result

I built a six-stage pipeline to mine that answer out of public review data. It found the opposite
of what I expected, and that turned out to be the useful part.

```
3,000 reviews  →  628 relevant (21%)  →  107 carry a discovery barrier (3.6%)
```

| Barrier | n | Driven by |
|---|---|---|
| Assortment | 51 | `not available` ×21, `dont have` ×12, `out of stock` ×6 |
| "Trust" | 41 | `expired product` ×17, `expiry date` ×13 |
| Occasion | 6 | |
| Price risk | 6 | |
| Awareness | 3 | |
| **Fit** | **0** | *no term matched in 628 relevant reviews* |

Three results contradicted the hypothesis:

- **Fit scored zero.** Nobody in 628 relevant reviews describes being unable to choose between products.
- **"Trust" isn't deliberation trust.** It's expiry and counterfeit complaints — goods received in
  bad condition. A fulfilment failure, not hesitation before a purchase.
- **Four competitor mentions in the entire corpus.** Nykaa: zero.

**Why:** app-store reviews are written about *orders that happened*. A category a user never entered
produces no order, no complaint and no review. **You cannot observe a non-purchase in a record of
purchases.** The silence is a structural property of the instrument, not a gap in the data.

That negative result is the finding, and it's what made primary research load-bearing rather than
decorative.

## Validation — the part that matters

An LLM will label 3,000 rows and hand you a clean chart whether or not the labels mean anything. The
chart looks identical either way. So I scored the classifier against myself.

```
30 reviews, stratified by label, fixed seed, hand-labelled blind
before looking at any classifier output

Raw agreement            53.3%
Cohen's kappa            0.319   (fair — below substantial, reported as-is)
Negative-control leakage 0 / 20
```

Per-barrier precision, recall, F1 and the full confusion matrix are in
[`3_validate.py`](engine/3_validate.py) output and the appendix.

**The errors run in one direction.** Ten of the disagreements are the classifier finding a barrier
where I saw none; three are the reverse. It over-triggers. So the 107 count is an **upper bound**,
and the real signal is thinner still.

### The bug this caught

My first run reported **trust as 71% of all barriers.** Clean chart. Nothing about it looked wrong.

I made the classifier report which term fired on every row. Trust was being carried by the bare words
`review` and `rating` — which in app-store data mostly appear as self-reference: *"writing this
review"*, *"giving 1 star rating"*. Neither says anything about trusting a product.

The same audit exposed a second bug: substring matching had made **`cat` the top category**, because
it matches inside *category*, *location*, *complicated*.

Both fixed — trust cues now require product context, all matching moved to word boundaries. Trust
fell to 38% and its meaning changed entirely.

> Without the validation step, 71% would have shipped as a finding.

## User research

Six interviews, recruited on behaviour rather than demographics: 2+ orders/week, 12+ months' tenure,
a narrow repeating repertoire, no recent new-category purchase.

**Finding 1 — the barrier is on the product page, not in discovery.** 3 of 6 named the same gap
unprompted: no verified reviews, generic stock images, no specs or dimensions, no seller
verification. Two named the competitor they go to instead and gave the identical reason. A fourth
described a *"pantry replenishment mindset"* that stops him recalling that beauty products exist on
the app at all — he's aware, he just doesn't remember in the moment.

**Finding 2 — expansion happens at the cart, never while browsing.** 2 of 6 had already entered a
new category through a checkout prompt. A third asked for contextual cart bundling by name. Nobody
expanded by browsing; one skips home banners entirely.

**Finding 2 overturned my own design.** I had built the MVP for the post-payment delivery-tracking
screen, reasoning that the basket had already converted so there was zero cannibalisation risk. No
participant supported that. The surface moved to the cart — which reintroduces the risk the original
design had engineered away, and is why cart-to-order conversion became the hardest guardrail.

## The MVP — First Buy

A deliberation layer in the cart. One observation about the user's own behaviour, one question, one
product carrying what the product page is missing, and free return on the first purchase in any new
category.

Ranking is not the bottleneck — collaborative filtering solved that fifteen years ago. **Justification
is:** producing a specific, trustworthy reason at the moment of hesitation. That's a generative
problem, and it's fed by the same corpus that diagnosed the barrier.

[Click through the prototype →](https://zepto-discovery-engine.netlify.app)

## Architecture

```
1  Ingest       Google Play + App Store, deduped, provenance logged      python
2  Gate         binary relevance screen, tuned for recall                lexicon / LLM
3  Extract      JTBD, category, barrier code, competitor, verbatim       lexicon / LLM
4  Aggregate    frequency, severity, category × barrier                  python
5  Synthesise   themes ranked by strategic weight, carrying review IDs   python / LLM
6  Validate     blind hold-out → precision, recall, kappa, confusion     human + python
```

Three decisions worth explaining:

**A separate cheap gate.** ~4 in 5 reviews are about delivery, price or bugs. Screening first cuts
extraction cost by most of the corpus. It fails *open*: on genuine uncertainty it returns YES,
because a false positive costs one extra classification and a false negative loses the signal
permanently. Asymmetric error, asymmetric threshold.

**A closed taxonomy.** Seven fixed barrier codes, not open coding. A closed set is countable,
comparable across runs, and can be scored against a human. Open coding produces labels you cannot
measure.

**Mandatory verbatims.** Every extracted row must carry a quote copied character-for-character from
the source. If the quote isn't found in the source text, the row is dropped automatically. That makes
fabrication detectable rather than invisible.

## Run it

```bash
pip install google-play-scraper

python3 1_collect.py                    # ingest + provenance log
python3 2_analyse.py                    # stages 2–5 → analysis.json, app/corpus.js
python3 3_validate.py sample            # draws the blind hold-out
#   ... hand-label validation_sheet.csv (or open label.html) ...
python3 3_validate.py score             # precision / recall / kappa / confusion
```

The pipeline is provider-agnostic and auto-detects whichever key you have:

```bash
export GEMINI_API_KEY=...        # free tier, aistudio.google.com/apikey
export ANTHROPIC_API_KEY=...
export OPENAI_API_KEY=...
python3 2_analyse.py --provider offline # no key, no network, deterministic lexicon
```

Requests are batched (25 per call for the gate, 5 for extraction) because free-tier rate limits make
one-call-per-review impossible — 3,000 reviews at ~15 RPM is over three hours. Batching makes it
~120 calls. Any malformed batch falls back to the offline classifier rather than dropping rows.

## Repo layout

```
engine/
  1_collect.py       ingest, unified schema, provenance log
  2_analyse.py       the pipeline — multi-provider, batched, resumable
  3_validate.py      stratified hold-out, kappa, confusion matrix, negative control
  label.html         keyboard-driven labelling tool for the hold-out
app/
  index.html         the deployed site — engine dashboard, live classifier, prototype
  corpus.js          generated analysis output
deck/
  NL Zepto.pdf       10-slide deck
appendix/            full research appendix (method, interviews, validation)
```

`app/index.html` is a single file with zero dependencies and no build step — deliberately, because
you cannot debug a broken build at 3am the night before a deadline.

## Limitations

- **n=6** interviews. The pattern held across all six, but six people cannot size a population.
- **n=30** validation hold-out, kappa 0.319. Fair, not substantial. The error direction is diagnosed
  (systematic over-triggering) but the classifier is not reliable at the row level. Conclusions are
  directional and were cross-checked against interviews.
- **Lexicon classifier, not an LLM**, because free-tier quota ran out mid-run. It misses nuance,
  sarcasm and paraphrase, and almost certainly under-recalls the fit and occasion codes. The pipeline
  supports both — one flag — and both label sets should be scored against the same hold-out to
  quantify the cost.
- **Android-only.** The Apple RSS feed returned empty.
- **12-day collection window.** A snapshot, not a trend.
- **Reviews are a complaint channel.** Users who are quietly satisfied and quietly narrow — precisely
  the target segment — don't write reviews. Counts here indicate salience, not prevalence.

## Sources

- Zepto DRHP analysis — cohort breadth, ATU, per-order economics:
  [finixschool.substack.com](https://finixschool.substack.com/p/inside-zepto-how-the-business-actually)
- Zepto DRHP, further detail — ATU decline, delivery times, CCPA notice:
  [tradebrains.in](https://tradebrains.in/zepto-ipo-here-are-10-hidden-things-in-the-drhp-that-most-investors-will-miss/)
- India quick-commerce market and category mix:
  [mordorintelligence.com](https://www.mordorintelligence.com/industry-reports/q-commerce-industry-in-india)

## Stack

Python 3 (stdlib + `google-play-scraper`) · Gemini / Claude / GPT, interchangeable · vanilla HTML,
CSS and JS, no framework · `python-pptx` for the deck · Netlify

---

*Built as a graduation project. Zepto is used as a case study; this work is not affiliated with or
endorsed by the company. All data is public.*
