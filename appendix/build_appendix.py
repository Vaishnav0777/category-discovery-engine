#!/usr/bin/env python3
"""Builds the research appendix as .docx. Drag into Google Drive -> opens as a Doc.
Contains no name, per the submission guidelines."""

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

MID = RGBColor(0x5B, 0x2D, 0x90)
GREY = RGBColor(0x60, 0x5A, 0x70)
INK = RGBColor(0x1C, 0x15, 0x26)

doc = Document()

# base style
st = doc.styles["Normal"]
st.font.name = "Calibri"; st.font.size = Pt(11); st.font.color.rgb = INK
st.paragraph_format.space_after = Pt(8)
st.paragraph_format.line_spacing = 1.15

for lvl, size in [(1, 20), (2, 15), (3, 12.5)]:
    h = doc.styles[f"Heading {lvl}"]
    h.font.name = "Calibri"; h.font.size = Pt(size); h.font.bold = True
    h.font.color.rgb = MID if lvl < 3 else INK
    h.paragraph_format.space_before = Pt(18 if lvl == 1 else 14)
    h.paragraph_format.space_after = Pt(6)

sec = doc.sections[0]
sec.left_margin = sec.right_margin = Inches(1.0)
sec.top_margin = sec.bottom_margin = Inches(0.9)


def para(text, bold=False, italic=False, size=11, color=None, space=8):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space)
    r = p.add_run(text); r.bold = bold; r.italic = italic
    r.font.size = Pt(size); r.font.color.rgb = color or INK
    return p


def bullets(items, style="List Bullet"):
    for it in items:
        p = doc.add_paragraph(style=style)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(it); r.font.size = Pt(11)


def table(headers, rows, widths):
    """Dual widths — column widths on the table AND on every cell, in inches.
    Percentage widths break when the file is opened in Google Docs."""
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.LEFT
    t.autofit = False
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]; c.width = Inches(widths[i])
        c.text = ""
        r = c.paragraphs[0].add_run(h)
        r.bold = True; r.font.size = Pt(10); r.font.color.rgb = MID
        c.paragraphs[0].paragraph_format.space_after = Pt(2)
        sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear")
        sh.set(qn("w:fill"), "F1EEF7"); c._tc.get_or_add_tcPr().append(sh)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].width = Inches(widths[i])
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v))
            r.font.size = Pt(10)
            cells[i].paragraphs[0].paragraph_format.space_after = Pt(2)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return t


# ══════════════════════════════════════════════════ title
t = doc.add_paragraph(); t.paragraph_format.space_after = Pt(2)
r = t.add_run("Research Appendix"); r.bold = True
r.font.size = Pt(26); r.font.color.rgb = MID; r.font.name = "Calibri"

s = doc.add_paragraph(); s.paragraph_format.space_after = Pt(16)
r = s.add_run("Increasing the share of monthly active customers who purchase from at least "
              "one new category each month · Zepto · Graduation Project, July 2026")
r.font.size = Pt(11.5); r.font.color.rgb = GREY

para("This document holds the working evidence behind the submitted deck: the discovery-engine "
     "method and full results, the validation protocol and its scores, the user-research "
     "instrument, six interview records, and the synthesis. It exists so that any claim in the "
     "deck can be traced to something checkable.", size=11)

para("Everything here is reproducible. The engine is three Python scripts; the validation sample "
     "is drawn with a fixed seed; the classified corpus is browsable in the deployed app.", size=11)

# ══════════════════════════════════════════════════ 1
doc.add_heading("1 · The discovery engine", level=1)

doc.add_heading("Method", level=2)
para("Six stages. Stages 2 and 3 do the classification; stage 6 is what makes the other five "
     "believable.")
table(["Stage", "What it does", "How"],
      [["1 · Ingest", "Google Play reviews, deduped, provenance logged", "python"],
       ["2 · Relevance gate", "Binary screen, tuned for recall. Most reviews are delivery or price and carry no discovery signal", "lexicon / LLM"],
       ["3 · Extract", "JTBD, categories, barrier code, competitor, workaround, verbatim, confidence", "lexicon / LLM"],
       ["4 · Aggregate", "Frequency, severity from star rating, category × barrier co-occurrence", "python"],
       ["5 · Synthesise", "Themes ranked by strategic weight, each carrying review IDs", "python / LLM"],
       ["6 · Validate", "Blind hand-labelled hold-out. Precision, recall, F1, Cohen's kappa, confusion matrix, negative control", "human + python"]],
      [1.2, 3.9, 1.3])

doc.add_heading("Three design decisions worth defending", level=2)
bullets([
 "A separate, cheap relevance gate. Roughly four in five reviews are about delivery time, price or "
 "bugs. Screening them out first cuts extraction cost by most of the corpus. The gate fails open: "
 "on genuine uncertainty it returns YES, because a false positive costs one extra classification "
 "and a false negative loses the signal permanently. Asymmetric error, asymmetric threshold.",
 "A closed barrier taxonomy, not open coding. Seven fixed codes. A closed set is countable, "
 "comparable across runs, and can be scored against a human. Open coding produces labels that "
 "cannot be measured.",
 "Every row must carry a verbatim quote copied character-for-character from the source. If the "
 "quote is not found in the source text, the row is dropped automatically. That makes fabrication "
 "detectable rather than invisible.",
])

doc.add_heading("Corpus and provenance", level=2)
table(["Field", "Value"],
      [["Source", "Google Play Store, com.zeptoconsumerapp"],
       ["Reviews collected", "3,000"],
       ["Date range", "20 July – 1 August 2026"],
       ["Mean length", "14.6 words"],
       ["Mean rating", "3.38 / 5"],
       ["Apple App Store", "Attempted; the RSS feed returned empty. Corpus is Android-only — a stated limitation."],
       ["Classifier used", "Deterministic lexicon (free-tier LLM quota was exhausted mid-run)"]],
      [1.9, 4.5])

doc.add_heading("Funnel", level=2)
table(["Stage", "n", "Note"],
      [["Collected", "3,000", "after dedupe"],
       ["Passed relevance gate", "628", "21% of collected"],
       ["Carry a discovery barrier", "107", "3.6% of collected — and validation indicates this is an overcount"]],
      [2.2, 0.9, 3.3])

doc.add_heading("Results", level=2)
table(["Barrier", "n", "% of 107", "Terms that drove the label"],
      [["B4 Assortment", "51", "47.7%", "not available ×21, dont have ×12, unavailable ×8, out of stock ×6"],
       ["B1 Trust", "41", "38.3%", "expired product ×17, expiry date ×13, dont trust ×4, fake product ×3"],
       ["B5 Occasion", "6", "5.6%", "last minute ×3, in the middle of, forgot to, forget to"],
       ["B3 Price risk", "6", "5.6%", "waste of money ×6"],
       ["B6 Awareness", "3", "2.8%", "didnt know ×3"],
       ["B2 Fit", "0", "0%", "no term matched in any of the 628 relevant reviews"]],
      [1.3, 0.5, 0.8, 3.8])

para("Categories mentioned most: vegetables, fruits, perfume, dairy, cosmetics, shampoo.")
para("Competitor mentions across the entire relevant corpus: Blinkit 2, Amazon 2. Nykaa: zero.")

doc.add_heading("Reading the results honestly", level=2)
bullets([
 "What was coded as trust is not deliberation trust. The terms driving it are expiry and "
 "authenticity: goods received in poor condition or suspected of being counterfeit. That is a "
 "fulfilment complaint, not hesitation before a purchase.",
 "Fit scored zero across 628 relevant reviews. Nobody describes being unable to choose between "
 "products.",
 "Four competitor mentions in the whole corpus. The hypothesis that users research on Nykaa and "
 "then purchase there has no support in this data.",
 "The mechanism: app-store reviews are written about orders that happened. A category a user never "
 "entered produces no order, no complaint and no review. A non-purchase cannot be observed in a "
 "record of purchases. The silence is a structural property of the instrument, not a gap in the data.",
])

# ══════════════════════════════════════════════════ 2
doc.add_heading("2 · Validation", level=1)

para("A classifier will label thousands of rows and return a clean chart whether or not the labels "
     "mean anything. The chart looks identical either way. So the labels were scored against a human.")

doc.add_heading("Protocol", level=2)
bullets([
 "Stratified hold-out drawn by the model's own label, so rare barriers appear in the sample. "
 "Unstratified sampling from a skewed distribution returns mostly the majority class and says "
 "nothing about the classes that matter. Fixed seed (42), so the sample is reproducible.",
 "Hand-labelled blind against the same seven codes, before viewing any classifier output.",
 "Scored on per-barrier precision, recall and F1 rather than accuracy alone, which is inflated by "
 "the majority class.",
 "Cohen's kappa, which corrects agreement for chance. Across seven classes, raw agreement flatters.",
 "Full confusion matrix reported, because which pair is confused matters more than the headline.",
 "Negative control: reviews the gate rejected, checked for leakage into the classified set.",
])

doc.add_heading("Results", level=2)
table(["Measure", "Value", "Reading"],
      [["Hand-labelled", "30", "Partial hold-out; reported as n=30, not rounded up"],
       ["Raw agreement", "53.3%", "Across 7 classes"],
       ["Cohen's kappa", "0.319", "Fair. Below substantial. Reported as-is."],
       ["Negative-control leakage", "0 of 20", "The gate is not manufacturing signal"]],
      [1.9, 1.0, 3.5])

doc.add_heading("Per-barrier scores", level=2)
table(["Barrier", "n", "Precision", "Recall", "F1"],
      [["B1 Trust", "7", "0.750", "0.429", "0.545"],
       ["B2 Fit", "0", "—", "—", "—"],
       ["B3 Price risk", "0", "0.000", "—", "—"],
       ["B4 Assortment", "3", "0.600", "1.000", "0.750"],
       ["B5 Occasion", "0", "0.000", "—", "—"],
       ["B6 Awareness", "0", "0.000", "—", "—"],
       ["B7 None", "20", "0.833", "0.500", "0.625"]],
      [1.5, 0.6, 1.1, 1.0, 1.0])

doc.add_heading("Disagreements", level=2)
table(["Human said", "Classifier said", "n"],
      [["B7 None", "B5 Occasion", "3"],
       ["B7 None", "B4 Assortment", "2"],
       ["B7 None", "B3 Price risk", "2"],
       ["B7 None", "B6 Awareness", "2"],
       ["B7 None", "B1 Trust", "1"],
       ["B1 Trust", "B7 None", "2"],
       ["B1 Trust", "B5 Occasion", "1"],
       ["B1 Trust", "B3 Price risk", "1"]],
      [2.0, 2.0, 0.8])

para("The errors run in one direction. Ten of the disagreements are the classifier finding a "
     "barrier where the human saw none; three are the reverse. It over-triggers, firing on keywords "
     "out of context. The practical consequence: the 107 barrier count is an upper bound, and the "
     "true signal in this corpus is thinner still.", bold=False)

doc.add_heading("A bug the audit caught", level=2)
para("The first run reported trust as 71% of all barriers. It was a clean, confident chart and "
     "nothing about it looked wrong.")
bullets([
 "The classifier was made to report which term fired on every row. Trust was being driven by the "
 "bare words “review” and “rating”, which in app-store data mostly appear as self-reference — "
 "“writing this review”, “giving 1 star rating”. Neither says anything about trusting a product.",
 "The same audit exposed a second bug: substring matching had made “cat” the top category, because "
 "it matches inside “category”, “location” and “complicated”.",
 "Both were fixed — trust cues now require product context, and all term matching is on word "
 "boundaries. On the second run trust fell to 38% and its meaning changed entirely, from reviews "
 "to expiry. Assortment overtook it.",
])
para("This is the reason the validation step exists. Without it, the 71% figure would have gone "
     "into the deck as a finding.", italic=True)

# ══════════════════════════════════════════════════ 3
doc.add_heading("3 · User research", level=1)

doc.add_heading("Recruiting and screener", level=2)
para("Recruited on behaviour rather than demographics, because behaviour is what predicts the "
     "problem. Participants had to pass all four:")
bullets(["Orders on a quick-commerce app at least twice a week",
         "Has used it for 12 months or more",
         "Describes a narrow, repeating purchase list",
         "Cannot recall recently buying from a category new to them"])
para("Six interviews, 25–30 minutes each, conducted by phone. Consent given for anonymised quotes. "
     "Names below are first names only.")

doc.add_heading("Interview guide", level=2)
para("Structured to get behaviour rather than opinion. Three rules held throughout: ask about the "
     "last specific time rather than what someone “usually” does; never use the word “would”, "
     "because people predict their own behaviour badly and describe it well; and describe the "
     "proposed solution only at the very end, so it cannot contaminate everything before it.")
bullets([
 "Open the app and read me your last five orders. How much of that is the same every time?",
 "Walk me through the last order start to finish. Where were you, how long did it take?",
 "When did you last buy something on there you'd never bought before? What made you try it?",
 "Name something you buy regularly but have never bought on this app, even though they sell it. "
 "Where do you buy it instead? Walk me through the last time.",
 "What would have to be true before you'd buy that here? And if the price were identical?",
 "Last time you bought something you weren't sure about, what did you do before buying? What were "
 "you actually trying to find out?",
 "(Last) Here is the proposed feature. What's wrong with it? When would it most annoy you?",
])

doc.add_heading("Participants", level=2)
table(["#", "Profile", "Frequency", "Repertoire"],
      [["P1", "Ananya, 28, software engineer, Bengaluru", "4–5 / week", "Milk, coffee, snacks"],
       ["P2", "Rohan, 22, student, Delhi NCR", "3–4 / week", "Late-night snacks, beverages"],
       ["P3", "Meera, 36, homemaker, Mumbai", "5–6 / week", "Fresh vegetables, cooking essentials"],
       ["P4", "Vikram, 31, product marketing, Gurgaon", "3 / week", "Groceries, party supplies, office tech"],
       ["P5", "Sneha, 25, designer, Hyderabad", "2–3 / week", "Organic produce, health foods"],
       ["P6", "Siddharth, 34, finance, Pune", "2 / week", "Party mixers, ice, snacks"]],
      [0.5, 2.6, 1.0, 2.3])

doc.add_heading("Records", level=2)
for name, browse, barrier, trigger in [
 ("P1 · Ananya, 28, software engineer, Bengaluru",
  "Goal-directed, under 30 seconds a session. Skips home banners entirely.",
  "Uses dedicated platforms for beauty because of detailed reviews. Sceptical about returns and "
  "warranties on higher-value electronics.",
  "Immediate necessity — bought a charger cable when hers broke just before travel."),
 ("P2 · Rohan, 22, student, Delhi NCR",
  "Open to discounts and cross-selling in the cart.",
  "Buys household supplies in bulk offline to save money.",
  "Impulse deals and low-friction cart recommendations — bought face wash from a 20%-off checkout banner."),
 ("P3 · Meera, 36, homemaker, Mumbai",
  "Functional daily re-ordering.",
  "Hesitant on toys, home decor and stationery: generic stock images, no size or quality specs. "
  "Prefers Amazon for detailed reviews.",
  "Verified user reviews, high-resolution photos, clear product dimensions on the product page."),
 ("P4 · Vikram, 31, product marketing, Gurgaon",
  "Speed-focused utility buyer.",
  "A “pantry replenishment mindset” stops him remembering that beauty and grooming products exist "
  "on the app at all.",
  "High-urgency utility needs — mousepads, HDMI cables — and context-based prompts."),
 ("P5 · Sneha, 25, designer, Hyderabad",
  "Quality-conscious inspector.",
  "Abandoned a health-supplement purchase because seller authorisation and nutritional information "
  "were not clearly visible.",
  "Verified seller badges, readable ingredient labels, customer rating summaries."),
 ("P6 · Siddharth, 34, finance, Pune",
  "Strictly weekend entertainment orders.",
  "Uses offline supermarkets for routine monthly groceries out of habit.",
  "Contextual bundling at cart checkout — suggesting morning-after items alongside party supplies."),
]:
    doc.add_heading(name, level=3)
    for lab, txt in [("Browsing behaviour", browse), ("Barrier to expansion", barrier),
                     ("What triggered expansion", trigger)]:
        p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(4)
        r = p.add_run(lab + ": "); r.bold = True; r.font.size = Pt(10.5)
        r2 = p.add_run(txt); r2.font.size = Pt(10.5)

doc.add_heading("Synthesis", level=2)
para("Two patterns held across the six, and one of them overturned a design decision.")

doc.add_heading("Finding 1 — the barrier sits on the product page, not in discovery", level=3)
para("Three of six named the same gap unprompted: no verified reviews, generic stock images, "
     "missing specifications and dimensions, no seller verification, no ingredient information. Two "
     "named the destination they go to instead and gave the identical reason — reviews. One "
     "abandoned a purchase mid-flow over it.")
para("A fourth described the mode-lock directly: a “pantry replenishment mindset” that prevents him "
     "recalling that beauty products exist on the app. He is aware they exist; he does not remember "
     "in the moment. That is consistent with the engine finding only three awareness mentions in "
     "3,000 reviews — awareness was never the binding constraint.")

doc.add_heading("Finding 2 — expansion happens at the cart, never while browsing", level=3)
para("Two of six had already entered a new category through a checkout prompt. A third asked for "
     "contextual cart bundling by name, unprompted. Two more expanded through immediate utility "
     "need. None expanded by browsing; one skips home banners entirely.")
para("Critically, nobody described anything resembling a post-delivery moment.")

doc.add_heading("What this changed", level=2)
table(["Claim going in", "What users said", "Verdict"],
      [["The barrier is deliberation, not awareness",
        "3 of 6 named a product-page information gap; awareness never raised as a blocker",
        "Confirmed, and located more precisely"],
       ["Users research on a competitor, then buy there",
        "2 of 6 described exactly this, for beauty and for toys/decor",
        "Confirmed in interviews; not visible in review data"],
       ["The right surface is the post-payment delivery-tracking screen",
        "Nobody mentioned any post-delivery moment. Two had converted via checkout prompts; one asked for cart bundling by name",
        "Challenged — the design moved to the cart"]],
      [1.9, 3.0, 1.5])

para("The MVP surface was changed as a result. The original design placed the card on the "
     "delivery-tracking screen, reasoning that the basket had already converted and so carried zero "
     "cannibalisation risk. No participant supported that. Moving to the cart follows the evidence "
     "and reintroduces the risk that the original design had engineered away — which is why "
     "cart-to-order conversion became the hardest guardrail, with a stopping rule agreed before the "
     "test begins.")

# ══════════════════════════════════════════════════ 4
doc.add_heading("4 · Limitations", level=1)
bullets([
 "n=6. A small sample, stated as small. The pattern held across all six, but six people cannot size "
 "a population.",
 "n=30 on the validation hold-out, with kappa at 0.319 — fair, below substantial. The direction of "
 "the error is diagnosed (systematic over-triggering) but the classifier is not reliable at the "
 "row level. Conclusions drawn from it are directional and were cross-checked against interviews.",
 "A deterministic lexicon classifier was used rather than a language model, because free-tier API "
 "quota was exhausted mid-run. It misses nuance, sarcasm and paraphrase, and would very likely "
 "under-recall the fit and occasion codes in particular. The pipeline supports either; given more "
 "time both label sets would be scored against the same hold-out to quantify the cost.",
 "Android-only corpus. The Apple App Store feed returned empty.",
 "A 12-day collection window. This is a snapshot, not a trend.",
 "App-store reviews are a complaint channel. Users who are quietly satisfied and quietly narrow — "
 "precisely the target segment — do not write reviews. Frequency counts here indicate salience, "
 "not prevalence, and were used to rank hypotheses rather than to size anything.",
 "Segment sizing is not attempted. It requires internal cohort data: users with 12+ months' tenure, "
 "5+ orders in the trailing 30 days, and zero first-time-category purchases in 60 days.",
])

# ══════════════════════════════════════════════════ 5
doc.add_heading("5 · Sources", level=1)
bullets([
 "Zepto DRHP analysis — category cohort breadth (2.6 categories in month one to 18.0 by month 23, "
 "April 2024 cohort), annual transacting users, per-order economics: "
 "finixschool.substack.com/p/inside-zepto-how-the-business-actually",
 "Zepto DRHP, further detail — sequential ATU decline, delivery times, CCPA dark-patterns notice: "
 "tradebrains.in/zepto-ipo-here-are-10-hidden-things-in-the-drhp-that-most-investors-will-miss",
 "India quick-commerce market and category mix, CY25–CY30: "
 "mordorintelligence.com/industry-reports/q-commerce-industry-in-india",
])

doc.add_heading("Reproducing the engine", level=2)
for line in ["pip install google-play-scraper",
             "python3 1_collect.py            # ingest + provenance log",
             "python3 2_analyse.py            # stages 2–5, writes analysis.json",
             "python3 3_validate.py sample    # draws the blind hold-out",
             "#   ... hand-label validation_sheet.csv ...",
             "python3 3_validate.py score     # precision / recall / kappa / confusion"]:
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(1)
    r = p.add_run(line); r.font.name = "Consolas"; r.font.size = Pt(9.5); r.font.color.rgb = GREY

doc.save("NL Zepto - Research Appendix.docx")
print("wrote NL Zepto - Research Appendix.docx")
