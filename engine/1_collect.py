#!/usr/bin/env python3
"""
STAGE 1 — INGEST
Collects real Zepto user reviews from Google Play + Apple App Store.

Run on your own machine (needs open internet).

    pip install google-play-scraper requests
    python 1_collect.py

Outputs:
    corpus_raw.json   — every review, unified schema
    corpus_raw.csv    — same, for eyeballing in Excel
    collection_log.txt — provenance record. Screenshot this for the deck.

Everything downstream reads corpus_raw.json.
"""

import json, csv, sys, time, datetime, urllib.request, urllib.error

# ---------------------------------------------------------------- config
PLAY_APP_ID   = "com.zeptoconsumerapp"     # Zepto: Groceries in minutes
APPSTORE_ID   = "1575323645"               # Zepto, Indian App Store
PLAY_TARGET   = 3000                       # reviews to pull from Play
APPSTORE_PAGES = 10                        # Apple caps the RSS feed at ~10 pages x 50
COUNTRY       = "in"
LANG          = "en"

LOG = []
def log(msg):
    stamp = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line)
    LOG.append(line)


# ---------------------------------------------------------------- play store
def collect_play():
    try:
        from google_play_scraper import Sort, reviews
    except ImportError:
        log("SKIP Play Store — run: pip install google-play-scraper")
        return []

    out, token = [], None
    log(f"Play Store: pulling up to {PLAY_TARGET} reviews for {PLAY_APP_ID}")

    while len(out) < PLAY_TARGET:
        try:
            batch, token = reviews(
                PLAY_APP_ID,
                lang=LANG, country=COUNTRY,
                sort=Sort.NEWEST,
                count=200,
                continuation_token=token,
            )
        except Exception as e:
            log(f"  Play Store stopped early: {type(e).__name__}: {e}")
            break

        if not batch:
            break

        for r in batch:
            out.append({
                "id":      f"play_{r['reviewId']}",
                "source":  "google_play",
                "date":    r["at"].isoformat() if r.get("at") else None,
                "rating":  r.get("score"),
                "text":    (r.get("content") or "").strip(),
                "version": r.get("reviewCreatedVersion"),
                "helpful": r.get("thumbsUpCount", 0),
            })

        log(f"  {len(out)} collected")
        if token is None:
            break
        time.sleep(0.4)          # be polite

    return out[:PLAY_TARGET]


# ---------------------------------------------------------------- app store
def collect_appstore():
    out = []
    log(f"App Store: pulling up to {APPSTORE_PAGES} pages for id={APPSTORE_ID}")

    for page in range(1, APPSTORE_PAGES + 1):
        url = (f"https://itunes.apple.com/{COUNTRY}/rss/customerreviews/"
               f"page={page}/id={APPSTORE_ID}/sortby=mostrecent/json")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = json.loads(urllib.request.urlopen(req, timeout=25).read())
        except Exception as e:
            log(f"  page {page} failed: {type(e).__name__}: {e}")
            break

        entries = data.get("feed", {}).get("entry", [])
        if not entries:
            log(f"  page {page} empty — feed exhausted")
            break

        # first entry on page 1 is the app itself, not a review
        for e in entries:
            if "im:rating" not in e:
                continue
            out.append({
                "id":      f"ios_{e['id']['label']}",
                "source":  "app_store",
                "date":    e.get("updated", {}).get("label"),
                "rating":  int(e["im:rating"]["label"]),
                "text":    (e.get("title", {}).get("label", "") + ". " +
                            e.get("content", {}).get("label", "")).strip(),
                "version": e.get("im:version", {}).get("label"),
                "helpful": 0,
            })

        log(f"  {len(out)} collected")
        time.sleep(0.4)

    return out


# ---------------------------------------------------------------- main
def main():
    log("=" * 60)
    log("ZEPTO REVIEW CORPUS — STAGE 1: INGEST")
    log("=" * 60)

    rows = collect_play() + collect_appstore()

    # dedupe + drop empties + drop very short reviews (no signal in "good app")
    seen, clean = set(), []
    for r in rows:
        t = r["text"]
        if not t or r["id"] in seen:
            continue
        seen.add(r["id"])
        r["word_count"] = len(t.split())
        clean.append(r)

    clean.sort(key=lambda r: r["date"] or "", reverse=True)

    log("-" * 60)
    log(f"TOTAL collected : {len(rows)}")
    log(f"After dedupe    : {len(clean)}")
    if clean:
        by_src = {}
        for r in clean:
            by_src[r["source"]] = by_src.get(r["source"], 0) + 1
        for k, v in by_src.items():
            log(f"  {k:14s}: {v}")
        dates = [r["date"] for r in clean if r["date"]]
        log(f"Date range      : {min(dates)[:10]} to {max(dates)[:10]}")
        avg = sum(r["word_count"] for r in clean) / len(clean)
        log(f"Mean length     : {avg:.1f} words")
        rat = [r["rating"] for r in clean if r["rating"]]
        if rat:
            log(f"Mean rating     : {sum(rat)/len(rat):.2f}")

    if not clean:
        log("NOTHING COLLECTED. Check your internet connection / VPN, then rerun.")
        sys.exit(1)

    with open("corpus_raw.json", "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=1)

    with open("corpus_raw.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(clean[0].keys()))
        w.writeheader()
        w.writerows(clean)

    with open("collection_log.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(LOG))

    log("-" * 60)
    log("Wrote corpus_raw.json, corpus_raw.csv, collection_log.txt")
    log("Next: python 2_analyse.py")


if __name__ == "__main__":
    main()
