"""Run the five analysis questions, save charts to reports/charts and numbers to reports/findings.txt."""
from pathlib import Path
import pandas as pd, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
CH = ROOT / "reports" / "charts"; CH.mkdir(parents=True, exist_ok=True)
r = pd.read_csv(P / "restaurants.csv"); v = pd.read_csv(P / "reviews.csv")
out = []
def say(s=""): print(s); out.append(s)

g = (v.groupby("restaurant").agg(n=("rating", "size"), avg=("rating", "mean"), sd=("rating", "std"),
     low=("rating", lambda x: (x <= 2).mean()), five=("rating", lambda x: (x == 5).mean())).reset_index().merge(r, on="restaurant"))
navy = "#1F3A5F"; red = "#C0392B"; grey = "#9AA5B1"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 10})

say(f"Restaurants with reviews: {len(g)} | reviews: {len(v)} | mean rating {v.rating.mean():.2f}")
say(f"5-star share {np.mean(v.rating==5)*100:.1f}% | 1-2 star share {np.mean(v.rating<=2)*100:.1f}%")

# Q1 price vs rating
rho, p = stats.spearmanr(g.cost_for_two, g.avg)
say(f"\nQ1 cost vs avg rating: Spearman rho={rho:.2f}, p={p:.5f}")
g["band"] = pd.cut(g.cost_for_two, [0, 400, 700, 1000, 1500, 3000], labels=["<=400", "401-700", "701-1000", "1001-1500", ">1500"])
b = g.groupby("band", observed=True).agg(restaurants=("avg", "size"), avg_rating=("avg", "mean"))
say(b.round(2).to_string())
fig, ax = plt.subplots(figsize=(7, 4)); ax.bar(b.index.astype(str), b.avg_rating, color=navy)
for i, x in enumerate(b.avg_rating): ax.text(i, x + .03, f"{x:.2f}", ha="center")
ax.set_ylim(0, 5); ax.set_xlabel("Cost for two (Rs)"); ax.set_ylabel("Average rating"); ax.set_title("Pricier restaurants are rated higher")
fig.tight_layout(); fig.savefig(CH / "1_cost_vs_rating.png", dpi=150); plt.close()

# Best value: rating above what the cost band predicts, cheap only
cheap = g[g.cost_for_two <= 500].sort_values("avg", ascending=False).head(8)
say("\nBest rated under Rs 500 for two:"); say(cheap[["restaurant", "cost_for_two", "avg"]].round(2).to_string(index=False))
fig, ax = plt.subplots(figsize=(7, 4)); c = cheap.iloc[::-1]
ax.barh(c.restaurant, c.avg, color=navy); ax.set_xlim(3, 4.3); ax.set_xlabel("Average rating (axis starts at 3)")
ax.set_title("Top rated restaurants under Rs 500 for two"); fig.tight_layout(); fig.savefig(CH / "2_best_value.png", dpi=150); plt.close()

# Q2 collections, with price control
mw = stats.mannwhitneyu(g[g.has_collection].avg, g[~g.has_collection].avg)
say(f"\nQ2 with collection tag: {g[g.has_collection].avg.mean():.2f} (n={g.has_collection.sum()}) vs without {g[~g.has_collection].avg.mean():.2f} (n={(~g.has_collection).sum()}), Mann-Whitney p={mw.pvalue:.4f}")
g["cost_band3"] = pd.cut(g.cost_for_two, [0, 500, 1000, 3000], labels=["<=500", "501-1000", ">1000"])
t = g.groupby(["cost_band3", "has_collection"], observed=True).avg.agg(["size", "mean"]).round(2)
say("Same comparison inside price bands:"); say(t.to_string())
pv = g.groupby(["cost_band3", "has_collection"], observed=True).avg.mean().unstack()
fig, ax = plt.subplots(figsize=(7, 4)); x = np.arange(3)
ax.bar(x - .2, pv[False], .4, label="No collection tag", color=grey); ax.bar(x + .2, pv[True], .4, label="Has collection tag", color=navy)
ax.set_xticks(x); ax.set_xticklabels(pv.index); ax.set_xlabel("Cost for two (Rs)"); ax.set_ylabel("Average rating"); ax.set_ylim(0, 5)
ax.legend(frameon=False); ax.set_title("Collection tags matter far less once price is controlled")
fig.tight_layout(); fig.savefig(CH / "3_collections_by_price.png", dpi=150); plt.close()

# Q3 review themes, low vs 5-star
txt = v[v.has_text]; neg = txt[txt.rating <= 2]; pos = txt[txt.rating == 5]
themes = {"Service / staff": r"service|staff|waiter|rude|behav", "Food taste": r"taste|tasty|flavou?r|delicious",
          "Price / value": r"price|cost|expensive|pricey|value|worth|pocket", "Waiting / slow": r"\bwait|slow|late|delay|long time",
          "Hygiene / stale": r"hygien|clean|stale|dirty|raw|hair|smell", "Ambience": r"ambience|ambiance|decor|music|view", "Quantity": r"quantity|portion"}
th = pd.DataFrame({"low_1_2_star_%": {k: neg.review.str.contains(p, case=False).mean() * 100 for k, p in themes.items()},
                   "five_star_%": {k: pos.review.str.contains(p, case=False).mean() * 100 for k, p in themes.items()}}).round(1)
say(f"\nQ3 theme mentions ({len(neg)} low-rated vs {len(pos)} five-star reviews with text; keyword match):"); say(th.to_string())
fig, ax = plt.subplots(figsize=(7, 4.2)); y = np.arange(len(th)); 
ax.barh(y - .2, th["low_1_2_star_%"], .4, color=red, label="1-2 star reviews"); ax.barh(y + .2, th["five_star_%"], .4, color=navy, label="5 star reviews")
ax.set_yticks(y); ax.set_yticklabels(th.index); ax.invert_yaxis(); ax.set_xlabel("% of reviews mentioning theme"); ax.legend(frameon=False)
ax.set_title("What low-rated reviews talk about more"); fig.tight_layout(); fig.savefig(CH / "4_review_themes.png", dpi=150); plt.close()

# Q4 polarising
g["extreme"] = g.low + g.five
pol = g[(g.low >= .25) & (g.five >= .25)].sort_values("extreme", ascending=False).head(6)
say("\nQ4 most polarising (both >=25% 1-2 star and >=25% 5 star, ranked by combined share):"); say(pol[["restaurant", "avg", "low", "five", "extreme"]].round(2).to_string(index=False))
fig, ax = plt.subplots(figsize=(6, 5)); ax.scatter(g.avg, g.extreme, color=grey, s=22)
ax.scatter(pol.avg, pol.extreme, color=red, s=30)
for _, rw in pol.iterrows(): ax.annotate(rw.restaurant, (rw.avg, rw.extreme), fontsize=8, xytext=(4, 3), textcoords="offset points")
ax.set_xlabel("Average rating"); ax.set_ylabel("Share of 1-2 star + 5 star reviews"); ax.set_title("Average rating hides polarised restaurants")
fig.tight_layout(); fig.savefig(CH / "5_polarising.png", dpi=150); plt.close()

# Q5 late night
gg = g.dropna(subset=["closes_late"]); a = gg[gg.closes_late == True].avg; bb = gg[gg.closes_late == False].avg
say(f"\nQ5 closes at/after midnight: {a.mean():.2f} (n={len(a)}) vs earlier {bb.mean():.2f} (n={len(bb)}), Mann-Whitney p={stats.mannwhitneyu(a, bb).pvalue:.2f}")

# extras
say(f"\nReviews with pictures: avg {v[v.has_pictures].rating.mean():.2f} (n={v.has_pictures.sum()}) vs without {v[~v.has_pictures].rating.mean():.2f}")
cu = pd.read_csv(P / "restaurant_cuisines.csv").merge(g[["restaurant", "avg"]], on="restaurant")
cc = cu.groupby("cuisine").agg(k=("avg", "size"), avg=("avg", "mean")); cc = cc[cc.k >= 8].sort_values("avg", ascending=False)
say("\nCuisines with >=8 restaurants, by avg rating:"); say(cc.round(2).to_string())
(ROOT / "reports" / "findings.txt").write_text("\n".join(out) + "\n")
