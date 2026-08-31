import json
from dataclasses import fields
from pathlib import Path

import pytest

from gallop.core.models import PracticeResult


@pytest.fixture
def manifest():
    path = Path(__file__).parents[1] / "examples/mathematics/practice-manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def result():
    path = Path(__file__).parents[1] / "examples/mathematics/practice-result.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    names = {field.name for field in fields(PracticeResult)}
    return PracticeResult(**{key: value for key, value in data.items() if key in names})
