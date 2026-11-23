"""Demo catalog: departments, roles, datasets and grants.

Datasets here are SYNTHETIC placeholders so access rules can be exercised end to end.
Replace them with real public datasets (listed in data/README.md) as they are chosen.
"""

from __future__ import annotations

from typing import Any

from accounts.constants import Sensitivity as S

PUB, INT, CONF, RES = S.PUBLIC, S.INTERNAL, S.CONFIDENTIAL, S.RESTRICTED

DEPARTMENTS = {
    "finance": "Finance",
    "marketing": "Marketing",
    "operations": "Operations",
    "executive": "Executive",
    "sales": "Sales",
    "hr": "HR",
    "product": "Product",
    "customer-support": "Customer Support",
    "legal-compliance": "Legal & Compliance",
    "engineering-data": "Engineering & Data",
    "general": "General",
}

# department -> [(slug, name, sensitivity ceiling, self selectable, description)]
ROLES: dict[str, list[tuple[str, str, Any, bool, str]]] = {
    "finance": [
        ("finance-analyst", "Finance Analyst", INT, True, "Revenue, cost and budget aggregates."),
        (
            "fpa-analyst",
            "FP&A Analyst",
            CONF,
            True,
            "Planning and forecasting; ledger in aggregate.",
        ),
        ("controller", "Controller", CONF, True, "Full ledger and financial summaries."),
        ("ap-ar-clerk", "AP/AR Clerk", INT, True, "Payables and receivables ledger entries."),
        ("auditor", "Auditor", RES, False, "Read-only across finance. Admin-assigned, time-boxed."),
    ],
    "marketing": [
        (
            "marketing-analyst",
            "Marketing Analyst",
            INT,
            True,
            "Campaign performance and aggregate sales.",
        ),
        ("performance-marketer", "Performance Marketer", INT, True, "Ad spend and conversions."),
        ("marketing-manager", "Marketing Manager", INT, True, "Campaigns and aggregate sales."),
    ],
    "operations": [
        ("ops-analyst", "Operations Analyst", INT, True, "Inventory and fulfilment."),
        (
            "logistics-coordinator",
            "Logistics Coordinator",
            INT,
            True,
            "Shipping volumes, no supplier terms.",
        ),
        ("ops-manager", "Operations Manager", CONF, True, "Inventory and suppliers."),
        ("procurement", "Procurement", CONF, True, "Supplier performance."),
    ],
    "executive": [
        (
            "executive",
            "Executive (CEO/CFO/COO)",
            CONF,
            True,
            "Cross-department aggregates. Restricted data stays hidden.",
        ),
        ("board-viewer", "Board Viewer", INT, True, "Curated headline KPIs only."),
    ],
    "sales": [
        ("sales-rep", "Sales Representative", INT, True, "Own region only."),
        ("sales-manager", "Sales Manager", INT, True, "All regions, no customer identifiers."),
        ("revops-analyst", "RevOps Analyst", INT, True, "Pipeline and order analytics."),
    ],
    "hr": [
        (
            "hr-business-partner",
            "HR Business Partner",
            INT,
            True,
            "Headcount and attrition, aggregate only.",
        ),
        ("hr-manager", "HR Manager", CONF, True, "Headcount and attrition."),
        ("recruiter", "Recruiter", INT, True, "Hiring pipeline (no datasets yet)."),
        ("payroll-specialist", "Payroll Specialist", RES, False, "Salaries. Admin-assigned."),
    ],
    "product": [
        ("product-manager", "Product Manager", INT, True, "Usage and funnels (no datasets yet)."),
        ("product-analyst", "Product Analyst", INT, True, "Usage and funnels (no datasets yet)."),
        ("ux-researcher", "UX Researcher", INT, True, "Research data (no datasets yet)."),
    ],
    "customer-support": [
        ("support-agent", "Support Agent", INT, True, "Tickets (no datasets yet)."),
        (
            "support-manager",
            "Support Manager",
            INT,
            True,
            "Tickets and satisfaction (no datasets yet).",
        ),
    ],
    "legal-compliance": [
        ("compliance-officer", "Compliance Officer", RES, False, "Audit logs. Admin-assigned."),
        ("legal-counsel", "Legal Counsel", CONF, True, "Policy data (no datasets yet)."),
    ],
    "engineering-data": [
        ("engineer", "Engineer", INT, True, "System metrics (no datasets yet)."),
        ("data-analyst", "Data Analyst", INT, True, "Broad internal data, no PII."),
        (
            "data-steward",
            "Data Steward",
            CONF,
            True,
            "Maintains the catalog; no data grants by default.",
        ),
    ],
    "general": [
        ("guest", "Guest", PUB, True, "Public data only."),
        (
            "platform-admin",
            "Platform Admin",
            PUB,
            False,
            "Manages roles. No data access unless granted.",
        ),
    ],
}

# column spec: (name, type, sensitivity, is_pii)
DATASETS: dict[str, dict] = {
    "finance-revenue-summary": {
        "name": "Revenue and expenses by month and region",
        "dept": "finance",
        "sens": INT,
        "table": "finance_revenue_summary",
        "columns": [
            ("month", "date", INT, False),
            ("region", "string", INT, False),
            ("revenue", "float", INT, False),
            ("expenses", "float", INT, False),
        ],
    },
    "finance-ledger": {
        "name": "General ledger entries",
        "dept": "finance",
        "sens": CONF,
        "table": "finance_ledger",
        "columns": [
            ("entry_id", "integer", CONF, False),
            ("entry_date", "date", CONF, False),
            ("account", "string", CONF, False),
            ("cost_center", "string", CONF, False),
            ("amount", "float", CONF, False),
            ("currency", "string", CONF, False),
        ],
    },
    "hr-headcount": {
        "name": "Headcount and attrition by department",
        "dept": "hr",
        "sens": INT,
        "table": "hr_headcount",
        "columns": [
            ("month", "date", INT, False),
            ("department", "string", INT, False),
            ("headcount", "integer", INT, False),
            ("attrition", "integer", INT, False),
        ],
    },
    "hr-payroll": {
        "name": "Employee payroll",
        "dept": "hr",
        "sens": RES,
        "table": "hr_payroll",
        "columns": [
            ("employee_id", "integer", CONF, True),
            ("department", "string", INT, False),
            ("salary", "float", RES, False),
            ("bonus", "float", RES, False),
        ],
    },
    "marketing-campaigns": {
        "name": "Campaign spend and results",
        "dept": "marketing",
        "sens": INT,
        "table": "marketing_campaigns",
        "columns": [
            ("campaign_id", "integer", INT, False),
            ("channel", "string", INT, False),
            ("month", "date", INT, False),
            ("spend", "float", INT, False),
            ("impressions", "integer", INT, False),
            ("clicks", "integer", INT, False),
            ("conversions", "integer", INT, False),
        ],
    },
    "sales-orders": {
        "name": "Sales orders",
        "dept": "sales",
        "sens": INT,
        "table": "sales_orders",
        "columns": [
            ("order_id", "integer", INT, False),
            ("order_date", "date", INT, False),
            ("region", "string", INT, False),
            ("product", "string", INT, False),
            ("quantity", "integer", INT, False),
            ("revenue", "float", INT, False),
            ("customer_id", "integer", CONF, True),
        ],
    },
    "ops-inventory": {
        "name": "Inventory and shipments",
        "dept": "operations",
        "sens": INT,
        "table": "ops_inventory",
        "columns": [
            ("sku", "string", INT, False),
            ("warehouse", "string", INT, False),
            ("month", "date", INT, False),
            ("units_on_hand", "integer", INT, False),
            ("units_shipped", "integer", INT, False),
            ("supplier", "string", CONF, False),
        ],
    },
    "public-country-indicators": {
        "name": "Country indicators (public)",
        "dept": "engineering-data",
        "sens": PUB,
        "table": "public_country_indicators",
        "columns": [
            ("country", "string", PUB, False),
            ("year", "integer", PUB, False),
            ("gdp_per_capita", "float", PUB, False),
            ("population", "integer", PUB, False),
        ],
    },
}

ALL = "ALL"  # every column the role's ceiling allows
NON_PII = "NON_PII"  # all non-PII columns


def g(
    dataset: str,
    columns: object = ALL,
    *,
    agg: bool = False,
    min_group: int = 1,
    row_filter: list | None = None,
) -> dict:
    return {
        "dataset": dataset,
        "columns": columns,
        "agg": agg,
        "min_group": min_group,
        "row_filter": row_filter or [],
    }


REGION_FILTER = [{"column": "region", "op": "eq", "value": "$user.region"}]
SALES_AGG_COLS = ["order_date", "region", "product", "quantity", "revenue"]

# role slug -> grants
GRANTS: dict[str, list[dict]] = {
    "finance-analyst": [
        g("finance-revenue-summary"),
        g("finance-ledger", ["entry_date", "account", "cost_center", "amount"], agg=True),
    ],
    "fpa-analyst": [g("finance-revenue-summary"), g("finance-ledger", agg=True)],
    "controller": [g("finance-revenue-summary"), g("finance-ledger")],
    "ap-ar-clerk": [g("finance-ledger")],
    "auditor": [g("finance-revenue-summary"), g("finance-ledger")],
    "marketing-analyst": [
        g("marketing-campaigns"),
        g("sales-orders", SALES_AGG_COLS, agg=True, min_group=5),
    ],
    "performance-marketer": [g("marketing-campaigns")],
    "marketing-manager": [
        g("marketing-campaigns"),
        g("sales-orders", SALES_AGG_COLS, agg=True, min_group=5),
    ],
    "ops-analyst": [
        g("ops-inventory", ["sku", "warehouse", "month", "units_on_hand", "units_shipped"])
    ],
    "logistics-coordinator": [g("ops-inventory", ["sku", "warehouse", "month", "units_shipped"])],
    "ops-manager": [g("ops-inventory")],
    "procurement": [g("ops-inventory", ["sku", "month", "units_shipped", "supplier"])],
    "executive": [
        g("finance-revenue-summary"),
        g("finance-ledger", agg=True),
        g("marketing-campaigns"),
        g("sales-orders", NON_PII, agg=True),
        g("hr-headcount"),
        g("ops-inventory"),
    ],
    "board-viewer": [
        g("finance-revenue-summary", agg=True, min_group=1),
        g("sales-orders", ["order_date", "region", "revenue"], agg=True, min_group=5),
    ],
    "sales-rep": [g("sales-orders", NON_PII, row_filter=REGION_FILTER)],
    "sales-manager": [g("sales-orders", NON_PII)],
    "revops-analyst": [g("sales-orders", NON_PII)],
    "hr-business-partner": [g("hr-headcount", agg=True, min_group=5)],
    "hr-manager": [g("hr-headcount")],
    "payroll-specialist": [g("hr-payroll"), g("hr-headcount")],
    "data-analyst": [
        g("finance-revenue-summary"),
        g("marketing-campaigns"),
        g("ops-inventory", NON_PII),
        g("sales-orders", NON_PII),
        g("hr-headcount", agg=True, min_group=5),
    ],
}
