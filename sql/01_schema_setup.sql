-- 01_schema_setup.sql
-- Normalizes the raw flat transaction file into a simple relational schema
-- (customers, invoices, invoice_items) so downstream queries can use real
-- JOINs and subqueries instead of operating on one flat table.
-- Run with DuckDB: duckdb retail.duckdb < sql/01_schema_setup.sql

CREATE OR REPLACE TABLE raw_transactions AS
SELECT *
FROM read_parquet('data/online_retail.parquet');

-- customers: one row per customer
CREATE OR REPLACE TABLE customers AS
SELECT DISTINCT
    CustomerID::INTEGER AS customer_id,
    Country              AS country
FROM raw_transactions;

-- invoices: one row per invoice (order)
CREATE OR REPLACE TABLE invoices AS
SELECT
    InvoiceNo::VARCHAR                     AS invoice_no,
    CustomerID::INTEGER                    AS customer_id,
    MIN(InvoiceDate)::TIMESTAMP            AS invoice_date
FROM raw_transactions
GROUP BY InvoiceNo, CustomerID;

-- invoice_items: one row per line item within an invoice
CREATE OR REPLACE TABLE invoice_items AS
SELECT
    InvoiceNo::VARCHAR   AS invoice_no,
    StockCode            AS stock_code,
    Description          AS description,
    Quantity::INTEGER    AS quantity,
    UnitPrice::DOUBLE    AS unit_price,
    (Quantity * UnitPrice)::DOUBLE AS line_revenue
FROM raw_transactions;

SELECT 'customers'      AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL
SELECT 'invoices',      COUNT(*) FROM invoices
UNION ALL
SELECT 'invoice_items', COUNT(*) FROM invoice_items;
