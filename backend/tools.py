from datetime import date, timedelta
from typing import Optional

from database import get_connection


VALID_STATUSES = {"New", "Contacted", "Won", "Lost"}

SALESPERSONS = {
    "David",
    "Priya",
    "Alex",
    "Michael",
    "Sarah",
}


def search_customers(name: Optional[str] = None):
    connection = get_connection()

    if name:
        rows = connection.execute(
            """
            SELECT *
            FROM customers
            WHERE LOWER(name) LIKE LOWER(?)
               OR LOWER(company) LIKE LOWER(?)
            ORDER BY name
            """,
            (f"%{name}%", f"%{name}%"),
        ).fetchall()
    else:
        rows = connection.execute(
            """
            SELECT *
            FROM customers
            ORDER BY name
            """
        ).fetchall()

    connection.close()

    return {
        "success": True,
        "count": len(rows),
        "customers": [dict(row) for row in rows],
    }


def search_deals(
    customer_name: Optional[str] = None,
    status: Optional[str] = None,
    min_amount: Optional[float] = None,
    older_than_days: Optional[int] = None,
):
    connection = get_connection()

    query = """
        SELECT
            d.id,
            d.title,
            d.amount,
            d.status,
            d.salesperson,
            d.last_updated,
            c.id AS customer_id,
            c.name AS customer_name,
            c.company
        FROM deals d
        JOIN customers c ON d.customer_id = c.id
        WHERE 1 = 1
    """

    params = []

    if customer_name:
        query += """
            AND (
                LOWER(c.name) LIKE LOWER(?)
                OR LOWER(c.company) LIKE LOWER(?)
            )
        """
        params.extend([
            f"%{customer_name}%",
            f"%{customer_name}%"
        ])

    if status:
        if status not in VALID_STATUSES:
            connection.close()
            return {
                "success": False,
                "error": f"Invalid status. Use one of: {', '.join(sorted(VALID_STATUSES))}"
            }

        query += " AND d.status = ?"
        params.append(status)

    if min_amount is not None:
        query += " AND d.amount > ?"
        params.append(min_amount)

    if older_than_days is not None:
        cutoff = date.today() - timedelta(days=older_than_days)

        query += " AND date(d.last_updated) < date(?)"
        params.append(str(cutoff))

    query += " ORDER BY d.amount DESC"

    rows = connection.execute(query, params).fetchall()

    connection.close()

    return {
        "success": True,
        "count": len(rows),
        "deals": [dict(row) for row in rows],
    }


def get_customer_history(customer_name: str):
    connection = get_connection()

    customers = connection.execute(
        """
        SELECT *
        FROM customers
        WHERE LOWER(name) LIKE LOWER(?)
           OR LOWER(company) LIKE LOWER(?)
        ORDER BY name
        """,
        (f"%{customer_name}%", f"%{customer_name}%"),
    ).fetchall()

    if len(customers) == 0:
        connection.close()

        return {
            "success": False,
            "error": f"No customer found matching '{customer_name}'."
        }

    if len(customers) > 1:
        connection.close()

        return {
            "success": False,
            "ambiguous": True,
            "error": "Multiple customers matched. Please provide a more specific customer name.",
            "matches": [dict(row) for row in customers],
        }

    customer = customers[0]

    interactions = connection.execute(
        """
        SELECT *
        FROM interactions
        WHERE customer_id = ?
        ORDER BY date(created_at) ASC
        """,
        (customer["id"],),
    ).fetchall()

    notes = connection.execute(
        """
        SELECT *
        FROM notes
        WHERE customer_id = ?
        ORDER BY date(created_at) ASC
        """,
        (customer["id"],),
    ).fetchall()

    deals = connection.execute(
        """
        SELECT *
        FROM deals
        WHERE customer_id = ?
        ORDER BY id
        """,
        (customer["id"],),
    ).fetchall()

    connection.close()

    return {
        "success": True,
        "customer": dict(customer),
        "deals": [dict(row) for row in deals],
        "interactions": [dict(row) for row in interactions],
        "notes": [dict(row) for row in notes],
    }


def update_deal_status(deal_id: int, new_status: str):
    if new_status not in VALID_STATUSES:
        return {
            "success": False,
            "error": f"Invalid status '{new_status}'."
        }

    connection = get_connection()

    deal = connection.execute(
        """
        SELECT
            d.*,
            c.name AS customer_name,
            c.company
        FROM deals d
        JOIN customers c ON d.customer_id = c.id
        WHERE d.id = ?
        """,
        (deal_id,),
    ).fetchone()

    if not deal:
        connection.close()

        return {
            "success": False,
            "error": f"Deal with ID {deal_id} does not exist. No changes were made."
        }

    old_status = deal["status"]

    connection.execute(
        """
        UPDATE deals
        SET status = ?, last_updated = ?
        WHERE id = ?
        """,
        (new_status, str(date.today()), deal_id),
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "message": "Deal status updated successfully.",
        "deal": {
            "id": deal_id,
            "customer_name": deal["customer_name"],
            "company": deal["company"],
            "title": deal["title"],
            "amount": deal["amount"],
            "old_status": old_status,
            "new_status": new_status,
        },
    }


def add_customer_note(customer_name: str, note: str):
    connection = get_connection()

    customers = connection.execute(
        """
        SELECT *
        FROM customers
        WHERE LOWER(name) LIKE LOWER(?)
           OR LOWER(company) LIKE LOWER(?)
        ORDER BY name
        """,
        (f"%{customer_name}%", f"%{customer_name}%"),
    ).fetchall()

    if not customers:
        connection.close()

        return {
            "success": False,
            "error": f"Customer '{customer_name}' was not found. Note was NOT added."
        }

    if len(customers) > 1:
        connection.close()

        return {
            "success": False,
            "ambiguous": True,
            "error": "Multiple customers matched. Note was NOT added.",
            "matches": [dict(row) for row in customers],
        }

    customer = customers[0]

    connection.execute(
        """
        INSERT INTO notes (customer_id, content, created_at)
        VALUES (?, ?, ?)
        """,
        (
            customer["id"],
            note,
            str(date.today()),
        ),
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "message": "Note added successfully.",
        "customer": customer["name"],
        "note": note,
    }


def assign_deal(deal_id: int, salesperson: str):
    salesperson = salesperson.strip()

    if salesperson not in SALESPERSONS:
        return {
            "success": False,
            "error": (
                f"Salesperson '{salesperson}' is not available. "
                f"Available salespeople: {', '.join(sorted(SALESPERSONS))}"
            ),
        }

    connection = get_connection()

    deal = connection.execute(
        """
        SELECT
            d.*,
            c.name AS customer_name,
            c.company
        FROM deals d
        JOIN customers c ON d.customer_id = c.id
        WHERE d.id = ?
        """,
        (deal_id,),
    ).fetchone()

    if not deal:
        connection.close()

        return {
            "success": False,
            "error": f"Deal {deal_id} does not exist. No assignment was made."
        }

    connection.execute(
        """
        UPDATE deals
        SET salesperson = ?, last_updated = ?
        WHERE id = ?
        """,
        (
            salesperson,
            str(date.today()),
            deal_id,
        ),
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "message": "Deal assigned successfully.",
        "deal_id": deal_id,
        "customer_name": deal["customer_name"],
        "deal_title": deal["title"],
        "salesperson": salesperson,
    }


def get_at_risk_deals():
    return search_deals(
        min_amount=10000,
        older_than_days=14,
    )


def get_all_deals():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            d.id,
            d.title,
            d.amount,
            d.status,
            d.salesperson,
            d.last_updated,
            c.id AS customer_id,
            c.name AS customer_name,
            c.company
        FROM deals d
        JOIN customers c ON d.customer_id = c.id
        ORDER BY d.id DESC
        """
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]


def get_all_customers():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT *
        FROM customers
        ORDER BY name
        """
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]