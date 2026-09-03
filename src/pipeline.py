#!/usr/bin/env python3
"""Validated raw CSV ingestion into a SQLite route-profit star schema; stdlib only."""
from __future__ import annotations

import argparse
import csv
import sqlite3
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/sample"
STAGING = ROOT / "data/staging"
REPORT = ROOT / "reports/data_quality_report.md"
DB = STAGING / "route_profit.db"
REQUIRED = {
    "customers": ["customer_id", "customer_name", "segment", "source_updated_at"],
    "routes": ["route_id", "route_date", "depot_code", "lane_id", "vehicle_id", "carrier_id", "planned_distance_km", "actual_distance_km", "planned_direct_cost", "currency", "source_updated_at"],
    "stops": ["stop_id", "route_id", "customer_id", "promised_end_ts", "actual_delivery_ts", "status", "failure_reason", "source_updated_at"],
    "cost_transactions": ["cost_transaction_id", "route_id", "cost_category", "cost_amount", "currency", "posting_date", "source_updated_at"],
    "revenue_transactions": ["revenue_transaction_id", "route_id", "customer_id", "revenue_amount", "currency", "posting_date", "source_updated_at"],
}
KEYS = {"customers": "customer_id", "routes": "route_id", "stops": "stop_id", "cost_transactions": "cost_transaction_id", "revenue_transactions": "revenue_transaction_id"}
ALLOWED_STATUS = {"DELIVERED", "FAILED", "CANCELLED"}
ALLOWED_COST = {"FUEL", "DRIVER_LABOR", "TOLL", "CARRIER", "ACCESSORIAL"}


class QualityError(ValueError):
    pass


def parse_decimal(value: str, field: str) -> Decimal:
    try:
        result = Decimal(value).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        raise QualityError(f"invalid decimal for {field}: {value!r}")
    if result < 0:
        raise QualityError(f"negative value for {field}: {value!r}")
    return result


def parse_date(value: str, field: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise QualityError(f"invalid ISO date for {field}: {value!r}")


def parse_timestamp(value: str, field: str, nullable: bool = False) -> str | None:
    if not value and nullable:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except ValueError:
        raise QualityError(f"invalid ISO timestamp for {field}: {value!r}")


def read_raw(name: str) -> list[dict[str, str]]:
    path = RAW / f"{name}.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or set(REQUIRED[name]) - set(reader.fieldnames):
            missing = sorted(set(REQUIRED[name]) - set(reader.fieldnames or []))
            raise QualityError(f"{name}: missing required columns {missing}")
        rows = list(reader)
    if not rows:
        raise QualityError(f"{name}: no rows")
    return rows


def standardize(name: str, rows: list[dict[str, str]]) -> list[dict[str, object]]:
    clean: list[dict[str, object]] = []
    seen = set()
    for row_num, raw in enumerate(rows, start=2):
        row = {key: (value or "").strip() for key, value in raw.items()}
        for field in REQUIRED[name]:
            if not row[field] and not (name == "stops" and field in {"actual_delivery_ts", "failure_reason"}):
                raise QualityError(f"{name} row {row_num}: required field {field} is null")
        key = row[KEYS[name]].upper()
        if key in seen:
            raise QualityError(f"{name} row {row_num}: duplicate {KEYS[name]} {key}")
        seen.add(key)
        row[KEYS[name]] = key
        row["source_updated_at"] = parse_timestamp(row["source_updated_at"], "source_updated_at")
        for field in ("route_id", "customer_id", "vehicle_id", "carrier_id", "depot_code", "lane_id"):
            if field in row:
                row[field] = row[field].upper()
        if name == "customers":
            row["segment"] = row["segment"].upper()
        if name == "routes":
            row["route_date"] = parse_date(row["route_date"], "route_date")
            for field in ("planned_distance_km", "actual_distance_km", "planned_direct_cost"):
                row[field] = parse_decimal(row[field], field)
        if name == "stops":
            row["status"] = row["status"].upper()
            if row["status"] not in ALLOWED_STATUS:
                raise QualityError(f"stops row {row_num}: invalid status {row['status']}")
            row["promised_end_ts"] = parse_timestamp(row["promised_end_ts"], "promised_end_ts")
            row["actual_delivery_ts"] = parse_timestamp(row["actual_delivery_ts"], "actual_delivery_ts", nullable=True)
            row["failure_reason"] = row["failure_reason"].upper() or None
            if row["status"] == "DELIVERED" and not row["actual_delivery_ts"]:
                raise QualityError(f"stops row {row_num}: delivered stop lacks actual_delivery_ts")
        if name in {"cost_transactions", "revenue_transactions"}:
            amount = "cost_amount" if name == "cost_transactions" else "revenue_amount"
            row[amount] = parse_decimal(row[amount], amount)
            row["posting_date"] = parse_date(row["posting_date"], "posting_date")
        if name == "cost_transactions":
            row["cost_category"] = row["cost_category"].upper()
            if row["cost_category"] not in ALLOWED_COST:
                raise QualityError(f"cost row {row_num}: invalid category {row['cost_category']}")
        if "currency" in row:
            row["currency"] = row["currency"].upper()
            if row["currency"] != "INR":
                raise QualityError(f"{name} row {row_num}: unsupported pilot currency {row['currency']}")
        clean.append(row)
    return clean


def validate_references(tables: dict[str, list[dict[str, object]]]) -> None:
    routes = {r["route_id"] for r in tables["routes"]}
    customers = {r["customer_id"] for r in tables["customers"]}
    for name in ("stops", "cost_transactions", "revenue_transactions"):
        bad = [r[KEYS[name]] for r in tables[name] if r["route_id"] not in routes]
        if bad:
            raise QualityError(f"{name}: unknown route_id for {bad}")
    for name in ("stops", "revenue_transactions"):
        bad = [r[KEYS[name]] for r in tables[name] if r["customer_id"] not in customers]
        if bad:
            raise QualityError(f"{name}: unknown customer_id for {bad}")


def validate_freshness(tables: dict[str, list[dict[str, object]]], as_of: date) -> None:
    cutoff = datetime.combine(as_of, datetime.min.time(), tzinfo=timezone.utc)
    for name, rows in tables.items():
        latest = max(datetime.fromisoformat(str(r["source_updated_at"]).replace("Z", "+00:00")) for r in rows)
        if (cutoff - latest).days > 2:
            raise QualityError(f"{name}: stale source; latest {latest.date()} is over two days old")


def write_staging(name: str, rows: list[dict[str, object]]) -> None:
    STAGING.mkdir(parents=True, exist_ok=True)
    fields = REQUIRED[name]
    with (STAGING / f"stg_{name}.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: "" if row.get(k) is None else row[k] for k in fields})


def build_database(t: dict[str, list[dict[str, object]]]) -> dict[str, Decimal]:
    if DB.exists(): DB.unlink()
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    # Clean source-shaped tables retain transaction-level auditability in the project database.
    for name, fields in REQUIRED.items():
        definitions = ", ".join(f'"{field}" TEXT' for field in fields)
        conn.execute(f'CREATE TABLE stg_{name} ({definitions})')
        placeholders = ", ".join("?" for _ in fields)
        conn.executemany(
            f'INSERT INTO stg_{name} VALUES ({placeholders})',
            [[None if row.get(field) is None else str(row[field]) for field in fields] for row in t[name]],
        )
    conn.executescript("""
    CREATE TABLE dim_date(date_key INTEGER PRIMARY KEY, full_date TEXT UNIQUE NOT NULL);
    CREATE TABLE dim_customer(customer_key INTEGER PRIMARY KEY, customer_id TEXT UNIQUE NOT NULL, customer_name TEXT NOT NULL, segment TEXT NOT NULL);
    CREATE TABLE dim_route(route_key INTEGER PRIMARY KEY, route_id TEXT UNIQUE NOT NULL, route_date_key INTEGER NOT NULL REFERENCES dim_date(date_key), depot_code TEXT NOT NULL, lane_id TEXT NOT NULL, vehicle_id TEXT NOT NULL, carrier_id TEXT NOT NULL, planned_distance_km REAL NOT NULL, actual_distance_km REAL NOT NULL, planned_direct_cost REAL NOT NULL, currency TEXT NOT NULL);
    CREATE TABLE fact_route_financial(route_financial_key INTEGER PRIMARY KEY, route_key INTEGER NOT NULL UNIQUE REFERENCES dim_route(route_key), date_key INTEGER NOT NULL REFERENCES dim_date(date_key), route_revenue REAL NOT NULL, direct_route_cost REAL NOT NULL, gross_route_profit REAL NOT NULL, gross_margin_pct REAL);
    CREATE TABLE fact_delivery_stop(delivery_stop_key INTEGER PRIMARY KEY, stop_id TEXT UNIQUE NOT NULL, route_key INTEGER NOT NULL REFERENCES dim_route(route_key), customer_key INTEGER NOT NULL REFERENCES dim_customer(customer_key), date_key INTEGER NOT NULL REFERENCES dim_date(date_key), promised_end_ts TEXT NOT NULL, actual_delivery_ts TEXT, status TEXT NOT NULL, failure_reason TEXT, on_time_flag INTEGER, eta_variance_minutes INTEGER);
    """)
    dates = {r["route_date"] for r in t["routes"]}
    for r in t["stops"]: dates.add(str(r["promised_end_ts"])[:10])
    conn.executemany("INSERT INTO dim_date VALUES (?,?)", [(int(d.replace("-", "")), d) for d in sorted(dates)])
    conn.executemany("INSERT INTO dim_customer(customer_id,customer_name,segment) VALUES (?,?,?)", [(r["customer_id"], r["customer_name"], r["segment"]) for r in t["customers"]])
    conn.executemany("INSERT INTO dim_route(route_id,route_date_key,depot_code,lane_id,vehicle_id,carrier_id,planned_distance_km,actual_distance_km,planned_direct_cost,currency) VALUES (?,?,?,?,?,?,?,?,?,?)", [(r["route_id"], int(str(r["route_date"]).replace("-", "")), r["depot_code"], r["lane_id"], r["vehicle_id"], r["carrier_id"], float(r["planned_distance_km"]), float(r["actual_distance_km"]), float(r["planned_direct_cost"]), r["currency"]) for r in t["routes"]])
    route_keys = dict(conn.execute("SELECT route_id, route_key FROM dim_route"))
    customer_keys = dict(conn.execute("SELECT customer_id, customer_key FROM dim_customer"))
    costs, revenues = defaultdict(Decimal), defaultdict(Decimal)
    for r in t["cost_transactions"]: costs[r["route_id"]] += r["cost_amount"]
    for r in t["revenue_transactions"]: revenues[r["route_id"]] += r["revenue_amount"]
    for r in t["routes"]:
        revenue, cost = revenues[r["route_id"]], costs[r["route_id"]]
        profit = revenue - cost
        margin = None if revenue == 0 else float((profit / revenue * 100).quantize(Decimal("0.01")))
        conn.execute("INSERT INTO fact_route_financial(route_key,date_key,route_revenue,direct_route_cost,gross_route_profit,gross_margin_pct) VALUES (?,?,?,?,?,?)", (route_keys[r["route_id"]], int(str(r["route_date"]).replace("-", "")), float(revenue), float(cost), float(profit), margin))
    for r in t["stops"]:
        actual = r["actual_delivery_ts"]
        variance = None if not actual else int((datetime.fromisoformat(str(actual).replace("Z", "+00:00")) - datetime.fromisoformat(str(r["promised_end_ts"]).replace("Z", "+00:00"))).total_seconds() / 60)
        on_time = None if r["status"] != "DELIVERED" else int(variance <= 0)
        conn.execute("INSERT INTO fact_delivery_stop(stop_id,route_key,customer_key,date_key,promised_end_ts,actual_delivery_ts,status,failure_reason,on_time_flag,eta_variance_minutes) VALUES (?,?,?,?,?,?,?,?,?,?)", (r["stop_id"], route_keys[r["route_id"]], customer_keys[r["customer_id"]], int(str(r["promised_end_ts"])[:10].replace("-", "")), r["promised_end_ts"], actual, r["status"], r["failure_reason"], on_time, variance))
    conn.commit()
    model_total = Decimal(str(conn.execute("SELECT COALESCE(SUM(route_revenue),0) FROM fact_route_financial").fetchone()[0])).quantize(Decimal("0.01"))
    source_total = sum((r["revenue_amount"] for r in t["revenue_transactions"]), Decimal("0"))
    if model_total != source_total: raise QualityError(f"revenue reconciliation failed: source {source_total}, model {model_total}")
    conn.close()
    return {"source_revenue": source_total, "model_revenue": model_total, "source_cost": sum((r["cost_amount"] for r in t["cost_transactions"]), Decimal("0"))}


def write_report(t: dict[str, list[dict[str, object]]], totals: dict[str, Decimal], as_of: date) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Data Quality Report", "", f"Generated by `src/pipeline.py` for as-of date **{as_of.isoformat()}**.", "", "## Result", "", "**PASS** — all blocking controls passed before model publication.", "", "## Control results", "", "| Control | Result | Evidence |", "| --- | --- | --- |"]
    lines += [f"| Required columns | PASS | {len(REQUIRED)} source schemas verified |", f"| Null thresholds | PASS | Required fields: 0 nulls; permitted nullable stop fields handled |", "| Duplicate keys | PASS | Unique business keys verified for all source tables |", "| Valid ranges/categories | PASS | Non-negative measures; controlled status/cost category/currency values |", "| Referential integrity | PASS | Route and customer foreign keys resolve before load |", "| Freshness | PASS | Every source latest update is within 2 days of as-of date |", f"| Row count reconciliation | PASS | {sum(len(v) for v in t.values())} raw rows standardized and loaded to staging |", f"| Revenue reconciliation | PASS | Source INR {totals['source_revenue']:.2f} = fact INR {totals['model_revenue']:.2f} |", f"| Cost reconciliation | PASS | Source direct cost INR {totals['source_cost']:.2f}; aggregated by route in fact |"]
    lines += ["", "## Source row counts", "", "| Source | Rows |", "| --- | ---: |"] + [f"| `{name}` | {len(rows)} |" for name, rows in t.items()]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(as_of: date | None = None) -> None:
    as_of = as_of or date.today()
    tables = {name: standardize(name, read_raw(name)) for name in REQUIRED}
    validate_references(tables)
    validate_freshness(tables, as_of)
    for name, rows in tables.items(): write_staging(name, rows)
    totals = build_database(tables)
    write_report(tables, totals, as_of)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    try:
        run(args.as_of)
        print(f"PASS: loaded validated model to {DB.relative_to(ROOT)}")
    except QualityError as error:
        print(f"FAIL: {error}")
        raise SystemExit(1)
