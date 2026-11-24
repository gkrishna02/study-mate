import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("output/paired_data.csv")
fig, ax = plt.subplots(figsize=(7, 4))
x = np.arange(len(df))
w = 0.35
ax.bar(x - w/2, df["current"], w, label="WhatsApp", color="#ef4444")
ax.bar(x + w/2, df["studymate"], w, label="StudyMate", color="#4f46e5")
ax.set_xticks(x)
ax.set_xticklabels([f"P{int(i)}" for i in df["participant_id"]])
ax.set_ylabel("Time to find file (seconds)")
ax.set_title("Search Time: WhatsApp vs StudyMate (paired test, n = 3)")
ax.legend()
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("output/paired_comparison.png", dpi=150)
print("✅ Saved chart to output/paired_comparison.png")