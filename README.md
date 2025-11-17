# JP Database (PMDA → SQLite)

Builds `data/jp_pmda_devices.sqlite` (table `devices`) from PMDA Excel.

## Build
python .\pmda_japan_build_db.py --db-path data\jp_pmda_devices.sqlite --excel-path data\raw\pmda_certified_devices.xlsx

## Verify
sqlite3 data\jp_pmda_devices.sqlite "SELECT COUNT(*) FROM devices;"

## Source
PMDA Excel: https://www.pmda.go.jp/files/000277537.xlsx
Accessed on: <YYYY-MM-DD>
