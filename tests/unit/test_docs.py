import re
from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_relative_markdown_links_resolve():
    missing = []
    for document in [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"))]:
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "#")):
                continue
            path = (document.parent / target.split("#", 1)[0]).resolve()
            if not path.exists():
                missing.append(f"{document.relative_to(ROOT)} -> {target}")
    assert not missing, "Broken documentation links: " + ", ".join(missing)
