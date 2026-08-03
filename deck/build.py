#!/usr/bin/env python3
"""Builds 'NL Zepto.pptx'. Palette is Okabe-Ito based (colour-blind safe).
Every font size is >= 14pt, per the submission guidelines."""

from pptx import Presentation
from pptx.util import Inches as I, Pt
from pptx.dml.color import RGBColor as C
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_TICK_MARK

INK=C(0x1C,0x15,0x26); DEEP=C(0x3B,0x1F,0x5C); MID=C(0x5B,0x2D,0x90)
PAPER=C(0xFF,0xFF,0xFF); WASH=C(0xF7,0xF5,0xFB); GREY=C(0x60,0x5A,0x70)
LINE=C(0xE3,0xDF,0xEC); CARD2=C(0x4A,0x2A,0x70); CARD2L=C(0x6B,0x4A,0x93)
BLU=C(0x00,0x72,0xB2); ORA=C(0xE6,0x9F,0x00); GRN=C(0x00,0x9E,0x73)
ROSE=C(0xCC,0x79,0xA7); SKY=C(0x56,0xB4,0xE9); SLATE=C(0x8C,0x8A,0x97)
LILAC=C(0xD7,0xCD,0xE8); LILAC2=C(0xE0,0xD6,0xEF); LILAC3=C(0xCF,0xC3,0xE4)
AMBER=C(0xE6,0x9F,0x00)          # amber == a value you must replace
CREAM=C(0xFD,0xF6,0xE8); TINT=C(0xF1,0xEE,0xF7); PROTO=C(0xFB,0xF9,0xFE)

H="Cambria"; B="Calibri"

prs=Presentation(); prs.slide_width=I(13.333); prs.slide_height=I(7.5)
BLANK=prs.slide_layouts[6]


def slide(dark=False):
    s=prs.slides.add_slide(BLANK)
    s.background.fill.solid(); s.background.fill.fore_color.rgb = DEEP if dark else PAPER
    return s


def text(s,t,x,y,w,h,size=14,bold=False,italic=False,color=INK,face=B,
         space=None,ls=None,align=None,bullets=False,link=None):
    """t: str, or list of str for bullets/paragraphs."""
    box=s.shapes.add_textbox(I(x),I(y),I(w),I(h)); tf=box.text_frame
    tf.word_wrap=True
    tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
    items = t if isinstance(t,list) else [t]
    for i,item in enumerate(items):
        p = tf.paragraphs[0] if i==0 else tf.add_paragraph()
        if ls: p.line_spacing=Pt(ls)
        if align: p.alignment=align
        if bullets: p.space_after=Pt(5)
        for j,seg in enumerate(item.split("\n")):
            if j: p=tf.add_paragraph(); p.line_spacing=Pt(ls) if ls else p.line_spacing
            r=p.add_run(); r.text=("•  "+seg if bullets and j==0 else seg)
            f=r.font; f.size=Pt(size); f.bold=bold; f.italic=italic
            f.color.rgb=color; f.name=face
            if space is not None: f._rPr.set('spc',str(int(space*100)))
            if link: r.hyperlink.address=link
    return box


def rect(s,x,y,w,h,fill,edge=None,radius=0.055,sharp=False):
    sh=s.shapes.add_shape(MSO_SHAPE.RECTANGLE if sharp else MSO_SHAPE.ROUNDED_RECTANGLE,
                          I(x),I(y),I(w),I(h))
    if not sharp:
        try: sh.adjustments[0]=radius
        except Exception: pass
    sh.fill.solid(); sh.fill.fore_color.rgb=fill
    if edge: sh.line.color.rgb=edge; sh.line.width=Pt(0.75)
    else:    sh.line.fill.background()
    sh.shadow.inherit=False
    if sh.has_text_frame: sh.text_frame.text=""
    return sh


def kicker(s,t,dark=False):
    text(s,t,0.62,0.24,12.1,0.3,14,True,color=SKY if dark else MID,space=1.4)

def title(s,t,dark=False,size=30):
    text(s,t,0.62,0.62,12.1,1.15,size,True,color=PAPER if dark else INK,face=H,ls=size+7)

def foot(s,t,dark=False):
    text(s,t,0.62,6.94,12.1,0.4,14,color=SLATE if dark else GREY,ls=16)

def notes(s,t):
    s.notes_slide.notes_text_frame.text=t


def style_chart(ch,label_size=14):
    ch.font.size=Pt(label_size); ch.font.name=B; ch.font.color.rgb=GREY
    ch.has_legend=False
    try:
        va=ch.value_axis
        va.has_major_gridlines=True
        gl=va.major_gridlines.format.line; gl.color.rgb=LINE; gl.width=Pt(0.75)
        va.format.line.color.rgb=LINE
        va.major_tick_mark=XL_TICK_MARK.NONE; va.minor_tick_mark=XL_TICK_MARK.NONE
        va.tick_labels.font.size=Pt(label_size); va.tick_labels.font.name=B
        va.tick_labels.font.color.rgb=GREY
    except Exception: pass
    try:
        ca=ch.category_axis
        ca.has_major_gridlines=False
        ca.format.line.color.rgb=LINE
        ca.major_tick_mark=XL_TICK_MARK.NONE; ca.minor_tick_mark=XL_TICK_MARK.NONE
        ca.tick_labels.font.size=Pt(label_size); ca.tick_labels.font.name=B
        ca.tick_labels.font.color.rgb=INK
    except Exception: pass


# ══════════════════════════════════════════════════════ 1 · TITLE
s=slide(True)
text(s,"GRADUATION PROJECT  ·  GROWTH  ·  JUL 2026",0.75,0.72,11,0.3,14,True,color=SKY,space=1.8)
text(s,"Zepto users already reach 18 categories.\nThe problem is the month they stop.",
     0.75,1.42,11.6,2.2,38,True,color=PAPER,face=H,ls=48)
text(s,"Getting more monthly actives into a new category — by fixing the thing Zepto's own speed broke.",
     0.75,3.72,10.9,0.5,17,color=LILAC)
for i,(n,l) in enumerate([("47.97M","annual transacting users, FY26"),
                          ("₹59.40","lost per order, Q4FY26"),
                          ("29% → 44%","non-grocery share of q-commerce GMV, CY25→CY30")]):
    x=0.75+i*3.95
    rect(s,x,4.62,3.6,1.34,CARD2,CARD2L)
    text(s,n,x+0.28,4.78,3.1,0.55,25,True,color=ORA,face=H)
    text(s,l,x+0.28,5.32,3.05,0.6,14,color=LILAC3,ls=16)
foot(s,"All figures from Zepto's DRHP (July 2026) and published quick-commerce market research. Sources on the final slide.",True)
notes(s,"Opening: Zepto's category problem is usually told as a habit story. The DRHP says otherwise, and that changes what you build.")

# ══════════════════════════════════════════════════════ 2 · REFRAME
s=slide(); kicker(s,"THE REFRAME")
title(s,"Breadth isn't the problem. The rate of new categories per month is — and it has already fallen 30%.")

cd=CategoryChartData(); cd.categories=["Month 1","Month 12","Month 23"]
cd.add_series("Categories purchased",(2.6,12.0,18.0))
gf=s.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS,I(0.62),I(1.95),I(6.5),I(3.95),cd)
ch=gf.chart; style_chart(ch)
ser=ch.plots[0].series[0]
ser.format.line.color.rgb=MID; ser.format.line.width=Pt(3.25)
ser.marker.format.fill.solid(); ser.marker.format.fill.fore_color.rgb=MID
ch.plots[0].has_data_labels=True
dl=ch.plots[0].data_labels; dl.font.size=Pt(14); dl.font.name=B; dl.font.bold=True
dl.font.color.rgb=INK; dl.position=XL_LABEL_POSITION.ABOVE
ch.value_axis.maximum_scale=20
ch.has_title=True; ch.chart_title.text_frame.text="Categories purchased per user · April 2024 cohort"
tr=ch.chart_title.text_frame.paragraphs[0].runs[0].font
tr.size=Pt(14); tr.name=B; tr.color.rgb=GREY; tr.bold=False

rect(s,7.4,1.95,5.3,1.72,WASH,LINE)
text(s,"Months 1 – 12",7.68,2.1,2.4,0.3,14,True,color=GREY)
text(s,"0.78",7.68,2.4,2.4,0.6,32,True,color=BLU,face=H)
text(s,"new categories / month",7.68,3.0,2.5,0.5,14,color=GREY,ls=16)
text(s,"Months 12 – 23",10.22,2.1,2.4,0.3,14,True,color=GREY)
text(s,"0.55",10.22,2.4,2.4,0.6,32,True,color=ORA,face=H)
text(s,"a 30% collapse in rate",10.22,3.0,2.5,0.5,14,color=GREY,ls=16)

rect(s,7.4,3.85,5.3,2.15,CREAM,C(0xF0,0xE0,0xB8))
text(s,"Why the obvious answer is wrong",7.68,4.0,4.8,0.32,16,True,color=INK)
text(s,["“Users are stuck in a habit loop, so show them more.” But they add 15 categories in two years. They are not stuck.",
        "The goal is a monthly rate, not a lifetime total. A flattening cumulative curve is a rate approaching zero.",
        "So the question is what is different about the categories still left after month 12."],
     7.68,4.38,4.78,1.5,14,color=INK,ls=16,bullets=True)
foot(s,"Three points are disclosed in Zepto's DRHP (2.6 at month 1, 12+ at month 12, 18.0 at month 23). The rates are arithmetic on those figures; the intermediate curve shape is not disclosed and is not assumed.")
notes(s,"The rate arithmetic is the whole slide: 9.4 categories added over 11 months, then 6.0 over the next 11.")

# ══════════════════════════════════════════════════════ 3 · THE ENGINE
s=slide(); kicker(s,"PART 1 · THE DISCOVERY ENGINE")
title(s,"A six-stage pipeline that reads 3,000 reviews and cites a checkable source for every claim.")

for i,(n,t,d,m) in enumerate([
    ("1","Ingest","Play Store + App Store, deduped, provenance logged","python"),
    ("2","Relevance gate","Binary screen tuned for recall. ~9 in 10 reviews are delivery or price","haiku"),
    ("3","Extract","JTBD, category, barrier code, competitor, workaround, verbatim","sonnet · strict JSON"),
    ("4","Aggregate","Frequency, severity from star rating, category × barrier","python"),
    ("5","Synthesise","Themes ranked by strategic weight, each carrying review IDs","sonnet"),
    ("6","Validate","60-review blind hold-out, hand-labelled. Precision, recall, kappa","human")]):
    x=0.62+i*2.03; dk=(i==5)
    rect(s,x,1.98,1.92,2.48,DEEP if dk else WASH,DEEP if dk else LINE)
    text(s,n,x+0.17,2.1,0.6,0.3,14,True,color=SKY if dk else MID)
    text(s,t,x+0.17,2.4,1.6,0.5,15,True,color=PAPER if dk else INK)
    text(s,d,x+0.17,2.92,1.6,1.2,14,color=LILAC3 if dk else GREY,ls=15)
    text(s,m,x+0.17,4.1,1.6,0.3,14,color=SKY if dk else SLATE)

for i,(t,d) in enumerate([
  ("Why a separate cheap gate","Cuts extraction spend by ~90% at almost no recall cost, and makes the funnel legible. It fails open: on genuine uncertainty it returns YES, because a false positive costs one API call and a false negative loses the signal forever."),
  ("Why a closed taxonomy","Seven fixed barrier codes, not open coding. A closed set is countable, comparable, and can be scored against a human. Open coding produces labels you cannot measure."),
  ("Why every row carries a verbatim","The quote must appear character-for-character in the source or the row is dropped automatically. That makes hallucination detectable instead of invisible.")]):
    x=0.62+i*4.06
    rect(s,x,4.76,3.88,1.95,WASH,LINE)
    text(s,t,x+0.26,4.92,3.4,0.32,15,True,color=MID)
    text(s,d,x+0.26,5.28,3.38,1.35,14,color=INK,ls=15)
foot(s,"A live, runnable version of every stage — including a classifier you can paste any review into — is linked on the final slide.")
notes(s,"This is the required workflow slide. Emphasise stage 6: validation is what makes the other five believable.")

# ══════════════════════════════════════════════════════ 4 · FINDINGS
s=slide(); kicker(s,"PART 1 · WHAT THE ENGINE FOUND")
title(s,"The barriers everyone assumes are the cheap ones. The stubborn two cannot be merchandised away.")

cd=CategoryChartData()
cd.categories=["Occasion","Price risk","Awareness","Assortment","Fit","Trust"]
cd.add_series("Reviews",(15,25,40,51,78,92))
gf=s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED,I(0.62),I(1.98),I(6.6),I(3.4),cd)
ch=gf.chart; style_chart(ch)
pl=ch.plots[0]; pl.gap_width=48; pl.has_data_labels=True
dl=pl.data_labels; dl.font.size=Pt(14); dl.font.name=B; dl.font.bold=True
dl.font.color.rgb=INK; dl.position=XL_LABEL_POSITION.OUTSIDE_END
ser=pl.series[0]; ser.format.fill.solid(); ser.format.fill.fore_color.rgb=BLU
for idx,col in [(2,SLATE),(3,SLATE)]:                # awareness + assortment
    pt=ser.points[idx]; pt.format.fill.solid(); pt.format.fill.fore_color.rgb=col
ch.has_title=True
ch.chart_title.text_frame.text="Reviews carrying each barrier   ⟨replace with your own run⟩"
tr=ch.chart_title.text_frame.paragraphs[0].runs[0].font
tr.size=Pt(14); tr.name=B; tr.color.rgb=AMBER; tr.bold=False

rect(s,0.66,5.48,0.17,0.17,BLU,sharp=True)
text(s,"Deliberation barriers — no merchandising fix exists",0.95,5.42,5.4,0.3,14,color=INK)
rect(s,0.66,5.86,0.17,0.17,SLATE,sharp=True)
text(s,"Merchandising barriers — a banner or a supply deal solves these",0.95,5.8,5.9,0.3,14,color=INK)

rect(s,7.45,1.98,5.25,2.42,CREAM,C(0xF0,0xE0,0xB8))
text(s,"The finding that changes the brief",7.72,2.14,4.8,0.32,16,True,color=INK)
text(s,"Awareness and assortment are what a growth team reaches for first — and they are also the cheapest to fix. If they were the binding constraint, this metric would already have moved.\n\nWhat is left is trust and fit: two forms of uncertainty a ten-minute retrieval interface has no mechanism to resolve.",
     7.72,2.54,4.78,1.75,14,color=INK,ls=16)

rect(s,7.45,4.56,5.25,2.16,WASH,LINE)
text(s,"In their words",7.72,4.7,4.8,0.3,15,True,color=MID)
text(s,"⟨REPLACE — paste two real verbatims from your own run, with review IDs. One trust quote, one fit quote. Nine words lands harder than a paragraph.⟩",
     7.72,5.06,4.78,1.5,14,italic=True,color=AMBER,ls=16)
foot(s,"⟨REPLACE the chart values and the caption with your own run: n ingested, n through the gate, n carrying a barrier.⟩")
notes(s,"Do not claim precision this source doesn't have. Reviews indicate salience, not prevalence — say so if asked.")

# ══════════════════════════════════════════════════════ 5 · VALIDATION
s=slide(); kicker(s,"PART 1 + 2 · DOES ANY OF THIS HOLD UP")
title(s,"A model hands you a clean chart whether or not it is right. So I scored it against myself, then against users.")

rect(s,0.62,1.98,6.0,4.76,WASH,LINE)
text(s,"Machine vs. me",0.9,2.14,5.4,0.32,17,True,color=MID)
text(s,"60 reviews, stratified by label, fixed seed. Hand-labelled blind, before seeing any model output.",
     0.9,2.5,5.4,0.5,14,color=GREY,ls=16)
for i,(v,l,d) in enumerate([("⟨0.00⟩","Cohen's kappa","agreement corrected for chance"),
                            ("⟨00%⟩","raw agreement","inflated by the majority class"),
                            ("⟨0/20⟩","negative-control leakage","gate-rejected reviews wrongly given a barrier")]):
    y=2.98+i*0.96
    text(s,v,0.9,y,1.85,0.5,23,True,color=AMBER,face=H)
    text(s,l,2.8,y+0.02,3.5,0.3,15,True,color=INK)
    text(s,d,2.8,y+0.32,3.45,0.5,14,color=GREY,ls=15)
text(s,"Per-barrier precision, recall, F1 and the confusion matrix are in the appendix. Which pair the model confuses matters more than the headline.",
     0.9,5.9,5.4,0.5,14,color=GREY,ls=16)

rect(s,6.9,1.98,5.8,4.76,WASH,LINE)
text(s,"Machine vs. six users",7.18,2.14,5.2,0.32,17,True,color=MID)
text(s,"n=6, recruited on a behavioural screen: 5+ orders/month, 12+ months tenure, no new category in 60+ days — plus one deliberate contrast case.",
     7.18,2.5,5.2,0.65,14,color=GREY,ls=16)
text(s,"ENGINE SAID",7.18,3.24,3.1,0.28,14,True,color=GREY,space=1)
text(s,"USERS SAID",10.5,3.24,2.0,0.28,14,True,color=GREY,space=1)
for i,(a,b) in enumerate([("Trust is the top barrier","⟨Confirmed⟩"),
                          ("Fit is second","⟨…⟩"),
                          ("They research on Nykaa, then buy there","⟨…⟩"),
                          ("Awareness is NOT the blocker","⟨…⟩"),
                          ("Tracking screen is a viable surface","⟨Challenged⟩")]):
    y=3.58+i*0.49
    text(s,a,7.18,y,3.2,0.44,14,color=INK,ls=15)
    text(s,b,10.5,y,2.0,0.44,14,True,color=AMBER)
text(s,"At least one row has to read “Challenged”. If the engine was right about everything, I ran a leading interview.",
     7.18,6.04,5.2,0.42,14,italic=True,color=MID,ls=16)
foot(s,"⟨REPLACE every amber value with your own numbers and findings before submitting.⟩")
notes(s,"If kappa comes out low, report it and say the insight is directional and cross-checked in interviews. Reporting a weak number honestly beats hiding it.")

# ══════════════════════════════════════════════════════ 6 · PROBLEM
s=slide(); kicker(s,"PART 3 · THE PROBLEM")
title(s,"Zepto is a retrieval interface being asked to sell deliberation — so users research elsewhere, then buy there.")

rect(s,0.62,1.92,4.0,2.3,TINT,LINE)
text(s,"THE SEGMENT",0.88,2.08,3.5,0.28,14,True,color=MID,space=1)
text(s,"The Plateaued Regular",0.88,2.4,3.6,0.4,18,True,color=INK,face=H)
text(s,["6+ orders a month","12+ months on the app","A fixed 6–9 category repertoire","No new category in 60+ days"],
     0.88,2.86,3.5,1.25,14,color=INK,ls=17,bullets=True)

rect(s,4.82,1.92,7.88,2.3,WASH,LINE)
text(s,"THE ROOT CAUSE",5.1,2.08,7.2,0.28,14,True,color=MID,space=1)
text(s,"The ten-minute promise sets the user's mental mode to task execution, and the app has no mechanism for resolving uncertainty. The categories left unentered after month 12 are exactly the ones carrying personal consequence and regret risk — sunscreen, a first protein powder, a new puppy's food, a baby's first solids.",
     5.1,2.42,7.3,1.1,15,color=INK,ls=18)
text(s,"Zepto's greatest strength is the direct cause of the metric it is now trying to move.",
     5.1,3.56,7.3,0.42,15,True,italic=True,color=MID)

text(s,"WHAT USERS DO INSTEAD",0.62,4.42,6.0,0.28,14,True,color=GREY,space=1)
for i,(a,b) in enumerate([
    ("Research on Google, YouTube, Instagram","…then buy on the platform they researched on"),
    ("Ask a friend or family on WhatsApp","Borrowed trust, because the app supplies none"),
    ("Buy the brand they physically saw somewhere","Shelf presence as a substitute for a review"),
    ("Keep a mental “not from Zepto” list","Zepto is for consumables; everything else is elsewhere")]):
    x=0.62+(i%2)*6.28; y=4.78+(i//2)*1.0
    rect(s,x,y,6.06,0.88,WASH,LINE)
    text(s,a,x+0.24,y+0.11,5.6,0.3,15,True,color=INK)
    text(s,b,x+0.24,y+0.44,5.6,0.34,14,color=GREY)
foot(s,"Every workaround costs the user real time and they are still doing it — the strongest evidence the problem is worth solving.")
notes(s,"Land the line: Zepto does the demand-generation work and Amazon banks it.")

# ══════════════════════════════════════════════════════ 7 · BUSINESS CASE
s=slide(True); kicker(s,"WHY NOW",True)
title(s,"This is not a growth metric. It is the only margin lever left that does not require buying more users.",True)
for i,(n,d,col) in enumerate([
  ("49.54M → 47.97M","Annual transacting users fell sequentially in Q4FY26 while quarterly orders rose from 167M to 210M. Acquisition is slowing; growth now has to come from existing users going wider.",ORA),
  ("₹59.40","Lost per order in Q4FY26. Blinkit made ₹1.35 on theirs. Every incremental order in a low-margin staple deepens the hole.",ROSE),
  ("29% → 39–44%","Non-grocery share of quick-commerce GMV, CY25 to CY30. The higher-margin categories — and the ones a retrieval interface cannot sell.",GRN)]):
    x=0.62+i*4.06
    rect(s,x,2.05,3.88,3.05,CARD2,CARD2L)
    text(s,n,x+0.3,2.28,3.35,0.75,25,True,color=col,face=H,ls=29)
    text(s,d,x+0.3,3.12,3.32,1.85,15,color=LILAC2,ls=19)
text(s,"So the categories Zepto needs for margin are the categories its interface is worst at selling. Fixing deliberation unlocks both problems at once.",
     0.62,5.45,12.1,0.9,18,True,color=PAPER,face=H,ls=25)
foot(s,"Zepto DRHP, July 2026 · quick-commerce category-mix forecasts from published market research. Links on the final slide.",True)
notes(s,"The user-value case is the previous slide. This one is purely the business case.")

# ══════════════════════════════════════════════════════ 8 · MVP
s=slide(); kicker(s,"PART 4 · THE MVP")
title(s,"First Buy: one observation, one question, one answer — while the order is already on its way.")

rect(s,0.62,1.92,3.05,4.72,INK,radius=0.09)
rect(s,0.75,2.05,2.79,4.46,PAPER,radius=0.07)
rect(s,0.88,2.19,2.53,0.8,MID)
text(s,"Arriving in 8 min",1.02,2.3,2.3,0.32,16,True,color=PAPER)
text(s,"6 items · ₹612",1.02,2.62,2.3,0.28,14,color=LILAC)
sh=rect(s,0.88,3.1,2.53,3.2,PROTO,MID); sh.line.width=Pt(1.5)
text(s,"FIRST BUY",1.02,3.2,2.25,0.26,14,True,color=MID,space=1)
text(s,"You've ordered from 7 categories in 90 days. Never sunscreen.",
     1.02,3.48,2.22,0.72,14,True,color=INK,ls=16)
rect(s,1.02,4.26,2.25,0.42,PAPER,LINE)
text(s,"Oily, shiny by 4pm",1.14,4.34,2.0,0.3,14,color=INK)
rect(s,1.02,4.76,2.25,1.02,TINT)
text(s,"Most re-ordered by oily-skin buyers. Top complaint on the cheaper two: sticky.",
     1.14,4.86,2.02,0.9,14,color=INK,ls=15)
rect(s,1.02,5.88,2.25,0.42,MID)
text(s,"Add  ·  ₹449",1.14,5.96,2.0,0.3,14,True,color=PAPER)

for i,(k,t,d) in enumerate([
 ("SURFACE","The delivery-tracking screen, not the home feed","The basket has already converted, so there is zero cannibalisation risk — and it is the only moment a high-frequency user is present but not busy. The home feed is where task mode lives."),
 ("TRIGGER","An observation about their own behaviour, not a recommendation","“You've ordered cereal and milk 21 times, never fruit.” Specific and checkable, so it reads as the app noticing rather than the app advertising."),
 ("RESOLUTION","One question, then exactly one product","Not an open chat box — blank inputs get ignored in task mode. Not a grid — the grid is what they were already failing at. One reason, one objection pre-handled, written from mined review language."),
 ("DE-RISK","Free return on the first buy in any new category","Attacks price-risk structurally rather than with a discount. Cheaper per conversion, and it does not train users to wait for coupons.")]):
    y=1.92+i*1.2
    rect(s,3.92,y,8.78,1.08,WASH,LINE)
    text(s,k,4.16,y+0.14,1.5,0.28,14,True,color=MID,space=1)
    text(s,t,5.72,y+0.12,6.75,0.32,15,True,color=INK)
    text(s,d,5.72,y+0.46,6.72,0.58,14,color=GREY,ls=15)
foot(s,"Ranking is not the bottleneck — collaborative filtering solved that years ago. Justification is. That is why this is generative, and why it is fed by the corpus that diagnosed the barrier.")
notes(s,"If asked why not the home feed: the home feed is where the user is executing a list. Interrupting a task is how you get dismissed.")

# ══════════════════════════════════════════════════════ 9 · METRICS
s=slide(); kicker(s,"MEASUREMENT")
title(s,"How I would know it worked — including the one metric that could prove it did not.")
for i,(lvl,m,w,col) in enumerate([
 ("North star","% of MAC buying from ≥1 new category per month","The stated goal. Needs two monthly cycles, so it reads as directional at four weeks.",MID),
 ("Primary","New-category purchases per 1,000 tracking-screen impressions","What the experiment is actually powered on.",BLU),
 ("Secondary","30-day repeat rate within the newly entered category","Separates behaviour change from a novelty transaction. Buy sunscreen once and never again and this made a sale, not a habit.",ORA),
 ("Guardrail","Return rate on First Buy items","Free returns must not quietly become a loss centre.",SLATE),
 ("Guardrail","Main-basket AOV","Must not cannibalise the order that already converted.",SLATE),
 ("Guardrail","Tracking-screen dismiss rate","An annoyance signal on a surface the user cannot escape.",SLATE)]):
    y=1.95+i*0.79
    rect(s,0.62,y,12.08,0.71,CREAM if i==2 else WASH,C(0xF0,0xE0,0xB8) if i==2 else LINE)
    text(s,lvl,0.86,y+0.21,1.4,0.32,14,True,color=col)
    text(s,m,2.3,y+0.2,4.2,0.44,15,True,color=INK)
    text(s,w,6.62,y+0.11,5.85,0.6,14,color=GREY,ls=15)
text(s,"Experiment: geo-split A/B on the Plateaued Regular cohort, four weeks, powered on the primary metric. Before any of it — instrument tracking-screen dwell time. If users background the app the second they order, this surface has an attention ceiling and the design has to move.",
     0.62,6.68,12.08,0.6,14,color=INK,ls=17)
notes(s,"Volunteer the secondary metric. Most decks avoid a metric that can make their own feature look bad; including one is the point.")

# ══════════════════════════════════════════════════════ 10 · RISKS + LINKS
s=slide(True); kicker(s,"WHAT I'D DO NEXT",True)
title(s,"The four things most likely to kill this — and what I would check before writing production code.",True)
for i,(t,d) in enumerate([
 ("The surface may not have the attention","Users might close the app the second they order. This is the assumption most likely to be fatal, so it gets instrumented before anything is built."),
 ("Reverse logistics is the expensive half","Free returns is a one-line policy change and a genuinely hard operational programme on a ten-minute network. The policy is not the work."),
 ("A wrong reason is a category risk, not a bug","Generation stays constrained to verified catalogue and review data, with a hard blocklist on health and safety claims. One invented ingredient claim on a baby product is a regulatory event."),
 ("Checkout-adjacent additions have history","Zepto already holds a CCPA notice on basket sneaking. That is precisely why this card sits after payment, clearly separated from the committed order, and unmistakably opt-in.")]):
    x=0.62+(i%2)*6.28; y=1.98+(i//2)*1.6
    rect(s,x,y,6.06,1.42,CARD2,CARD2L)
    text(s,t,x+0.26,y+0.14,5.5,0.34,16,True,color=ORA)
    text(s,d,x+0.26,y+0.5,5.5,0.86,14,color=LILAC2,ls=16)

text(s,"Everything here is live and testable",0.62,5.32,12.1,0.36,17,True,color=PAPER,face=H)
for i,(l,u) in enumerate([
    ("Discovery engine — paste any review and watch it classify","⟨YOUR-DEPLOY-URL⟩"),
    ("First Buy prototype — click the whole flow","⟨YOUR-DEPLOY-URL⟩"),
    ("Method, validation numbers and the full prompt","⟨YOUR-DEPLOY-URL⟩"),
    ("Zepto DRHP coverage — every figure used in this deck","⟨SOURCE-URL⟩")]):
    y=5.76+i*0.34
    text(s,l,0.62,y,6.4,0.3,14,color=LILAC)
    text(s,u,7.1,y,5.6,0.3,14,True,color=SKY,link="https://example.com")
notes(s,"Replace all four links with real, publicly reachable URLs and open each in a private window before submitting. A broken link costs marks.")

# Strip authorship metadata — the guidelines say the fellow's name must not appear
# anywhere in the deck, and File > Properties counts as anywhere.
cp=prs.core_properties
cp.author=""; cp.last_modified_by=""; cp.title="NL Zepto"
cp.comments=""; cp.category=""; cp.keywords=""; cp.subject=""

prs.save("NL Zepto.pptx")
print("wrote NL Zepto.pptx —", len(prs.slides.__iter__.__self__._sldIdLst), "slides")
