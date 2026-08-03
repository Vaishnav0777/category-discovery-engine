# Strategy Brief — Zepto Category Expansion

Internal working doc. This is the spine. Everything else (engine, interviews, MVP, deck) hangs off it.

---

## 1. The number that reframes the brief

Zepto's DRHP contains a cohort chart most people will skim past:

> A new user transacts in **2.6 categories in month one**, and **18.0 categories by month 23**. (April 2024 cohort)

Read that carefully, because it kills the obvious answer.

The obvious answer — the one most submissions will give — is "users are stuck in habit loops, they only buy the same things, so show them more things." That story is wrong on its own terms. Zepto users already broaden enormously. Breadth is not the problem.

The strategic goal isn't lifetime breadth. It's **% of Monthly Active Customers who buy from at least one new category every month.** That's a *recurring rate*, not a cumulative total. And a cumulative curve that flattens is a rate that has collapsed.

2.6 → 18.0 over 23 months averages ~0.7 new categories per month. But cohort breadth curves are concave: the gain is front-loaded. Most of those 15 new categories land in the first 6–9 months. After that, the monthly rate approaches zero — not because the user stopped needing things, but because **the categories they haven't entered yet are a structurally different kind of category.**

That's the whole project.

**Note on rigour:** the front-loading is an inference from the shape of the disclosed curve, not a disclosed number. I flag it as an inference in the deck and treat it as the hypothesis my primary research is designed to test. Do not present it as fact.

---

## 2. The thesis: The Retrieval Trap

Zepto is the best **retrieval** interface in Indian commerce and one of the worst **deliberation** interfaces.

Retrieval: *I know what I want. Find it. Ten minutes.* Atta, milk, Maggi, onions, Amul butter. Zepto is extraordinary at this — 12.35 min median delivery in Q4FY26, 2,140 orders/day/store, roughly double Instamart's throughput on an identical store count.

Deliberation: *I don't know which one. Is it right for me? Will I regret ₹600?* Sunscreen for oily skin. First protein powder. A dog's food when you've just got a dog. A baby's first solid food. Vitamin D supplements.

Zepto gives you almost nothing here. Thin review counts, no comparison view, no ingredient or fit guidance, no way to resolve a question. Amazon has 4,000 reviews on a face serum. Nykaa has skin-type filters and swatches. Zepto has a grid of SKUs and a 10-minute timer.

**And the 10-minute timer is itself the problem.** Speed sets the mental mode. Users open Zepto in *task-execution mode* — list in head, clock running. Task mode is actively hostile to exploration. Every discovery surface Zepto builds has to fight the mode the product's own core promise installed.

So:

> **The better Zepto gets at retrieval, the deeper the habit lock, and the harder new-category entry becomes.** Zepto's greatest strength is the direct cause of the metric it's now trying to move.

The categories still unentered after month 12 are precisely the **deliberation-heavy, high-margin** ones: beauty & personal care, baby, pet, wellness/supplements, home, electronics accessories. Non-grocery went from <5% of industry GMV in CY2022 to **29% in CY2025**, heading to **39–44% by CY2030**. These are the categories with the better unit economics. They are also the ones a retrieval interface cannot sell.

---

## 3. Why this is urgent, not nice-to-have

Three DRHP facts, together:

1. **Acquisition is stalling.** Annual transacting users fell sequentially, 49.54M in Q3FY26 → 47.97M in Q4FY26, even as quarterly orders rose 166.91M → 210.01M. Growth is shifting from new users to existing users doing more.
2. **Every order loses money.** Zepto lost ₹59.40 per order in Q4FY26. Blinkit made ₹1.35. Instamart lost ₹76.20.
3. **Non-grocery carries the margin.** Higher-value, higher-margin categories are exactly where the unit-economics fix lives.

So category expansion is not a growth-team vanity metric. **It is the margin path, and it is the only lever left that doesn't require buying more users.** That's your "why solving this makes business sense" slide, and it's built entirely on the company's own filed numbers.

---

## 4. Barrier taxonomy (the closed set)

This is the backbone of the AI engine. Closed set, not open coding — because a closed set is countable, comparable, and testable. Open coding produces mush you can't measure.

| Code | Barrier | What it sounds like | Deliberation cost |
|---|---|---|---|
| **B1** | **Trust** | "I'd never buy skincare here without reading reviews" | High |
| **B2** | **Fit** | "Which one is right for me? Too many options, no help" | High |
| **B3** | **Price-risk** | "₹700 on something I might not like — not from a 10-min app" | Medium |
| **B4** | **Assortment** | "They just don't stock what I want in that category" | Low (supply fix) |
| **B5** | **Occasion** | "I only remember I need it when I'm not on the app" | Medium |
| **B6** | **Awareness** | "I genuinely didn't know Zepto sold that" | Low (surface fix) |
| **B7** | **None/Other** | Off-topic, delivery/pricing complaints, praise | — |

The strategic point: **B6 and B4 are the barriers everyone assumes.** They're cheap to fix — a banner, a supply deal. If those were the real constraint it would already be solved, because they're the first thing any growth team tries.

The hypothesis is that the residual, stubborn blockers are **B1 and B2** — trust and fit. Those are deliberation costs, and no amount of merchandising fixes them.

**The engine's job is to test whether that's true, at scale, with traceable evidence. The interviews' job is to test whether the engine was right.**

---

## 5. Target segment: The Plateaued Regular

Defined behaviourally, not demographically. Demographics don't predict this; behaviour does.

**The Plateaued Regular**
- 6+ orders/month
- 12+ months tenure
- Stable repertoire of 6–9 categories
- **No new category entered in 60+ days**
- Trusts Zepto completely for speed; trusts it not at all for judgment

Why this segment and not, say, new users:

- **Most at-bats.** 6+ sessions/month means the most opportunities to intervene per user.
- **Zero acquisition cost.** Already retained, already loyal. Any incremental basket is close to pure contribution.
- **The gap is widest here.** They're already in the app constantly. They aren't leaving because Zepto is bad — they're going to Nykaa and Amazon for one specific job Zepto never learned to do.
- **It's the segment where the metric definition actually bites.** New users trivially buy new categories (everything is new). The MAC metric is dragged down by exactly this cohort.

Sizing note: don't invent a number. Frame it as "the cohort implied by the flattening of the DRHP breadth curve" and state clearly it needs internal data to size. Saying "I'd size this with a cohort query on the following definition" scores better than a fabricated percentage.

---

## 6. Root cause

Surface symptom: users don't buy new categories.

Wrong root cause (what most will write): *low awareness / poor discovery surfaces.*

Actual root cause:

> **Zepto has no mechanism for resolving uncertainty, and the categories it needs users to enter are uncertainty-heavy. Users don't lack options. They lack a basis for choosing — and the app never gives them one, so they go elsewhere to get it and buy there too.**

The five-why:
1. Why don't Plateaued Regulars buy new categories? → They open the app to execute a list.
2. Why only a list? → Because retrieval is what the app is good at, and 10 minutes sets the mode.
3. Why doesn't a browse surface fix it? → Browsing shows options; it doesn't resolve which option is right.
4. Why does that matter more in these categories? → Because BPC/baby/pet/wellness carry real personal consequence and real regret risk.
5. Why does Zepto lose the order entirely? → Because the user leaves to research, and the platform where they researched is the platform where they buy.

**Zepto is doing the demand-generation work and Amazon is banking it.**

---

## 7. Existing workarounds (to validate in interviews)

- Research on Google/YouTube/Instagram → buy on Amazon/Nykaa
- WhatsApp a friend or family member ("which brand?")
- Buy the brand they physically saw in a store or at someone's house
- Maintain a mental "not from Zepto" list — Zepto is for consumables, everything else is elsewhere
- Wait for the monthly big-basket trip and buy it in person

Each workaround is a paid-for behaviour: it costs time, and users are still doing it. That's the strongest evidence the problem is real.

---

## 8. The MVP: First Buy

**One sentence:** A deliberation layer that runs during the delivery-tracking window, uses the user's own basket history to name a category they've never entered, resolves the single biggest uncertainty in one tap, and de-risks the purchase.

**Why it's not a recommendation carousel.** Ranking is solved — collaborative filtering has been good at "what would this user like" for fifteen years. Ranking is not the bottleneck. The bottleneck is **justification**: producing a specific, personal, trustworthy *reason* at the moment of hesitation. That is a generative problem, and it is fed directly by the review-mining engine from Part 1.

Four design decisions, each defensible:

**1. Surface: the delivery-tracking screen.**
The most under-used real estate in the app. The user has already converted — zero cannibalisation risk to the main basket. They're watching a dot move for 10 minutes with nothing to do. Task mode is *over*; the list is done. This is the only moment in the session when a high-frequency user is both present and not busy.

**2. Trigger: derived, not generic.**
Not "you might like." A stated observation about their own behaviour: *"You've bought cereal and milk every week for 5 months. You've never bought fruit."* Specificity is what makes it feel like the app noticed rather than the app advertised.

**3. Deliberation: one question, one answer.**
Not an open chat box — blank boxes in task-mode apps get ignored. One question that resolves the largest uncertainty in the category (`oily or dry skin?`), then **one** product: price, one reason, and the top objection pre-handled. The reason is written from mined real-user language, not marketing copy. This is the direct handoff from Part 1.

**4. De-risk: the First Buy promise.**
Free return on your first order in any new category, plus trial size where available. This attacks B3 (price-risk) structurally rather than with a discount. Cheaper than a coupon, and it doesn't train users to wait for discounts.

**What I'd cut if I had to ship in two weeks:** the trial-size supply work. Free-return-on-first-buy is a policy change, not a supply-chain change, and it carries most of the de-risking value.

---

## 9. Success metrics

**North star:** % of MAC purchasing from ≥1 new category in the month.

**Primary:** First Buy conversion — new-category purchases per 1,000 tracking-screen impressions.

**Secondary (the honest one):** **30-day repeat rate within the newly-entered category.** This is the metric that separates a real behaviour change from a one-off novelty conversion. If someone buys sunscreen once and never again, the feature didn't work — it just generated a transaction. Most submissions will not include a metric that can make their own feature look bad. Include it.

**Guardrails:**
- Return rate on First Buy purchases (the free-return promise must not be abused into a loss)
- Main-basket AOV (must not cannibalise)
- Dismiss rate on the tracking screen (annoyance signal)
- Delivery-screen NPS

**Experiment design:** geo-split A/B on the Plateaued Regular cohort, 4 weeks. Powered on the primary metric; north star read as directional over a longer window since monthly metrics need ~2 cycles.

---

## 10. Risks I'd flag to my own team

- **The tracking screen may have an attention ceiling.** Users may simply close the app after ordering. Mitigate: instrument tracking-screen dwell time before building anything.
- **Free returns on a 10-minute delivery network are operationally expensive.** Reverse logistics is the hard part, not the policy.
- **The AI reason must never be wrong.** One hallucinated ingredient claim on a baby product is a regulatory and trust catastrophe. Constrain generation to a retrieval set of verified catalogue and review data; never let the model assert a fact not present in the source.
- **Blinkit can copy the surface in a quarter.** The defensibility isn't the UI, it's the review corpus and the reason-generation quality compounding over time.

---

## Source list (all publicly verifiable — hyperlink these in the deck)

- Zepto DRHP coverage: category cohort 2.6 → 18.0, ATU 47.97M, orders, delivery times, per-order economics — Trade Brains, Univest, INDmoney, Precize (July 2026)
- Non-grocery GMV share 29% CY25 → 39–44% CY30 — Mordor Intelligence, India quick commerce market reports
- Market size and category split — Mordor Intelligence, Bain "How India Shops Online 2026"
