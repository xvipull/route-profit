# KPI Catalog

All currency values use the finance reporting currency; a route is a completed planned movement identified by `route_id`.

| KPI | Definition / formula | Grain | Owner | Cadence |
| --- | --- | --- | --- | --- |
| Route revenue | Sum of recognized transportation revenue attributed to route | Route | Finance | Daily; certified monthly |
| Direct route cost | Fuel + driver labor + tolls + carrier charges + route-linked accessorials | Route | Finance / Fleet | Daily; certified monthly |
| Allocated route cost | Approved shared-cost allocation assigned to route | Route | Finance | Monthly |
| Gross route profit | Route revenue − direct route cost − allocated route cost | Route | Finance | Daily estimate; certified monthly |
| Gross margin % | Gross route profit / route revenue × 100; blank if revenue is zero | Route | Finance | Daily / monthly |
| Cost per km | Direct route cost / actual distance km | Route | Fleet | Daily |
| Cost per delivery | Direct route cost / delivered stops | Route | Fleet | Daily |
| On-time delivery % | Delivered stops at or before promised end timestamp / eligible delivered stops × 100 | Stop | Logistics | Daily |
| Failed-delivery % | Stops with final failed delivery status / attempted stops × 100 | Stop | Logistics | Daily |
| ETA variance | Actual delivery timestamp − promised end timestamp in minutes | Stop | Logistics | Daily |
| Cost variance to plan | Actual direct route cost − planned direct route cost | Route | Fleet / Finance | Daily |
| Revenue leakage | Expected billable revenue − invoiced/recognized revenue, after approved exclusions | Stop / route | Finance | Weekly / monthly |

**Eligibility:** cancelled, test, training, and customer-approved service-window changes are excluded from service KPIs but retained for audit. Cost allocations must use Finance-approved rules and version identifiers.
