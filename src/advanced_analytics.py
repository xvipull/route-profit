#!/usr/bin/env python3
"""Build governed customer allocation and deterministic route-cluster outputs."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/staging/route_profit.db"


def allocate_profit(connection: sqlite3.Connection) -> None:
    """Allocate route financials by direct customer revenue, then delivered stops, then equal share."""
    connection.executescript("""
    DROP VIEW IF EXISTS vw_customer_route_profitability;
    DROP TABLE IF EXISTS fact_customer_route_profitability;
    CREATE TABLE fact_customer_route_profitability (
      customer_route_profitability_key INTEGER PRIMARY KEY,
      route_key INTEGER NOT NULL REFERENCES dim_route(route_key),
      customer_key INTEGER NOT NULL REFERENCES dim_customer(customer_key),
      allocation_method TEXT NOT NULL CHECK(allocation_method IN ('DIRECT_REVENUE_SHARE','DELIVERED_STOP_SHARE','EQUAL_SHARE')),
      allocation_weight REAL NOT NULL CHECK(allocation_weight >= 0 AND allocation_weight <= 1),
      allocated_revenue REAL NOT NULL,
      allocated_direct_cost REAL NOT NULL,
      allocated_gross_profit REAL NOT NULL,
      UNIQUE(route_key, customer_key)
    );
    WITH revenue AS (
      SELECT r.route_key, c.customer_key, SUM(CAST(s.revenue_amount AS REAL)) customer_revenue
      FROM stg_revenue_transactions s JOIN dim_route r ON r.route_id=s.route_id
      JOIN dim_customer c ON c.customer_id=s.customer_id GROUP BY r.route_key,c.customer_key
    ), delivered AS (
      SELECT route_key, customer_key, COUNT(*) delivered_stops
      FROM fact_delivery_stop WHERE status='DELIVERED' GROUP BY route_key,customer_key
    ), population AS (
      SELECT route_key, customer_key FROM revenue UNION SELECT route_key, customer_key FROM delivered
    ), weighted AS (
      SELECT p.route_key,p.customer_key, COALESCE(revenue.customer_revenue,0) customer_revenue,
        COALESCE(delivered.delivered_stops,0) delivered_stops,
        SUM(COALESCE(revenue.customer_revenue,0)) OVER(PARTITION BY p.route_key) route_customer_revenue,
        SUM(COALESCE(delivered.delivered_stops,0)) OVER(PARTITION BY p.route_key) route_delivered_stops,
        COUNT(*) OVER(PARTITION BY p.route_key) customer_count
      FROM population p LEFT JOIN revenue USING(route_key,customer_key) LEFT JOIN delivered USING(route_key,customer_key)
    )
    INSERT INTO fact_customer_route_profitability(route_key,customer_key,allocation_method,allocation_weight,allocated_revenue,allocated_direct_cost,allocated_gross_profit)
    SELECT w.route_key,w.customer_key,
      CASE WHEN w.route_customer_revenue>0 THEN 'DIRECT_REVENUE_SHARE' WHEN w.route_delivered_stops>0 THEN 'DELIVERED_STOP_SHARE' ELSE 'EQUAL_SHARE' END,
      CASE WHEN w.route_customer_revenue>0 THEN w.customer_revenue/w.route_customer_revenue WHEN w.route_delivered_stops>0 THEN 1.0*w.delivered_stops/w.route_delivered_stops ELSE 1.0/w.customer_count END,
      ROUND(f.route_revenue*(CASE WHEN w.route_customer_revenue>0 THEN w.customer_revenue/w.route_customer_revenue WHEN w.route_delivered_stops>0 THEN 1.0*w.delivered_stops/w.route_delivered_stops ELSE 1.0/w.customer_count END),2),
      ROUND(f.direct_route_cost*(CASE WHEN w.route_customer_revenue>0 THEN w.customer_revenue/w.route_customer_revenue WHEN w.route_delivered_stops>0 THEN 1.0*w.delivered_stops/w.route_delivered_stops ELSE 1.0/w.customer_count END),2),
      ROUND(f.gross_route_profit*(CASE WHEN w.route_customer_revenue>0 THEN w.customer_revenue/w.route_customer_revenue WHEN w.route_delivered_stops>0 THEN 1.0*w.delivered_stops/w.route_delivered_stops ELSE 1.0/w.customer_count END),2)
    FROM weighted w JOIN fact_route_financial f USING(route_key);
    CREATE VIEW vw_customer_route_profitability AS
    SELECT d.full_date route_date,r.route_id,c.customer_id,c.customer_name,c.segment,
      a.allocation_method,a.allocation_weight,a.allocated_revenue,a.allocated_direct_cost,a.allocated_gross_profit,
      ROUND(100.0*a.allocated_gross_profit/NULLIF(a.allocated_revenue,0),2) allocated_gross_margin_pct
    FROM fact_customer_route_profitability a JOIN dim_route r USING(route_key) JOIN dim_customer c USING(customer_key)
    JOIN dim_date d ON d.date_key=r.route_date_key;
    """)


def kmeans(features: np.ndarray, k: int, iterations: int = 50) -> np.ndarray:
    """Small deterministic Lloyd implementation; stable initial centroids use sorted risk values."""
    risk = features[:, 0] - features[:, 1] + features[:, 2] - features[:, 3]
    seeds = np.argsort(risk)[np.linspace(0, len(features) - 1, k, dtype=int)]
    centroids = features[seeds].copy()
    for _ in range(iterations):
        labels = ((features[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2).argmin(axis=1)
        updated = np.array([features[labels == cluster].mean(axis=0) if np.any(labels == cluster) else centroids[cluster] for cluster in range(k)])
        if np.allclose(centroids, updated): break
        centroids = updated
    return labels


def cluster_routes(connection: sqlite3.Connection) -> None:
    rows = connection.execute("""
      SELECT r.route_key,p.cost_per_km,p.gross_margin_pct,COALESCE(p.failed_delivery_pct,0),COALESCE(p.on_time_delivery_pct,0),
             CASE WHEN p.on_time_delivery_pct IS NULL THEN 1 ELSE 0 END reliability_imputed_flag
      FROM vw_route_profitability p JOIN dim_route r ON r.route_id=p.route_id ORDER BY r.route_key
    """).fetchall()
    if not rows: raise ValueError("No routes are available for clustering")
    raw = np.array([row[1:5] for row in rows], dtype=float)
    means, stds = raw.mean(axis=0), raw.std(axis=0)
    scaled = (raw - means) / np.where(stds == 0, 1, stds)
    labels = kmeans(scaled, min(3, len(rows)))
    connection.executescript("DROP VIEW IF EXISTS vw_route_cluster_profile; DROP TABLE IF EXISTS route_cluster_assignment;")
    connection.execute("""
      CREATE TABLE route_cluster_assignment (
        route_key INTEGER PRIMARY KEY REFERENCES dim_route(route_key), cluster_id INTEGER NOT NULL,
        cluster_label TEXT NOT NULL, cost_per_km REAL NOT NULL, gross_margin_pct REAL NOT NULL,
        failed_delivery_pct REAL NOT NULL, on_time_delivery_pct REAL NOT NULL, reliability_imputed_flag INTEGER NOT NULL,
        z_cost_per_km REAL NOT NULL, z_gross_margin_pct REAL NOT NULL, z_failed_delivery_pct REAL NOT NULL, z_on_time_delivery_pct REAL NOT NULL
      )
    """)
    # Higher cost/failure and lower margin/on-time constitute higher operational risk.
    cluster_risk = {cluster: float(np.mean(scaled[labels == cluster, 0] - scaled[labels == cluster, 1] + scaled[labels == cluster, 2] - scaled[labels == cluster, 3])) for cluster in set(labels)}
    ranked = {cluster: rank for rank, cluster in enumerate(sorted(cluster_risk, key=cluster_risk.get, reverse=True))}
    names = {0: "Highest cost/reliability risk", 1: "Watchlist", 2: "Relative strength"}
    values = []
    for index, row in enumerate(rows):
        cluster = int(labels[index]); rank = ranked[cluster]
        values.append((row[0], cluster, names.get(rank, "Relative strength"), *raw[index], row[5], *scaled[index]))
    connection.executemany("INSERT INTO route_cluster_assignment VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", values)
    connection.executescript("""
      CREATE VIEW vw_route_cluster_profile AS
      SELECT a.cluster_id,a.cluster_label,COUNT(*) route_count,
        ROUND(AVG(a.cost_per_km),2) avg_cost_per_km,ROUND(AVG(a.gross_margin_pct),2) avg_gross_margin_pct,
        ROUND(AVG(a.failed_delivery_pct),2) avg_failed_delivery_pct,ROUND(AVG(a.on_time_delivery_pct),2) avg_on_time_delivery_pct,
        SUM(a.reliability_imputed_flag) imputed_reliability_routes
      FROM route_cluster_assignment a GROUP BY a.cluster_id,a.cluster_label;
    """)


def run() -> None:
    if not DB.exists(): raise SystemExit("Database missing; run pipeline and apply_sql first.")
    with sqlite3.connect(DB) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        allocate_profit(connection)
        cluster_routes(connection)
        connection.commit()
    print("Built governed allocation and cluster outputs")


if __name__ == "__main__": run()
