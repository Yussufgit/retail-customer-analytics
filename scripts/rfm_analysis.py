"""
rfm_analysis.py

Segments customers by Recency, Frequency, and Monetary value (RFM) and
builds a cohort retention view, using the normalized tables created by
sql/01_schema_setup.sql. Outputs:
  - data/rfm_segments.csv        (customer-level RFM scores + segment)
  - data/segment_summary.csv     (segment-level rollup)
  - data/cohort_retention.csv    (month-over-month retention matrix)
"""

import duckdb
import pandas as pd

con = duckdb.connect("retail.duckdb")

# ---- Pull per-customer Recency / Frequency / Monetary ----
rfm_raw = con.execute("""
    SELECT
        i.customer_id,
        MAX(i.invoice_date)                AS last_purchase_date,
        COUNT(DISTINCT i.invoice_no)        AS frequency,
        SUM(ii.line_revenue)                AS monetary
    FROM invoices i
    JOIN invoice_items ii ON i.invoice_no = ii.invoice_no
    GROUP BY i.customer_id
""").fetchdf()

reference_date = rfm_raw["last_purchase_date"].max() + pd.Timedelta(days=1)
rfm_raw["recency"] = (reference_date - rfm_raw["last_purchase_date"]).dt.days

# ---- Score each dimension into quartiles (4 = best) ----
rfm_raw["r_score"] = pd.qcut(rfm_raw["recency"], 4, labels=[4, 3, 2, 1]).astype(int)
rfm_raw["f_score"] = pd.qcut(rfm_raw["frequency"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
rfm_raw["m_score"] = pd.qcut(rfm_raw["monetary"], 4, labels=[1, 2, 3, 4]).astype(int)


def assign_segment(row):
    r, f, m = row["r_score"], row["f_score"], row["m_score"]
    if r >= 3 and f >= 3 and m >= 3:
        return "Champions"
    if f >= 3 and r >= 2:
        return "Loyal Customers"
    if r <= 2 and f >= 3:
        return "At Risk"
    if r >= 3 and f <= 2:
        return "New / Promising"
    if r <= 1 and f <= 2:
        return "Lost"
    return "Needs Attention"


rfm_raw["segment"] = rfm_raw.apply(assign_segment, axis=1)

rfm_raw.to_csv("data/rfm_segments.csv", index=False)

# ---- Segment-level summary ----
total_revenue = rfm_raw["monetary"].sum()
segment_summary = (
    rfm_raw.groupby("segment")
    .agg(
        num_customers=("customer_id", "count"),
        total_revenue=("monetary", "sum"),
        avg_recency_days=("recency", "mean"),
        avg_frequency=("frequency", "mean"),
    )
    .assign(pct_of_customers=lambda d: (d["num_customers"] / d["num_customers"].sum() * 100).round(1))
    .assign(pct_of_revenue=lambda d: (d["total_revenue"] / total_revenue * 100).round(1))
    .sort_values("total_revenue", ascending=False)
)
segment_summary.to_csv("data/segment_summary.csv")

print("=== RFM SEGMENT SUMMARY ===")
print(segment_summary.round(1).to_string())

# ---- Cohort retention: month of first purchase vs. which later months they returned ----
cohort_raw = con.execute("""
    SELECT
        customer_id,
        invoice_no,
        DATE_TRUNC('month', invoice_date) AS order_month,
        MIN(DATE_TRUNC('month', invoice_date)) OVER (PARTITION BY customer_id) AS cohort_month
    FROM invoices
""").fetchdf()

cohort_raw["period_number"] = (
    (cohort_raw["order_month"].dt.year - cohort_raw["cohort_month"].dt.year) * 12
    + (cohort_raw["order_month"].dt.month - cohort_raw["cohort_month"].dt.month)
)

cohort_counts = (
    cohort_raw.groupby(["cohort_month", "period_number"])["customer_id"]
    .nunique()
    .reset_index()
)
cohort_pivot = cohort_counts.pivot(index="cohort_month", columns="period_number", values="customer_id")
cohort_sizes = cohort_pivot.iloc[:, 0]
retention = cohort_pivot.divide(cohort_sizes, axis=0).round(3)
retention.to_csv("data/cohort_retention.csv")

print("\n=== COHORT RETENTION (share of cohort still buying, by month offset) ===")
print(retention.round(2).to_string())

con.close()
