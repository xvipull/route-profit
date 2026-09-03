# Analytics Data Model

The pipeline builds `data/staging/route_profit.db` with a Kimball-style star schema. Each source business key is retained for lineage; integer surrogate keys are generated in the warehouse tables.

## Grain and keys

| Table | Grain | Surrogate key | Business key(s) |
| --- | --- | --- | --- |
| `dim_date` | One calendar date | `date_key` (YYYYMMDD) | `full_date` |
| `dim_customer` | One customer | `customer_key` | `customer_id` |
| `dim_route` | One completed route | `route_key` | `route_id` |
| `fact_route_financial` | One route | `route_financial_key` | `route_id` |
| `fact_delivery_stop` | One delivery attempt/stop | `delivery_stop_key` | `stop_id` |

`fact_route_financial` aggregates direct cost and recognized revenue by `route_id`; it is not a transaction-level ledger. `fact_delivery_stop` has one row per source stop, including failed stops. `dim_route` is a type-1 snapshot for the pilot; historized route attributes are a future extension.

## Relationships

```text
dim_date 1 ── * fact_route_financial * ── 1 dim_route
dim_date 1 ── * fact_delivery_stop    * ── 1 dim_route
dim_customer 1 ── * fact_delivery_stop
```

Financial revenue is route-level because a route may serve several customers. The source transaction tables remain in `stg_cost_transactions` and `stg_revenue_transactions` for audit and reconciliation.

## Load order

1. Validate immutable raw CSVs; 2. standardize and write `stg_*`; 3. load dimensions; 4. aggregate and load facts; 5. run post-load reconciliation and publish the report. The database enables foreign keys for every load.
