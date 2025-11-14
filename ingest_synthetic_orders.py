#!/usr/bin/env python3
"""
Ingest synthetic e-commerce JSON datasets into a SQLite database.
"""

import json
import sqlite3
from pathlib import Path
from typing import Iterable, Iterator, List, Dict, Any


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "synthetic_data"
DB_PATH = PROJECT_ROOT / "ecommerce.db"
TABLE_NAME = "orders"


def iterate_json_records(data_dir: Path) -> Iterator[Dict[str, Any]]:
    """
    Yield order records from every JSON file in the provided directory.
    """
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    json_files = sorted(data_dir.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {data_dir}")

    for json_file in json_files:
        with json_file.open("r", encoding="utf-8") as handle:
            try:
                records: List[Dict[str, Any]] = json.load(handle)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Failed to parse JSON file {json_file}") from exc

        for row in records:
            yield row


def ensure_table_exists(connection: sqlite3.Connection) -> None:
    """
    Create the orders table if it does not already exist.
    """
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (TABLE_NAME,),
    )

    if cursor.fetchone():
        return

    cursor.execute(
        f"""
        CREATE TABLE {TABLE_NAME} (
            order_id TEXT PRIMARY KEY,
            customer_id TEXT,
            customer_name TEXT,
            customer_email TEXT,
            product_id TEXT,
            product_name TEXT,
            category TEXT,
            quantity INTEGER,
            price_per_unit REAL,
            total_amount REAL,
            payment_method TEXT,
            order_date TEXT,
            shipping_address TEXT,
            city TEXT,
            state TEXT,
            delivery_status TEXT,
            rating INTEGER
        )
        """
    )
    connection.commit()


def insert_orders(connection: sqlite3.Connection, records: Iterable[Dict[str, Any]]) -> int:
    """
    Insert order records into the database using parameterized queries.
    """
    cursor = connection.cursor()
    inserted = 0

    insert_sql = f"""
        INSERT OR REPLACE INTO {TABLE_NAME} (
            order_id,
            customer_id,
            customer_name,
            customer_email,
            product_id,
            product_name,
            category,
            quantity,
            price_per_unit,
            total_amount,
            payment_method,
            order_date,
            shipping_address,
            city,
            state,
            delivery_status,
            rating
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    for record in records:
        cursor.execute(
            insert_sql,
            (
                record.get("order_id"),
                record.get("customer_id"),
                record.get("customer_name"),
                record.get("customer_email"),
                record.get("product_id"),
                record.get("product_name"),
                record.get("category"),
                record.get("quantity"),
                record.get("price_per_unit"),
                record.get("total_amount"),
                record.get("payment_method"),
                record.get("order_date"),
                record.get("shipping_address"),
                record.get("city"),
                record.get("state"),
                record.get("delivery_status"),
                record.get("rating"),
            ),
        )
        inserted += 1

    connection.commit()
    return inserted


def fetch_sample(connection: sqlite3.Connection, limit: int = 5) -> List[sqlite3.Row]:
    """
    Retrieve the first `limit` rows from the orders table.
    """
    cursor = connection.cursor()
    cursor.execute(
        f"""
        SELECT *
        FROM {TABLE_NAME}
        ORDER BY order_id
        LIMIT ?
        """,
        (limit,),
    )
    return cursor.fetchall()


def main() -> None:
    """
    Orchestrate the ingestion workflow.
    """
    try:
        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row
    except sqlite3.Error as exc:
        raise SystemExit(f"Failed to connect to database {DB_PATH}: {exc}") from exc

    with connection:
        ensure_table_exists(connection)

        try:
            records = iterate_json_records(DATA_DIR)
            inserted = insert_orders(connection, records)
        except (FileNotFoundError, ValueError) as exc:
            raise SystemExit(f"Data ingestion error: {exc}") from exc
        except sqlite3.Error as exc:
            raise SystemExit(f"Database error during insertion: {exc}") from exc

        print(f"Inserted or updated {inserted} records into {DB_PATH}")

        try:
            sample_rows = fetch_sample(connection, limit=5)
        except sqlite3.Error as exc:
            raise SystemExit(f"Failed to fetch sample rows: {exc}") from exc

    if not sample_rows:
        print("No records found in the orders table.")
        return

    print("\nFirst 5 records:")
    for row in sample_rows:
        row_dict = {key: row[key] for key in row.keys()}
        print(row_dict)


if __name__ == "__main__":
    main()

