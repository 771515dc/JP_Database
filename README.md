# JP Database (PMDA → SQLite)

Builds `data/jp_pmda_devices.sqlite` (table `devices`) from PMDA Excel.

## Build
python .\pmda_japan_build_db.py --db-path data\jp_pmda_devices.sqlite --excel-path data\raw\pmda_certified_devices.xlsx

## Verify
sqlite3 data\jp_pmda_devices.sqlite "SELECT COUNT(*) FROM devices;"

## Source
PMDA Excel((Pharmaceuticals and Medical Devices Agency, Japan)): https://www.pmda.go.jp/files/000277537.xlsx  
Accessed on: <2025-11-16>

## Extraction approach
**Language handling:**  
  - Source headers are Japanese; we map them to English lower_snake_case.  
  - Text values are kept as-is (UTF-8) — can be Japanese or English.

**Parsing:**  
  - Read Excel with pandas + openpyxl.  
  - Robust date parsing:  
    - Accepts mixed formats (e.g., 2025/08/01, 01-Aug-2025, 2024-12-31).  
    - Converts Excel serial dates to ISO.  
    - Output format is ISO 8601: YYYY-MM-DD; blanks → NULL.

**Flags / booleans:**  
  Columns like “承認からの移行認証 / 承継品目 / 承継時認証機関変更” are stored as "1" for true (any non-empty mark, e.g., ○) and NULL otherwise.

**Deduplication:**  
  - Business key for duplicate detection: (certification_number, brand_name, certificate_holder_name).  
  - Clear duplicates (all fields identical): collapse to one row.  
  - Ambiguous duplicates (same key but some fields differ): keep all and set duplicate_flag = 1.

**Provenance:**  
  - Every row stores:  
    - country_code = 'JP'  
    - source_url (download URL),  
    - source_file (local filename),  
    - ingested_at (UTC timestamp).

**Indexes:**  
  - Created for faster lookups:  
    - idx_devices_certnum on certification_number  
    - idx_devices_holder on certificate_holder_name  
    - idx_devices_brand on brand_name

**Multi-file aggregation:**  
  This repo currently ingests one official Excel per run.  
  To process multiple period files (future updates), concatenate DataFrames and run the same deduplication; the logic supports cross-file duplicates.


## Schema (table: devices)  
All text is UTF-8. Dates are ISO 8601 strings or NULL. Missing fields stay NULL.  
| Column                                     | Type             | Description                                                   | Example                                       |
| ------------------------------------------ | ---------------- | ------------------------------------------------------------- | --------------------------------------------- |
| id                                         | INTEGER PK       | Internal surrogate key                                        | `1`                                           |
| country_code                               | TEXT             | ISO country code                                              | `JP`                                          |
| certification_body_code                    | TEXT             | 認証機関コード (cert body code)                                      | `TUV01`                                       |
| certification_number                       | TEXT             | 認証番号 (primary business ID)                                    | `301AGBZX00001`                               |
| certification_date                         | TEXT (date)      | 認証年月日 (ISO)                                                   | `2025-08-01`                                  |
| brand_name                                 | TEXT             | 販売名 (commercial name)                                         | `Example Catheter`                            |
| generic_name                               | TEXT             | 一般的名称 (generic device name)                                   | `Catheter`                                    |
| certificate_holder_name                    | TEXT             | 業者名_認証取得者 (certificate holder / manufacturer when applicable) | `ABC株式会社`                                     |
| certificate_holder_corporate_number        | TEXT             | 法人番号 (holder)                                                 | `1234567890123`                               |
| designated_foreign_holder_name             | TEXT             | 選任外国製造医療機器等製造販売業者                                             | `XYZ Ltd.`                                    |
| designated_foreign_holder_corporate_number | TEXT             | 法人番号 (foreign holder)                                         | `9876543210000`                               |
| transition_from_approval_flag              | TEXT             | 承認からの移行認証 (`1` true / `NULL`)                                 | `1`                                           |
| succession_flag                            | TEXT             | 承継品目 (`1` / `NULL`)                                           | `1`                                           |
| succession_date                            | TEXT (date)      | 承継年月日 (ISO)                                                   | `2024-12-31`                                  |
| cert_body_changed_on_succession_flag       | TEXT             | 承継時認証機関変更 (`1` / `NULL`)                                      | `1`                                           |
| certification_discontinuation_date         | TEXT (date)      | 認証整理日                                                         | `2026-03-31`                                  |
| certification_cancellation_date            | TEXT (date)      | 認証取消日                                                         | `2027-01-15`                                  |
| row_number                                 | TEXT             | Source row/No if present                                      | `1234`                                        |
| source_url                                 | TEXT             | Provenance — file URL                                         | `https://www.pmda.go.jp/files/000277537.xlsx` |
| source_file                                | TEXT             | Provenance — local filename                                   | `pmda_certified_devices.xlsx`                 |
| ingested_at                                | TEXT (timestamp) | ETL run timestamp (UTC, ISO 8601)                             | `2025-11-17T05:42:10Z`                        |
| duplicate_flag                             | INTEGER          | `0` not duplicate, `1` ambiguous duplicate kept               | `0`                                           |
| extra_col_*                                | TEXT             | Any unmapped columns retained verbatim                        | (varies)                                      |

## Known limitations & edge cases
- **Schema drift:** If PMDA adds/renames columns, they will appear as extra_col_* until mapping is updated.

- **Boolean symbols:** Some tables use marks like ○; we treat any non-empty value as true. If stricter coding appears later, parsing may need tweaks.

- **Multi-file ingestion:** Current entry point handles one Excel at a time. For year-over-year merges, concatenate first and then run the same dedup rules.

- **Entity naming variance:** Full-width/half-width spaces or minor typography variations can affect grouping. (If needed, add a normalization step to trim/standardize whitespace before dedup.)

## Quality checks performed
- Row count against source.

- % NULL in key columns (e.g., certification_number).

- Duplicate groups report (by key triplet).

- Date sanity: MIN/MAX certification_date.

- Optional JSON snapshot at reports/jp_pmda_qa.json.

## Reproduction steps
- **Requirements:**  
  - Python 3.10+  
  - See requirements.txt:  
  - pandas, openpyxl, requests, python-dateutil  

- **Setup (PowerShell on Windows):**  
  - python -m venv .venv  
  - .\.venv\Scripts\activate  
  - pip install -r requirements.txt

- **Build the database:**  
  - #Path used by this repo:  
  - #data\raw\pmda_certified_devices.xlsx  
  - python .\pmda_japan_build_db.py --db-path data\jp_pmda_devices.sqlite --excel-path data\raw\pmda_certified_devices.xlsx
