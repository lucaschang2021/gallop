"""Stable value helpers with no runtime or infrastructure dependencies."""
from datetime import datetime, timezone
import hashlib
import json
import re


def digest(value):
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(body.encode('utf-8')).hexdigest()


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('Timestamp must be a string')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None or not re.match(r'^\d{4}-\d{2}-\d{2}T', value):
        raise ValueError('Timestamp must include a timezone')
    return parsed.astimezone(timezone.utc)
