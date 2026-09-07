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
from datetime import datetime
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
WEEKLY_DIR = ROOT / "weekly"
SITE_DIR = ROOT / "site"
REPORTS_DIR = SITE_DIR / "reports"

CSS = """
:root {
  --bg: #f4f6fb;
  --bg-accent: #eef2ff;
  --card: #ffffff;
  --text: #1f2430;
  --muted: #667085;
  --accent: #4f46e5;
  --accent-2: #0ea5e9;
  --border: #e2e8f0;
  --shadow: 0 1px 2px rgba(16, 24, 40, .04), 0 4px 16px rgba(16, 24, 40, .06);
  --shadow-hover: 0 4px 12px rgba(16, 24, 40, .08), 0 12px 32px rgba(79, 70, 229, .10);
  --radius: 16px;
  --radius-sm: 10px;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0f1117;
    --bg-accent: #171923;
    --card: #1a1d27;
    --text: #e5e7eb;
    --muted: #9aa3b2;
    --accent: #818cf8;
    --accent-2: #38bdf8;
    --border: #2a2f3a;
    --shadow: 0 1px 2px rgba(0, 0, 0, .3), 0 4px 16px rgba(0, 0, 0, .25);
    --shadow-hover: 0 4px 12px rgba(0, 0, 0, .35), 0 12px 32px rgba(129, 140, 248, .12);
  }
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: "Inter", "Segoe UI", "PingFang SC", "Microsoft YaHei", -apple-system, sans-serif;
  background:
    radial-gradient(1200px 400px at 20% -10%, var(--bg-accent), transparent 60%),
    radial-gradient(1000px 400px at 90% 0%, color-mix(in srgb, var(--accent-2) 12%, transparent), transparent 50%),
    var(--bg);
  color: var(--text);
  line-height: 1.75;
  -webkit-font-smoothing: antialiased;
}
.container { max-width: 960px; margin: 0 auto; padding: 36px 24px 72px; }

/* Hero */
.hero {
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  color: #fff;
  border-radius: var(--radius);
  padding: 36px 40px;
  margin-bottom: 32px;
  box-shadow: var(--shadow);
  position: relative;
  overflow: hidden;
}
.hero::after {
  content: "";
  position: absolute;
  right: -60px;
  top: -60px;
  width: 220px;
  height: 220px;
  border-radius: 50%;
  background: rgba(255, 255, 255, .12);
}
.hero h1 { margin: 0 0 8px; font-size: 2rem; letter-spacing: -.02em; }
.hero p { margin: 0; color: rgba(255, 255, 255, .9); max-width: 640px; }
.hero .badge {
  display: inline-block;
  background: rgba(255, 255, 255, .18);
  border: 1px solid rgba(255, 255, 255, .25);
  padding: 4px 12px;
  border-radius: 999px;
  font-size: .85rem;
  margin-top: 12px;
}

/* Cards */
.card-list { display: grid; gap: 16px; }
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 22px 26px;
  box-shadow: var(--shadow);
  transition: transform .18s ease, box-shadow .18s ease;
  text-decoration: none;
  color: inherit;
  display: block;
}
.card:hover { transform: translateY(-2px); box-shadow: var(--shadow-hover); }
.card h2 { margin: 0 0 6px; font-size: 1.3rem; letter-spacing: -.01em; }
.card .date {
  font-size: .85rem;
  color: var(--muted);
  display: inline-block;
  background: var(--bg-accent);
  border: 1px solid var(--border);
  padding: 2px 10px;
  border-radius: 999px;
  margin-bottom: 12px;
}
.card .excerpt { color: var(--muted); margin: 0; }
.empty { color: var(--muted); text-align: center; padding: 40px 0; }

/* Report article */
article.report {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 40px 48px;
  box-shadow: var(--shadow);
}
article.report h1 { font-size: 1.9rem; line-height: 1.35; margin: 0 0 8px; letter-spacing: -.02em; }
article.report blockquote {
  margin: 0 0 24px;
  padding: 12px 18px;
  background: var(--bg-accent);
  border-left: 4px solid var(--accent);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  color: var(--muted);
}
article.report h2 {
  font-size: 1.35rem;
  margin-top: 40px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--border);
  letter-spacing: -.01em;
}
article.report h3 { font-size: 1.1rem; margin-top: 28px; }
article.report p, article.report li { line-height: 1.8; }
article.report a { color: var(--accent); text-decoration: none; }
article.report a:hover { text-decoration: underline; }
article.report ul, article.report ol { padding-left: 1.4em; }
article.report li { margin-bottom: 6px; }
article.report pre {
  background: #0f172a;
  color: #e2e8f0;
  border-radius: var(--radius-sm);
  padding: 14px 18px;
  overflow-x: auto;
  border: 1px solid #1e293b;
}
article.report code {
  background: var(--bg-accent);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 2px 6px;
  font-size: .9em;
}
article.report pre code { background: transparent; border: 0; padding: 0; color: inherit; }
article.report table { border-collapse: collapse; width: 100%; margin: 16px 0; }
article.report th, article.report td { border: 1px solid var(--border); padding: 8px 12px; text-align: left; }
article.report th { background: var(--bg-accent); }

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 20px;
  font-size: .95rem;
  color: var(--accent);
  text-decoration: none;
}
.back-link:hover { text-decoration: underline; }

.footer {
  margin-top: 40px;
  color: var(--muted);
  font-size: .85rem;
  text-align: center;
  border-top: 1px solid var(--border);
  padding-top: 20px;
}
"""


def slug_for(path: Path) -> str:
    return path.stem


def render_report(page_title: str, body_html: str, build_time: str) -> str:
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
<div class="footer">由 scripts/build_site.py 自动生成 ｜ 更新时间：{build_time}</div>
</div>
</body>
</html>
"""


def render_index(items: list[dict], build_time: str) -> str:
    cards = "\n".join(
        f"""<a class="card" href="reports/{item['slug']}.html">
<h2>{item['title']}</h2>
<div class="date">{item['date']}</div>
<p class="excerpt">{item['excerpt']}</p>
</a>"""
        for item in items
    )
    empty_html = '<div class="empty">还没有周报，先把 Markdown 放进 <code>weekly/</code> 目录。</div>'
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
<section class="hero">
<h1>AI 每周热点同步</h1>
<p>每周末自动更新｜AI 热点 / Skill 与插件 / GitHub 热门 / AI + 生物医药科研</p>
<div class="badge">共 {len(items)} 期</div>
</section>
<div class="card-list">
{cards or empty_html}
</div>
<div class="footer">由 scripts/build_site.py 自动生成 ｜ 更新时间：{build_time}</div>
</div>
</body>
</html>
"""


def excerpt_from_html(html: str, limit: int = 180) -> str:
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
    build_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    items: list[dict] = []
    for path in report_files:
        md_text = path.read_text(encoding="utf-8")
        html_body = markdown.markdown(
            md_text,
            extensions=["extra", "sane_lists", "toc"],
        )
        slug = slug_for(path)
        title_match = re.search(r"^#\s+(.+)$", md_text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else path.stem
        date = path.stem[:10]

        report_page = render_report(title, html_body, build_time)
        (REPORTS_DIR / f"{slug}.html").write_text(report_page, encoding="utf-8")

        items.append(
            {
                "slug": slug,
                "title": title,
                "date": date,
                "excerpt": excerpt_from_html(html_body),
            }
        )

    (SITE_DIR / "index.html").write_text(render_index(items, build_time), encoding="utf-8")
    print(f"Generated site: {len(items)} report(s) -> {SITE_DIR}")


if __name__ == "__main__":
    main()