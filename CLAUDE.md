# The Hangout — Business Automation

Bar & restaurant automation system. Syncs sales data directly from Rista POS API into local SQLite, powering an interactive dashboard and daily email reports.

## Project structure
- `hangout/` — Core Python package
  - `config.py` — Paths, thresholds, settings
  - `rista_api.py` — Direct Rista POS API client (JWT HS256 auth)
  - `sync.py` — API → SQLite sync logic
  - `db.py` — SQLite database layer
  - `data.py` — Data access (SQLite primary, Excel fallback)
  - `ingest.py` — Excel → SQLite ingestion (legacy)
  - `analytics.py` — Business calculations
  - `report.py` — HTML email builder
  - `mailer.py` — Gmail sender
- `dashboard/` — Streamlit web dashboard (4 pages)
- `scripts/` — Google Apps Script backup
- `.env` — API credentials (gitignored)
- `hangout.db` — Local SQLite database

## Running

```bash
# Sync from Rista POS API
python sync.py                            # sync today
python sync.py --yesterday                # sync yesterday
python sync.py --date 2026-04-12          # specific date
python sync.py --range 2026-04-01 2026-04-12  # date range
python sync.py --backfill 30             # last 30 days
python sync.py --stats                    # show DB stats

# Start dashboard (has sync buttons built in)
streamlit run dashboard/app.py

# Email reports
python run_report.py --preview
python run_report.py

# Legacy: ingest from Excel
python ingest.py --stats
```

## Data flow (current)
```
Rista POS API → sync.py → SQLite → Dashboard / Reports
```
No Google dependency. The dashboard has "Sync Today" / "Sync Yesterday" buttons.

## Credentials
Stored in `.env` file (gitignored). See `.env.example` for format.
