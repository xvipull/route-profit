# Project Charter: Logistics Route Profitability & Delivery Reliability Analytics

## Purpose and business problem

Transportation leaders lack a reconciled view of route contribution after fuel, labor, tolls, accessorials, carrier charges, and failed-delivery costs. Reliability signals sit separately in TMS, telematics, and customer-service systems, making it difficult to see which operational failures destroy margin. This product creates a trusted daily-to-monthly decision layer at route, lane, customer, vehicle/carrier, and stop level.

## Stakeholder personas

| Persona | Needs | Primary actions |
| --- | --- | --- |
| Logistics Director | Network-level profit, service risk, and improvement opportunities | Prioritize lanes, set service targets, approve network changes |
| Fleet Manager | Dispatch-ready exceptions and controllable cost/reliability drivers | Reassign assets, coach drivers, schedule maintenance, resolve late routes |
| Finance Business Partner | Auditable route margin and variance to plan | Validate accruals, challenge cost allocations, forecast margin, close month |

## Decisions supported

1. Which lanes, customers, and routes should be expanded, repriced, redesigned, consolidated, or exited?
2. Which active routes need intervention because ETA risk, capacity, or cost variance threatens service or margin?
3. Are fleet, carrier, fuel, labor, and accessorial costs performing to plan, and who owns the variance?
4. Which carriers, vehicles, depots, and delivery windows consistently meet promised service at an acceptable cost?
5. What is the verified monthly transportation margin and the operational explanation for its change?

## Scope

**In scope:** daily route/lane profit measurement; planned-versus-actual cost and revenue; on-time delivery and exception analytics; filters by date, depot, lane, customer, carrier, vehicle, and driver where permitted; Power BI dashboards; Excel export pack; data-quality monitoring; monthly finance reconciliation.

**Out of scope:** dispatch optimization or automatic route assignment; dynamic pricing execution; driver performance management/disciplinary decisions; real-time safety monitoring; customer-facing tracking; predictive ETA or demand models in release 1; changing source-system records.

## Functional requirements

- Publish a certified daily dashboard by 08:00 local time for the prior operating day, with monthly close refresh after finance approval.
- Show revenue, allocated and direct cost, gross route profit, margin %, cost per km, cost per delivery, on-time delivery %, failed-delivery %, and exception drivers.
- Reconcile route-level totals to ERP transportation revenue and cost within agreed tolerance; disclose unmatched records.
- Preserve drill-through from portfolio to route and stop where access allows; show source freshness and data-quality status.
- Support exportable Finance and Fleet Manager views with consistent metric definitions.

## Acceptance criteria

| Criterion | Measure | Target |
| --- | --- | --- |
| Financial reconciliation | Monthly certified route revenue/cost vs ERP | within ±1.0%; exceptions listed |
| Coverage | Completed TMS shipments mapped to a route/lane | ≥98% for pilot depots |
| Delivery reliability validity | Delivered stops with promised and actual timestamps | ≥97% |
| Refresh | Prior-day dataset available | by 08:00 local time on ≥95% of business days |
| Usability | Pilot users completing five defined decisions without analyst help | ≥80% |
| Performance | Portfolio page at agreed pilot volume | ≤10 seconds for 90th percentile interaction |
| Trust | Critical data-quality test failures in a certified release | 0 |

## Governance

The Logistics Director owns business adoption and prioritization. Finance owns certified revenue/cost logic and monthly sign-off. The Analytics Product Owner owns the backlog, metric glossary, and release communication. Changes to certified KPI definitions require Finance and Logistics Director approval, versioned documentation, and effective dates.

## Delivery milestones

1. Discovery and source profiling; 2. pilot route profitability model; 3. reliability exception model; 4. finance reconciliation and UAT; 5. certified pilot release and adoption review.
