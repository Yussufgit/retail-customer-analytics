-- 02_business_queries.sql
-- Core business questions answered with JOINs, subqueries, and aggregations
-- against the normalized schema built in 01_schema_setup.sql

-- Q1: Monthly revenue trend
-- JOIN invoices to invoice_items, aggregate revenue by month
SELECT
    DATE_TRUNC('month', i.invoice_date) AS month,
    ROUND(SUM(ii.line_revenue), 2)      AS revenue,
    COUNT(DISTINCT i.invoice_no)        AS orders
FROM invoices i
JOIN invoice_items ii ON i.invoice_no = ii.invoice_no
GROUP BY 1
ORDER BY 1;

-- Q2: Repeat vs. one-time customers
-- Subquery counts orders per customer; outer query buckets them
SELECT
    CASE WHEN order_count = 1 THEN 'One-time' ELSE 'Repeat' END AS customer_type,
    COUNT(*)                                                     AS num_customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)           AS pct_of_customers
FROM (
    SELECT customer_id, COUNT(DISTINCT invoice_no) AS order_count
    FROM invoices
    GROUP BY customer_id
) AS customer_orders
GROUP BY 1;

-- Q3: Average order value by country (top 10 by revenue)
-- JOIN across all three tables
SELECT
    c.country,
    COUNT(DISTINCT i.invoice_no)               AS num_orders,
    ROUND(SUM(ii.line_revenue), 2)             AS total_revenue,
    ROUND(SUM(ii.line_revenue) / COUNT(DISTINCT i.invoice_no), 2) AS avg_order_value
FROM customers c
JOIN invoices i       ON c.customer_id = i.customer_id
JOIN invoice_items ii ON i.invoice_no  = ii.invoice_no
GROUP BY c.country
ORDER BY total_revenue DESC
LIMIT 10;

-- Q4: First purchase date per customer (feeds cohort/RFM analysis)
-- Subquery/window function to find each customer's first invoice date
SELECT
    customer_id,
    MIN(invoice_date) AS first_purchase_date
FROM invoices
GROUP BY customer_id
ORDER BY first_purchase_date;

-- Q5: Revenue concentration - what % of revenue comes from top 20% of customers
WITH customer_revenue AS (
    SELECT
        i.customer_id,
        SUM(ii.line_revenue) AS customer_total_revenue
    FROM invoices i
    JOIN invoice_items ii ON i.invoice_no = ii.invoice_no
    GROUP BY i.customer_id
),
ranked AS (
    SELECT
        *,
        NTILE(5) OVER (ORDER BY customer_total_revenue DESC) AS revenue_quintile
    FROM customer_revenue
)
SELECT
    revenue_quintile,
    COUNT(*)                              AS num_customers,
    ROUND(SUM(customer_total_revenue), 2) AS total_revenue,
    ROUND(100.0 * SUM(customer_total_revenue) / SUM(SUM(customer_total_revenue)) OVER (), 1) AS pct_of_total_revenue
FROM ranked
GROUP BY revenue_quintile
ORDER BY revenue_quintile;
