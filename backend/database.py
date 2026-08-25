import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / "crm.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            company TEXT NOT NULL,
            phone TEXT
        );

        CREATE TABLE IF NOT EXISTS deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL CHECK (
                status IN ('New', 'Contacted', 'Won', 'Lost')
            ),
            salesperson TEXT NOT NULL,
            last_updated TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );

        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );

        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            interaction_type TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );
    """)

    # Insert sample customer if it doesn't already exist
    cursor.execute("""
        INSERT OR IGNORE INTO customers
        (name, email, company, phone)
        VALUES (?, ?, ?, ?)
    """, (
        "John Smith",
        "john@acme.com",
        "Acme Corp",
        "9876543210"
    ))

    # Get customer ID
    cursor.execute("""
        SELECT id FROM customers
        WHERE email = ?
    """, ("john@acme.com",))

    customer = cursor.fetchone()

    if customer:
        customer_id = customer["id"]

        # Insert sample deal if it doesn't already exist
        cursor.execute("""
            SELECT id FROM deals
            WHERE customer_id = ? AND title = ?
        """, (
            customer_id,
            "Acme CRM Implementation"
        ))

        existing_deal = cursor.fetchone()

        if not existing_deal:
            cursor.execute("""
                INSERT INTO deals
                (
                    customer_id,
                    title,
                    amount,
                    status,
                    salesperson,
                    last_updated
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                customer_id,
                "Acme CRM Implementation",
                25000.00,
                "New",
                "Vasu",
                "2026-08-25"
            ))

    connection.commit()
    connection.close()