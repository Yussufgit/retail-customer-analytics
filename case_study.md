# Case Study: Customer Retention & Revenue Concentration

## Problem

This retailer has no visibility into which customers actually drive revenue or which are at risk of leaving. Marketing spend and retention effort are currently undifferentiated — every customer gets the same treatment regardless of value or purchase behavior. Before recommending any retention campaign, this analysis first needed to answer a basic question: is revenue broadly spread across the customer base, or concentrated in a smaller group worth protecting specifically?

## Approach

Using 531,282 transactions (Dec 2010–Dec 2011, 4,340 customers), this analysis:

1. Normalized the raw transaction log into a relational schema (customers, invoices, invoice items) in SQL to enable proper joins and aggregation.
2. Calculated Recency, Frequency, and Monetary (RFM) value for every customer and segmented them into six behavioral groups using quartile scoring.
3. Cross-checked the segmentation against a simpler, independent method — ranking customers into revenue quintiles — to confirm the finding wasn't an artifact of the segmentation rules chosen.
4. Built a month-over-month cohort retention table to understand how quickly new customers typically stop buying.

## Key Finding

Revenue is highly concentrated: the top 31% of customers ("Champions") generate 77.9% of all revenue. This was confirmed independently — the top 20% of customers by the simpler quintile method account for 78.8% of revenue, essentially the same result reached a different way. This is not a business with broadly distributed revenue; it depends heavily on a defined group of repeat, high-frequency customers.

At the other end, a small but notable segment — 138 customers labeled "At Risk" — historically purchased almost as often as Champions (4.2 orders on average, versus 10.8 for Champions) but haven't ordered in 204 days on average. This group previously behaved like high-value customers and went quiet, which is different from customers who were never engaged in the first place (the "Lost" and "Needs Attention" segments, who never had comparable frequency).

Cohort data supports the same story from a different angle: only 15-25% of customers who make a first purchase in a given month are still buying the following month. Most of the customer base churns quickly, which makes it even more important to know exactly who the retained, high-value customers are — and to notice quickly when one of them stops buying.

## Why This Matters (Not User Error, Not Random)

This concentration pattern is a structural characteristic of the business, not a data quality issue or random noise — it held up under two independently-built measures (RFM segmentation and quintile ranking), and the "At Risk" segment's historical behavior (high frequency, similar to Champions) rules out the alternative explanation that they were simply low-value customers to begin with. The pattern that matters here is behavioral: high-frequency customers going quiet, not never engaging in the first place.

## Recommendation

**Priority 1:** Launch a targeted win-back outreach to the 138 At Risk customers specifically — not a broad re-engagement campaign to the full "Lost" or "Needs Attention" segments, whose historical value doesn't justify the same investment per customer.

**Priority 2:** Build a simple recency alert (e.g., flag any Champion-segment customer who hasn't purchased in 30+ days) so this kind of drop-off is caught while a customer is still recoverable, rather than 200 days later.

**Priority 3:** Given the sharp Q4 seasonality (revenue roughly doubles from August to November), time any retention campaign to land before the seasonal ramp — recovering an At Risk customer in September protects far more revenue than recovering the same customer in January.

## Limitations

This dataset covers one retailer over roughly one year, so seasonal patterns are observed only once, not confirmed across multiple years. RFM segmentation is also a purchase-history-based method — it reflects past behavior, not stated customer intent, so it can miss customers who are about to become valuable but don't have the purchase history yet to show it.
