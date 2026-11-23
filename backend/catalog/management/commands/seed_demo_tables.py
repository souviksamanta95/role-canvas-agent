"""Create synthetic demo tables in the `datasets` schema (Postgres only). Idempotent."""

from __future__ import annotations

import random
from datetime import date
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from catalog.models import AGENT_SCHEMA

REGIONS = ["EMEA", "NA", "APAC", "LATAM"]
MONTHS = [date(2025, m, 1) for m in range(1, 13)]
TABLES: dict[str, str] = {
    "finance_revenue_summary": "month date, region text, revenue numeric, expenses numeric",
    "finance_ledger": (
        "entry_id int, entry_date date, account text, cost_center text, "
        "amount numeric, currency text"
    ),
    "hr_headcount": "month date, department text, headcount int, attrition int",
    "hr_payroll": "employee_id int, department text, salary numeric, bonus numeric",
    "marketing_campaigns": (
        "campaign_id int, channel text, month date, spend numeric, "
        "impressions int, clicks int, conversions int"
    ),
    "sales_orders": (
        "order_id int, order_date date, region text, product text, "
        "quantity int, revenue numeric, customer_id int"
    ),
    "ops_inventory": (
        "sku text, warehouse text, month date, units_on_hand int, units_shipped int, supplier text"
    ),
    "public_country_indicators": "country text, year int, gdp_per_capita numeric, population int",
}


def rows(rng: random.Random) -> dict[str, list[tuple[Any, ...]]]:
    depts = ["Finance", "Marketing", "Operations", "Sales", "HR", "Product"]
    out: dict[str, list[tuple[Any, ...]]] = {
        "finance_revenue_summary": [
            (m, r, round(rng.uniform(80, 200) * 1000, 2), round(rng.uniform(50, 150) * 1000, 2))
            for m in MONTHS
            for r in REGIONS
        ],
        "finance_ledger": [
            (
                i,
                MONTHS[i % 12],
                rng.choice(["Revenue", "COGS", "Opex", "Payroll"]),
                rng.choice(["CC-100", "CC-200", "CC-300"]),
                round(rng.uniform(-5000, 20000), 2),
                "USD",
            )
            for i in range(1, 121)
        ],
        "hr_headcount": [
            (m, d, rng.randint(8, 60), rng.randint(0, 4)) for m in MONTHS for d in depts
        ],
        "hr_payroll": [
            (
                i,
                rng.choice(depts),
                round(rng.uniform(45, 180) * 1000, 2),
                round(rng.uniform(0, 20) * 1000, 2),
            )
            for i in range(1, 81)
        ],
        "marketing_campaigns": [
            (
                i,
                rng.choice(["search", "social", "email", "display"]),
                MONTHS[i % 12],
                round(rng.uniform(500, 9000), 2),
                rng.randint(5000, 90000),
                rng.randint(100, 4000),
                rng.randint(5, 400),
            )
            for i in range(1, 97)
        ],
        "sales_orders": [
            (
                i,
                MONTHS[i % 12],
                rng.choice(REGIONS),
                rng.choice(["Basic", "Plus", "Pro"]),
                rng.randint(1, 20),
                round(rng.uniform(100, 5000), 2),
                rng.randint(1000, 1300),
            )
            for i in range(1, 241)
        ],
        "ops_inventory": [
            (
                f"SKU-{s:03d}",
                rng.choice(["WH-A", "WH-B", "WH-C"]),
                m,
                rng.randint(0, 900),
                rng.randint(0, 300),
                rng.choice(["Acme", "Globex", "Initech"]),
            )
            for s in range(1, 21)
            for m in MONTHS[:6]
        ],
        "public_country_indicators": [
            (c, y, round(rng.uniform(2000, 60000), 2), rng.randint(1_000_000, 90_000_000))
            for c in ["Aland", "Borduria", "Carpania", "Draconia"]
            for y in range(2018, 2024)
        ],
    }
    return out


class Command(BaseCommand):
    help = "Create synthetic demo tables in the datasets schema. Replaces their contents."

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        if connection.vendor != "postgresql":
            raise CommandError("seed_demo_tables needs PostgreSQL.")
        data = rows(random.Random(42))  # noqa: S311 - synthetic data, not security relevant
        with connection.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {AGENT_SCHEMA}")
            for table, ddl in TABLES.items():
                cur.execute(f"CREATE TABLE IF NOT EXISTS {AGENT_SCHEMA}.{table} ({ddl})")  # noqa: S608
                cur.execute(f"TRUNCATE {AGENT_SCHEMA}.{table}")  # noqa: S608
                width = len(data[table][0])
                placeholders = ", ".join(["%s"] * width)
                cur.executemany(
                    f"INSERT INTO {AGENT_SCHEMA}.{table} VALUES ({placeholders})",  # noqa: S608
                    data[table],
                )
        self.stdout.write(
            self.style.SUCCESS(f"Loaded {len(TABLES)} synthetic tables into {AGENT_SCHEMA}.")
        )
