from __future__ import annotations

import re
from typing import Any

from django.core.exceptions import ValidationError

IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")
ROW_FILTER_OPS = {"eq", "neq", "in", "lt", "lte", "gt", "gte"}
USER_REGION = "$user.region"


def validate_identifier(value: str) -> None:
    if not IDENTIFIER.match(value):
        raise ValidationError(
            "Use lowercase letters, digits and underscores, starting with a letter."
        )


def validate_parquet_path(value: str) -> None:
    if value.startswith(("/", "\\")) or ".." in value.replace("\\", "/").split("/"):
        raise ValidationError("Parquet path must be relative and must not contain '..'.")
    if not value.endswith((".parquet", "/")):
        raise ValidationError("Parquet location must end with .parquet (file) or / (folder).")


def validate_row_filter(filters: Any, valid_columns: set[str] | None = None) -> None:
    """A row filter is a list of {"column", "op", "value"} conditions that are ANDed together.

    value may be "$user.region", which is replaced by the user's region at request time.
    """
    if not isinstance(filters, list):
        raise ValidationError("Row filter must be a list of conditions.")
    for cond in filters:
        if not isinstance(cond, dict) or set(cond) != {"column", "op", "value"}:
            raise ValidationError('Each condition needs exactly: "column", "op", "value".')
        if cond["op"] not in ROW_FILTER_OPS:
            raise ValidationError(
                f"Unsupported operator {cond['op']!r}. Use: {sorted(ROW_FILTER_OPS)}."
            )
        if not isinstance(cond["column"], str) or not IDENTIFIER.match(cond["column"]):
            raise ValidationError("Invalid column name in row filter.")
        if valid_columns is not None and cond["column"] not in valid_columns:
            raise ValidationError(f"Row filter column {cond['column']!r} is not in this dataset.")
        value = cond["value"]
        if cond["op"] == "in":
            if not isinstance(value, list) or not value:
                raise ValidationError('"in" needs a non-empty list value.')
        elif isinstance(value, (list, dict)) or value is None:
            raise ValidationError("Value must be a string, number or boolean.")
