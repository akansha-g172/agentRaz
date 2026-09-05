"""Growth analytics from PostgreSQL — no fabricated metrics."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def _paid_orders_base() -> str:
    return """
        SELECT
            o.id,
            o.total_amount,
            o.status,
            o.created_at,
            s.id AS session_id
        FROM orders o
        LEFT JOIN agent_sessions s ON s.started_at <= o.created_at
            AND (s.ended_at IS NULL OR s.ended_at >= o.created_at)
        WHERE o.status = 'paid'
    """


def get_revenue(db: Session) -> dict:
    row = db.execute(
        text("""
            SELECT
                COALESCE(SUM(total_amount), 0) AS total_revenue,
                COUNT(*) AS paid_orders,
                COALESCE(AVG(total_amount), 0) AS avg_order_value
            FROM orders
            WHERE status = 'paid'
        """)
    ).fetchone()

    return {
        "total_revenue": float(row.total_revenue),
        "paid_orders": int(row.paid_orders),
        "average_order_value": round(float(row.avg_order_value), 2),
        "currency": "INR",
    }


def get_conversion(db: Session) -> dict:
    sessions = db.execute(
        text("SELECT COUNT(*) AS cnt FROM agent_sessions")
    ).fetchone()
    paid = db.execute(
        text("SELECT COUNT(*) AS cnt FROM orders WHERE status = 'paid'")
    ).fetchone()
    total_orders = db.execute(
        text("SELECT COUNT(*) AS cnt FROM orders")
    ).fetchone()

    session_count = int(sessions.cnt)
    paid_count = int(paid.cnt)
    order_count = int(total_orders.cnt)

    conversion_rate = (paid_count / session_count * 100) if session_count else 0.0
    order_conversion = (paid_count / order_count * 100) if order_count else 0.0

    return {
        "sessions": session_count,
        "orders_created": order_count,
        "orders_paid": paid_count,
        "conversion_rate": round(conversion_rate, 2),
        "order_to_paid_rate": round(order_conversion, 2),
    }


def get_aov(db: Session) -> dict:
    row = db.execute(
        text("""
            SELECT
                COALESCE(AVG(total_amount), 0) AS aov,
                COALESCE(MIN(total_amount), 0) AS min_order,
                COALESCE(MAX(total_amount), 0) AS max_order,
                COUNT(*) AS paid_orders
            FROM orders
            WHERE status = 'paid'
        """)
    ).fetchone()

    return {
        "average_order_value": round(float(row.aov), 2),
        "min_order_value": float(row.min_order),
        "max_order_value": float(row.max_order),
        "paid_orders": int(row.paid_orders),
        "currency": "INR",
    }


def get_upsell_metrics(db: Session) -> dict:
    """Orders with multiple distinct product categories count as upsell/cross-sell."""
    row = db.execute(
        text("""
            WITH order_categories AS (
                SELECT
                    oi.order_id,
                    COUNT(DISTINCT p.category) AS category_count,
                    COUNT(oi.id) AS item_count
                FROM order_items oi
                JOIN products p ON p.id = oi.product_id
                JOIN orders o ON o.id = oi.order_id
                WHERE o.status = 'paid'
                GROUP BY oi.order_id
            )
            SELECT
                COUNT(*) AS paid_orders,
                COUNT(*) FILTER (WHERE item_count > 1) AS multi_item_orders,
                COUNT(*) FILTER (WHERE category_count > 1) AS cross_category_orders,
                COALESCE(AVG(item_count), 0) AS avg_items_per_order
            FROM order_categories
        """)
    ).fetchone()

    paid = int(row.paid_orders or 0)
    multi = int(row.multi_item_orders or 0)
    cross = int(row.cross_category_orders or 0)

    return {
        "paid_orders": paid,
        "multi_item_orders": multi,
        "cross_category_orders": cross,
        "upsell_rate": round((multi / paid * 100) if paid else 0.0, 2),
        "cross_sell_rate": round((cross / paid * 100) if paid else 0.0, 2),
        "avg_items_per_order": round(float(row.avg_items_per_order or 0), 2),
    }


def get_uplift(db: Session) -> dict:
    """Compare revenue/session for sessions with vs without paid orders."""
    row = db.execute(
        text("""
            WITH session_revenue AS (
                SELECT
                    s.id AS session_id,
                    COALESCE(SUM(o.total_amount) FILTER (WHERE o.status = 'paid'), 0) AS revenue,
                    COUNT(o.id) FILTER (WHERE o.status = 'paid') AS paid_orders
                FROM agent_sessions s
                LEFT JOIN orders o ON o.created_at >= s.started_at
                    AND (s.ended_at IS NULL OR o.created_at <= s.ended_at)
                GROUP BY s.id
            )
            SELECT
                COUNT(*) AS total_sessions,
                COUNT(*) FILTER (WHERE paid_orders > 0) AS converting_sessions,
                COALESCE(AVG(revenue), 0) AS revenue_per_session,
                COALESCE(SUM(revenue), 0) AS total_revenue
            FROM session_revenue
        """)
    ).fetchone()

    sessions = int(row.total_sessions or 0)
    converting = int(row.converting_sessions or 0)
    rps = float(row.revenue_per_session or 0)

    return {
        "total_sessions": sessions,
        "converting_sessions": converting,
        "revenue_per_session": round(rps, 2),
        "total_revenue": float(row.total_revenue or 0),
        "conversion_rate": round((converting / sessions * 100) if sessions else 0.0, 2),
        "currency": "INR",
        "note": "Computed from live order and session data",
    }


def get_summary(db: Session) -> dict:
    return {
        "revenue": get_revenue(db),
        "conversion": get_conversion(db),
        "aov": get_aov(db),
        "upsell": get_upsell_metrics(db),
        "uplift": get_uplift(db),
    }
