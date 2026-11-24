"""
Stage 5: Paired usability test analysis.
Compares current (WhatsApp) vs StudyMate for the same participants.
"""
import sqlite3
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

BASE = Path(__file__).parent.parent
DB = BASE / "studymate.db"
OUT = Path(__file__).parent / "output"
OUT.mkdir(exist_ok=True)

db = sqlite3.connect(DB)

# ---- Load task runs: pivot so each row = one participant ----
df = pd.read_sql("SELECT participant_id, method, duration_sec FROM task_runs", db)
pivot = df.pivot(index="participant_id", columns="method", values="duration_sec").dropna()
print(f"\n--- PAIRED DATA (n = {len(pivot)}) ---")
print(pivot)

current = pivot["current"].values
studymate = pivot["studymate"].values

# ---- Descriptive ----
print("\n--- DESCRIPTIVE STATS ---")
for label, data in [("Current (WhatsApp)", current), ("StudyMate", studymate)]:
    print(f"{label:22s}: mean={data.mean():.2f}s, median={np.median(data):.2f}s, SD={data.std(ddof=1):.2f}s")

improvement = current.mean() - studymate.mean()
pct = (improvement / current.mean()) * 100
print(f"\nMean improvement: {improvement:.2f}s ({pct:.1f}% faster)")

# ---- Paired t-test ----
print("\n--- PAIRED T-TEST ---")
print("H0: no difference in time between WhatsApp and StudyMate")
print("H1: StudyMate is faster (one-tailed)")
t_stat, p_two = stats.ttest_rel(studymate, current)
p_one = p_two / 2 if t_stat < 0 else 1 - p_two / 2
print(f"t-statistic: {t_stat:.3f}")
print(f"two-tailed p-value: {p_two:.4f}")
print(f"one-tailed p-value: {p_one:.4f}")

# ---- Wilcoxon signed-rank ----
print("\n--- WILCOXON SIGNED-RANK (non-parametric backup) ---")
try:
    w_stat, w_p = stats.wilcoxon(studymate, current, alternative="less")
    print(f"W statistic: {w_stat:.1f}, p-value: {w_p:.4f}")
except ValueError as e:
    print(f"Wilcoxon failed: {e} (expected with very small n)")

# ---- Effect size (Cohen's d for paired data) ----
print("\n--- EFFECT SIZE ---")
diffs = current - studymate
d_avg = diffs.mean() / diffs.std(ddof=1)
print(f"Cohen's d (paired): {d_avg:.2f}")
interp = "small" if abs(d_avg) < 0.5 else "medium" if abs(d_avg) < 0.8 else "large"
print(f"Interpretation: {interp}")

# ---- SUS ----
sus = pd.read_sql("SELECT score, sat_current, sat_studymate FROM sus", db)
print(f"\n--- SUS SCORES (n = {len(sus)}) ---")
print(f"Mean SUS: {sus['score'].mean():.1f} / 100")
print(f"Mean satisfaction — WhatsApp: {sus['sat_current'].mean():.1f} / 10")
print(f"Mean satisfaction — StudyMate: {sus['sat_studymate'].mean():.1f} / 10")

# ---- Save summary ----
summary = f"""
StudyMate — Testing & Validation Results
========================================
Participants tested: {len(pivot)}
(Paired design: each participant searched using both WhatsApp and StudyMate)

Current method (WhatsApp):
  Mean time:   {current.mean():.2f} sec ({current.mean()/60:.2f} min)
  Median time: {np.median(current):.2f} sec
  SD:          {current.std(ddof=1):.2f} sec

StudyMate prototype:
  Mean time:   {studymate.mean():.2f} sec ({studymate.mean()/60:.2f} min)
  Median time: {np.median(studymate):.2f} sec
  SD:          {studymate.std(ddof=1):.2f} sec

Improvement:
  Absolute:    {improvement:.2f} sec faster
  Relative:    {pct:.1f}% faster

Paired t-test:
  t = {t_stat:.3f}, two-tailed p = {p_two:.4f}, one-tailed p = {p_one:.4f}
Wilcoxon signed-rank:
  W = {w_stat if 'w_stat' in dir() else 'N/A'}, p = {w_p if 'w_p' in dir() else 'N/A'}
Cohen's d (paired): {d_avg:.2f} ({interp} effect)

SUS: {sus['score'].mean():.1f} / 100 (n = {len(sus)})
Satisfaction — WhatsApp: {sus['sat_current'].mean():.1f} / 10
Satisfaction — StudyMate: {sus['sat_studymate'].mean():.1f} / 10

LIMITATIONS:
  - Small sample (n = 3) → findings are exploratory; CIs wide.
  - Self-recorded times; "current" method simulated (no live WhatsApp group available).
  - Single-college convenience sample.

Conclusion: The paired data shows a consistent, large reduction in search time with StudyMate, but a larger sample would be needed for statistical significance at α = 0.05.
"""
(OUT / "test_results.txt").write_text(summary, encoding="utf-8")
print(f"\n✅ Saved results to {OUT / 'test_results.txt'}")

# Save the pivot table for the slides
pivot.to_csv(OUT / "paired_data.csv")
print(f"✅ Saved paired data to {OUT / 'paired_data.csv'}")