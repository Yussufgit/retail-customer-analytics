"""
build_visuals.py
Generates the chart set used in the README and case study, from the
real query/analysis outputs (no synthetic data).
"""

import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

sns.set_theme(style="whitegrid", font_scale=1.05)
PALETTE = ["#2E5266", "#6E8898", "#9FB1BC", "#D3D0CB", "#E8DAB2", "#C08552"]

con = duckdb.connect("retail.duckdb")

# ---------- Chart 1: Monthly revenue trend ----------
monthly = con.execute("""
    SELECT DATE_TRUNC('month', i.invoice_date) AS month, SUM(ii.line_revenue) AS revenue
    FROM invoices i JOIN invoice_items ii ON i.invoice_no = ii.invoice_no
    GROUP BY 1 ORDER BY 1
""").fetchdf()

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(monthly["month"], monthly["revenue"], marker="o", color=PALETTE[0], linewidth=2)
ax.fill_between(monthly["month"], monthly["revenue"], color=PALETTE[0], alpha=0.08)
ax.set_title("Monthly Revenue — Dec 2010 to Dec 2011", fontsize=13, fontweight="bold")
ax.set_ylabel("Revenue (£)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"£{x/1000:.0f}K"))
ax.set_xlabel("")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("visuals/01_monthly_revenue_trend.png", dpi=150)
plt.close()

# ---------- Chart 2: Revenue share by RFM segment ----------
seg = pd.read_csv("data/segment_summary.csv")
seg = seg.sort_values("pct_of_revenue", ascending=True)

fig, ax = plt.subplots(figsize=(8, 4.5))
bars = ax.barh(seg["segment"], seg["pct_of_revenue"], color=PALETTE[0])
for bar, pct, n in zip(bars, seg["pct_of_revenue"], seg["num_customers"]):
    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
            f"{pct}%  ({n:,} customers)", va="center", fontsize=9.5)
ax.set_xlim(0, 95)
ax.set_xlabel("Share of Total Revenue (%)")
ax.set_title("Revenue Concentration by Customer Segment (RFM)", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig("visuals/02_revenue_by_segment.png", dpi=150)
plt.close()

# ---------- Chart 3: Revenue concentration by quintile (Pareto view) ----------
quintile = con.execute("""
    WITH customer_revenue AS (
        SELECT i.customer_id, SUM(ii.line_revenue) AS customer_total_revenue
        FROM invoices i JOIN invoice_items ii ON i.invoice_no = ii.invoice_no
        GROUP BY i.customer_id
    ),
    ranked AS (
        SELECT *, NTILE(5) OVER (ORDER BY customer_total_revenue DESC) AS revenue_quintile
        FROM customer_revenue
    )
    SELECT revenue_quintile,
           ROUND(100.0 * SUM(customer_total_revenue) / SUM(SUM(customer_total_revenue)) OVER (), 1) AS pct_of_total_revenue
    FROM ranked GROUP BY revenue_quintile ORDER BY revenue_quintile
""").fetchdf()
quintile["label"] = ["Top 20%", "21-40%", "41-60%", "61-80%", "Bottom 20%"]

fig, ax = plt.subplots(figsize=(7.5, 4.5))
bars = ax.bar(quintile["label"], quintile["pct_of_total_revenue"], color=PALETTE[0])
bars[0].set_color(PALETTE[5])
for bar, pct in zip(bars, quintile["pct_of_total_revenue"]):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1, f"{pct}%",
            ha="center", fontsize=10, fontweight="bold")
ax.set_ylabel("Share of Total Revenue (%)")
ax.set_title("Revenue Concentration by Customer Value Quintile", fontsize=13, fontweight="bold")
ax.set_ylim(0, 90)
plt.tight_layout()
plt.savefig("visuals/03_revenue_concentration_quintile.png", dpi=150)
plt.close()

# ---------- Chart 4: Cohort retention heatmap ----------
retention = pd.read_csv("data/cohort_retention.csv", index_col=0)
retention = retention.iloc[:, :9]  # first 9 months of retention for readability
retention.index = pd.to_datetime(retention.index).strftime("%b %Y")

fig, ax = plt.subplots(figsize=(9, 5.5))
sns.heatmap(retention, annot=True, fmt=".0%", cmap="Blues", vmin=0, vmax=0.5,
            cbar_kws={"label": "Share of cohort still purchasing"}, ax=ax,
            linewidths=0.5, linecolor="white")
ax.set_title("Monthly Cohort Retention", fontsize=13, fontweight="bold")
ax.set_xlabel("Months Since First Purchase")
ax.set_ylabel("First Purchase Month (Cohort)")
plt.tight_layout()
plt.savefig("visuals/04_cohort_retention_heatmap.png", dpi=150)
plt.close()

con.close()
print("Saved 4 charts to visuals/")
