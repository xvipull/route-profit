import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pipeline


class PipelineUnitTests(unittest.TestCase):
    def test_decimal_rejects_negative_amount(self):
        with self.assertRaises(pipeline.QualityError):
            pipeline.parse_decimal("-0.01", "cost_amount")

    def test_timestamp_is_normalized_to_utc(self):
        self.assertEqual(pipeline.parse_timestamp("2026-09-02T14:00:00+05:30", "ts"), "2026-09-02T08:30:00Z")

    def test_unknown_route_fails_referential_integrity(self):
        tables = {name: [] for name in pipeline.REQUIRED}
        tables["routes"] = [{"route_id": "R1"}]
        tables["customers"] = [{"customer_id": "C1"}]
        tables["stops"] = [{"stop_id": "S1", "route_id": "BAD", "customer_id": "C1"}]
        with self.assertRaises(pipeline.QualityError):
            pipeline.validate_references(tables)

    def test_pipeline_creates_database_and_report(self):
        pipeline.run(date(2026, 9, 3))
        self.assertTrue(pipeline.DB.exists())
        self.assertIn("**PASS**", pipeline.REPORT.read_text(encoding="utf-8"))

    def test_revenue_is_decimal(self):
        self.assertEqual(pipeline.parse_decimal("12500", "revenue_amount"), Decimal("12500.00"))


if __name__ == "__main__":
    unittest.main()
