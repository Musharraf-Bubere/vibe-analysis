"""Build fact_orders: drop exact duplicates, flag dirty keys/dates, mark returns."""

from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "Data" / "orders_raw.csv"
OUT_PATH = ROOT / "Data" / "facts" / "fact_orders.csv"

DATE_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d")

COLUMNS = [
    "order_id",
    "order_date_raw",
    "order_date",
    "customer_id",
    "product_id",
    "region_id",
    "quantity",
    "discount",
    "sales_amount",
    "cost_amount",
    "profit",
    "is_return",
    "missing_customer_id",
    "missing_product_id",
    "invalid_date",
]


def load_orders(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def drop_exact_duplicates(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    seen: set[tuple[tuple[str, str], ...]] = set()
    kept: list[dict[str, str]] = []
    dropped = 0
    for row in rows:
        key = tuple(row.items())
        if key in seen:
            dropped += 1
            continue
        seen.add(key)
        kept.append(row)
    return kept, dropped


def parse_order_date(raw: str) -> str | None:
    value = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def flag(value: bool) -> str:
    return "1" if value else "0"


def clean_orders(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    cleaned: list[dict[str, str]] = []
    for row in rows:
        customer_id = row["customer_id"].strip()
        product_id = row["product_id"].strip()
        order_date_raw = row["order_date"]
        order_date = parse_order_date(order_date_raw)
        quantity = int(row["quantity"])
        cleaned.append(
            {
                "order_id": row["order_id"],
                "order_date_raw": order_date_raw,
                "order_date": order_date or "",
                "customer_id": customer_id,
                "product_id": product_id,
                "region_id": row["region_id"].strip(),
                "quantity": row["quantity"],
                "discount": row["discount"],
                "sales_amount": row["sales_amount"],
                "cost_amount": row["cost_amount"],
                "profit": row["profit"],
                "is_return": flag(quantity < 0),
                "missing_customer_id": flag(customer_id == ""),
                "missing_product_id": flag(product_id == ""),
                "invalid_date": flag(order_date is None),
            }
        )
    return cleaned


def write_fact(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    raw_rows = load_orders(RAW_PATH)
    deduped, dropped = drop_exact_duplicates(raw_rows)
    cleaned = clean_orders(deduped)
    write_fact(OUT_PATH, cleaned)

    n_return = sum(row["is_return"] == "1" for row in cleaned)
    n_miss_c = sum(row["missing_customer_id"] == "1" for row in cleaned)
    n_miss_p = sum(row["missing_product_id"] == "1" for row in cleaned)
    n_bad_date = sum(row["invalid_date"] == "1" for row in cleaned)
    unique_ids = {row["order_id"] for row in cleaned}

    print(f"Raw rows: {len(raw_rows)}")
    print(f"Exact duplicate rows dropped: {dropped}")
    print(f"fact_orders rows: {len(cleaned)}")
    print(f"Unique order_id: {len(unique_ids)}")
    print(f"Missing customer_id: {n_miss_c}")
    print(f"Missing product_id: {n_miss_p}")
    print(f"Invalid dates (blanked order_date): {n_bad_date}")
    if n_bad_date:
        bad_values = Counter(
            row["order_date_raw"] for row in cleaned if row["invalid_date"] == "1"
        )
        print(f"  raw invalid date values: {dict(bad_values)}")
    print(f"is_return = 1 (negative quantity): {n_return}")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
