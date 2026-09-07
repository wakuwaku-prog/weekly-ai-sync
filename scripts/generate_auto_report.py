"""Generate an automatic weekly AI digest from keyless public APIs.

Sources:
- GitHub Trending (weekly)
- Hugging Face trending models
- arXiv (cs.AI / q-bio recent papers)
- PubMed (recent AI + bioinformatics)

This is a raw digest for email automation; the agent can later refine it into
a more analytic report. Requires only Python stdlib.
"""

from __future__ import annotations

import html as html_lib
import json
import os
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path

from llm import available as llm_available
from llm import llm_complete

ROOT = Path(__file__).resolve().parent.parent
WEEKLY_DIR = ROOT / "weekly"

USER_AGENT = "Mozilla/5.0 (weekly-ai-sync)"


def fetch(url: str, timeout: int = 20, retries: int = 3) -> bytes:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as exc:
            last_error = exc
            time.sleep(2 * (attempt + 1))
    raise last_error


def fetch_json(url: str, timeout: int = 20):
    return json.loads(fetch(url, timeout).decode("utf-8", "ignore"))


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", html_lib.unescape(text)).strip()


def github_trending(limit: int = 10) -> list[dict]:
    try:
        txt = fetch("https://github.com/trending?since=weekly").decode("utf-8", "ignore")
        rows = re.findall(r'<article class="Box-row">(.*?)</article>', txt, re.S)
        items = []
        for row in rows[:limit]:
            name_m = re.search(r'href="/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"', row)
            desc_m = re.search(r'<p class="col-9 color-fg-muted[^"]*"[^>]*>(.*?)</p>', row, re.S)
            if not name_m:
                continue
            desc = clean(re.sub(r"<[^>]+>", "", desc_m.group(1))) if desc_m else ""
            items.append({"name": name_m.group(1), "description": desc, "url": f"https://github.com/{name_m.group(1)}"})
        return items
    except Exception as e:
        return [{"name": f"GitHub Trending fetch failed: {e}", "description": "", "url": "https://github.com/trending"}]


def hf_trending(limit: int = 6) -> list[dict]:
    try:
        data = fetch_json("https://huggingface.co/api/trending")
        items = []
        for item in data.get("recentlyTrending", [])[:limit]:
            rd = item.get("repoData", {})
            items.append({
                "id": rd.get("id", ""),
                "downloads": rd.get("downloads", 0),
                "likes": rd.get("likes", 0),
                "url": f"https://huggingface.co/{rd.get('id', '')}",
            })
        return items
    except Exception as e:
        return [{"id": f"HF trending fetch failed: {e}", "downloads": 0, "likes": 0, "url": "https://huggingface.co/models"}]


def arxiv_papers(queries: list[tuple[str, str, int]]) -> list[tuple[str, str, str, str]]:
    ns = {"a": "http://www.w3.org/2005/Atom"}
    results = []
    for label, query, maxr in queries:
        try:
            q = urllib.parse.quote(query)
            url = f"http://export.arxiv.org/api/query?search_query={q}&start=0&max_results={maxr}&sortBy=submittedDate&sortOrder=descending"
            xml = fetch(url).decode("utf-8", "ignore")
            root = ET.fromstring(xml)
            for e in root.findall("a:entry", ns):
                title = clean(" ".join(e.find("a:title", ns).text.split()))
                aid = e.find("a:id", ns).text
                pub = e.find("a:published", ns).text[:10]
                results.append((label, pub, title, aid))
        except Exception as ex:
            results.append((label, "", f"{label} fetch failed: {ex}", ""))
    return results


def pubmed_recent(query: str | None = None, limit: int = 6) -> list[tuple[str, str, str]]:
    try:
        term = query or '"artificial intelligence"[Title/Abstract] AND "bioinformatics"[Title/Abstract] AND 2026/01:2026/12[dp]'
        params = urllib.parse.urlencode({"db": "pubmed", "term": term, "retmax": limit, "retmode": "json", "sort": "date"})
        data = json.loads(fetch(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{params}").decode("utf-8"))
        ids = data["esearchresult"].get("idlist", [])
        if not ids:
            return []
        params = urllib.parse.urlencode({"db": "pubmed", "id": ",".join(ids), "retmode": "json"})
        data = json.loads(fetch(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?{params}").decode("utf-8"))
        result = data.get("result", {})
        out = []
        for pid in ids:
            it = result.get(pid, {})
            out.append((pid, it.get("pubdate", ""), it.get("title", "")))
        return out
    except Exception as e:
        return [("", "", f"PubMed fetch failed: {e}")]


def load_config() -> dict:
    path = ROOT / "config.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def llm_digest_insight(report_md: str) -> str:
    if not llm_available():
        return ""
    prompt = f"""你是一位资深的技术编辑，关注 AI 前沿、Agent/工具生态以及 AI 在生物医药科研中的应用。
下面是本周自动抓取的原始聚合周报。请用中文生成一段「本周速览与重点推荐」，要求：

1. 先用一两句话总结本周整体趋势；
2. 列出 3-5 条关键趋势洞察（可以涉及模型、Agent、MCP、GitHub 生态、AI+生物医药）；
3. 挑出 3-5 个最值得关注的项目/论文/模型，并说明为什么值得关注、可能适合什么场景。

要求输出 Markdown，简洁、信息密度高，不要简单复述原始列表，不要给出无法从原文推出的具体数据。

原始周报：
{report_md[:6000]}"""
    try:
        return llm_complete(
            prompt,
            system="你是资深 AI 与生物医药交叉领域的技术编辑，擅长把技术动态提炼成可行动的洞察。",
            max_tokens=2500,
        )
    except Exception as exc:
        return f"\n> LLM 摘要生成失败：{exc}\n"


def render_markdown(config: dict | None = None) -> str:
    config = config or {}
    arxiv_cfg = config.get("arxiv", {})
    ai_cats = arxiv_cfg.get("ai_categories", ["cs.AI", "cs.LG", "cs.CL"])
    bio_cats = arxiv_cfg.get("bio_categories", ["q-bio.*"])
    ai_query = " OR ".join(f"cat:{c}" for c in ai_cats)
    bio_query = " OR ".join(f"cat:{c}" for c in bio_cats)

    today = date.today()
    week_ago = today - timedelta(days=7)
    gh = github_trending()
    hf = hf_trending()
    arx = arxiv_papers([
        ("AI", f"({ai_query}) AND submittedDate:[{week_ago:%Y%m%d} TO {today:%Y%m%d}]", 6),
        ("Bio", f"({bio_query}) AND (all:\"machine learning\" OR all:\"large language model\") AND submittedDate:[{week_ago:%Y%m%d} TO {today:%Y%m%d}]", 5),
    ])
    pm = pubmed_recent(config.get("pubmed_query"))

    lines = [
        f"# AI 每周热点同步（自动抓取 {week_ago.isoformat()} ~ {today.isoformat()}）",
        "",
        "> 本报告由自动脚本生成，属于原始信息聚合，用于邮件推送和快速浏览。",
        "",
        "## 1. GitHub Trending（过去一周）",
        "",
    ]
    if gh:
        for item in gh:
            lines.append(f"- **{item['name']}**：{item['description']}  {item['url']}")
    else:
        lines.append("- 暂无数据")
    lines += ["", "## 2. Hugging Face 趋势模型", ""]
    if hf:
        for item in hf:
            lines.append(f"- **{item['id']}**｜下载 {item['downloads']}｜点赞 {item['likes']}  {item['url']}")
    else:
        lines.append("- 暂无数据")
    lines += ["", "## 3. arXiv 近期论文（AI / 生物医药）", ""]
    if arx:
        for label, pub, title, aid in arx:
            if aid:
                lines.append(f"- [{label}] {pub}｜{title}  {aid}")
            else:
                lines.append(f"- {title}")
    else:
        lines.append("- 暂无数据")
    lines += ["", "## 4. PubMed 近期 AI + 生物医药", ""]
    if pm:
        for pid, pubdate, title in pm:
            if pid:
                lines.append(f"- {pubdate}｜{title}  PMID {pid}（https://pubmed.ncbi.nlm.nih.gov/{pid}/）")
            else:
                lines.append(f"- {title}")
    else:
        lines.append("- 暂无数据")
    lines += ["", "## 5. 说明", "", "- 自动报告为原始聚合，未做深度筛选和“可应用建议”。", "- 如需带 AI 分析和应用建议的最终版周报，仍可让 Agent 在本地生成后覆盖/补充。"]

    md = "\n".join(lines)
    insight = llm_digest_insight(md)
    if insight:
        md = md.replace(
            "## 1. GitHub Trending（过去一周）",
            f"## 本周速览与重点推荐（AI 生成）\n\n{insight}\n\n## 1. GitHub Trending（过去一周）",
            1,
        )
    return md


def main() -> None:
    WEEKLY_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    path = WEEKLY_DIR / f"auto-{today}-ai-weekly.md"
    path.write_text(render_markdown(load_config()), encoding="utf-8")
    print(f"Auto report written: {path}")


if __name__ == "__main__":
    main()