-- Part 1, Task 3 — Reports

-- ---------------------------------------------------------------------------
-- (a) Order totals — revenue per row = quantity * price * (1 - discount_pct/100),
--     NULL discount treated as 0% via COALESCE. Joins orders to products.
-- Output:
--   total_orders | total_revenue | avg_order_value
--   180          | 99860.20      | 554.78
SELECT
    COUNT(*)                                                                   AS total_orders,
    ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_revenue,
    ROUND(AVG(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS avg_order_value
FROM orders o
JOIN products p ON o.product_id = p.product_id;

-- ---------------------------------------------------------------------------
-- (b) COUNT(*) vs COUNT(column) — 15 orders have no rating yet.
-- Output:
--   total_rows | rated_rows | missing_ratings
--   180        | 165        | 15
SELECT
    COUNT(*)                     AS total_rows,
    COUNT(rating)                AS rated_rows,
    COUNT(*) - COUNT(rating)     AS missing_ratings
FROM orders;

-- ---------------------------------------------------------------------------
-- (c) LEFT JOIN with a genuine zero-match row — customer with zero orders.
-- Output (both queries): C045 | Vihaan
SELECT c.customer_id, c.name, COUNT(o.order_id) AS order_count
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
HAVING COUNT(o.order_id) = 0;

-- Independent confirmation via NOT IN — must return the same single customer.
SELECT customer_id, name
FROM customers
WHERE customer_id NOT IN (SELECT DISTINCT customer_id FROM orders);

-- ---------------------------------------------------------------------------
-- (d) GROUP BY + HAVING — return rate by city, HAVING return_rate_pct > 20,
--     ordered by return_rate_pct DESC.
-- Output:
--   city      | total_orders | returned_orders | return_rate_pct
--   Jaipur    | 19           | 8               | 42.1
--   Lucknow   | 49           | 15              | 30.6
--   Bangalore | 33           | 8               | 24.2
SELECT
    c.city,
    COUNT(o.order_id)                                            AS total_orders,
    SUM(o.returned)                                             AS returned_orders,
    ROUND(100.0 * SUM(o.returned) / COUNT(o.order_id), 1)       AS return_rate_pct
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.city
HAVING return_rate_pct > 20
ORDER BY return_rate_pct DESC;

-- ---------------------------------------------------------------------------
-- (e) Ranking with ORDER BY + LIMIT/OFFSET — total spend per customer.
--     Tie-break customer_id ASC makes the ordering deterministic when two
--     customers have identical total_spend, so LIMIT/OFFSET paging is stable.
-- Output (LIMIT 5):
--   C043 | Reyansh | 12920.00
--   C026 | Isha    | 8371.60
--   C008 | Meera   | 4564.60
--   C011 | Arjun   | 4111.00
--   C042 | Sanya   | 3785.00
SELECT
    c.customer_id,
    c.name,
    ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_spend
FROM orders o
JOIN products  p ON o.product_id = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 5;

-- Ranks 3–5 without re-deriving the top 5:
-- Output (LIMIT 3 OFFSET 2):
--   C008 | Meera | 4564.60
--   C011 | Arjun | 4111.00
--   C042 | Sanya | 3785.00
SELECT
    c.customer_id,
    c.name,
    ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_spend
FROM orders o
JOIN products  p ON o.product_id = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 3 OFFSET 2;

-- ---------------------------------------------------------------------------
-- (f) Three-table JOIN with GROUP BY — revenue by category.
-- Output:
--   category     | order_count | category_revenue
--   Haircare     | 54          | 44956.10
--   Skincare     | 60          | 27346.00
--   Babycare     | 30          | 16805.00
--   PersonalCare | 36          | 10753.10
SELECT
    p.category,
    COUNT(o.order_id)                                                              AS order_count,
    ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS category_revenue
FROM orders o
JOIN products  p ON o.product_id = p.product_id
JOIN customers c ON o.customer_id = c.customer_id   -- three-way join compiles cleanly (Part 3 needs it)
GROUP BY p.category
ORDER BY category_revenue DESC;

-- ---------------------------------------------------------------------------
-- (g) LIKE — customers whose name starts with 'A'. Output: 10 rows.
SELECT customer_id, name
FROM customers
WHERE name LIKE 'A%';

-- ---------------------------------------------------------------------------
-- (h) DISTINCT — acquisition sources. Output: Ad, Organic, Referral, Social (4).
SELECT DISTINCT acquisition_source
FROM customers
ORDER BY acquisition_source;

-- ---------------------------------------------------------------------------
-- (i) ALTER TABLE + UPDATE with CASE — loyalty_tier.
-- Output of the final GROUP BY: Gold | 28  and  Silver | 17
ALTER TABLE customers ADD COLUMN loyalty_tier VARCHAR(10);

UPDATE customers
SET loyalty_tier = CASE WHEN city_tier = 1 THEN 'Gold' ELSE 'Silver' END;

SELECT loyalty_tier, COUNT(*) AS n
FROM customers
GROUP BY loyalty_tier;
