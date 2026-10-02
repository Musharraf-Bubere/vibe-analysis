"""Build dim_customer: one row per customer_id from customers_raw.csv."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "Data" / "customers_raw.csv"
OUT_PATH = ROOT / "Data" / "dimensions" / "dim_customer.csv"

COLUMNS = [
    "customer_id",
    "customer_name",
    "gender",
    "age",
    "customer_segment",
    "signup_date",
]


def load_customers(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def find_duplicate_ids(rows: list[dict[str, str]]) -> list[str]:
    counts = Counter(row["customer_id"] for row in rows)
    return sorted(customer_id for customer_id, n in counts.items() if n > 1)


def deduplicate(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    """Keep the first occurrence of each customer_id. Duplicates in the source are identical."""
    seen: set[str] = set()
    clean: list[dict[str, str]] = []
    dropped = 0
    for row in rows:
        customer_id = row["customer_id"]
        if customer_id in seen:
            dropped += 1
            continue
        seen.add(customer_id)
        clean.append({column: row[column] for column in COLUMNS})
    return clean, dropped


def write_dimension(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    raw_rows = load_customers(RAW_PATH)
    duplicate_ids = find_duplicate_ids(raw_rows)
    clean_rows, dropped = deduplicate(raw_rows)
    write_dimension(OUT_PATH, clean_rows)

    unique_ids = {row["customer_id"] for row in clean_rows}
    print(f"Raw rows: {len(raw_rows)}")
    print(f"Duplicate customer IDs ({len(duplicate_ids)}): {', '.join(duplicate_ids)}")
    print(f"Exact duplicate rows dropped: {dropped}")
    print(f"dim_customer rows: {len(clean_rows)}")
    print(f"Unique customer_id: {len(unique_ids)}")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
