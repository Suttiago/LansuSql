import operator
from typing import Any, Dict, List
from sqlalchemy.sql.elements import BinaryExpression

OPERATOR_MAP = {
    "eq": operator.eq,   # ==
    "neq": operator.ne,  # !=
    "gt": operator.gt,   # >
    "gte": operator.ge,  # >=
    "lt": operator.lt,   # <
    "lte": operator.le,  # <=
}

def build_filters(model: any, filter_dict: Dict[str, Any]) -> List[BinaryExpression]:
    filters = []
    
    for key, value in filter_dict.items():
        if "__" in key:
            field_name, op =key.split("__",1)
        else:
            field_name, op = key, "eq" 
            
        column = getattr(model, field_name, None)
        if column is None:
            continue
        
        func = OPERATOR_MAP.get(op)
        if func:
            filters.append(func(column,value))
            
        elif op == "in":
            filters.append(column.in_(value))
        
        elif op == "like":
            filters.append(column.like(f"%{value}%"))
            
        elif op == "ilike":
            filters.append(column.ilike(f"%{value}%"))
            
    return filters
            