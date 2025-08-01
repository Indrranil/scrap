from sqlalchemy import inspect


def object_as_dict(obj):
    return {c.key: str(getattr(obj, c.key)) for c in inspect(obj).mapper.column_attrs}
