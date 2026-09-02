# Data Dictionary

## Core entities

| Entity | Key | Source owner | Description / key fields |
| --- | --- | --- | --- |
| Route | `route_id` | TMS Operations | Planned movement: depot, lane, planned start/end, vehicle, carrier, planned distance and cost |
| Stop | `stop_id` | TMS Operations | Delivery activity: route ID, customer ID, promised window, actual arrival/departure, status, failure reason |
| Shipment | `shipment_id` | TMS Operations | Commercial shipment: route ID, weight/volume, service type, planned and actual status |
| Telematics event | `event_id` | Fleet / Telematics | Vehicle position, timestamp, odometer, engine/fuel signal; joinable by vehicle and time |
| Cost transaction | `cost_transaction_id` | Finance | Fuel, labor, toll, carrier, maintenance, accessorial amount, currency, posting date, route reference where available |
| Revenue transaction | `revenue_transaction_id` | Finance | Recognized/invoiced transportation revenue, customer, shipment/route reference, posting period |
| Customer | `customer_id` | CRM / Master Data | Customer name, segment, contractual service commitment; restricted commercial data |
| Carrier / vehicle | `carrier_id`, `vehicle_id` | Fleet Procurement | Ownership, carrier, vehicle class, depot, capacity; driver identity excluded from standard outputs |

## Required fields and quality rules

| Field | Type | Rule |
| --- | --- | --- |
| `route_id` | string | Non-null, unique in route extract, stable across source refreshes |
| `route_date` | date | Required; within reporting calendar |
| `lane_id` | string | Origin/destination mapping maintained by Network Planning |
| `actual_distance_km` | decimal | Non-negative; flag variance >20% to planned distance |
| `promised_end_ts` | timestamp | Required for service-eligible stop; stored with timezone |
| `actual_delivery_ts` | timestamp | Required for delivered stop; must not precede route start without exception |
| `cost_amount` | decimal | Currency and cost category required; non-null for posted transaction |
| `revenue_amount` | decimal | Currency, posting period, and attribution key required |
| `source_updated_at` | timestamp | Required for freshness monitoring |

## Data ownership and retention

TMS Operations owns route, stop, and shipment definitions; Fleet owns telematics and asset attributes; Finance owns cost/revenue and allocation rules; CRM/Master Data owns customer attributes; Analytics owns transformed models and lineage. Raw operational and financial extracts follow source-system retention policy; analytics datasets retain only the minimum history approved by Finance and Privacy, with standard target of 25 months for trend analysis.
