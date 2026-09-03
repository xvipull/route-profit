-- Reconciliation tolerance: INR 0.01 (rounding only); row counts must match exactly.
WITH source_totals AS (
 SELECT 'revenue' metric,ROUND(SUM(CAST(revenue_amount AS REAL)),2) source_value FROM stg_revenue_transactions
 UNION ALL SELECT 'direct_cost',ROUND(SUM(CAST(cost_amount AS REAL)),2) FROM stg_cost_transactions
 UNION ALL SELECT 'delivery_stops',COUNT(*) FROM stg_stops
), curated_totals AS (
 SELECT 'revenue' metric,ROUND(SUM(route_revenue),2) curated_value FROM fact_route_financial
 UNION ALL SELECT 'direct_cost',ROUND(SUM(direct_route_cost),2) FROM fact_route_financial
 UNION ALL SELECT 'delivery_stops',COUNT(*) FROM fact_delivery_stop
)
SELECT s.metric,s.source_value,c.curated_value,ROUND(c.curated_value-s.source_value,2) variance,
 CASE WHEN ABS(c.curated_value-s.source_value)<=CASE WHEN s.metric IN('revenue','direct_cost') THEN .01 ELSE 0 END THEN 'PASS' ELSE 'FAIL' END reconciliation_status
FROM source_totals s JOIN curated_totals c USING(metric) ORDER BY s.metric;

WITH curated AS (SELECT ROUND(SUM(route_revenue),2) revenue,ROUND(SUM(direct_route_cost),2) cost FROM fact_route_financial),
reporting AS (SELECT ROUND(SUM(route_revenue),2) revenue,ROUND(SUM(direct_route_cost),2) cost FROM vw_route_profitability)
SELECT curated.revenue curated_revenue,reporting.revenue reporting_revenue,curated.cost curated_cost,reporting.cost reporting_cost,
 CASE WHEN ABS(curated.revenue-reporting.revenue)<=.01 AND ABS(curated.cost-reporting.cost)<=.01 THEN 'PASS' ELSE 'FAIL' END reporting_reconciliation_status
FROM curated CROSS JOIN reporting;
