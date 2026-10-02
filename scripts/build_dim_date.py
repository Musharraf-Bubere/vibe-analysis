"""Build dim_date from unique valid order dates in fact_orders."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACT_PATH = ROOT / "Data" / "facts" / "fact_orders.csv"
OUT_PATH = ROOT / "Data" / "dimensions" / "dim_date.csv"

COLUMNS = [
    "date_key",
    "date",
    "day",
    "month",
    "month_name",
    "quarter",
    "year",
]


def unique_valid_dates(path: Path) -> list[datetime]:
    dates: set[datetime] = set()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            value = row["order_date"].strip()
            if not value:
                continue
            dates.add(datetime.strptime(value, "%Y-%m-%d"))
    return sorted(dates)


def build_dim_date(dates: list[datetime]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for dt in dates:
        rows.append(
            {
                "date_key": dt.strftime("%Y%m%d"),
                "date": dt.date().isoformat(),
                "day": str(dt.day),
                "month": str(dt.month),
                "month_name": dt.strftime("%B"),
                "quarter": str((dt.month - 1) // 3 + 1),
                "year": str(dt.year),
            }
        )
    return rows


def write_dimension(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    dates = unique_valid_dates(FACT_PATH)
    rows = build_dim_date(dates)
    write_dimension(OUT_PATH, rows)

    years = {row["year"] for row in rows}
    print(f"Unique valid order dates: {len(rows)}")
    print(f"Date range: {rows[0]['date']} to {rows[-1]['date']}")
    print(f"Years: {', '.join(sorted(years))}")
    print(f"Unique date_key: {len({row['date_key'] for row in rows})}")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
