import json


def parse_json_field(value):
    """Parse a JSON field that may already be a dict/list or a JSON string.

    Used for SQLAlchemy Text columns storing JSON (conditions, steps, step_results).
    """
    if isinstance(value, str):
        return json.loads(value)
    return value
