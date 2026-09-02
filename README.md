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
