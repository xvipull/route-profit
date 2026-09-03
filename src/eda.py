#!/usr/bin/env python3
"""Purposeful EDA on curated facts; saves only decision-relevant figures."""
import sqlite3
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]; DB=ROOT/'data/staging/route_profit.db'
FIG=ROOT/'reports/figures'; SUMMARY=ROOT/'reports/eda_summary.md'

def run():
    if not DB.exists(): raise SystemExit('Database missing; run ingestion and apply_sql first.')
    FIG.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(DB) as con:
        routes=pd.read_sql_query('SELECT * FROM vw_route_profitability ORDER BY route_id',con)
        stops=pd.read_sql_query("SELECT s.stop_id,r.route_id,s.status,s.on_time_flag,s.eta_variance_minutes,s.failure_reason FROM fact_delivery_stop s JOIN dim_route r USING(route_key)",con)
    # Economics: direct view of routes consuming margin.
    ax=routes.set_index('route_id')[['route_revenue','direct_route_cost','gross_route_profit']].plot(kind='bar',figsize=(9,5),color=['#2563eb','#f97316','#16a34a'])
    ax.set(title='Route revenue, direct cost, and gross profit (INR)',xlabel='Route',ylabel='INR'); plt.tight_layout(); plt.savefig(FIG/'route_economics.png',dpi=160); plt.close()
    # Reliability: highlights lateness and failure exceptions by stop.
    p=stops.assign(label=lambda x:x.route_id+' / '+x.stop_id)
    colors=np.where(p.status.eq('FAILED'),'#dc2626',np.where(p.on_time_flag.eq(1),'#16a34a','#f59e0b'))
    ax=p.plot.scatter(x='label',y='eta_variance_minutes',c=colors,s=90,figsize=(9,5)); ax.axhline(0,color='#64748b',linewidth=1)
    ax.set(title='Delivery ETA variance: late, on-time, and failed stops',xlabel='Route / stop',ylabel='Minutes vs promised end'); plt.tight_layout(); plt.savefig(FIG/'delivery_reliability.png',dpi=160); plt.close()
    # Correlation is exploratory only: the report makes the tiny pilot sample explicit.
    fields=['route_revenue','direct_route_cost','gross_route_profit','actual_distance_km','gross_margin_pct']; corr=routes[fields].corr()
    fig,ax=plt.subplots(figsize=(7,6)); im=ax.imshow(corr,vmin=-1,vmax=1,cmap='RdYlGn'); ax.set_xticks(range(len(fields)),fields,rotation=45,ha='right'); ax.set_yticks(range(len(fields)),fields)
    for i in range(len(fields)):
        for j in range(len(fields)): ax.text(j,i,f'{corr.iloc[i,j]:.2f}',ha='center',va='center',fontsize=8)
    fig.colorbar(im,ax=ax,label='Pearson correlation'); ax.set_title('Route driver correlation (exploratory)'); plt.tight_layout(); plt.savefig(FIG/'route_driver_correlation.png',dpi=160); plt.close()
    numeric=routes[['route_revenue','direct_route_cost','gross_route_profit','actual_distance_km']]; q1,q3=numeric.quantile(.25),numeric.quantile(.75)
    outliers=((numeric < q1-1.5*(q3-q1)) | (numeric > q3+1.5*(q3-q1))).any(axis=1).sum()
    missing=stops.isna().sum()
    driver=corr['gross_route_profit'].drop('gross_route_profit').abs().idxmax()
    SUMMARY.write_text('# EDA Summary\n\n'
      f'Exploratory run covers **{len(routes)} routes** and **{len(stops)} delivery stops**. This pilot sample is too small for statistically conclusive correlation; findings are directional.\n\n'
      '## Missingness\n\n'+''.join(f'- `{k}`: {v} missing\n' for k,v in missing.items())+
      f'\n## Outliers\n\nIQR screening found **{outliers}** route rows with at least one outlying economics/distance value.\n\n'
      f'## Business drivers\n\n- Gross profit: INR {routes.gross_route_profit.sum():,.2f}; direct cost: INR {routes.direct_route_cost.sum():,.2f}.\n- On-time delivery: {100*stops.on_time_flag.dropna().mean():.1f}% of delivered stops; failed attempts: {100*stops.status.eq("FAILED").mean():.1f}%.\n- Largest absolute exploratory correlation with gross profit: `{driver}`.\n\nCharts are limited to route economics, delivery reliability, and exploratory driver correlation.\n',encoding='utf-8')
    print(f'EDA complete: {FIG.relative_to(ROOT)}')
if __name__=='__main__': run()
