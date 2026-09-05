# Advanced Decision-Support Analytics

## Customer-route profitability allocation

**Grain:** one customer-route pair. `fact_customer_route_profitability` allocates a route's curated revenue, direct cost, and gross profit to its customers. It reconciles to `fact_route_financial` by route within INR 0.01 rounding tolerance.

Allocation follows an explicit hierarchy: (1) direct revenue share from the route/customer revenue transaction; (2) delivered-stop share where no customer revenue is available; (3) equal customer share only where neither is available. The method and weight are persisted per row. This is a management-allocation view, not an invoice-level profitability ledger.

## Route clustering

**Grain:** one completed route in `route_cluster_assignment`. The deterministic k-means implementation standardizes cost per km, gross margin %, failed-delivery %, and on-time-delivery %. It chooses up to three clusters (fewer where route volume is small), then assigns business labels by a transparent risk score: high cost/failure minus margin/on-time. `vw_route_cluster_profile` is the leadership roll-up.

## Assumptions and limitations

- Direct customer revenue is the most defensible allocation basis; it is assumed to be complete and correctly linked to the route.
- The current pilot contains only two routes and one operating date. Clusters are demonstrative, not statistically stable segmentation; do not use them for pricing, carrier sanctions, or performance management.
- An unavailable on-time percentage is conservatively imputed as 0 for clustering and flagged in `reliability_imputed_flag`; source-data remediation remains preferred.
- Clusters describe similarity, not causality or forecasts. Reassess feature weights, thresholds, and stability when at least 30 routes across several weeks are available.
- Rounding can cause route/customer allocated amounts to differ from the route total by no more than INR 0.01; reconciliation is enforced in tests.
