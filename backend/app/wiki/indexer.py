"""Rebuild wiki/index.md from the current directory listing."""

import os
from pathlib import Path

WIKI_DIR = Path("wiki")


def rebuild_index() -> str:
    """Scan wiki directories and rebuild index.md. Returns the path."""
    sections: dict[str, list[str]] = {
        "etfs": [],
        "decisions": [],
        "daily": [],
    }

    # ETFs
    etfs_dir = WIKI_DIR / "etfs"
    if etfs_dir.exists():
        for f in sorted(etfs_dir.glob("*.md")):
            name = f.stem
            sections["etfs"].append(f"- [{name}](etfs/{f.name})")

    # Decisions
    decisions_dir = WIKI_DIR / "decisions"
    if decisions_dir.exists():
        for f in sorted(decisions_dir.glob("*.md"), reverse=True)[:30]:
            sections["decisions"].append(f"- [{f.stem}](decisions/{f.name})")

    # Daily
    daily_dir = WIKI_DIR / "daily"
    if daily_dir.exists():
        for f in sorted(daily_dir.glob("*.md"), reverse=True)[:30]:
            sections["daily"].append(f"- [{f.stem}](daily/{f.name})")

    content = f"""# ETF Compass — Wiki Index

Catalog of all wiki pages. Auto-generated at {__import__('datetime').datetime.now().isoformat()}.

## ETFs
{chr(10).join(sections['etfs']) if sections['etfs'] else '_(no ETF pages yet)_'}

## Recent Decisions
{chr(10).join(sections['decisions']) if sections['decisions'] else '_(no decisions yet)_'}

## Recent Daily Summaries
{chr(10).join(sections['daily']) if sections['daily'] else '_(no daily summaries yet)_'}
"""
    index_path = str(WIKI_DIR / "index.md")
    tmp_path = index_path + ".tmp"
    with open(tmp_path, "w") as fh:
        fh.write(content)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp_path, index_path)
    return index_path
