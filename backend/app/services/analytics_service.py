"""Analytics derived from PostgreSQL — real order/session data."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_revenue(db: Session) -> dict:
    row = db.execute(
        text("""
            SELECT
                COALESCE(SUM(total_amount), 0) AS total_revenue,
                COUNT(*) AS paid_orders
            FROM orders
            WHERE status = 'paid'
        """)
    ).fetchone()

    return {
        "total_revenue": float(row.total_revenue),
        "paid_orders": int(row.paid_orders),
        "currency": "INR",
    }


def get_aov(db: Session) -> dict:
    row = db.execute(
        text("""
            SELECT
                COALESCE(AVG(total_amount), 0) AS average_order_value,
                COUNT(*) AS paid_orders
            FROM orders
            WHERE status = 'paid'
        """)
    ).fetchone()

    return {
        "average_order_value": round(float(row.average_order_value), 2),
        "paid_orders": int(row.paid_orders),
        "currency": "INR",
    }


def get_conversion(db: Session) -> dict:
    row = db.execute(
        text("""
            SELECT
                COUNT(*) AS total_sessions,
                COUNT(*) FILTER (
                    WHERE EXISTS (
                        SELECT 1 FROM audit_logs al
                        WHERE al.session_id = s.id
                          AND al.action = 'Create Order'
                          AND al.policy_result = 'APPROVED'
                    )
                ) AS orders_created,
                COUNT(*) FILTER (
                    WHERE EXISTS (
                        SELECT 1 FROM audit_logs al
                        WHERE al.session_id = s.id
                          AND al.policy_result = 'APPROVED'
                          AND al.action IN ('Payment Verification', 'Webhook: payment.captured', 'Webhook: order.paid')
                    )
                ) AS converted_sessions
            FROM agent_sessions s
        """)
    ).fetchone()

    total = int(row.total_sessions)
    converted = int(row.converted_sessions)
    orders_created = int(row.orders_created)

    return {
        "total_sessions": total,
        "orders_created": orders_created,
        "converted_sessions": converted,
        "conversion_rate": round(converted / total, 4) if total else 0.0,
        "order_creation_rate": round(orders_created / total, 4) if total else 0.0,
    }


def get_upsell_metrics(db: Session) -> dict:
    row = db.execute(
        text("""
            WITH order_categories AS (
                SELECT
                    o.id AS order_id,
                    o.status,
                    COUNT(DISTINCT oi.product_id) AS item_count,
                    COUNT(DISTINCT p.category) AS category_count,
                    BOOL_OR(p.category IN ('Accessory', 'Mouse', 'Storage', 'Keyboard')) AS has_addon
                FROM orders o
                JOIN order_items oi ON oi.order_id = o.id
                JOIN products p ON p.id = oi.product_id
                GROUP BY o.id, o.status
            )
            SELECT
                COUNT(*) AS total_orders,
                COUNT(*) FILTER (WHERE item_count > 1) AS multi_item_orders,
                COUNT(*) FILTER (WHERE has_addon) AS upsell_orders,
                COUNT(*) FILTER (WHERE category_count > 1) AS cross_sell_orders
            FROM order_categories
            WHERE status IN ('paid', 'created', 'payment_initiated')
        """)
    ).fetchone()

    total = int(row.total_orders)
    upsell = int(row.upsell_orders)
    cross_sell = int(row.cross_sell_orders)

    return {
        "total_orders": total,
        "multi_item_orders": int(row.multi_item_orders),
        "upsell_orders": upsell,
        "cross_sell_orders": cross_sell,
        "upsell_rate": round(upsell / total, 4) if total else 0.0,
        "cross_sell_rate": round(cross_sell / total, 4) if total else 0.0,
    }


def get_revenue_per_session(db: Session) -> dict:
    revenue = get_revenue(db)
    conversion = get_conversion(db)
    total_sessions = conversion["total_sessions"]
    rps = revenue["total_revenue"] / total_sessions if total_sessions else 0.0

    return {
        "revenue_per_session": round(rps, 2),
        "total_revenue": revenue["total_revenue"],
        "total_sessions": total_sessions,
        "currency": "INR",
    }


def get_summary(db: Session) -> dict:
    return {
        "revenue": get_revenue(db),
        "aov": get_aov(db),
        "conversion": get_conversion(db),
        "upsell": get_upsell_metrics(db),
        "revenue_per_session": get_revenue_per_session(db),
    }
