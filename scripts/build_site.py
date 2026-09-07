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
LITERATURE_DIR = ROOT / "literature"

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

/* Top navigation */
.nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 28px;
}
.nav .brand {
  font-weight: 700;
  font-size: 1.05rem;
  letter-spacing: -.01em;
  color: var(--text);
  text-decoration: none;
}
.nav .brand span { color: var(--accent); }
.nav .gh {
  font-size: .9rem;
  color: var(--muted);
  text-decoration: none;
}
.nav .gh:hover { color: var(--accent); }

/* Category filter tabs */
.filters { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 24px; }
.filter-btn {
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--muted);
  padding: 8px 16px;
  border-radius: 999px;
  font-size: .9rem;
  cursor: pointer;
  transition: all .15s ease;
}
.filter-btn:hover { border-color: var(--accent); color: var(--accent); }
.filter-btn.active {
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  color: #fff;
  border-color: transparent;
}

/* Category tag on cards */
.tag {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: .72rem;
  color: #fff;
  font-weight: 600;
  margin-bottom: 10px;
}
.tag.ai { background: linear-gradient(135deg, #4f46e5, #6366f1); }
.tag.lit { background: linear-gradient(135deg, #0ea5e9, #22d3ee); }

/* Back to top */
.back-top {
  position: fixed;
  right: 22px;
  bottom: 22px;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  color: #fff;
  border: none;
  font-size: 20px;
  cursor: pointer;
  display: none;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-hover);
  z-index: 10;
}
.back-top.visible { display: flex; }
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
        f"""<a class="card" data-category="{item['category_key']}" href="reports/{item['slug']}.html">
<span class="tag {item['category_key']}">{item['category']}</span>
<h2>{item['title']}</h2>
<div class="date">{item['date']}</div>
<p class="excerpt">{item['excerpt']}</p>
</a>"""
        for item in items
    )
    empty_html = '<div class="empty">还没有内容，先把 Markdown 放进 <code>weekly/</code> 或 <code>literature/</code> 目录。</div>'
    ai_count = sum(1 for i in items if i["category_key"] == "ai")
    lit_count = sum(1 for i in items if i["category_key"] == "lit")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>科研信息同步站</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">
<nav class="nav">
<a class="brand" href="#">科研信息<span>同步站</span></a>
<a class="gh" href="https://github.com/wakuwaku-prog/weekly-ai-sync" target="_blank" rel="noopener">GitHub ↗</a>
</nav>
<section class="hero">
<h1>科研信息同步站</h1>
<p>每周 AI 热点 ｜ 植物外泌体/植物囊泡文献追踪</p>
<div class="badge">AI 周报 {ai_count} 项 ｜ 文献追踪 {lit_count} 项</div>
</section>
<div class="filters">
<button class="filter-btn active" data-filter="all">全部</button>
<button class="filter-btn" data-filter="ai">AI 周报</button>
<button class="filter-btn" data-filter="lit">文献追踪</button>
</div>
<div class="card-list">
{cards or empty_html}
</div>
<div class="footer">由 scripts/build_site.py 自动生成 ｜ 更新时间：{build_time}</div>
</div>
<button class="back-top" id="backTop" aria-label="回到顶部">↑</button>
<script>
(function() {{
  const buttons = document.querySelectorAll('.filter-btn');
  const cards = document.querySelectorAll('.card');
  buttons.forEach(btn => {{
    btn.addEventListener('click', () => {{
      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const cat = btn.dataset.filter;
      cards.forEach(c => {{
        c.style.display = (cat === 'all' || c.dataset.category === cat) ? '' : 'none';
      }});
    }});
  }});
  const backTop = document.getElementById('backTop');
  const onScroll = () => {{
    backTop.classList.toggle('visible', window.scrollY > 400);
  }};
  window.addEventListener('scroll', onScroll);
  onScroll();
  backTop.addEventListener('click', () => window.scrollTo({{ top: 0, behavior: 'smooth' }}));
}})();
</script>
</body>
</html>
"""


def excerpt_from_html(html: str, limit: int = 180) -> str:
    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] + ("…" if len(text) > limit else "")


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    build_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    def add_item(path: Path, category: str, slug_prefix: str = "") -> None:
        md_text = path.read_text(encoding="utf-8")
        html_body = markdown.markdown(
            md_text,
            extensions=["extra", "sane_lists", "toc"],
        )
        slug = f"{slug_prefix}{slug_for(path)}"
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
                "category": category,
                "category_key": "ai" if category == "AI 周报" else "lit",
                "excerpt": excerpt_from_html(html_body),
            }
        )

    items: list[dict] = []

    weekly_files = sorted(
        (p for p in WEEKLY_DIR.glob("*-ai-weekly.md") if not p.name.startswith("auto-")),
        key=lambda p: p.name,
        reverse=True,
    )
    for path in weekly_files:
        add_item(path, "AI 周报")

    if LITERATURE_DIR.exists():
        literature_files = sorted(
            LITERATURE_DIR.glob("*.md"),
            key=lambda p: p.name,
            reverse=True,
        )
        for path in literature_files:
            add_item(path, "文献追踪", slug_prefix="lit-")

    (SITE_DIR / "index.html").write_text(render_index(items, build_time), encoding="utf-8")
    print(f"Generated site: {len(items)} item(s) -> {SITE_DIR}")


if __name__ == "__main__":
    main()