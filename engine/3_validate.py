#!/usr/bin/env python3
"""
STAGE 6 — VALIDATION

This is the part almost nobody does, and it is the reason to trust anything above.

An LLM that labels 3,000 reviews will produce a confident-looking chart whether
or not it is right. The only way to know is to label a sample by hand, blind,
and score the machine against yourself.

Two steps.

  1)  python 3_validate.py sample
      Draws a stratified random hold-out of 60 reviews and writes
      validation_sheet.csv with the model's labels HIDDEN.

      Now label all 60 yourself, by hand, in the my_label column.
      Do this before looking at corpus_extracted.json. Blind or it's worthless.

  2)  python 3_validate.py score
      Scores the model against your labels:
        - per-barrier precision / recall / F1
        - overall accuracy
        - Cohen's kappa (agreement corrected for chance)
        - confusion matrix, so you can see WHICH pairs the model confuses
        - negative control: 20 obviously-irrelevant reviews, checking the
          model doesn't invent barriers where none exist

      Writes validation.json (feeds the deck) and prints a report.

No external dependencies. Runs on a plain Python install.
"""

import json, csv, random, sys, collections

BARRIERS = ["B1_TRUST", "B2_FIT", "B3_PRICE_RISK", "B4_ASSORTMENT",
            "B5_OCCASION", "B6_AWARENESS", "B7_NONE"]

SEED = 42          # fixed so the sample is reproducible and auditable
N_SAMPLE = 60
N_CONTROL = 20


# ------------------------------------------------------------------ sample
def make_sample():
    data = json.load(open("corpus_extracted.json", encoding="utf-8"))
    rows = [r for r in data if r.get("extraction")]
    random.seed(SEED)

    # stratify by the model's label so rare barriers actually appear in the
    # hold-out. Unstratified random sampling from a skewed distribution gives
    # you 55 B7s and tells you nothing about the classes you care about.
    by_label = collections.defaultdict(list)
    for r in rows:
        by_label[r["extraction"]["barrier"]].append(r)

    per = max(1, N_SAMPLE // max(1, len(by_label)))
    sample = []
    for lab, group in by_label.items():
        random.shuffle(group)
        sample += group[:per]

    pool = [r for r in rows if r not in sample]
    random.shuffle(pool)
    sample += pool[:max(0, N_SAMPLE - len(sample))]
    random.shuffle(sample)

    with open("validation_sheet.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["row", "id", "rating", "review_text", "my_label", "notes"])
        for i, r in enumerate(sample, 1):
            w.writerow([i, r["id"], r.get("rating"),
                        r["text"][:900].replace("\n", " "), "", ""])

    # model labels held separately so you can't peek while labelling
    json.dump({r["id"]: r["extraction"]["barrier"] for r in sample},
              open("_model_labels.json", "w"), indent=1)

    print(f"Wrote validation_sheet.csv — {len(sample)} reviews.")
    print("\nLabel the my_label column yourself using ONLY these codes:")
    for b in BARRIERS:
        print(f"   {b}")
    print("\nDo NOT open _model_labels.json or corpus_extracted.json first.")
    print("Then run: python 3_validate.py score")


# ------------------------------------------------------------------ score
def kappa(a, b, labels):
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = sum((a.count(l) / n) * (b.count(l) / n) for l in labels)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def score():
    model = json.load(open("_model_labels.json", encoding="utf-8"))

    human, machine, skipped = [], [], 0
    with open("validation_sheet.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            lab = (row.get("my_label") or "").strip().upper()
            if lab not in BARRIERS:
                skipped += 1
                continue
            human.append(lab)
            machine.append(model.get(row["id"], "B7_NONE"))

    if not human:
        sys.exit("No labels found in validation_sheet.csv. Fill in my_label first.")

    n = len(human)
    acc = sum(1 for h, m in zip(human, machine) if h == m) / n
    k = kappa(human, machine, BARRIERS)

    per = {}
    for b in BARRIERS:
        tp = sum(1 for h, m in zip(human, machine) if h == b and m == b)
        fp = sum(1 for h, m in zip(human, machine) if h != b and m == b)
        fn = sum(1 for h, m in zip(human, machine) if h == b and m != b)
        p = tp / (tp + fp) if tp + fp else None
        r = tp / (tp + fn) if tp + fn else None
        f1 = 2 * p * r / (p + r) if p and r else None
        per[b] = {"support": tp + fn,
                  "precision": round(p, 3) if p is not None else None,
                  "recall":    round(r, 3) if r is not None else None,
                  "f1":        round(f1, 3) if f1 is not None else None}

    confusion = collections.Counter(zip(human, machine))

    # -------------------------------------------------- report
    print("=" * 62)
    print(f"VALIDATION — {n} hand-labelled reviews (seed {SEED})")
    if skipped:
        print(f"({skipped} rows skipped — no valid label)")
    print("=" * 62)
    print(f"Accuracy       : {acc:.1%}")
    print(f"Cohen's kappa  : {k:.3f}   {interpret(k)}")
    print()
    print(f"{'barrier':16s} {'n':>4s} {'prec':>7s} {'rec':>7s} {'F1':>7s}")
    for b in BARRIERS:
        d = per[b]
        fmt = lambda x: f"{x:7.3f}" if x is not None else "      -"
        print(f"{b:16s} {d['support']:4d} {fmt(d['precision'])}"
              f"{fmt(d['recall'])}{fmt(d['f1'])}")

    print("\nTop disagreements (you said -> model said):")
    for (h, m), c in confusion.most_common():
        if h != m:
            print(f"  {h:14s} -> {m:14s}  {c}")

    out = {
        "n": n, "seed": SEED, "accuracy": round(acc, 4),
        "cohens_kappa": round(k, 4), "kappa_reading": interpret(k),
        "per_barrier": per,
        "confusion": {f"{h}->{m}": c for (h, m), c in confusion.items()},
    }

    # -------------------------------------------------- negative control
    try:
        allrows = json.load(open("corpus_gated.json", encoding="utf-8"))
        rejected = [r for r in allrows if not r.get("relevant")]
        random.seed(SEED + 1)
        random.shuffle(rejected)
        ctrl = rejected[:N_CONTROL]
        ext = {r["id"]: r for r in
               json.load(open("corpus_extracted.json", encoding="utf-8"))}
        leaked = sum(1 for r in ctrl if r["id"] in ext)
        out["negative_control"] = {
            "n": len(ctrl),
            "note": "reviews the gate rejected; none should carry a barrier",
            "leaked_into_extraction": leaked,
        }
        print(f"\nNegative control: {len(ctrl)} gate-rejected reviews, "
              f"{leaked} leaked into extraction")
    except FileNotFoundError:
        pass

    json.dump(out, open("validation.json", "w"), indent=1)
    print("\nWrote validation.json")
    print(headline(acc, k))


def interpret(k):
    if k < 0.20: return "(poor — do not trust the labels)"
    if k < 0.40: return "(fair)"
    if k < 0.60: return "(moderate)"
    if k < 0.80: return "(substantial — usable)"
    return "(near-perfect — check for leakage before believing it)"


def headline(acc, k):
    if k >= 0.6:
        return ("\nHEADLINE FOR THE DECK: agreement is substantial. Report the "
                "kappa AND the weakest per-barrier F1. Do not report accuracy alone.")
    return ("\nHEADLINE FOR THE DECK: agreement is below substantial. Say so, "
            "name the confused pair, and say the insight is directional and "
            "was cross-checked in interviews. Reporting a weak number honestly "
            "scores better than hiding it.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "sample":
        make_sample()
    elif cmd == "score":
        score()
    else:
        print(__doc__)
