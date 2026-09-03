-- SQLite KPI semantic layer; all monetary measures are INR in the pilot.
DROP VIEW IF EXISTS vw_route_profitability;
DROP VIEW IF EXISTS vw_daily_route_kpis;
DROP VIEW IF EXISTS vw_customer_segment_performance;
DROP VIEW IF EXISTS vw_route_exception;
DROP VIEW IF EXISTS vw_route_profit_rank;

CREATE VIEW vw_route_profitability AS
WITH stop_rollup AS (
  SELECT route_key, COUNT(*) attempted_stops,
    SUM(status = 'DELIVERED') delivered_stops, SUM(status = 'FAILED') failed_stops,
    SUM(on_time_flag = 1) on_time_stops,
    AVG(CASE WHEN status = 'DELIVERED' THEN eta_variance_minutes END) avg_eta_variance_minutes
  FROM fact_delivery_stop GROUP BY route_key
)
SELECT d.full_date route_date, r.route_id, r.depot_code, r.lane_id, r.vehicle_id, r.carrier_id,
  r.planned_distance_km, r.actual_distance_km, r.planned_direct_cost,
  f.route_revenue, f.direct_route_cost, f.gross_route_profit, f.gross_margin_pct,
  ROUND(f.direct_route_cost / NULLIF(r.actual_distance_km, 0), 2) cost_per_km,
  ROUND(f.direct_route_cost / NULLIF(s.delivered_stops, 0), 2) cost_per_delivery,
  ROUND(f.direct_route_cost - r.planned_direct_cost, 2) cost_variance_to_plan,
  s.attempted_stops, s.delivered_stops, s.failed_stops, s.on_time_stops,
  ROUND(100.0 * s.on_time_stops / NULLIF(s.delivered_stops, 0), 2) on_time_delivery_pct,
  ROUND(100.0 * s.failed_stops / NULLIF(s.attempted_stops, 0), 2) failed_delivery_pct,
  ROUND(s.avg_eta_variance_minutes, 2) avg_eta_variance_minutes
FROM fact_route_financial f JOIN dim_route r ON r.route_key=f.route_key
JOIN dim_date d ON d.date_key=f.date_key LEFT JOIN stop_rollup s ON s.route_key=r.route_key;

CREATE VIEW vw_daily_route_kpis AS
WITH daily_base AS (
  SELECT route_date, SUM(route_revenue) revenue, SUM(direct_route_cost) direct_cost,
    SUM(gross_route_profit) gross_profit, SUM(delivered_stops) delivered_stops,
    SUM(on_time_stops) on_time_stops, SUM(failed_stops) failed_stops, SUM(attempted_stops) attempted_stops
  FROM vw_route_profitability GROUP BY route_date
)
SELECT *, ROUND(100.0*gross_profit/NULLIF(revenue,0),2) gross_margin_pct,
  ROUND(100.0*on_time_stops/NULLIF(delivered_stops,0),2) on_time_delivery_pct,
  ROUND(100.0*failed_stops/NULLIF(attempted_stops,0),2) failed_delivery_pct,
  LAG(revenue) OVER (ORDER BY route_date) prior_period_revenue,
  LAG(gross_profit) OVER (ORDER BY route_date) prior_period_gross_profit,
  ROUND(100.0*(revenue-LAG(revenue) OVER (ORDER BY route_date))/NULLIF(LAG(revenue) OVER (ORDER BY route_date),0),2) revenue_pop_pct
FROM daily_base;

CREATE VIEW vw_customer_segment_performance AS
SELECT c.segment, c.customer_id, c.customer_name, COUNT(*) attempted_stops,
  SUM(s.status='DELIVERED') delivered_stops, SUM(s.status='FAILED') failed_stops,
  ROUND(100.0*SUM(s.on_time_flag=1)/NULLIF(SUM(s.status='DELIVERED'),0),2) on_time_delivery_pct,
  ROUND(AVG(CASE WHEN s.status='DELIVERED' THEN s.eta_variance_minutes END),2) avg_eta_variance_minutes
FROM fact_delivery_stop s JOIN dim_customer c ON c.customer_key=s.customer_key
GROUP BY c.segment,c.customer_id,c.customer_name;

CREATE VIEW vw_route_exception AS
SELECT p.*, CASE WHEN gross_route_profit<0 THEN 1 ELSE 0 END loss_making_flag,
  CASE WHEN on_time_delivery_pct<95 THEN 1 ELSE 0 END service_breach_flag,
  CASE WHEN failed_delivery_pct>2 THEN 1 ELSE 0 END failed_delivery_breach_flag,
  CASE WHEN ABS(actual_distance_km-planned_distance_km)/NULLIF(planned_distance_km,0)>0.20 THEN 1 ELSE 0 END distance_variance_flag,
  CASE WHEN direct_route_cost>planned_direct_cost THEN 1 ELSE 0 END over_plan_cost_flag
FROM vw_route_profitability p
WHERE gross_route_profit<0 OR on_time_delivery_pct<95 OR failed_delivery_pct>2
  OR ABS(actual_distance_km-planned_distance_km)/NULLIF(planned_distance_km,0)>0.20 OR direct_route_cost>planned_direct_cost;

CREATE VIEW vw_route_profit_rank AS
SELECT p.*, DENSE_RANK() OVER(PARTITION BY route_date ORDER BY gross_route_profit DESC) profit_rank_in_day,
  DENSE_RANK() OVER(PARTITION BY route_date ORDER BY gross_margin_pct DESC) margin_rank_in_day
FROM vw_route_profitability p;
