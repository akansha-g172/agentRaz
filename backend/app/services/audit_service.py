"""Structured audit and agent action logging."""

from __future__ import annotations

import json
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session


def create_session(
    db: Session,
    *,
    buyer_id: str | None = None,
    merchant_id: str | None = None,
) -> str:
    session_id = str(uuid4())
    db.execute(
        text("""
            INSERT INTO agent_sessions (id, buyer_id, merchant_id)
            VALUES (:id, :buyer_id, :merchant_id)
        """),
        {
            "id": session_id,
            "buyer_id": buyer_id,
            "merchant_id": merchant_id,
        },
    )
    db.commit()
    return session_id


def log_agent_action(
    db: Session,
    *,
    session_id: str,
    agent_type: str,
    action: str,
    arguments: dict | None = None,
    result: dict | None = None,
) -> None:
    db.execute(
        text("""
            INSERT INTO agent_actions (
                session_id, agent_type, action, arguments, result
            )
            VALUES (
                :session_id, :agent_type, :action,
                CAST(:arguments AS jsonb), CAST(:result AS jsonb)
            )
        """),
        {
            "session_id": session_id,
            "agent_type": agent_type,
            "action": action,
            "arguments": json.dumps(arguments or {}),
            "result": json.dumps(result or {}),
        },
    )
    db.commit()


def log_audit(
    db: Session,
    *,
    session_id: str | None,
    action: str,
    reason: str | None = None,
    amount: float | None = None,
    authorization_status: str | None = None,
    policy_result: str | None = None,
) -> None:
    db.execute(
        text("""
            INSERT INTO audit_logs (
                session_id, action, reason, amount,
                authorization_status, policy_result
            )
            VALUES (
                :session_id, :action, :reason, :amount,
                :authorization_status, :policy_result
            )
        """),
        {
            "session_id": session_id,
            "action": action,
            "reason": reason,
            "amount": amount,
            "authorization_status": authorization_status,
            "policy_result": policy_result,
        },
    )
    db.commit()


def get_session_audit(db: Session, session_id: str) -> dict:
    session = db.execute(
        text("""
            SELECT id, buyer_id, merchant_id, started_at, ended_at
            FROM agent_sessions
            WHERE id::text = :session_id
        """),
        {"session_id": session_id},
    ).fetchone()

    if not session:
        return {"found": False}

    actions = db.execute(
        text("""
            SELECT id, agent_type, action, arguments, result, created_at
            FROM agent_actions
            WHERE session_id::text = :session_id
            ORDER BY created_at
        """),
        {"session_id": session_id},
    ).fetchall()

    audits = db.execute(
        text("""
            SELECT id, action, reason, amount, authorization_status,
                   policy_result, created_at
            FROM audit_logs
            WHERE session_id::text = :session_id
            ORDER BY created_at
        """),
        {"session_id": session_id},
    ).fetchall()

    return {
        "found": True,
        "session": dict(session._mapping),
        "agent_actions": [dict(row._mapping) for row in actions],
        "audit_logs": [dict(row._mapping) for row in audits],
    }
