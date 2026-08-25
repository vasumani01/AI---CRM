from datetime import date, timedelta

from database import get_connection, initialize_database


def seed_database():
    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    # Don't insert duplicate data if database is already populated.
    existing = cursor.execute(
        "SELECT COUNT(*) AS count FROM customers"
    ).fetchone()["count"]

    if existing > 0:
        print("Database already contains data.")
        connection.close()
        return

    customers = [
        ("John Smith", "john@acme.com", "Acme Corp", "+1-555-0101"),
        ("Sarah Wilson", "sarah@technova.com", "TechNova", "+1-555-0102"),
        ("Michael Brown", "michael@globex.com", "Globex Inc", "+1-555-0103"),
        ("Priya Sharma", "priya@brighttech.com", "BrightTech", "+91-9876543210"),
        ("David Miller", "david@infralabs.com", "InfraLabs", "+1-555-0105"),
        ("Emily Davis", "emily@cloudworks.com", "CloudWorks", "+1-555-0106"),
        ("Robert Taylor", "robert@nextgen.com", "NextGen Systems", "+1-555-0107"),
        ("Lisa Anderson", "lisa@finserve.com", "FinServe", "+1-555-0108"),
        ("James Wilson", "james@softcorp.com", "SoftCorp", "+1-555-0109"),
        ("Anna Thomas", "anna@datawise.com", "DataWise", "+1-555-0110"),
    ]

    cursor.executemany(
        """
        INSERT INTO customers (name, email, company, phone)
        VALUES (?, ?, ?, ?)
        """,
        customers,
    )

    customer_ids = {
        row["name"]: row["id"]
        for row in cursor.execute(
            "SELECT id, name FROM customers"
        ).fetchall()
    }

    today = date.today()

    deals = [
        (
            customer_ids["John Smith"],
            "Website Development",
            15000,
            "Contacted",
            "David",
            str(today - timedelta(days=5)),
        ),
        (
            customer_ids["Sarah Wilson"],
            "Mobile Application",
            25000,
            "New",
            "Priya",
            str(today - timedelta(days=20)),
        ),
        (
            customer_ids["Michael Brown"],
            "CRM Integration",
            12000,
            "Contacted",
            "David",
            str(today - timedelta(days=18)),
        ),
        (
            customer_ids["Priya Sharma"],
            "AI Automation",
            30000,
            "Won",
            "Priya",
            str(today - timedelta(days=3)),
        ),
        (
            customer_ids["David Miller"],
            "Cloud Migration",
            18000,
            "Contacted",
            "David",
            str(today - timedelta(days=25)),
        ),
        (
            customer_ids["Emily Davis"],
            "Data Analytics",
            9000,
            "New",
            "Priya",
            str(today - timedelta(days=7)),
        ),
        (
            customer_ids["Robert Taylor"],
            "Cybersecurity Audit",
            22000,
            "Lost",
            "David",
            str(today - timedelta(days=30)),
        ),
        (
            customer_ids["Lisa Anderson"],
            "Payment Integration",
            14000,
            "Contacted",
            "Priya",
            str(today - timedelta(days=16)),
        ),
        (
            customer_ids["James Wilson"],
            "ERP Integration",
            11000,
            "New",
            "David",
            str(today - timedelta(days=2)),
        ),
        (
            customer_ids["Anna Thomas"],
            "AI Dashboard",
            28000,
            "Won",
            "Priya",
            str(today - timedelta(days=6)),
        ),
    ]

    cursor.executemany(
        """
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
        """,
        deals,
    )

    notes = [
        (
            customer_ids["John Smith"],
            "Interested in website redesign. Follow up next week.",
            str(today - timedelta(days=4)),
        ),
        (
            customer_ids["Sarah Wilson"],
            "Requested mobile app pricing.",
            str(today - timedelta(days=10)),
        ),
        (
            customer_ids["Michael Brown"],
            "Needs CRM integration with existing ERP.",
            str(today - timedelta(days=15)),
        ),
        (
            customer_ids["Priya Sharma"],
            "AI automation project successfully completed.",
            str(today - timedelta(days=3)),
        ),
        (
            customer_ids["David Miller"],
            "Waiting for cloud migration requirements.",
            str(today - timedelta(days=20)),
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO notes (customer_id, content, created_at)
        VALUES (?, ?, ?)
        """,
        notes,
    )

    interactions = [
        (
            customer_ids["John Smith"],
            "Call",
            "Discussed website requirements and project timeline.",
            str(today - timedelta(days=5)),
        ),
        (
            customer_ids["John Smith"],
            "Email",
            "Sent initial project proposal.",
            str(today - timedelta(days=4)),
        ),
        (
            customer_ids["John Smith"],
            "Call",
            "Customer asked about payment milestones.",
            str(today - timedelta(days=2)),
        ),
        (
            customer_ids["Sarah Wilson"],
            "Email",
            "Sent mobile application quotation.",
            str(today - timedelta(days=8)),
        ),
        (
            customer_ids["Sarah Wilson"],
            "Call",
            "Discussed application features.",
            str(today - timedelta(days=6)),
        ),
        (
            customer_ids["Michael Brown"],
            "Meeting",
            "Discussed CRM and ERP integration requirements.",
            str(today - timedelta(days=15)),
        ),
        (
            customer_ids["David Miller"],
            "Email",
            "Sent cloud migration proposal.",
            str(today - timedelta(days=20)),
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO interactions
        (
            customer_id,
            interaction_type,
            content,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        interactions,
    )

    connection.commit()
    connection.close()

    print("Database seeded successfully.")


if __name__ == "__main__":
    seed_database()