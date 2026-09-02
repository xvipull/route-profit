# Assumptions, Risks, and Controls

## Assumptions

- TMS route and stop identifiers are stable and can be linked to finance transactions directly or by an approved attribution rule.
- Finance can provide a monthly approved allocation method for shared costs and a reporting-currency conversion rule.
- Promised delivery windows and actual timestamps are captured for pilot depots.
- Initial pilot covers completed routes only; open routes are clearly labeled as provisional.
- Local operating time zones are available or can be mapped from depot.

## Risks and mitigations

| Risk | Impact | Mitigation / owner |
| --- | --- | --- |
| Missing route references in invoices/costs | Margin cannot be attributed accurately | Maintain unmatched queue and documented allocation hierarchy; Finance |
| Inconsistent timestamp/time-zone capture | Incorrect service KPI | Normalize to UTC plus local display; Operations validates pilot extracts |
| Fuel/labor posting lag | Daily profit volatility | Label estimates, refresh late postings, certify monthly; Finance |
| Cost allocation disputed by operations | Low trust and adoption | Publish allocation version and direct-vs-allocated cost; Finance + Logistics |
| PII exposure in driver/stop data | Privacy or labor-relations harm | Pseudonymize/minimize, role-based access, no driver ranking; Privacy + Fleet |
| Source refresh failure | Stale operational decisions | Freshness alerts, last-success banner, retry/runbook; Data Engineering |

## Refresh cadence and operating controls

Operational TMS and telematics data refresh daily by 07:00 local time. Fuel and carrier feeds refresh daily when available; ERP revenue/cost transactions refresh daily with a three-business-day late-posting lookback. Finance-approved allocations and currency rates refresh monthly at close. Every published dataset exposes `source_updated_at`, refresh status, and a reconciliation status.

## Security and privacy

Use least-privilege, role-based access: Fleet may see operational route detail; Finance may see customer commercial values; aggregated dashboards are the default for leadership. Do not place names, phone numbers, street-level delivery addresses, driver identifiers, credentials, or unmasked production extracts in this repository. Encrypt data in transit and at rest, audit dashboard access, retain data per approved policy, and conduct a privacy review before enabling stop-level detail.
