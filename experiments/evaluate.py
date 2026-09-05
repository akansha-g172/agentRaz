#!/usr/bin/env python3
"""
Evaluate synthetic A/B experiment results.

IMPORTANT: Input data must be labeled as SYNTHETIC experiment data.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def load_sessions(path: Path) -> list[dict]:
    with path.open() as f:
        return list(csv.DictReader(f))


def evaluate(rows: list[dict]) -> dict:
    by_variant: dict[str, list[dict]] = {"control": [], "ai": []}
    for row in rows:
        by_variant[row["variant"]].append(row)

    metrics = {}
    for variant, sessions in by_variant.items():
        n = len(sessions)
        conversions = sum(int(s["converted"]) for s in sessions)
        revenue = sum(float(s["revenue"]) for s in sessions)
        upsells = sum(int(s["upsell"]) for s in sessions)
        cross_sells = sum(int(s["cross_sell"]) for s in sessions)
        paid = [s for s in sessions if int(s["converted"])]

        metrics[variant] = {
            "sessions": n,
            "conversion_rate": round(conversions / n * 100, 2) if n else 0,
            "average_order_value": round(revenue / conversions, 2) if conversions else 0,
            "revenue_per_session": round(revenue / n, 2) if n else 0,
            "upsell_rate": round(upsells / n * 100, 2) if n else 0,
            "cross_sell_rate": round(cross_sells / n * 100, 2) if n else 0,
            "total_revenue": round(revenue, 2),
            "avg_items": round(
                sum(int(s["items"]) for s in paid) / len(paid), 2
            ) if paid else 0,
        }

    control = metrics.get("control", {})
    ai = metrics.get("ai", {})

    uplift = {}
    if control.get("revenue_per_session"):
        uplift["revenue_uplift_pct"] = round(
            (ai.get("revenue_per_session", 0) - control["revenue_per_session"])
            / control["revenue_per_session"] * 100,
            2,
        )
    if control.get("conversion_rate"):
        uplift["conversion_uplift_pct"] = round(
            ai.get("conversion_rate", 0) - control["conversion_rate"], 2
        )

    return {
        "label": "Synthetic experiment",
        "control": control,
        "ai": ai,
        "uplift": uplift,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate synthetic experiment CSV")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).parent / "data" / "experiment_sessions.csv",
    )
    args = parser.parse_args()

    rows = load_sessions(args.input)
    result = evaluate(rows)

    print("=== Synthetic Experiment Results ===")
    print(f"Label: {result['label']}")
    print()
    for variant in ("control", "ai"):
        m = result[variant]
        print(f"[{variant.upper()}] sessions={m['sessions']} conversion={m['conversion_rate']}% "
              f"AOV=₹{m['average_order_value']} RPS=₹{m['revenue_per_session']} "
              f"upsell={m['upsell_rate']}% cross-sell={m['cross_sell_rate']}%")
    print()
    print("Uplift (AI vs Control):", result["uplift"])


if __name__ == "__main__":
    main()
