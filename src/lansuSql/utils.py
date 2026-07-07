import operator
from collections.abc import Iterable
from typing import Any, Dict, List, Type

from sqlalchemy.sql.elements import ColumnElement

OPERATOR_MAP = {
    "eq": operator.eq,   # ==
    "neq": operator.ne,  # !=
    "gt": operator.gt,   # >
    "gte": operator.ge,  # >=
    "lt": operator.lt,   # <
    "lte": operator.le,  # <=
}

SUPPORTED_OPERATORS = {*OPERATOR_MAP.keys(), "in", "nin", "like", "ilike"}


def build_filters(
    model: Type[Any],
    filter_dict: Dict[str, Any],
    *,
    strict: bool = True,
) -> List[ColumnElement[bool]]:
    filters = []
    
    for key, value in filter_dict.items():
        if "__" in key:
            field_name, op =key.split("__",1)
        else:
            field_name, op = key, "eq" 
            
        column = getattr(model, field_name, None)
        if column is None:
            if strict:
                raise ValueError(
                    f"Invalid filter field '{field_name}' for model '{model.__name__}'."
                )
            continue
        
        func = OPERATOR_MAP.get(op)
        if func:
            filters.append(func(column,value))
            
        elif op == "in":
            _validate_iterable_filter_value(field_name, op, value)
            filters.append(column.in_(value))

        elif op == "nin":
            _validate_iterable_filter_value(field_name, op, value)
            filters.append(column.not_in(value))
        
        elif op == "like":
            filters.append(column.like(f"%{value}%"))
            
        elif op == "ilike":
            filters.append(column.ilike(f"%{value}%"))

        elif strict:
            supported = ", ".join(sorted(SUPPORTED_OPERATORS))
            raise ValueError(
                f"Invalid filter operator '{op}' for field '{field_name}'. "
                f"Supported operators: {supported}."
            )
            
    return filters


def _validate_iterable_filter_value(field_name: str, op: str, value: Any) -> None:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError(
            f"Filter '{field_name}__{op}' expects a non-string iterable value."
        )
