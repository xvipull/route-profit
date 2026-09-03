#!/usr/bin/env python3
"""Apply versioned KPI SQL to the local SQLite analytics database."""
import sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DB=ROOT/'data/staging/route_profit.db'; SQL=ROOT/'sql/01_kpi_views.sql'
if not DB.exists(): raise SystemExit('Database missing; run src/pipeline.py first.')
with sqlite3.connect(DB) as con: con.executescript(SQL.read_text(encoding='utf-8'))
print(f'Applied KPI layer: {SQL.relative_to(ROOT)}')
