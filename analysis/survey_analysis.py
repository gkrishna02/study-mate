"""Stage 1-2 survey analysis: descriptives, charts, correlations, baseline hypothesis test, pain-point ranking.
Usage (from the analysis folder):
    python survey_analysis.py data/pilot_v1.csv --form v1      # original 8-question form
    python survey_analysis.py data/responses.csv --form v2     # revised questionnaire
Export the Google Form as CSV first, and delete the email/timestamp columns before committing it."""
import argparse, re
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Question numbers in each form version (the CSV headers must start with "1.", "2.", ...)
FORMS = {
    "v1": dict(year=1, freq=2, sources=3, struggle=4, time=5, problems=6, exact=7, useful=8, severity="struggle"),
    "v2": dict(year=1, freq=2, sources=3, time=4, exact=5, satisfaction=6, frustration=7, problems=8, useful=9, severity="frustration"),
}
MULTI = ["sources", "problems"]
WORDS = {"never": 1, "rarely": 2, "sometimes": 3, "often": 4, "usually": 4, "very often": 5, "always": 5}
OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)
lines = []

def say(text=""):
    print(text); lines.append(text)

def col(df, n):
    for c in df.columns:
        if re.match(rf"^\s*{n}\s*[.)]", str(c)):
            return c
    return None

def likert(s):
    if pd.api.types.is_numeric_dtype(s):
        return s.astype(float)
    return s.astype(str).str.strip().str.lower().map(WORDS)

def minutes(v):
    t = str(v).lower().replace("–", "-").replace("—", "-")
    nums = [float(x) for x in re.findall(r"\d+\.?\d*", t)]
    if not nums: return np.nan
    if len(nums) >= 2: return sum(nums[:2]) / 2
    if any(w in t for w in ("more", ">", "over", "above", "+")): return nums[0] * 1.25
    if any(w in t for w in ("less", "<", "under", "below")): return nums[0] / 2
    return nums[0]

def mean_ci(x, conf=0.95):
    x = pd.Series(x).dropna()
    if len(x) < 2: return (np.nan, np.nan)
    if x.std() == 0: return (x.mean(), x.mean())
    return stats.t.interval(conf, len(x) - 1, loc=x.mean(), scale=stats.sem(x))

def describe(name, s):
    s = pd.Series(s).dropna()
    if s.empty: return
    lo, hi = mean_ci(s)
    mode = ", ".join(f"{m:g}" for m in s.mode().tolist())
    say(f"  {name}: n={len(s)}, mean={s.mean():.2f}, median={s.median():.2f}, mode={mode}, SD={s.std():.2f}, "
        f"min={s.min():g}, max={s.max():g}, 95% CI for mean=({lo:.2f}, {hi:.2f})")

def wilson(k, n):
    ci = stats.binomtest(k, n).proportion_ci(method="wilson")
    return ci.low, ci.high

def explode(series):
    return Counter(x.strip() for v in series.dropna() for x in str(v).split(", ") if x.strip())

def bar(counter, title, fname, n):
    if not counter: return
    items = sorted(counter.items(), key=lambda kv: kv[1])
    plt.figure(figsize=(8, 0.6 * len(items) + 1.5))
    plt.barh([k for k, _ in items], [v / n * 100 for _, v in items], color="#2f55d4")
    plt.xlabel("% of respondents"); plt.title(title); plt.tight_layout(pad=2.0)
    plt.savefig(OUT / fname, dpi=150); plt.close()

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("csv"); ap.add_argument("--form", default="v1", choices=FORMS)
    a = ap.parse_args()
    Q = FORMS[a.form]
    df = pd.read_csv(a.csv)
    n = len(df)
    say(f"STUDYMATE SURVEY ANALYSIS  (form {a.form}, n = {n})")
    if n < 30: say(f"WARNING: n={n} is below the 30 required by the brief. Treat all tests as exploratory.")
    for c in df.columns:
        if "email" in str(c).lower(): say("WARNING: an email column is present. Remove it before sharing or committing this file.")

    num = {}
    for key in ("struggle", "exact", "satisfaction", "frustration", "useful"):
        if key in Q and col(df, Q[key]) is not None:
            s = likert(df[col(df, Q[key])])
            if s.notna().any(): num[key] = s
    if "time" in Q and col(df, Q["time"]) is not None:
        num["time_min"] = df[col(df, Q["time"])].map(minutes)

    say("\n1. DESCRIPTIVE STATISTICS (Likert items coded 1-5; time in minutes, bins use midpoints)")
    for k, s in num.items(): describe(k, s)
    for key in ("year", "freq", "struggle", "exact", "useful"):
        c = col(df, Q.get(key, -1)) if key in Q else None
        if c is not None: say(f"  {key} counts: {df[c].value_counts().to_dict()}")

    for key in MULTI:
        c = col(df, Q[key]) if key in Q else None
        if c is None: continue
        cnt = explode(df[c])
        say(f"\n  {key} (multi-select, % of respondents):")
        for k, v in sorted(cnt.items(), key=lambda kv: -kv[1]):
            lo, hi = wilson(v, n)
            say(f"    {k}: {v}/{n} = {v / n * 100:.0f}%  (95% Wilson CI {lo * 100:.0f}-{hi * 100:.0f}%)")
        bar(cnt, f"{key}", f"{key}_bar.png", n)

    if "time_min" in num and num["time_min"].notna().sum() > 1:
        plt.figure(figsize=(6, 4)); num["time_min"].dropna().plot.hist(bins=6, color="#2f55d4", edgecolor="white")
        plt.xlabel("Minutes to find one resource"); plt.title("Time spent finding a resource"); plt.tight_layout()
        plt.savefig(OUT / "time_hist.png", dpi=150); plt.close()
    lik = {k: v.dropna() for k, v in num.items() if k != "time_min" and v.notna().sum() > 1}
    if lik:
        plt.figure(figsize=(7, 4)); plt.boxplot(list(lik.values())); plt.xticks(range(1, len(lik) + 1), list(lik)); plt.ylabel("Score (1-5)")
        plt.title("Likert items"); plt.tight_layout(); plt.savefig(OUT / "likert_box.png", dpi=150); plt.close()

    say("\n2. CORRELATIONS (Spearman rank, because Likert data are ordinal)")
    keys = list(num)
    done = False
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            pair = pd.concat([num[keys[i]], num[keys[j]]], axis=1).dropna()
            if len(pair) < 5 or pair.iloc[:, 0].nunique() < 2 or pair.iloc[:, 1].nunique() < 2: continue
            rho, p = stats.spearmanr(pair.iloc[:, 0], pair.iloc[:, 1]); done = True
            size = "weak" if abs(rho) < .3 else "moderate" if abs(rho) < .6 else "strong"
            sig = "statistically significant" if p < .05 else "not statistically significant"
            say(f"  {keys[i]} vs {keys[j]}: rho={rho:+.2f}, p={p:.3f}, n={len(pair)} -> {size} {'positive' if rho > 0 else 'negative'}, {sig}")
    if not done: say("  Not enough varied data for correlations.")
    say("  Reminder: correlation does not show cause.")

    say("\n3. BASELINE HYPOTHESIS TEST (current situation vs neutral score 3)")
    var = "satisfaction" if "satisfaction" in num else "exact" if "exact" in num else None
    if var and num[var].notna().sum() >= 3:
        x = num[var].dropna(); d = x - 3
        say(f"  Variable: {var}. H0: mean = 3 (neutral). H1: mean < 3 (users are below neutral). alpha = 0.05")
        t = stats.ttest_1samp(x, 3, alternative="less")
        say(f"  One-sample t-test: t={t.statistic:.2f}, p={t.pvalue:.3f}")
        if (d != 0).any():
            w = stats.wilcoxon(d, alternative="less"); say(f"  Wilcoxon signed-rank: W={w.statistic:.1f}, p={w.pvalue:.3f}  (preferred for Likert data)")
            p = w.pvalue
        else: p = t.pvalue
        lo, hi = mean_ci(x); say(f"  Mean={x.mean():.2f}, 95% CI=({lo:.2f}, {hi:.2f}), effect size d={(x.mean() - 3) / x.std():+.2f}")
        say("  Conclusion: " + ("Reject H0. Users are significantly below neutral." if p < .05 else
            f"Fail to reject H0. With n={len(x)} we cannot show the current situation is below neutral (this is not proof that it is fine)."))
    else: say("  Not enough data (need a satisfaction or 'find exact material' item with n >= 3).")

    say("\n4. PAIN-POINT RANKING (share of users affected x average severity)")
    c = col(df, Q["problems"]) if "problems" in Q else None
    sev = num.get(Q["severity"])
    if c is not None:
        rows = []
        for prob in explode(df[c]):
            mask = df[c].fillna("").str.contains(re.escape(prob))
            s = sev[mask].mean() if sev is not None and sev[mask].notna().any() else np.nan
            share = mask.sum() / n
            rows.append((prob, mask.sum(), share, s, share * (s if not np.isnan(s) else 1)))
        for prob, k, share, s, score in sorted(rows, key=lambda r: -r[4]):
            say(f"  {prob}: {k}/{n} affected ({share * 100:.0f}%), mean {Q['severity']}={s:.2f}, priority score={score:.2f}")
    say("\nLIMITS: convenience sample, self-reported data, small n; results describe this sample only.")
    (OUT / "survey_results.txt").write_text("\n".join(lines), encoding="utf-8")
    say(f"\nSaved results and charts to {OUT}")

if __name__ == "__main__":
    main()