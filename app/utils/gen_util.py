from typing import Any

from sqlalchemy import inspect


def object_as_dict(obj):
    return {c.key: str(getattr(obj, c.key)) for c in inspect(obj).mapper.column_attrs}


def format_nested_dict(p: dict):
    formatted = {}
    for k, v in p.items():
        split = k.split('.')

        def drill(keys: list[str], value) -> dict:
            if len(keys) == 1:
                return {keys[0]: value}
            return {keys[0]: drill(keys[1:], value)}

        def merge_dict(parent: dict, child: dict):
            for key, value in child.items():
                if isinstance(value, dict):
                    if parent.get(key, None) is None:
                        parent[key] = value
                        return
                    else:
                        merge_dict(parent[key], child[key])
                else:
                    parent[key] = value

        merge_dict(formatted, drill(split, v))
    return formatted


def form_generic_response(data: Any):
    return {'data': data}
