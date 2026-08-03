#!/usr/bin/env python3
"""
STAGES 2-5 — THE DISCOVERY ENGINE

  Stage 2  Relevance gate      cheap pass, binary, tuned for recall
  Stage 3  Structured extract  strong pass, strict JSON, closed taxonomy
  Stage 4  Aggregate           counts, co-occurrence, severity
  Stage 5  Synthesise themes   every claim carries review IDs

WHICH PROVIDER
--------------
Works with whichever you have. Free option first.

  GOOGLE GEMINI — free, no credit card, no pip install
      1. aistudio.google.com/apikey  ->  "Create API key"
      2. export GEMINI_API_KEY=...
      3. python 2_analyse.py
      The free tier covers a 3,000-review run comfortably.

  ANTHROPIC
      pip install anthropic
      export ANTHROPIC_API_KEY=sk-ant-...
      python 2_analyse.py --provider anthropic

  OPENAI
      pip install openai
      export OPENAI_API_KEY=sk-...
      python 2_analyse.py --provider openai

  OFFLINE — no key, no network, no cost
      python 2_analyse.py --provider offline
      A deterministic lexicon classifier that mirrors the prompt's decision
      rules. Weaker than a model, and you must SAY SO on the slide. It exists
      so a dead API key can never block you at 2am.

Reads   corpus_raw.json
Writes  corpus_gated.json      stage 2, resumable
        corpus_extracted.json  stage 3, resumable
        analysis.json          final, feeds the deck
        ../app/corpus.js       final, feeds the live web app

DESIGN NOTES worth being able to defend out loud
------------------------------------------------
* The relevance gate is a separate cheap stage for cost, not accuracy. Roughly
  9 in 10 store reviews are about delivery time, price or bugs. Running the
  expensive extraction over all of them wastes most of the budget. The gate is
  tuned for RECALL: a false positive costs one extra call, a false negative
  loses a signal permanently. Asymmetric error, asymmetric threshold.
* The barrier taxonomy is a CLOSED set. Open-ended coding produces labels you
  cannot count. A closed set is countable, comparable, and can be scored
  against a human-labelled hold-out (3_validate.py).
* Every extraction must return a verbatim copied from the source. That gives
  every downstream claim a traceable citation and makes hallucination
  detectable: if the quote is not in the source, the row is dropped.
"""

import json, os, sys, re, time, argparse, collections, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

BARRIERS = ["B1_TRUST","B2_FIT","B3_PRICE_RISK","B4_ASSORTMENT",
            "B5_OCCASION","B6_AWARENESS","B7_NONE"]

# Free tiers cap requests per minute, not just per day. Three concurrent
# workers plus the exponential backoff below keeps a long run under the limit
# instead of hammering it into a 429 wall.
WORKERS = 3


# ══════════════════════════════════════════════════ providers
class Provider:
    """One interface, four backends. Keeps the pipeline logic identical
    regardless of which key the user happens to have."""

    def __init__(self, name):
        self.name = name
        if name == "gemini":
            self.key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            if not self.key:
                sys.exit("Set GEMINI_API_KEY. Free key: https://aistudio.google.com/apikey")
            self.model = self._pick_gemini_model()
        elif name == "anthropic":
            import anthropic
            self.client = anthropic.Anthropic()
            self.fast, self.strong = "claude-haiku-4-5-20251001", "claude-sonnet-5"
        elif name == "openai":
            from openai import OpenAI
            self.client = OpenAI()
            self.fast, self.strong = "gpt-4o-mini", "gpt-4o"
        elif name == "offline":
            pass
        else:
            sys.exit(f"unknown provider {name}")

    def _pick_gemini_model(self):
        """Model names drift and Google retires them fast. Try current
        candidates and keep the first that actually returns text, rather than
        hard-coding one and discovering it's dead at 2am.

        The probe budget is deliberately generous. Gemini 3.x models spend
        tokens on internal reasoning before emitting anything, so a small
        maxOutputTokens returns finishReason=MAX_TOKENS with empty content —
        which looks like auth failure but is really token starvation."""
        errs = []
        for m in ["gemini-flash-latest", "gemini-3.5-flash", "gemini-2.5-flash",
                  "gemini-2.0-flash", "gemini-flash-lite-latest"]:
            try:
                t = self._gemini(m, "Reply with the single word OK.", 400)
                if t.strip():
                    print(f"  gemini model: {m}")
                    return m
                errs.append(f"    {m}: empty text")
            except Exception as e:
                errs.append(f"    {m}: {str(e)[:140]}")
        print("No Gemini model responded:")
        print("\n".join(errs))
        sys.exit("Check the key at https://aistudio.google.com/api-keys, "
                 "or run: python3 2_analyse.py --provider offline")

    def _gemini(self, model, prompt, max_tokens):
        # Auth goes in the x-goog-api-key HEADER, not the ?key= query parameter.
        # Keys issued since 2026 start "AQ." and are service-account-bound auth
        # keys, rejected on the query-parameter path. The header works for both
        # those and legacy AIza keys.
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{model}:generateContent")

        def send(with_thinking_off):
            cfg = {"temperature": 0, "maxOutputTokens": max_tokens}
            if with_thinking_off:
                # Stop reasoning models burning the whole budget before speaking.
                cfg["thinkingConfig"] = {"thinkingBudget": 0}
            body = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                               "generationConfig": cfg}).encode()
            req = urllib.request.Request(url, data=body, headers={
                "Content-Type": "application/json", "x-goog-api-key": self.key})
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read())

        try:
            d = send(True)
        except urllib.error.HTTPError as e:
            detail = e.read().decode()[:250]
            # older models reject thinkingConfig outright — retry plainly
            if e.code == 400 and "thinking" in detail.lower():
                try:
                    d = send(False)
                except urllib.error.HTTPError as e2:
                    raise RuntimeError(f"HTTP {e2.code}: {e2.read().decode()[:220]}") from None
            else:
                raise RuntimeError(f"HTTP {e.code}: {detail}") from None

        try:
            return d["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            fr = (d.get("candidates") or [{}])[0].get("finishReason")
            if fr == "MAX_TOKENS":
                raise RuntimeError("MAX_TOKENS with no text (reasoning ate the budget)")
            raise RuntimeError(f"no text in response ({fr}): {json.dumps(d)[:200]}")

    def ask(self, prompt, strong=False, max_tokens=700):
        last = "no attempts made"
        for attempt in range(4):
            try:
                if self.name == "gemini":
                    return self._gemini(self.model, prompt, max_tokens)
                if self.name == "anthropic":
                    r = self.client.messages.create(
                        model=self.strong if strong else self.fast,
                        max_tokens=max_tokens,
                        messages=[{"role": "user", "content": prompt}])
                    return r.content[0].text
                if self.name == "openai":
                    r = self.client.chat.completions.create(
                        model=self.strong if strong else self.fast,
                        max_tokens=max_tokens, temperature=0,
                        messages=[{"role": "user", "content": prompt}])
                    return r.choices[0].message.content
            except Exception as e:
                last = str(e)
                # free tiers rate-limit hard; back off rather than dropping work
                if any(k in last for k in ("429","rate","quota","RESOURCE_EXHAUSTED")):
                    time.sleep(8 * (attempt + 1)); continue
                if attempt == 3: break
                time.sleep(2 * (attempt + 1))
        # Surface the underlying cause. A generic "failed after retries" tells
        # you nothing at 2am; the actual HTTP body tells you whether to wait,
        # switch model, or give up and run offline.
        raise RuntimeError(f"after retries — {last[:200]}")


# ══════════════════════════════════════════════════ offline classifier
STRIP = lambda s: s.lower().replace("’","").replace("'","").replace("`","")

# NOTE ON TWO REAL BUGS THIS VERSION FIXES — worth being able to explain, because
# it is a genuine finding about method rather than an embarrassment:
#
# 1) Bare "review" and "rating" as trust cues are catastrophic false positives.
#    App-store reviews are full of self-reference ("writing this review",
#    "giving 1 star rating") which says nothing about trusting a PRODUCT. The
#    first run put 71% of all barriers in B1_TRUST purely on that artifact, and
#    starved B2_FIT to zero. Trust cues now require multi-word product context.
#
# 2) Substring matching made "cat" the top category, because it matches inside
#    "category", "location", "complicated". All term matching is now on word
#    boundaries.
#
# A lexicon classifier is only as good as its lexicon. That is exactly why the
# hand-labelled hold-out in 3_validate.py exists: it is what caught this.

RULES = [
 ("B1_TRUST",      ["no reviews","without reviews","read reviews","check reviews",
                    "customer reviews","product reviews","user reviews","no ratings",
                    "cant trust","dont trust","not trustworthy","genuine product",
                    "fake product","duplicate product","first copy","not authentic",
                    "expired product","near expiry","expiry date","past expiry",
                    "quality is doubtful","no way to know"]),
 ("B2_FIT",        ["which one","which brand","which product","which variant","which size",
                    "which is best","confusing","too many options","too many choices",
                    "no information","no details","no description","dont know which",
                    "not sure which","cant decide","cannot decide","hard to choose",
                    "difficult to choose","suits my","for my skin","right size",
                    "no ingredients","ingredient list","hard to compare","cant compare"]),
 ("B3_PRICE_RISK", ["expensive to try","waste of money","too much money","too risky",
                    "regret buying","costly to try","not worth risking","wasted money"]),
 ("B4_ASSORTMENT", ["not available","out of stock","dont have","doesnt stock","doesnt have",
                    "limited options","limited variety","no variety","wish they had",
                    "unavailable","less options","fewer options","not stocked",
                    "never in stock","poor selection"]),
 ("B5_OCCASION",   ["forget to","forgot to","remember to","only when i","by the time",
                    "in a hurry","last minute","in the middle of"]),
 ("B6_AWARENESS",  ["didnt know","did not know","never knew","had no idea",
                    "no idea they sold","was unaware","never realised","never realized",
                    "didnt realise","just found out","recently discovered",
                    "didnt even know"]),
]
COMPS = ["amazon","flipkart","nykaa","bigbasket","blinkit","instamart","dmart",
         "jiomart","zomato","swiggy","meesho","myntra"]
CATS  = ["skincare","skin care","beauty","makeup","cosmetics","baby","diapers","pet food",
         "pet","dog food","cat food","electronics","appliance","appliances","kitchen",
         "supplements","protein","vitamins","medicine","pharmacy","fruits","vegetables",
         "snacks","personal care","home decor","fashion","clothes","toys","stationery",
         "groceries","dairy","cereal","meat","frozen","chocolate","beverages",
         "cleaning","haircare","shampoo","sunscreen","perfume","detergent"]
DELIVERY = re.compile(r"\b(late|delayed|rider|refund|crash|bug|charges?|fees?|support|"
                      r"slow|delivery boy|packaging|customer care)\b")

# Word-boundary matcher. Substring matching is how "cat" ends up the top
# category by matching inside "category".
_CACHE = {}
def has_term(s, term):
    rx = _CACHE.get(term)
    if rx is None:
        rx = _CACHE[term] = re.compile(r"(?<!\w)" + re.escape(term) + r"(?!\w)")
    return rx.search(s) is not None


def offline_gate(text):
    s = STRIP(text)
    if any(has_term(s, w) for _, ws in RULES for w in ws): return True
    if any(has_term(s, c) for c in CATS + COMPS):          return True
    return not DELIVERY.search(s) and len(s.split()) > 12


def offline_extract(text, rating=None):
    s = STRIP(text)
    matched = {b: [w for w in ws if has_term(s, w)] for b, ws in RULES}
    hits = sorted(((b, ms) for b, ms in matched.items() if ms),
                  key=lambda x: (-len(x[1]), -max(len(w) for w in x[1])))
    barrier = hits[0][0] if hits else "B7_NONE"
    terms = hits[0][1] if hits else []

    verb = None
    if barrier != "B7_NONE":
        kw = max(terms, key=len)                 # longest match = most specific
        m = re.search(r"(?<!\w)" + re.escape(kw) + r"(?!\w)", s)
        if m:
            i = m.start()
            verb = text[max(0, i-60): min(len(text), i+len(kw)+90)].strip()
            if STRIP(verb) not in s: verb = None

    return {
        "job_to_be_done": None,
        "categories_mentioned": sorted({c for c in CATS if has_term(s, c)}),
        "barrier": barrier,
        "barrier_reasoning": ("Lexicon match on: " + ", ".join(terms)) if terms
                             else "No barrier term matched.",
        "matched_terms": terms,          # provenance: audit every label yourself
        "competitor_mentioned": next((c for c in COMPS if has_term(s, c)), None),
        "workaround": None,
        "verbatim": verb,
        "sentiment": "negative" if (rating or 3) <= 2 else
                     "positive" if (rating or 3) >= 4 else "neutral",
        "confidence": round(min(0.45 + 0.15*len(terms), 0.85), 2) if terms else 0.55,
        "engine": "offline_lexicon",
    }


# ══════════════════════════════════════════════════ stage 2
# Batched. Free-tier request-per-minute limits make one-call-per-review
# impossible: 3,000 reviews at ~15 RPM is over three hours. Batching 25 to a
# call turns that into ~120 calls and about ten minutes. The answer format is a
# fixed-length Y/N string so a truncated or padded reply is detectable by
# length alone, and any malformed batch falls back to the offline gate rather
# than silently dropping reviews.
GATE_BATCH = 25

GATE_PROMPT = """You screen app reviews for a product research pipeline.

For EACH numbered review below decide:

Y if it says ANYTHING about:
- what the person does or does not buy, or which categories they use
- browsing, searching, finding or discovering products
- product range, selection, variety, or what is missing
- comparing the app to Amazon / Flipkart / Nykaa / BigBasket / a local shop
- deciding between products, or not knowing which product to pick
- product information: reviews, ratings, descriptions, ingredients, expiry

N if it is ONLY about: delivery speed or lateness, rider behaviour, prices or
discounts, fees, app crashes or bugs, refunds, customer support, or generic
praise or abuse with no product content.

When genuinely uncertain answer Y. A false Y costs almost nothing.
A false N loses the signal forever.

Output EXACTLY {n} characters, each Y or N, in order, no spaces, no newlines,
no numbering, no explanation. Example for 5 reviews: YNNYN

REVIEWS:
{block}"""


def stage2(corpus, prov):
    if os.path.exists("corpus_gated.json"):
        print("Stage 2: reusing corpus_gated.json (delete it to re-run)")
        return json.load(open("corpus_gated.json", encoding="utf-8"))

    print(f"Stage 2: relevance gate over {len(corpus)} reviews [{prov.name}]")

    if prov.name == "offline":
        for r in corpus: r["relevant"] = offline_gate(r["text"])
        json.dump(corpus, open("corpus_gated.json","w",encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        keep = sum(1 for r in corpus if r["relevant"])
        print(f"  relevant: {keep}/{len(corpus)}  ({keep/max(len(corpus),1)*100:.1f}%)")
        return corpus

    batches = [corpus[i:i+GATE_BATCH] for i in range(0, len(corpus), GATE_BATCH)]
    print(f"  {len(batches)} batched calls of {GATE_BATCH}")
    fallbacks = 0

    def run(batch):
        block = "\n".join(
            f"{i+1}. {re.sub(chr(10),' ',r['text'])[:400]}" for i, r in enumerate(batch))
        try:
            ans = prov.ask(GATE_PROMPT.format(n=len(batch), block=block),
                           max_tokens=200 + 6*len(batch))
            letters = re.sub(r"[^YN]", "", ans.upper())
            if len(letters) != len(batch):
                raise ValueError(f"got {len(letters)} answers for {len(batch)} reviews")
            for r, c in zip(batch, letters): r["relevant"] = (c == "Y")
            return batch, False
        except Exception as e:
            print(f"  batch fell back to offline gate: {str(e)[:90]}")
            for r in batch: r["relevant"] = offline_gate(r["text"])
            return batch, True

    out, done = [], 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for f in as_completed([ex.submit(run, b) for b in batches]):
            b, fell = f.result(); out += b; fallbacks += fell; done += 1
            if done % 10 == 0: print(f"  {done}/{len(batches)} batches")

    json.dump(out, open("corpus_gated.json","w",encoding="utf-8"),
              ensure_ascii=False, indent=1)
    keep = sum(1 for r in out if r["relevant"])
    print(f"  relevant: {keep}/{len(out)}  ({keep/max(len(out),1)*100:.1f}%)")
    if fallbacks: print(f"  batches gated offline instead of by model: {fallbacks}/{len(batches)}")
    return out


# ══════════════════════════════════════════════════ stage 3
EXTRACT_PROMPT = """Extract structured signal from one review of Zepto, an Indian
10-minute grocery delivery app. Zepto also sells beauty, baby, pet, wellness,
home, kitchen and electronics.

Research question: why do users keep buying from the same few categories
instead of trying new ones?

Return ONLY a JSON object, no other text, no markdown fence:

{{
 "job_to_be_done": "the underlying job in the user's own framing, one sentence, or null",
 "categories_mentioned": ["lowercase category names"],
 "barrier": "B1_TRUST | B2_FIT | B3_PRICE_RISK | B4_ASSORTMENT | B5_OCCASION | B6_AWARENESS | B7_NONE",
 "barrier_reasoning": "one sentence explaining the label",
 "competitor_mentioned": "amazon | flipkart | nykaa | bigbasket | blinkit | instamart | local_store | other | null",
 "workaround": "what the user does instead, or null",
 "verbatim": "an EXACT substring copied character-for-character from the review, max 200 chars, or null",
 "sentiment": "positive | negative | mixed | neutral",
 "confidence": 0.0
}}

B1_TRUST       will not buy without reviews, ratings or social proof
B2_FIT         cannot work out which variant or type suits them; options without guidance
B3_PRICE_RISK  the sum at stake feels too high to risk on something unfamiliar
B4_ASSORTMENT  the category exists but the specific item is not stocked
B5_OCCASION    the need arises away from the app; on the app they execute a list
B6_AWARENESS   did not know Zepto sold this at all
B7_NONE        not about category discovery

Rules:
- "verbatim" MUST be copied exactly from the review. Do not paraphrase, do not
  fix spelling. An invented quote invalidates the row and is auto-rejected.
- confidence is your own 0-1 calibration. Below 0.5 means you are guessing.
- Delivery, price, bugs or support only -> B7_NONE.

REVIEW (rating {rating}/5):
{text}"""

# Batched extraction. Smaller batches than the gate because per-row quality
# matters more here and long outputs are likelier to truncate. Any batch whose
# array length doesn't match falls back to the offline classifier for those
# rows, so a bad batch degrades those few rows rather than losing them.
EXTRACT_BATCH = 5

EXTRACT_BATCH_PROMPT = """Extract structured signal from EACH numbered review of
Zepto, an Indian 10-minute grocery delivery app. Zepto also sells beauty, baby,
pet, wellness, home, kitchen and electronics.

Research question: why do users keep buying from the same few categories
instead of trying new ones?

Return ONLY a JSON array of exactly {n} objects, in the same order as the
reviews. No markdown fence, no commentary. Each object:

{{
 "job_to_be_done": "the underlying job in the user's own framing, or null",
 "categories_mentioned": ["lowercase category names"],
 "barrier": "B1_TRUST | B2_FIT | B3_PRICE_RISK | B4_ASSORTMENT | B5_OCCASION | B6_AWARENESS | B7_NONE",
 "barrier_reasoning": "one sentence",
 "competitor_mentioned": "amazon | flipkart | nykaa | bigbasket | blinkit | instamart | local_store | other | null",
 "workaround": "what the user does instead, or null",
 "verbatim": "an EXACT substring copied from THAT review, max 200 chars, or null",
 "sentiment": "positive | negative | mixed | neutral",
 "confidence": 0.0
}}

B1_TRUST       will not buy without reviews, ratings or social proof
B2_FIT         cannot work out which variant or type suits them
B3_PRICE_RISK  the sum at stake feels too high to risk on something unfamiliar
B4_ASSORTMENT  the category exists but the specific item is not stocked
B5_OCCASION    the need arises away from the app
B6_AWARENESS   did not know Zepto sold this at all
B7_NONE        not about category discovery

Rules:
- "verbatim" MUST be copied exactly from its own review. Never paraphrase,
  never fix spelling. Invented quotes are auto-rejected downstream.
- Delivery, price, bugs or support only -> B7_NONE.
- Return exactly {n} objects even if many are B7_NONE.

REVIEWS:
{block}"""


def parse_json(raw):
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.S)          # models sometimes chat first
        if m: return json.loads(m.group(0))
        raise


def stage3(gated, prov):
    if os.path.exists("corpus_extracted.json"):
        print("Stage 3: reusing corpus_extracted.json (delete it to re-run)")
        return json.load(open("corpus_extracted.json", encoding="utf-8"))

    work = [r for r in gated if r.get("relevant")]
    print(f"Stage 3: extracting from {len(work)} reviews [{prov.name}]")

    if prov.name == "offline":
        for r in work: r["extraction"] = offline_extract(r["text"], r.get("rating"))
        out = work
    else:
        def clean(d, rec):
            """Shared post-processing: hallucination guard + label whitelist."""
            v = d.get("verbatim")
            if v:
                n = lambda s: re.sub(r"\s+", " ", s.lower()).strip()
                if n(v) not in n(rec["text"]):
                    d["verbatim"] = None; d["verbatim_rejected"] = True
            if d.get("barrier") not in BARRIERS: d["barrier"] = "B7_NONE"
            d["engine"] = prov.name
            return d

        batches = [work[i:i+EXTRACT_BATCH] for i in range(0, len(work), EXTRACT_BATCH)]
        print(f"  {len(batches)} batched calls of {EXTRACT_BATCH}")

        def run(batch):
            block = "\n\n".join(
                f"{i+1}. (rating {r.get('rating')}/5) {re.sub(chr(10),' ',r['text'])[:1200]}"
                for i, r in enumerate(batch))
            try:
                arr = parse_json(prov.ask(
                    EXTRACT_BATCH_PROMPT.format(n=len(batch), block=block),
                    strong=True, max_tokens=900*len(batch)))
                if not isinstance(arr, list) or len(arr) != len(batch):
                    raise ValueError(f"got {len(arr) if isinstance(arr,list) else '?'} "
                                     f"objects for {len(batch)} reviews")
                for r, d in zip(batch, arr): r["extraction"] = clean(d, r)
            except Exception as e:
                print(f"  batch fell back to offline extract: {str(e)[:90]}")
                for r in batch:
                    r["extraction"] = offline_extract(r["text"], r.get("rating"))
            return batch

        out, done = [], 0
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            for f in as_completed([ex.submit(run, b) for b in batches]):
                out += f.result(); done += 1
                if done % 10 == 0: print(f"  {done}/{len(batches)} batches")

    json.dump(out, open("corpus_extracted.json","w",encoding="utf-8"),
              ensure_ascii=False, indent=1)
    rej = sum(1 for r in out if (r.get("extraction") or {}).get("verbatim_rejected"))
    fb  = sum(1 for r in out if (r.get("extraction") or {}).get("engine")=="offline_lexicon")
    print(f"  quotes rejected as non-verbatim: {rej}")
    if prov.name != "offline" and fb: print(f"  rows that fell back to offline: {fb}")
    return out


# ══════════════════════════════════════════════════ stage 4
def stage4(extracted):
    print("Stage 4: aggregating")
    rows = [r for r in extracted
            if r.get("extraction") and r["extraction"]["barrier"] != "B7_NONE"]

    barriers = collections.Counter(r["extraction"]["barrier"] for r in rows)
    cats, comps, cxb = collections.Counter(), collections.Counter(), collections.Counter()
    workarounds = []

    for r in rows:
        e = r["extraction"]
        for c in (e.get("categories_mentioned") or []):
            c = c.lower().strip(); cats[c] += 1; cxb[(c, e["barrier"])] += 1
        if e.get("competitor_mentioned"): comps[e["competitor_mentioned"]] += 1
        if e.get("workaround"): workarounds.append({"id": r["id"], "workaround": e["workaround"]})

    sev = {}
    for b in barriers:
        rs = [r["rating"] for r in rows
              if r["extraction"]["barrier"] == b and r.get("rating")]
        sev[b] = round(sum(5-x for x in rs)/len(rs), 2) if rs else None

    conf = [r["extraction"].get("confidence") or 0 for r in rows]
    return {"n_total": len(extracted), "n_with_barrier": len(rows),
            "barriers": dict(barriers.most_common()), "barrier_severity": sev,
            "categories": dict(cats.most_common(30)), "competitors": dict(comps.most_common()),
            "category_x_barrier": {f"{c}|{b}": n for (c,b),n in cxb.most_common(40)},
            "workarounds": workarounds[:60],
            "mean_confidence": round(sum(conf)/len(conf),3) if conf else None,
            "rows": rows}


# ══════════════════════════════════════════════════ stage 5
SYNTH_PROMPT = """You are a product researcher writing the findings section for a
growth PM at Zepto, an Indian 10-minute delivery app.

Strategic goal: increase the share of monthly active customers who buy from at
least one NEW category each month.

Below are structured extractions from real app-store reviews.

Produce 4-6 themes. Return ONLY JSON, no markdown fence:

{{
 "themes":[
  {{"title":"a claim, not a topic — state the finding in the title",
    "what_we_found":"2-3 sentences",
    "why_it_happens":"the mechanism, 1-2 sentences",
    "evidence_ids":["review ids"],
    "quotes":["exact verbatims from the data below"],
    "n_reviews":0,
    "confidence":"high|medium|low",
    "confidence_reason":"why that level",
    "so_what":"what a PM should do about it, one sentence"}}
 ],
 "surprise":"the single finding that most contradicts what a PM would assume before reading this",
 "what_this_data_cannot_tell_us":"honest limits of app-store reviews as a source"
}}

Rules:
- Titles must be claims. "Users research on Nykaa then buy there", not "Competitor mentions".
- Never use a quote that is not in the data below.
- Rank themes by how much they matter to the goal, not by raw frequency.
- Mark a theme "low" confidence when it rests on few reviews, and say so.
- Be willing to report that a popular assumption is NOT supported by the data.

DATA:
{data}"""


def stage5(agg, prov):
    print("Stage 5: synthesising themes")
    sample = [{"id": r["id"], "rating": r.get("rating"),
               "barrier": r["extraction"]["barrier"],
               "jtbd": r["extraction"].get("job_to_be_done"),
               "cats": r["extraction"].get("categories_mentioned"),
               "competitor": r["extraction"].get("competitor_mentioned"),
               "workaround": r["extraction"].get("workaround"),
               "quote": r["extraction"].get("verbatim")}
              for r in agg["rows"] if r["extraction"].get("verbatim")][:200]

    if prov.name == "offline":
        # No model available. Build honest, mechanical theme stubs from the counts
        # so the deck still has structure — clearly flagged as not model-generated.
        top = list(agg["barriers"].items())[:4]
        names = {"B1_TRUST":"trust","B2_FIT":"fit","B3_PRICE_RISK":"price risk",
                 "B4_ASSORTMENT":"assortment","B5_OCCASION":"occasion",
                 "B6_AWARENESS":"awareness"}
        return {"themes": [{
            "title": f"⟨WRITE THIS YOURSELF⟩ {names.get(b,b)} appears in {n} reviews",
            "what_we_found": "Counts are real. The narrative is yours to write from the quotes below.",
            "why_it_happens": "⟨your reading⟩",
            "evidence_ids": [r["id"] for r in agg["rows"]
                             if r["extraction"]["barrier"] == b][:6],
            "quotes": [r["extraction"]["verbatim"] for r in agg["rows"]
                       if r["extraction"]["barrier"] == b
                       and r["extraction"].get("verbatim")][:3],
            "n_reviews": n, "confidence": "medium",
            "confidence_reason": f"n={n}, classified by lexicon rules rather than a model",
            "so_what": "⟨your recommendation⟩"} for b, n in top],
            "surprise": "⟨read the evidence explorer and write what surprised you⟩",
            "what_this_data_cannot_tell_us":
                "Labels come from a deterministic lexicon classifier, not a language model, "
                "so nuance and sarcasm are missed. App-store reviews are also a complaint "
                "channel: quietly satisfied narrow users never appear. Counts indicate "
                "salience, not prevalence."}

    payload = json.dumps({"counts": agg["barriers"], "severity": agg["barrier_severity"],
                          "top_categories": agg["categories"],
                          "competitors": agg["competitors"], "reviews": sample},
                         ensure_ascii=False)[:120000]
    try:
        return parse_json(prov.ask(SYNTH_PROMPT.format(data=payload),
                                   strong=True, max_tokens=4000))
    except Exception as e:
        print(f"  synthesis failed ({type(e).__name__}); writing counts only")
        return {"themes": [], "surprise": None,
                "what_this_data_cannot_tell_us": "Synthesis step did not complete."}


# ══════════════════════════════════════════════════ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default=None,
                    choices=["gemini","anthropic","openai","offline"])
    ap.add_argument("--limit", type=int, default=None,
                    help="analyse only the N most recent reviews (use if quota is tight)")
    a = ap.parse_args()

    name = a.provider
    if not name:                                     # autodetect from environment
        if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
            name = "gemini"
        elif os.environ.get("ANTHROPIC_API_KEY"): name = "anthropic"
        elif os.environ.get("OPENAI_API_KEY"):    name = "openai"
        else:
            name = "offline"
            print("No API key found. Running OFFLINE.")
            print("For a free key: https://aistudio.google.com/apikey\n")

    prov = Provider(name)
    corpus = json.load(open("corpus_raw.json", encoding="utf-8"))
    if a.limit:
        corpus = corpus[:a.limit]          # already sorted newest-first
        print(f"--limit {a.limit}: analysing the {len(corpus)} most recent reviews")
    print(f"Loaded {len(corpus)} reviews | provider: {name}\n")

    gated     = stage2(corpus, prov)
    extracted = stage3(gated, prov)
    agg       = stage4(extracted)
    themes    = stage5(agg, prov)

    out = {"generated_at": time.strftime("%Y-%m-%d %H:%M"),
           "provider": name,
           "funnel": {"collected": len(corpus),
                      "relevant": sum(1 for r in gated if r.get("relevant")),
                      "extracted": len(extracted),
                      "with_barrier": agg["n_with_barrier"]},
           "barriers": agg["barriers"], "barrier_severity": agg["barrier_severity"],
           "categories": agg["categories"], "competitors": agg["competitors"],
           "category_x_barrier": agg["category_x_barrier"],
           "workarounds": agg["workarounds"], "mean_confidence": agg["mean_confidence"],
           "themes": themes,
           "evidence": [{"id": r["id"], "source": r["source"], "rating": r.get("rating"),
                         "date": r.get("date"), "text": r["text"][:600],
                         **{k: r["extraction"].get(k) for k in
                            ("barrier","job_to_be_done","categories_mentioned",
                             "competitor_mentioned","workaround","verbatim","confidence")}}
                        for r in agg["rows"]]}

    json.dump(out, open("analysis.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
    os.makedirs("../app", exist_ok=True)
    with open("../app/corpus.js","w",encoding="utf-8") as f:
        f.write("window.ZEPTO_ANALYSIS = "); json.dump(out, f, ensure_ascii=False); f.write(";")

    print("\n" + "="*55)
    print("FUNNEL")
    for k,v in out["funnel"].items(): print(f"  {k:14s}: {v}")
    print("\nBARRIERS")
    tot = sum(out["barriers"].values()) or 1
    for k,v in out["barriers"].items():
        print(f"  {k:16s}: {v:4d}  ({v/tot*100:4.1f}%)")
    print("\nTOP CATEGORIES : " + ", ".join(list(out["categories"])[:8]))
    print("COMPETITORS    : " + ", ".join(f"{k} {v}" for k,v in list(out["competitors"].items())[:6]))

    # Provenance. If one term is driving most of a barrier, that barrier is an
    # artifact of the lexicon rather than a finding, and you need to know that
    # BEFORE it goes on a slide.
    drivers = collections.defaultdict(collections.Counter)
    for r in agg["rows"]:
        for t in (r["extraction"].get("matched_terms") or []):
            drivers[r["extraction"]["barrier"]][t] += 1
    if drivers:
        print("\nWHAT IS DRIVING EACH LABEL  (audit this before trusting it)")
        for b in out["barriers"]:
            top = drivers[b].most_common(4)
            if not top: continue
            tot = sum(drivers[b].values()) or 1
            share = top[0][1] / tot
            flag = "   <-- one term dominates, check for false positives" if share > .6 else ""
            print(f"  {b:16s} " + ", ".join(f"'{t}' x{n}" for t, n in top) + flag)

    print("\nSanity check before building on this:")
    print("  open corpus_raw.csv, read 20 reviews the engine labelled with a barrier,")
    print("  and ask whether you agree. 3_validate.py turns that into a number.")
    print("\nWrote analysis.json and ../app/corpus.js")
    print("Next: python 3_validate.py sample")


if __name__ == "__main__":
    main()
