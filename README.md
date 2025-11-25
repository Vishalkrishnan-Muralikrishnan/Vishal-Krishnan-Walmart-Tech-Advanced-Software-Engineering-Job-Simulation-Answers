For Task 4---

How It Works

You clone the Forage Walmart Task 4 repository.

The Python script searches the repo for:

spreadsheet_0

spreadsheet_1

spreadsheet_2
(CSV or XLSX files)

It loads the spreadsheets with pandas.

It inserts:

All product names from spreadsheet_0

Shipment metadata from spreadsheet_2

Shipment product rows from spreadsheet_1

It writes all data into the SQLite database.

Requirements

Before running the script, install dependencies:

pip install pandas openpyxl

How to Run
1. Clone the Forage repository
git clone https://github.com/theforage/forage-walmart-task-4

2. Run the script

Example:

python populate_walmart_db_direct.py --repo ./forage-walmart-task-4 --db shipment_database.db


Where:

--repo = path to your cloned forage Walmart repo

--db = path to the SQLite database you want to populate (e.g. shipment_database.db)
