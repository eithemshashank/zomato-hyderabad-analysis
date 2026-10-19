"""Clean the two raw Zomato Hyderabad CSVs and write tidy tables to data/processed/.

Outputs
-------
restaurants.csv         one row per restaurant (cost as int, flags for collections/late night)
restaurant_cuisines.csv restaurant, cuisine  (one row per pair)
restaurant_collections.csv restaurant, collection
reviews.csv             one row per valid review (rating numeric, reviewer stats parsed, datetime parsed)
cleaning_log.txt        what was dropped / fixed, with counts
"""
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

log = []


def note(msg):
    print(msg)
    log.append(msg)


# ---------------------------------------------------------------- restaurants
meta = pd.read_csv(RAW / "restaurants_metadata.csv")
note(f"restaurants raw rows: {len(meta)}")
meta = meta.rename(columns=str.lower).rename(columns={"name": "restaurant", "links": "url"})
meta["restaurant"] = meta["restaurant"].str.strip()
dups = meta["restaurant"].duplicated().sum()
note(f"duplicate restaurant names: {dups}")

meta["cost_for_two"] = (
    meta["cost"].astype(str).str.replace(",", "", regex=False).str.strip().astype(int)
)
meta = meta.drop(columns="cost")


def split_list(s):
    if pd.isna(s):
        return []
    return [x.strip() for x in str(s).split(",") if x.strip()]


meta["cuisine_list"] = meta["cuisines"].apply(split_list)
meta["collection_list"] = meta["collections"].apply(split_list)
meta["n_cuisines"] = meta["cuisine_list"].str.len()
meta["has_collection"] = meta["collection_list"].str.len() > 0
meta["late_night_collection"] = meta["collection_list"].apply(lambda l: "Late Night Restaurants" in l)


def parse_timings(t):
    """Return (is_24h, closes_late) from the free-text timings.

    closes_late = any closing time at midnight or later (11 PM closers are NOT counted: 91/104 close at 11 PM+, which does not separate anything). Best effort:
    timings are free text, so unparseable ones come back as None and are reported.
    """
    if pd.isna(t):
        return (None, None)
    s = str(t).lower()
    if "24 hours" in s or "24hours" in s or "24 hrs" in s:
        return (True, True)
    closes = re.findall(r"to\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm|noon|midnight)", s)
    if not closes:
        return (False, None)
    late = False
    for h, m, ap in closes:
        h = int(h)
        if ap == "midnight":
            late = True
        elif ap == "am" and (h <= 5 or h == 12):
            late = True
    return (False, late)


tm = meta["timings"].apply(parse_timings)
meta["is_24h"] = [a for a, _ in tm]
meta["closes_late"] = [b for _, b in tm]
note(f"timings not parseable: {meta['closes_late'].isna().sum()}")

restaurants = meta.drop(columns=["cuisine_list", "collection_list"])
cuisines = meta[["restaurant", "cuisine_list"]].explode("cuisine_list").dropna().rename(columns={"cuisine_list": "cuisine"})
collections = meta[["restaurant", "collection_list"]].explode("collection_list").dropna().rename(columns={"collection_list": "collection"})

# ------------------------------------------------------------------- reviews
rev = pd.read_csv(RAW / "restaurant_reviews.csv")
note(f"reviews raw rows: {len(rev)}")
rev.columns = [c.lower() for c in rev.columns]

# Rows with no reviewer and no rating are blank rows in the source
blank = rev["rating"].isna() & rev["reviewer"].isna()
note(f"blank rows dropped: {blank.sum()}")
rev = rev[~blank].copy()

# The rating column contains a stray text value ("Like")
rev["rating"] = pd.to_numeric(rev["rating"], errors="coerce")
bad_rating = rev["rating"].isna()
note(f"non-numeric / missing ratings dropped: {bad_rating.sum()}")
rev = rev[~bad_rating].copy()

# Reviewer metadata: "12 Reviews , 3 Followers" / "1 Review" / "2 Posts , 5 Followers"
pat = re.compile(r"^\s*(\d+)\s+(?:Reviews?|Posts?)(?:\s*,\s*(\d+)\s+Followers?)?\s*$")


def parse_meta(s):
    if pd.isna(s):
        return (None, None)
    m = pat.match(str(s))
    if not m:
        return (None, None)
    return (int(m.group(1)), int(m.group(2)) if m.group(2) else 0)


pm = rev["metadata"].apply(parse_meta)
rev["reviewer_reviews"] = [a for a, _ in pm]
rev["reviewer_followers"] = [b for _, b in pm]
note(f"reviewer metadata not parseable: {rev['reviewer_reviews'].isna().sum()}")
rev = rev.drop(columns="metadata")

rev["time"] = pd.to_datetime(rev["time"], format="%m/%d/%Y %H:%M", errors="coerce")
note(f"timestamps not parseable: {rev['time'].isna().sum()}")
rev["review"] = rev["review"].fillna("").str.strip()
rev["review_length"] = rev["review"].str.split().str.len()
rev["has_text"] = rev["review"].str.len() > 0
rev["has_pictures"] = rev["pictures"] > 0
rev["restaurant"] = rev["restaurant"].str.strip()
rev["rating"] = rev["rating"].astype(float)

# Restaurant names in reviews that are not in the metadata file (and vice versa)
unmatched = set(rev["restaurant"]) - set(restaurants["restaurant"])
no_reviews = sorted(set(restaurants["restaurant"]) - set(rev["restaurant"]))
note(f"review restaurants missing from metadata: {len(unmatched)}")
note(f"restaurants with zero reviews: {len(no_reviews)} -> {no_reviews}")

exact_dups = rev.duplicated(["restaurant", "reviewer", "review", "time"]).sum()
note(f"exact duplicate reviews: {exact_dups}")
rev = rev.drop_duplicates(["restaurant", "reviewer", "review", "time"]).reset_index(drop=True)
rev.insert(0, "review_id", range(1, len(rev) + 1))
note(f"reviews clean rows: {len(rev)}")
note(f"date range: {rev['time'].min()} -> {rev['time'].max()}")

restaurants.to_csv(OUT / "restaurants.csv", index=False)
cuisines.to_csv(OUT / "restaurant_cuisines.csv", index=False)
collections.to_csv(OUT / "restaurant_collections.csv", index=False)
rev.to_csv(OUT / "reviews.csv", index=False)
(OUT / "cleaning_log.txt").write_text("\n".join(log) + "\n")
