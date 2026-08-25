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

    # =========================
    # CREATE TABLES
    # =========================

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

    # =========================
    # SAMPLE CUSTOMERS
    # =========================

    customers = [
        (
            "John Smith",
            "john@acme.com",
            "Acme Corp",
            "9876543210"
        ),
        (
            "Sarah Johnson",
            "sarah@techvision.com",
            "TechVision Solutions",
            "9876543211"
        ),
        (
            "Michael Brown",
            "michael@globex.com",
            "Globex Corporation",
            "9876543212"
        ),
        (
            "Emily Davis",
            "emily@nextgen.com",
            "NextGen Technologies",
            "9876543213"
        ),
        (
            "David Wilson",
            "david@innovatech.com",
            "Innovatech Systems",
            "9876543214"
        ),
    ]

    for customer in customers:
        cursor.execute("""
            INSERT OR IGNORE INTO customers
            (name, email, company, phone)
            VALUES (?, ?, ?, ?)
        """, customer)

    # =========================
    # GET CUSTOMER IDS
    # =========================

    customer_ids = {}

    cursor.execute("""
        SELECT id, email
        FROM customers
    """)

    rows = cursor.fetchall()

    for row in rows:
        customer_ids[row["email"]] = row["id"]

    # =========================
    # SAMPLE DEALS
    # =========================

    deals = [
        (
            customer_ids["john@acme.com"],
            "Acme CRM Implementation",
            25000.00,
            "New",
            "Vasu",
            "2026-08-25"
        ),
        (
            customer_ids["sarah@techvision.com"],
            "AI Automation Platform",
            18000.00,
            "Contacted",
            "Rahul",
            "2026-08-20"
        ),
        (
            customer_ids["michael@globex.com"],
            "Cloud Migration Project",
            35000.00,
            "Won",
            "Priya",
            "2026-08-22"
        ),
        (
            customer_ids["emily@nextgen.com"],
            "Customer Support AI",
            12000.00,
            "Contacted",
            "Vasu",
            "2026-08-10"
        ),
        (
            customer_ids["david@innovatech.com"],
            "Enterprise CRM Upgrade",
            45000.00,
            "Lost",
            "Rahul",
            "2026-07-28"
        ),
    ]

    for deal in deals:
        customer_id = deal[0]
        title = deal[1]

        cursor.execute("""
            SELECT id
            FROM deals
            WHERE customer_id = ?
            AND title = ?
        """, (customer_id, title))

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
            """, deal)

    # =========================
    # SAMPLE NOTES
    # =========================

    notes = [
        (
            customer_ids["john@acme.com"],
            "Customer requested a CRM implementation proposal.",
            "2026-08-24"
        ),
        (
            customer_ids["sarah@techvision.com"],
            "Follow up regarding AI automation requirements.",
            "2026-08-21"
        ),
        (
            customer_ids["michael@globex.com"],
            "Project successfully completed. Customer is satisfied.",
            "2026-08-22"
        ),
        (
            customer_ids["emily@nextgen.com"],
            "Customer wants a demo of the AI support platform.",
            "2026-08-15"
        ),
        (
            customer_ids["david@innovatech.com"],
            "Deal lost because customer selected another vendor.",
            "2026-07-28"
        ),
    ]

    for note in notes:
        cursor.execute("""
            SELECT id
            FROM notes
            WHERE customer_id = ?
            AND content = ?
        """, (note[0], note[1]))

        existing_note = cursor.fetchone()

        if not existing_note:
            cursor.execute("""
                INSERT INTO notes
                (
                    customer_id,
                    content,
                    created_at
                )
                VALUES (?, ?, ?)
            """, note)

    # =========================
    # SAMPLE INTERACTIONS
    # =========================

    interactions = [
        (
            customer_ids["john@acme.com"],
            "Email",
            "Sent CRM implementation proposal.",
            "2026-08-24"
        ),
        (
            customer_ids["john@acme.com"],
            "Call",
            "Discussed project requirements and timeline.",
            "2026-08-23"
        ),
        (
            customer_ids["sarah@techvision.com"],
            "Call",
            "Discussed AI automation requirements.",
            "2026-08-20"
        ),
        (
            customer_ids["michael@globex.com"],
            "Meeting",
            "Final project review meeting completed.",
            "2026-08-22"
        ),
        (
            customer_ids["emily@nextgen.com"],
            "Email",
            "Customer requested an AI support demo.",
            "2026-08-15"
        ),
        (
            customer_ids["david@innovatech.com"],
            "Email",
            "Customer informed us that the deal was lost.",
            "2026-07-28"
        ),
    ]

    for interaction in interactions:
        cursor.execute("""
            SELECT id
            FROM interactions
            WHERE customer_id = ?
            AND interaction_type = ?
            AND content = ?
        """, (
            interaction[0],
            interaction[1],
            interaction[2]
        ))

        existing_interaction = cursor.fetchone()

        if not existing_interaction:
            cursor.execute("""
                INSERT INTO interactions
                (
                    customer_id,
                    interaction_type,
                    content,
                    created_at
                )
                VALUES (?, ?, ?, ?)
            """, interaction)

    # =========================
    # SAVE
    # =========================

    connection.commit()
    connection.close()