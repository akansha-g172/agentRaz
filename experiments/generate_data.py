#!/usr/bin/env python3
"""
Generate a synthetic A/B experiment dataset.

IMPORTANT: Results from this script are SYNTHETIC — not real-world outcomes.
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


def generate_sessions(count: int, seed: int = 42) -> list[dict]:
    random.seed(seed)
    sessions = []

    for i in range(count):
        variant = "control" if i < count // 2 else "ai"
        converted = random.random() < (0.08 if variant == "control" else 0.14)
        base_aov = random.uniform(35000, 55000)
        upsell_boost = random.uniform(1.0, 1.25) if variant == "ai" and converted else 1.0
        cross_sell = variant == "ai" and converted and random.random() < 0.35

        revenue = 0.0
        items = 0
        if converted:
            items = random.randint(1, 3 if cross_sell else 1)
            revenue = round(base_aov * upsell_boost * (1 + 0.05 * (items - 1)), 2)

        sessions.append({
            "session_id": f"S{i+1:04d}",
            "variant": variant,
            "converted": int(converted),
            "revenue": revenue,
            "items": items,
            "upsell": int(items > 1),
            "cross_sell": int(cross_sell and items > 1),
        })

    return sessions


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic experiment data")
    parser.add_argument("--sessions", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "data" / "experiment_sessions.csv",
    )
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    rows = generate_sessions(args.sessions, args.seed)

    with args.output.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["session_id", "variant", "converted", "revenue", "items", "upsell", "cross_sell"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Synthetic experiment: wrote {len(rows)} sessions to {args.output}")
    print("Label: SYNTHETIC — not real-world results")


if __name__ == "__main__":
    main()
