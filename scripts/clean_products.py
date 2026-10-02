"""Build dim_product: standardize categories and flag inconsistent sub-categories."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "Data" / "products_raw.csv"
OUT_PATH = ROOT / "Data" / "dimensions" / "dim_product.csv"

COLUMNS = [
    "product_id",
    "product_name",
    "category_raw",
    "category",
    "sub_category",
    "expected_category",
    "category_mismatch",
    "cost",
    "selling_price",
]

CATEGORY_ALIASES = {
    "clothing": "Clothing",
    "electronics": "Electronics",
    "furniture": "Furniture",
    "home & kitchen": "Home & Kitchen",
    "office supplies": "Office Supplies",
}

SUBCATEGORY_TO_CATEGORY = {
    "Kids": "Clothing",
    "Men": "Clothing",
    "Women": "Clothing",
    "Accessories": "Electronics",
    "Laptops": "Electronics",
    "Mobiles": "Electronics",
    "Chairs": "Furniture",
    "Storage": "Furniture",
    "Tables": "Furniture",
    "Appliances": "Home & Kitchen",
    "Cookware": "Home & Kitchen",
    "Decor": "Home & Kitchen",
    "Paper": "Office Supplies",
    "Printers": "Office Supplies",
    "Stationery": "Office Supplies",
}


def load_products(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def standardize_category(raw: str) -> str:
    key = raw.strip().lower()
    if key not in CATEGORY_ALIASES:
        raise ValueError(f"Unmapped category label: {raw!r}")
    return CATEGORY_ALIASES[key]


def expected_category(sub_category: str) -> str:
    if sub_category not in SUBCATEGORY_TO_CATEGORY:
        raise ValueError(f"Unmapped sub_category: {sub_category!r}")
    return SUBCATEGORY_TO_CATEGORY[sub_category]


def clean_products(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    cleaned: list[dict[str, str]] = []
    for row in rows:
        category_raw = row["category"]
        category = standardize_category(category_raw)
        sub_category = row["sub_category"].strip()
        expected = expected_category(sub_category)
        mismatch = category != expected
        cleaned.append(
            {
                "product_id": row["product_id"],
                "product_name": row["product_name"].strip(),
                "category_raw": category_raw,
                "category": category,
                "sub_category": sub_category,
                "expected_category": expected,
                "category_mismatch": "1" if mismatch else "0",
                "cost": row["cost"],
                "selling_price": row["selling_price"],
            }
        )
    return cleaned


def write_dimension(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    raw_rows = load_products(RAW_PATH)
    cleaned = clean_products(raw_rows)
    write_dimension(OUT_PATH, cleaned)

    raw_categories = Counter(row["category"] for row in raw_rows)
    std_categories = Counter(row["category"] for row in cleaned)
    mismatches = [row for row in cleaned if row["category_mismatch"] == "1"]

    print(f"Raw rows: {len(raw_rows)}")
    print(f"Unique product_id: {len({row['product_id'] for row in cleaned})}")
    print("Raw category labels:")
    for label, count in sorted(raw_categories.items(), key=lambda item: (-item[1], item[0])):
        print(f"  {label!r}: {count}")
    print("Standardized category labels:")
    for label, count in sorted(std_categories.items(), key=lambda item: (-item[1], item[0])):
        print(f"  {label}: {count}")
    print(f"Inconsistent category/sub-category rows: {len(mismatches)}")
    for row in mismatches:
        print(
            f"  {row['product_id']}: {row['category']!r} / {row['sub_category']} "
            f"(expected {row['expected_category']})"
        )
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
