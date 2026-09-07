"""Build the research info sync site.

Outputs:
- site/index.html                Home (AI weekly + literature reports)
- site/reports/<slug>.html       Per-report pages
- site/library.html              Paper library (from literature/data/papers.jsonl)
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
WEEKLY_DIR = ROOT / "weekly"
LITERATURE_DIR = ROOT / "literature"
DATA_DIR = LITERATURE_DIR / "data"
PAPERS_JSONL = DATA_DIR / "papers.jsonl"
SITE_DIR = ROOT / "site"
REPORTS_DIR = SITE_DIR / "reports"

SITE_URL = "https://wakuwaku-prog.github.io/weekly-ai-sync/"

CSS = """
:root {
  --paper: #F6F3ED;
  --card: #FFFFFF;
  --ink: #1C2A24;
  --leaf: #1F4A3C;
  --mint: #2E8B7A;
  --gold: #C9A24B;
  --line: #DCD5C8;
  --muted: #6B746E;
  --shadow: 0 1px 2px rgba(28, 42, 36, .05), 0 2px 8px rgba(28, 42, 36, .05);
}
@media (prefers-color-scheme: dark) {
  :root {
    --paper: #131812;
    --card: #1B231C;
    --ink: #E7E4D8;
    --leaf: #7FC3A6;
    --mint: #5BB99D;
    --gold: #D9B96A;
    --line: #303B31;
    --muted: #9AA69C;
    --shadow: 0 1px 2px rgba(0, 0, 0, .4), 0 2px 8px rgba(0, 0, 0, .25);
  }
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: "Avenir Next", "Inter", "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  line-height: 1.7;
  -webkit-font-smoothing: antialiased;
}
a { color: var(--mint); text-decoration: none; }
a:hover { text-decoration: underline; }
.container { max-width: 860px; margin: 0 auto; padding: 30px 22px 70px; }

/* Masthead nav */
.nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 34px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--line);
}
.nav .brand {
  font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, "Songti SC", serif;
  font-weight: 600;
  font-size: 1.12rem;
  letter-spacing: -.01em;
  color: var(--ink);
}
.nav .brand span { color: var(--mint); }
.nav .links { display: flex; gap: 18px; font-size: .92rem; }
.nav .links a { color: var(--muted); }
.nav .links a.active, .nav .links a:hover { color: var(--leaf); }

/* Hero */
.hero {
  background: var(--leaf);
  color: #F6F3ED;
  padding: 40px 36px;
  margin-bottom: 34px;
}
.hero .kicker {
  font-size: .85rem;
  color: rgba(246, 243, 237, .75);
  margin: 0 0 10px;
}
.hero h1 {
  font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, "Songti SC", serif;
  font-weight: 600;
  font-size: 2rem;
  line-height: 1.2;
  margin: 0 0 8px;
  letter-spacing: -.015em;
}
.hero p { margin: 0; color: rgba(246, 243, 237, .82); max-width: 620px; }
.hero .stats { margin-top: 18px; font-size: .88rem; color: rgba(246, 243, 237, .8); }
.hero .stats b { color: #fff; font-weight: 600; }

/* Category filter links */
.filters { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 26px; }
.filter-btn {
  border: 1px solid var(--line);
  background: transparent;
  color: var(--muted);
  padding: 7px 14px;
  font-size: .9rem;
  cursor: pointer;
  font-family: inherit;
  transition: border-color .15s ease, color .15s ease;
}
.filter-btn:hover { border-color: var(--mint); color: var(--leaf); }
.filter-btn.active { border-color: var(--leaf); color: var(--leaf); font-weight: 600; }

/* Editorial entries */
.card-list { display: block; }
.entry {
  display: block;
  border-bottom: 1px solid var(--line);
  border-left: 3px solid transparent;
  padding: 20px 0 18px 16px;
  margin-left: -16px;
  color: inherit;
  transition: border-color .15s ease;
}
.entry:hover { border-left-color: var(--mint); text-decoration: none; }
.entry h2 {
  font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, "Songti SC", serif;
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0 0 8px;
  line-height: 1.35;
  letter-spacing: -.01em;
}
.entry .meta { font-size: .84rem; color: var(--muted); margin-bottom: 8px; }
.entry .excerpt { color: var(--muted); margin: 0; font-size: .95rem; }
.tag {
  display: inline-block;
  padding: 2px 9px;
  border-radius: 999px;
  font-size: .72rem;
  font-weight: 600;
  margin-right: 8px;
  background: var(--card);
  border: 1px solid var(--line);
  color: var(--leaf);
}
.tag.ai { border-color: var(--mint); color: var(--mint); }
.tag.lit { border-color: var(--gold); color: #8a6d2c; }
@media (prefers-color-scheme: dark) { .tag.lit { color: var(--gold); } }

/* Report page */
article.report {
  background: var(--card);
  border: 1px solid var(--line);
  padding: 38px 42px;
  box-shadow: var(--shadow);
}
article.report h1 {
  font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, "Songti SC", serif;
  font-size: 1.9rem;
  line-height: 1.3;
  margin: 0 0 10px;
  letter-spacing: -.02em;
}
article.report blockquote {
  margin: 0 0 26px;
  padding: 12px 18px;
  background: var(--paper);
  border-left: 3px solid var(--gold);
  color: var(--muted);
}
article.report h2 {
  font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, "Songti SC", serif;
  font-size: 1.35rem;
  margin-top: 38px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--line);
}
article.report h3 { font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif; font-size: 1.12rem; margin-top: 26px; }
article.report p, article.report li { line-height: 1.8; }
article.report ul, article.report ol { padding-left: 1.4em; }
article.report li { margin-bottom: 6px; }
article.report pre {
  background: var(--paper);
  border: 1px solid var(--line);
  padding: 14px 18px;
  overflow-x: auto;
}
article.report code {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: .9em;
}
article.report pre code { background: transparent; border: 0; padding: 0; }
article.report table { border-collapse: collapse; width: 100%; margin: 16px 0; }
article.report th, article.report td { border: 1px solid var(--line); padding: 8px 12px; text-align: left; }
article.report th { background: var(--paper); }

.back-link {
  display: inline-block;
  margin-bottom: 18px;
  font-size: .93rem;
  color: var(--muted);
  padding-left: 0;
}
.back-link:hover { color: var(--leaf); text-decoration: none; }

/* Library */
.library-intro { margin-bottom: 28px; color: var(--muted); }
.library-search {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--line);
  background: var(--card);
  color: var(--ink);
  font-size: .95rem;
  font-family: inherit;
  margin-bottom: 22px;
}
.paper {
  border-bottom: 1px solid var(--line);
  padding: 18px 0 16px;
}
.paper h3 {
  font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, "Songti SC", serif;
  font-size: 1.12rem;
  font-weight: 600;
  margin: 0 0 6px;
  line-height: 1.4;
}
.paper .meta { font-size: .84rem; color: var(--muted); margin-bottom: 8px; }
.paper .links { font-size: .85rem; margin-bottom: 8px; }
.paper .links a { margin-right: 12px; }
.paper .abs { color: var(--muted); font-size: .9rem; margin: 0; }
.empty { color: var(--muted); text-align: center; padding: 40px 0; }
.footer {
  margin-top: 46px;
  color: var(--muted);
  font-size: .82rem;
  text-align: center;
  border-top: 1px solid var(--line);
  padding-top: 18px;
}
.back-top {
  position: fixed; right: 20px; bottom: 20px;
  width: 42px; height: 42px;
  border-radius: 50%;
  background: var(--leaf);
  color: #F6F3ED;
  border: none;
  font-size: 20px;
  cursor: pointer;
  display: none;
  align-items: center; justify-content: center;
  box-shadow: var(--shadow);
  z-index: 10;
}
.back-top.visible { display: flex; }
@media (max-width: 600px) {
  .container { padding: 20px 16px 60px; }
  article.report { padding: 26px 22px; }
  .hero { padding: 28px 22px; }
  .hero h1 { font-size: 1.6rem; }
}
"""


def slug_for(path: Path) -> str:
    return path.stem


def excerpt_from_html(html: str, limit: int = 170) -> str:
    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] + ("…" if len(text) > limit else "")


def nav_html(active: str) -> str:
    def cls(key: str) -> str:
        return ' class="active"' if key == active else ""
    return f"""<nav class="nav">
<a class="brand" href="index.html">科研信息<span>同步站</span></a>
<div class="links">
<a{cls('home')} href="index.html">首页</a>
<a{cls('library')} href="library.html">论文库</a>
</div>
</nav>"""


def back_top_html() -> str:
    return """<button class="back-top" id="backTop" aria-label="回到顶部">↑</button>
<script>
(function(){const b=document.getElementById('backTop');const f=()=>b.classList.toggle('visible',window.scrollY>400);window.addEventListener('scroll',f);f();b.addEventListener('click',()=>window.scrollTo({top:0,behavior:'smooth'}));})();
</script>"""


def render_report(page_title: str, body_html: str, build_time: str, active: str = "home") -> str:
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
{nav_html(active)}
<a class="back-link" href="index.html">← 返回首页</a>
<article class="report">
{body_html}
</article>
<div class="footer">由 scripts/build_site.py 自动生成 ｜ 更新时间：{build_time}</div>
</div>
{back_top_html()}
</body>
</html>
"""


def render_index(items: list[dict], build_time: str) -> str:
    cards = "\n".join(
        f"""<a class="entry" data-category="{item['category_key']}" href="reports/{item['slug']}.html">
<div><span class="tag {item['category_key']}">{item['category']}</span></div>
<h2>{item['title']}</h2>
<div class="meta">{item['date']}</div>
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
{nav_html('home')}
<section class="hero">
<p class="kicker">每周更新的实验室信息流</p>
<h1>科研信息同步站</h1>
<p>AI 周报与植物外泌体 / 植物囊泡文献追踪，自动收集、总结并汇总。</p>
<div class="stats"><b>{ai_count}</b> 篇 AI 周报 ｜ <b>{lit_count}</b> 篇文献追踪</div>
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
{back_top_html()}
<script>
(function(){{const buttons=document.querySelectorAll('.filter-btn');const cards=document.querySelectorAll('.entry');buttons.forEach(btn=>{{btn.addEventListener('click',()=>{{buttons.forEach(b=>b.classList.remove('active'));btn.classList.add('active');const cat=btn.dataset.filter;cards.forEach(c=>{{c.style.display=(cat==='all'||c.dataset.category===cat)?'':'none';}});}});}});}})();
</script>
</body>
</html>
"""


def load_papers() -> list[dict]:
    if not PAPERS_JSONL.exists():
        return []
    papers = []
    for line in PAPERS_JSONL.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            papers.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return papers


def library_links(p: dict) -> list[tuple[str, str]]:
    links = []
    pmid = p.get("pmid") or ""
    doi = p.get("doi") or ""
    url = p.get("url") or ""
    if pmid:
        links.append(("PubMed", f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"))
    if doi:
        links.append(("DOI", f"https://doi.org/{doi}"))
    if url and url not in [l for _, l in links]:
        if url.startswith("http"):
            links.append(("来源", url))
    return links


def render_library(papers: list[dict], build_time: str) -> str:
    rows = []
    for p in papers:
        links = library_links(p)
        link_html = " ".join(
            f'<a href="{href}" target="_blank" rel="noopener">{label}</a>' for label, href in links
        )
        abstract = p.get("abstract") or ""
        if len(abstract) > 260:
            abstract = abstract[:260] + "…"
        source = p.get("source") or "—"
        journal = p.get("journal") or ""
        year = p.get("year") or ""
        meta = " ｜ ".join(x for x in [journal, year] if x)
        rows.append(f"""<div class="paper" data-search="{ (p.get('title') or '') + ' ' + abstract }">
<h3><a href="{links[0][1] if links else '#'}" target="_blank" rel="noopener">{p.get('title', '')}</a></h3>
<div class="meta"><span class="tag">{source}</span>{meta}</div>
<div class="links">{link_html}</div>
<p class="abs">{abstract}</p>
</div>""")
    rows_html = "\n".join(rows) if rows else '<div class="empty">论文库为空，先运行文献抓取脚本。</div>'
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>论文库｜科研信息同步站</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">
{nav_html('library')}
<section class="hero">
<p class="kicker">自动收集的植物囊泡文献</p>
<h1>论文库</h1>
<p>这里汇总了本周及历史抓取的植物细胞外囊泡 / 植物外泌体相关文献，点击标题或下方链接即可跳转到原文。</p>
<div class="stats"><b>{len(papers)}</b> 篇已收录</div>
</section>
<p class="library-intro">数据来源：PubMed、Europe PMC、OpenAlex、Semantic Scholar。用下方搜索框可按标题或摘要快速过滤。</p>
<input class="library-search" id="libSearch" type="text" placeholder="搜索标题或摘要…">
<div id="libList">
{rows_html}
</div>
<div class="footer">由 scripts/build_site.py 自动生成 ｜ 更新时间：{build_time}</div>
</div>
{back_top_html()}
<script>
(function(){{const input=document.getElementById('libSearch');const rows=document.querySelectorAll('.paper');input.addEventListener('input',()=>{{const q=input.value.trim().toLowerCase();rows.forEach(r=>{{r.style.display=(!q||r.dataset.search.toLowerCase().includes(q))?'':'none';}});}});}})();
</script>
</body>
</html>
"""


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    build_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    def add_item(path: Path, category: str, slug_prefix: str = "") -> None:
        md_text = path.read_text(encoding="utf-8")
        html_body = markdown.markdown(md_text, extensions=["extra", "sane_lists", "toc"])
        slug = f"{slug_prefix}{slug_for(path)}"
        title_match = re.search(r"^#\s+(.+)$", md_text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else path.stem
        date = path.stem[:10]
        (REPORTS_DIR / f"{slug}.html").write_text(
            render_report(title, html_body, build_time), encoding="utf-8"
        )
        items.append({
            "slug": slug,
            "title": title,
            "date": date,
            "category": category,
            "category_key": "ai" if category == "AI 周报" else "lit",
            "excerpt": excerpt_from_html(html_body),
        })

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

    papers = load_papers()
    (SITE_DIR / "library.html").write_text(render_library(papers, build_time), encoding="utf-8")

    print(f"Generated site: {len(items)} report item(s), {len(papers)} library paper(s) -> {SITE_DIR}")


if __name__ == "__main__":
    main()