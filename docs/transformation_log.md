# Transformation Log

| Source | Transformation | Output | Rationale |
| --- | --- | --- | --- |
| All CSVs | Trim whitespace; uppercase identifiers/categories; preserve raw source file unchanged | `stg_*` | Stable joins and controlled dimensions |
| Routes | Parse ISO date; decimals to two-place numeric; currency uppercase | `stg_routes` / `dim_route` | Consistent measures and date keys |
| Stops | Parse ISO-8601 timestamps including offsets; normalize status to upper case; blank failure reason becomes null | `stg_stops` / `fact_delivery_stop` | Correct on-time and failed-delivery logic |
| Cost/revenue | Parse amounts as Decimal, reject negative values; require INR in pilot | staging + financial fact | Financial precision and pilot currency scope |
| Customers | Normalize segment to uppercase and customer ID to upper case | `stg_customers` / `dim_customer` | Conformed customer dimension |
| Transactions | Sum direct cost/revenue by route ID | `fact_route_financial` | Explicit one-row-per-route fact grain |

No source record is overwritten. Invalid records cause the run to fail before model loading; the generated report captures every check result. Currency conversion is intentionally not applied: the pilot admits INR only, and multi-currency conversion requires Finance-approved rates.
