#!/usr/bin/env python3
"""
populate_walmart_db_direct.py
--------------------------------
This script automatically:

1. Locates spreadsheet_0, spreadsheet_1, spreadsheet_2 inside the cloned repo.
2. Loads each spreadsheet using pandas.
3. Inserts products into the `product` table (deduplicated).
4. Inserts shipments into the `shipment` table.

Database schema (from your uploaded DB):
  product(id INTEGER PK, name TEXT)
  shipment(id INTEGER PK, product_id INTEGER, quantity INTEGER, origin TEXT, destination TEXT)

Usage:
    python populate_walmart_db_direct.py --repo PATH/TO/forage-walmart-task-4 --db /mnt/data/shipment_database.db
"""

import argparse
import sqlite3
from pathlib import Path
import pandas as pd
import re

def find_repo_files(repo_path: Path):
    """Find spreadsheet_0, spreadsheet_1, spreadsheet_2 inside the repository."""
    exts = ('.csv', '.xlsx', '.xls')
    spreadsheets = {}

    for file in repo_path.rglob("*"):
        if file.suffix.lower() in exts:
            name = file.stem.lower()
            if "0" in name and "spreadsheet" in name:
                spreadsheets['0'] = file
            if "1" in name and "spreadsheet" in name:
                spreadsheets['1'] = file
            if "2" in name and "spreadsheet" in name:
                spreadsheets['2'] = file

    if len(spreadsheets) < 3:
        raise Exception("Could not locate spreadsheets 0, 1, and 2 inside the repo.")

    return spreadsheets


def read_sheet(path: Path) -> pd.DataFrame:
    """Load CSV or Excel."""
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path)


def ensure_product(conn: sqlite3.Connection, name: str) -> int:
    """Insert product if it does not exist; return product_id."""
    cur = conn.execute("SELECT id FROM product WHERE name = ?", (name,))
    row = cur.fetchone()
    if row:
        return row[0]

    cur = conn.execute("INSERT INTO product (name) VALUES (?)", (name,))
    conn.commit()
    return cur.lastrowid


def detect_columns(df, keys):
    """Find column whose name contains certain keywords."""
    for col in df.columns:
        c = col.lower()
        if any(k in c for k in keys):
            return col
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="Path to cloned forage-walmart-task-4 repo")
    parser.add_argument("--db", required=True, help="Path to SQLite DB (shipment_database.db)")
    args = parser.parse_args()

    repo = Path(args.repo)
    if not repo.exists():
        raise Exception("Repository path does not exist.")

    print("🔍 Searching for spreadsheets...")
    sheets = find_repo_files(repo)
    print("✔ Found spreadsheets:")
    for k, v in sheets.items():
        print(f"  spreadsheet_{k}: {v}")

    df0 = read_sheet(sheets['0'])
    df1 = read_sheet(sheets['1'])
    df2 = read_sheet(sheets['2'])

    print("✔ Loaded spreadsheets.")

    # Connect to DB
    conn = sqlite3.connect(args.db)

    try:
        print("🛒 Processing spreadsheet_0 (products)...")

        # Detect product name column
        name_col = detect_columns(df0, ["name", "product"]) or df0.columns[0]

        for _, row in df0.iterrows():
            name = str(row[name_col]).strip()
            if name:
                ensure_product(conn, name)

        print("✔ Products inserted or verified.")

        # Extract columns from spreadsheet_2 (shipment metadata)
        sid_col = detect_columns(df2, ["shipment", "ship", "id"]) or df2.columns[0]
        origin_col = detect_columns(df2, ["origin", "from"]) or df2.columns[1]
        dest_col = detect_columns(df2, ["destination", "dest", "to"]) or df2.columns[2]

        shipment_meta = {}
        for _, row in df2.iterrows():
            sid = str(row[sid_col]).strip()
            origin = str(row[origin_col]).strip()
            dest = str(row[dest_col]).strip()
            shipment_meta[sid] = (origin, dest)

        print("✔ Shipment metadata extracted.")

        # Extract columns from spreadsheet_1 (products per shipment)
        sid1 = detect_columns(df1, ["shipment", "shipid", "id"]) or df1.columns[0]
        pname_col = detect_columns(df1, ["product", "name", "item"]) or df1.columns[1]
        qty_col = detect_columns(df1, ["qty", "quantity"]) or df1.columns[2]

        print("📦 Inserting shipment rows...")

        insert_count = 0

        for _, row in df1.iterrows():
            sid = str(row[sid1]).strip()
            pname = str(row[pname_col]).strip()
            qty = int(row[qty_col]) if not pd.isna(row[qty_col]) else 1

            if sid not in shipment_meta:
                continue

            origin, dest = shipment_meta[sid]

            # Ensure product exists
            pid = ensure_product(conn, pname)

            conn.execute(
                "INSERT INTO shipment (product_id, quantity, origin, destination) VALUES (?, ?, ?, ?)",
                (pid, qty, origin, dest)
            )
            insert_count += 1

        conn.commit()
        print(f"✔ Inserted {insert_count} shipment rows into database.")

    finally:
        conn.close()

    print("🎉 DONE — Database successfully populated!")


if __name__ == "__main__":
    main()


def ensure_product(conn: sqlite3.Connection, product_name: str) -> int:
    cur = conn.execute("SELECT id FROM product WHERE name = ?", (product_name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur = conn.execute("INSERT INTO product (name) VALUES (?)", (product_name,))
    conn.commit()
    return cur.lastrowid

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo', help='Path to cloned repo with spreadsheets (will search for spreadsheets 0/1/2)')
    p.add_argument('--sheet0', help='Path to spreadsheet 0 (products) - optional')
    p.add_argument('--sheet1', help='Path to spreadsheet 1 (products per shipment)')
    p.add_argument('--sheet2', help='Path to spreadsheet 2 (shipment origins/destinations)')
    p.add_argument('--db', required=True, help='Path to sqlite DB file (e.g. /mnt/data/shipment_database.db)')
    p.add_argument('--dry', action='store_true', help='Dry run (no DB writes)')
    args = p.parse_args()

    # resolve spreadsheet paths
    sheets = {}
    if args.repo:
        repo_path = Path(args.repo)
        mapping = find_spreadsheets(repo_path)
        sheets = mapping
    if args.sheet0:
        sheets['0'] = Path(args.sheet0)
    if args.sheet1:
        sheets['1'] = Path(args.sheet1)
    if args.sheet2:
        sheets['2'] = Path(args.sheet2)

    # require at least sheet1 and sheet2 (sheet0 optional)
    if '1' not in sheets or '2' not in sheets:
        raise SystemExit("Need spreadsheets 1 and 2 (sheets for products-per-shipment and shipment metadata). Provide via --repo or --sheet1/--sheet2.")

    # read sheets
    df1 = read_sheet(Path(sheets['1']))  # product per shipment
    df2 = read_sheet(Path(sheets['2']))  # shipment metadata (origin/destination)
    df0 = read_sheet(Path(sheets['0'])) if '0' in sheets else None

    # open DB
    conn = sqlite3.connect(args.db)
    try:
        cur = conn.cursor()
        # Optionally insert spreadsheet 0 into product table (if provided)
        if df0 is not None:
            # Expect df0 to have product name column; try to detect it
            name_col = None
            for c in df0.columns:
                if 'name' in c.lower() or 'product' in c.lower():
                    name_col = c
                    break
            if name_col is None:
                name_col = df0.columns[0]
            print(f"Inserting products from spreadsheet 0 using column '{name_col}'")
            for _, r in df0.iterrows():
                pname = r[name_col]
                if pd.isna(pname):
                    continue
                if not args.dry:
                    ensure_product(conn, str(pname).strip())

        # Build mapping: shipment_identifier -> (origin, destination)
        # Detect likely column names in df2
        sid_col = None; origin_col = None; dest_col = None
        for c in df2.columns:
            nc = c.lower()
            if any(k in nc for k in ('shipment','shipid','shipment_id','id')) and sid_col is None:
                sid_col = c
            if any(k in nc for k in ('origin','from','source')) and origin_col is None:
                origin_col = c
            if any(k in nc for k in ('destination','dest','to')) and dest_col is None:
                dest_col = c
        # Fallback: pick first/second/third if still None
        cols = list(df2.columns)
        if sid_col is None and len(cols) >= 1: sid_col = cols[0]
        if origin_col is None and len(cols) >= 2: origin_col = cols[1]
        if dest_col is None and len(cols) >= 3: dest_col = cols[2]
        print(f"Detected shipment metadata columns: id='{sid_col}', origin='{origin_col}', destination='{dest_col}'")

        # create mapping
        shipment_meta = {}
        for _, r in df2.iterrows():
            sid = r[sid_col]
            if pd.isna(sid):
                continue
            origin = r[origin_col] if origin_col in r.index else None
            dest = r[dest_col] if dest_col in r.index else None
            shipment_meta[str(sid)] = (None if pd.isna(origin) else str(origin), None if pd.isna(dest) else str(dest))

        # Detect columns in df1 (products per shipment)
        # Expect columns: shipment identifier, product name, quantity
        sid1 = None; pname_col = None; qty_col = None
        for c in df1.columns:
            nc = c.lower()
            if any(k in nc for k in ('shipment','shipid','shipment_id','id')) and sid1 is None:
                sid1 = c
            if any(k in nc for k in ('product','item','name','sku')) and pname_col is None:
                pname_col = c
            if any(k in nc for k in ('qty','quantity','amount')) and qty_col is None:
                qty_col = c
        # fallbacks
        cols1 = list(df1.columns)
        if sid1 is None and len(cols1) >= 1: sid1 = cols1[0]
        if pname_col is None and len(cols1) >= 2: pname_col = cols1[1]
        if qty_col is None:
            # try numeric column
            for c in cols1:
                if pd.api.types.is_numeric_dtype(df1[c]):
                    qty_col = c
                    break
        if qty_col is None:
            qty_col = cols1[2] if len(cols1) >= 3 else None

        print(f"Detected shipment-item columns: sid='{sid1}', product='{pname_col}', qty='{qty_col}'")

        # For each row in df1, insert into shipment (one row per product in a shipment)
        inserts = 0
        for _, r in df1.iterrows():
            sid = r[sid1]
            if pd.isna(sid):
                continue
            sid = str(sid)
            pname = r[pname_col] if pname_col in r.index else None
            if pd.isna(pname) or pname is None:
                continue
            qty = int(r[qty_col]) if (qty_col and not pd.isna(r.get(qty_col))) else 1
            origin, dest = shipment_meta.get(sid, (None, None))
            if origin is None or dest is None:
                # if metadata missing, we still insert with empty strings to satisfy NOT NULL if required
                origin = origin or ''
                dest = dest or ''
            if not args.dry:
                pid = ensure_product(conn, str(pname).strip())
                conn.execute(
                    "INSERT INTO shipment (product_id, quantity, origin, destination) VALUES (?, ?, ?, ?)",
                    (pid, qty, origin, dest)
                )
                conn.commit()
            inserts += 1

        print(f"Processed {len(df1)} shipment-item rows; inserted {inserts} shipments into DB (dry={args.dry})")

    finally:
        conn.close()

if __name__ == '__main__':
    import pandas as pd
    main()
