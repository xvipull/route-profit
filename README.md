# Route Profit

Analytics workspace for **Logistics Route Profitability & Delivery Reliability Analytics**. It gives operations and finance a shared, governed view of which lanes, customers, and routes create profit—and where delivery reliability is eroding it.

## Product objective

Turn shipment, dispatch, telematics, cost, and invoice data into daily decisions on route design, carrier/fleet performance, exception recovery, and margin improvement.

## Architecture

```text
TMS / WMS / GPS / fuel cards / ERP / invoices
                    |
              data/raw (immutable extracts)
                    |
          SQL + staging quality checks
                    |
       curated route, stop, cost, and KPI models
                    |
     Power BI semantic model + Excel analysis packs
                    |
        operational dashboards and monthly reports
```

| Layer | Location | Purpose |
| --- | --- | --- |
| Source extracts | `data/raw` | Access-controlled, immutable landing files |
| Standardization | `data/staging`, `sql`, `src` | Cleansing, matching, and calculations |
| Analysis | `notebooks`, `tests` | Exploration and automated data checks |
| Consumption | `powerbi`, `excel`, `reports` | Governed dashboards and exported reporting |

## Documentation

- [Project requirements and charter](docs/requirements.md)
- [KPI catalog](docs/kpi_catalog.md)
- [Data dictionary](docs/data_dictionary.md)
- [Assumptions and risk register](docs/assumptions.md)

## Screenshot placeholders

> **Route profitability overview** — screenshot to be added after the first Power BI release.

> **Delivery reliability exception map** — screenshot to be added after the first Power BI release.

## Repository conventions

Do not commit production extracts, personal data, credentials, or Power BI service exports. Keep raw extracts in approved storage and use this repository for schemas, transformations, tests, and sanitized samples only.

## Run the data pipeline

The repository includes sanitized, representative CSV extracts in `data/raw/sample`. They are immutable inputs: the pipeline only reads them and writes a SQLite project database, clean staging CSVs, and a generated quality report.

```bash
python3 src/pipeline.py --as-of 2026-09-03
python3 src/apply_sql.py
python3 src/advanced_analytics.py
python3 -m pip install -r requirements-eda.txt
python3 src/eda.py
python3 -m unittest discover -s tests -v
```

Outputs are `data/staging/route_profit.db`, cleaned staging tables, and [the quality report](reports/data_quality_report.md). The model and transformation rules are documented in [docs/data_model.md](docs/data_model.md) and [docs/transformation_log.md](docs/transformation_log.md).

KPI semantic views live in `sql/01_kpi_views.sql`; reconciliation controls and their INR 0.01 rounding tolerance live in `sql/02_reconciliation.sql`. The EDA script writes focused charts to `reports/figures` and findings to `reports/eda_summary.md`.

`src/advanced_analytics.py` persists governed customer-route allocation and route-cluster outputs. Their allocation hierarchy, feature logic, and decision-use limitations are documented in [advanced analytics](docs/advanced_analytics.md).
