# EDA Summary

Exploratory run covers **2 routes** and **3 delivery stops**. This pilot sample is too small for statistically conclusive correlation; findings are directional.

## Missingness

- `stop_id`: 0 missing
- `route_id`: 0 missing
- `status`: 0 missing
- `on_time_flag`: 1 missing
- `eta_variance_minutes`: 1 missing
- `failure_reason`: 2 missing

## Outliers

IQR screening found **0** route rows with at least one outlying economics/distance value.

## Business drivers

- Gross profit: INR 7,050.00; direct cost: INR 22,450.00.
- On-time delivery: 50.0% of delivered stops; failed attempts: 33.3%.
- Largest absolute exploratory correlation with gross profit: `route_revenue`.

Charts are limited to route economics, delivery reliability, and exploratory driver correlation.
