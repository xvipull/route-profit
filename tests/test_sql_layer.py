import sqlite3
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pipeline


class SqlLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pipeline.run(date(2026, 9, 3))
        with sqlite3.connect(pipeline.DB) as con:
            con.executescript((ROOT / "sql/01_kpi_views.sql").read_text(encoding="utf-8"))

    def test_route_kpi_view_has_one_row_per_route(self):
        with sqlite3.connect(pipeline.DB) as con:
            rows = con.execute("SELECT COUNT(*) FROM vw_route_profitability").fetchone()[0]
        self.assertEqual(rows, 2)

    def test_reconciliation_controls_pass(self):
        with sqlite3.connect(pipeline.DB) as con:
            script = (ROOT / "sql/02_reconciliation.sql").read_text(encoding="utf-8")
            first_query = script.split(";\n\n", 1)[0] + ";"
            statuses = [row[-1] for row in con.execute(first_query).fetchall()]
        self.assertEqual(statuses, ["PASS", "PASS", "PASS"])


if __name__ == "__main__":
    unittest.main()
