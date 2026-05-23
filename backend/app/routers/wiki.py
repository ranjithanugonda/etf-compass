"""Wiki viewer — serves markdown pages as HTML."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["wiki"])

WIKI_DIR = Path("wiki")
WIKI_CSS = """
<style>
  * { box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         max-width: 860px; margin: 0 auto; padding: 2rem;
         background: #0f1117; color: #e2e8f0; line-height: 1.7; }
  h1 { border-bottom: 1px solid #2a2d3e; padding-bottom: 0.5rem;
       color: #fff; font-size: 1.6rem; }
  h2 { margin-top: 2rem; padding-bottom: 0.3rem; border-bottom: 1px solid #2a2d3e;
       color: #cbd5e1; font-size: 1.15rem; }
  a { color: #60a5fa; text-decoration: none; } a:hover { text-decoration: underline; }
  .nav { margin-bottom: 1.5rem; display: flex; gap: 1rem; flex-wrap: wrap; }
  .nav a { color: #94a3b8; font-size: 0.9rem; }
  .nav a:hover { color: #e2e8f0; }
  ul { padding-left: 1.5rem; }
  li { margin-bottom: 0.25rem; color: #cbd5e1; }
  p { color: #cbd5e1; margin: 0.5rem 0; }
  table { width: 100%; border-collapse: collapse; margin: 1rem 0;
          background: #1a1d2e; border-radius: 8px; overflow: hidden; }
  th { background: #141720; color: #94a3b8; padding: 0.5rem 0.75rem;
       text-align: left; font-size: 0.8rem; text-transform: uppercase;
       letter-spacing: 0.05em; border-bottom: 1px solid #2a2d3e; }
  td { padding: 0.5rem 0.75rem; border-bottom: 1px solid #1e2130;
       font-size: 0.9rem; color: #cbd5e1; }
  tr:last-child td { border-bottom: none; }
  code { background: #1e2130; padding: 0.15rem 0.4rem; border-radius: 4px;
         font-size: 0.85em; color: #f59e0b; }
  .btn-backtest { display: inline-flex; align-items: center; gap: 0.4rem;
    background: #3b82f6; color: #fff; padding: 0.4rem 1rem; border-radius: 6px;
    font-size: 0.85rem; font-weight: 500; text-decoration: none;
    margin-bottom: 1.5rem; transition: background 0.15s; }
  .btn-backtest:hover { background: #2563eb; text-decoration: none; }
  .label { font-size: 0.7rem; color: #64748b; text-transform: uppercase;
           letter-spacing: 0.08em; }
</style>"""


def _md_to_html(md_text: str) -> str:
    import re
    lines = md_text.split("\n")
    out: list[str] = []
    for line in lines:
        if line.startswith("```"):
            continue
        line = re.sub(r"\[\[([^\]]+)\]\]", r'<a href="/wiki/\1">\1</a>', line)
        if line.startswith("# "):
            out.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            out.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("- "):
            out.append(f"<li>{line[2:]}</li>")
        elif line.strip():
            out.append(f"<p>{line}</p>")
        else:
            out.append("<br>")
    return "\n".join(out)


def _render(title: str, body: str, breadcrumb: str = "") -> str:
    return f"""<!DOCTYPE html><html>
<head><meta charset="utf-8"><title>{title} — ETF Compass</title>{WIKI_CSS}</head>
<body>
  <div class="nav"><a href="/">Home</a> <a href="/wiki/etfs">ETFs</a>
    <a href="/wiki/daily">Daily</a> <a href="/wiki/decisions">Decisions</a></div>
  {breadcrumb}{body}</body></html>"""


@router.get("/", response_class=HTMLResponse)
async def wiki_home() -> str:
    ip = WIKI_DIR / "index.md"
    body = _md_to_html(ip.read_text()) if ip.exists() else "<p>No wiki yet.</p>"
    return _render("ETF Compass", body)


@router.get("/etfs", response_class=HTMLResponse)
async def wiki_etfs_list() -> str:
    d = WIKI_DIR / "etfs"
    links = [f'<li><a href="/wiki/etfs/{f.stem}">{f.stem}</a></li>'
             for f in sorted(d.glob("*.md"))] if d.exists() else ["<li>None</li>"]
    return _render("ETFs", "<h1>ETF Pages</h1><ul>" + "\n".join(links) + "</ul>")


@router.get("/daily", response_class=HTMLResponse)
async def wiki_daily_list() -> str:
    d = WIKI_DIR / "daily"
    link_fmt = '<li><a href="/wiki/daily/{stem}">{stem}</a></li>'
    links = (
        [link_fmt.format(stem=f.stem) for f in sorted(d.glob("*.md"), reverse=True)[:30]]
        if d.exists() else ["<li>None</li>"]
    )
    return _render("Daily", "<h1>Daily Summaries</h1><ul>" + "\n".join(links) + "</ul>")


@router.get("/decisions", response_class=HTMLResponse)
async def wiki_decisions_list() -> str:
    d = WIKI_DIR / "decisions"
    link_fmt = '<li><a href="/wiki/decisions/{stem}">{stem}</a></li>'
    links = (
        [link_fmt.format(stem=f.stem) for f in sorted(d.glob("*.md"), reverse=True)[:30]]
        if d.exists() else ["<li>None</li>"]
    )
    return _render("Decisions", "<h1>Decisions</h1><ul>" + "\n".join(links) + "</ul>")


@router.get("/etfs/{symbol}", response_class=HTMLResponse)
async def wiki_etf_view(symbol: str) -> str:
    p = WIKI_DIR / "etfs" / f"{symbol}.md"
    if not p.exists():
        return _render(symbol, f"<p>No page for {symbol}.</p>")
    backtest_btn = (
        f'<p><a class="btn-backtest" href="http://localhost:5173" target="_blank">'
        f'View Backtest Data &rarr;</a></p>'
    )
    breadcrumb = '<p><a href="/wiki/etfs">All ETFs</a></p>'
    return _render(symbol, backtest_btn + _md_to_html(p.read_text()), breadcrumb)


@router.get("/daily/{date_str}", response_class=HTMLResponse)
async def wiki_daily_view(date_str: str) -> str:
    p = WIKI_DIR / "daily" / f"{date_str}.md"
    if not p.exists():
        return _render(date_str, "<p>No summary.</p>")
    return _render(date_str, _md_to_html(p.read_text()),
                   '<p><a href="/wiki/daily">All Summaries</a></p>')


@router.get("/decisions/{filename}", response_class=HTMLResponse)
async def wiki_decision_view(filename: str) -> str:
    p = WIKI_DIR / "decisions" / f"{filename}.md"
    if not p.exists():
        return _render(filename, "<p>No decision page.</p>")
    return _render(filename, _md_to_html(p.read_text()),
                   '<p><a href="/wiki/decisions">All Decisions</a></p>')
