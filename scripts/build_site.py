"""Build a tiny static site from weekly AI reports.

Usage:
    python scripts/build_site.py

Input:
    weekly/YYYY-MM-DD-ai-weekly.md   (files matching *-ai-weekly.md)

Output:
    site/index.html                  Home page listing all reports
    site/reports/<slug>.html         Rendered report pages
"""

from __future__ import annotations

import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
WEEKLY_DIR = ROOT / "weekly"
SITE_DIR = ROOT / "site"
REPORTS_DIR = SITE_DIR / "reports"

CSS = """
:root {
  --bg: #f6f8fa;
  --card: #ffffff;
  --text: #1f2328;
  --muted: #57606a;
  --accent: #0969da;
  --border: #d0d7de;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.7;
}
.container { max-width: 860px; margin: 0 auto; padding: 32px 20px 64px; }
header.page-header { border-bottom: 1px solid var(--border); padding-bottom: 16px; margin-bottom: 24px; }
header.page-header h1 { margin: 0 0 8px; }
.muted { color: var(--muted); }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px 24px;
  margin-bottom: 16px;
}
.card h2 { margin: 0 0 6px; font-size: 1.25rem; }
.card .date { font-size: 0.9rem; color: var(--muted); margin-bottom: 10px; }
article.report {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 28px 32px;
}
article.report h1 { border-bottom: 1px solid var(--border); padding-bottom: 12px; }
article.report h2 { margin-top: 32px; border-bottom: 1px solid #eaeef2; padding-bottom: 6px; }
article.report pre {
  background: #f6f8fa;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px 16px;
  overflow-x: auto;
}
article.report code {
  background: #f6f8fa;
  border-radius: 4px;
  padding: 2px 5px;
}
article.report blockquote {
  margin-left: 0;
  padding-left: 1em;
  border-left: 4px solid var(--border);
  color: var(--muted);
}
.back-link { display: inline-block; margin-bottom: 16px; font-size: 0.95rem; }
.footer { margin-top: 40px; color: var(--muted); font-size: 0.85rem; text-align: center; }
"""


def slug_for(path: Path) -> str:
    return path.stem


def render_report(page_title: str, body_html: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page_title}</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">
<a class="back-link" href="../index.html">← 返回目录</a>
<article class="report">
{body_html}
</article>
<div class="footer">由 scripts/build_site.py 自动生成</div>
</div>
</body>
</html>
"""


def render_index(items: list[dict]) -> str:
    cards = "\n".join(
        f"""<div class="card">
<h2><a href="reports/{item['slug']}.html">{item['title']}</a></h2>
<div class="date">{item['date']}</div>
<p>{item['excerpt']}</p>
</div>"""
        for item in items
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI 每周热点同步</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">
<header class="page-header">
<h1>AI 每周热点同步</h1>
<p class="muted">每周末更新｜AI 热点 / GitHub 热门 / AI + 生物医药科研</p>
</header>
{cards or '<p class="muted">还没有周报，先把 Markdown 放进 <code>weekly/</code> 目录。</p>'}
<div class="footer">由 scripts/build_site.py 自动生成</div>
</div>
</body>
</html>
"""


def excerpt_from_html(html: str, limit: int = 160) -> str:
    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] + ("…" if len(text) > limit else "")


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    report_files = sorted(
        WEEKLY_DIR.glob("*-ai-weekly.md"),
        key=lambda p: p.name,
        reverse=True,
    )

    items: list[dict] = []
    for path in report_files:
        md_text = path.read_text(encoding="utf-8")
        html_body = markdown.markdown(
            md_text,
            extensions=["extra", "sane_lists", "toc"],
        )
        slug = slug_for(path)
        # First non-empty line is used as the page title fallback.
        title_match = re.search(r"^#\s+(.+)$", md_text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else path.stem
        date = path.stem[:10]

        report_page = render_report(title, html_body)
        (REPORTS_DIR / f"{slug}.html").write_text(report_page, encoding="utf-8")

        items.append(
            {
                "slug": slug,
                "title": title,
                "date": date,
                "excerpt": excerpt_from_html(html_body),
            }
        )

    (SITE_DIR / "index.html").write_text(render_index(items), encoding="utf-8")
    print(f"Generated site: {len(items)} report(s) -> {SITE_DIR}")


if __name__ == "__main__":
    main()