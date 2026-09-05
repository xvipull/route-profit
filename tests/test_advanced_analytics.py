import sqlite3
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import advanced_analytics, pipeline


class AdvancedAnalyticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pipeline.run(date(2026, 9, 3))
        with sqlite3.connect(pipeline.DB) as con:
            con.executescript((ROOT / "sql/01_kpi_views.sql").read_text(encoding="utf-8"))
        advanced_analytics.run()

    def test_allocation_reconciles_to_route_profit(self):
        with sqlite3.connect(pipeline.DB) as con:
            variance = con.execute("""
              SELECT MAX(ABS(f.gross_route_profit - a.allocated_profit))
              FROM fact_route_financial f JOIN (
                SELECT route_key,ROUND(SUM(allocated_gross_profit),2) allocated_profit
                FROM fact_customer_route_profitability GROUP BY route_key
              ) a USING(route_key)
            """).fetchone()[0]
        self.assertLessEqual(variance, 0.01)

    def test_clusters_assign_every_route_once(self):
        with sqlite3.connect(pipeline.DB) as con:
            routes = con.execute("SELECT COUNT(*) FROM dim_route").fetchone()[0]
            assignments = con.execute("SELECT COUNT(*) FROM route_cluster_assignment").fetchone()[0]
            invalid_labels = con.execute("SELECT COUNT(*) FROM route_cluster_assignment WHERE cluster_label='' OR cluster_id IS NULL").fetchone()[0]
        self.assertEqual(routes, assignments)
        self.assertEqual(invalid_labels, 0)


if __name__ == "__main__": unittest.main()
