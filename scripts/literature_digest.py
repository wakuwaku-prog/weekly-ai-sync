"""Generate a weekly plant-extracellular-vesicle literature digest from PubMed.

Sources:
- PubMed E-utilities (esearch + efetch)
Optional:
- If LLM_API_KEY is configured, adds an LLM-written "本周文献速览" section.

Usage:
    python scripts/literature_digest.py
    python scripts/literature_digest.py --days 14
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path

from llm import available as llm_available
from llm import llm_complete

ROOT = Path(__file__).resolve().parent.parent
LITERATURE_DIR = ROOT / "literature"

USER_AGENT = "Mozilla/5.0 (weekly-literature-digest)"

DEFAULT_QUERY = (
    '("plant extracellular vesicle"[Title/Abstract] OR '
    '"plant-derived exosome"[Title/Abstract] OR '
    '"plant exosome-like nanovesicles"[Title/Abstract] OR '
    '"plant-derived nanovesicles"[Title/Abstract])'
)

EXTENDED_QUERY = (
    DEFAULT_QUERY + " AND ("
    "skin[Title/Abstract] OR dermal[Title/Abstract] OR "
    "skin aging[Title/Abstract] OR senescence[Title/Abstract] OR "
    "extracellular matrix[Title/Abstract] OR collagen[Title/Abstract] OR "
    "wound[Title/Abstract]"
    ")"
)


def fetch(url: str, timeout: int = 30, retries: int = 3) -> bytes:
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


def clean(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", " ".join(text.split())).strip()


def search_pubmed(query: str, retmax: int = 20) -> list[str]:
    params = urllib.parse.urlencode(
        {"db": "pubmed", "term": query, "retmax": retmax, "retmode": "json", "sort": "date"}
    )
    data = json.loads(fetch(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{params}").decode("utf-8"))
    return data["esearchresult"].get("idlist", [])


def fetch_articles(pmids: list[str]) -> list[dict]:
    if not pmids:
        return []
    params = urllib.parse.urlencode({"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"})
    xml = fetch(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?{params}").decode("utf-8", "ignore")
    ns = {"m": "http://www.w3.org/2005/Atom"}
    # PubMed efetch XML uses a default namespace on the root, but child tags are
    # commonly plain. Use local-name matching to avoid namespace pain.
    root = ET.fromstring(xml)
    articles = []
    for art in root.findall(".//PubmedArticle"):
        pmid_el = art.find(".//PMID")
        title_el = art.find(".//ArticleTitle")
        abstract_els = art.findall(".//AbstractText")
        journal_el = art.find(".//Journal/Title")
        year_el = art.find(".//JournalIssue/PubDate/Year")
        medline_date_el = art.find(".//JournalIssue/PubDate/MedlineDate")
        doi_el = art.find(".//ArticleIdList/ArticleId[@IdType='doi']")
        abstract = " ".join(clean(el.text or "") for el in abstract_els)
        year = (year_el.text if year_el is not None else None) or (medline_date_el.text[:4] if medline_date_el is not None and medline_date_el.text else "")
        articles.append({
            "pmid": clean(pmid_el.text) if pmid_el is not None else "",
            "title": clean(title_el.text) if title_el is not None else "",
            "journal": clean(journal_el.text) if journal_el is not None else "",
            "year": clean(year),
            "abstract": abstract,
            "doi": clean(doi_el.text) if doi_el is not None else "",
        })
    return articles


def render_markdown(days: int, query: str) -> str:
    today = date.today()
    since = today - timedelta(days=days)
    # PubMed date tag: use the last N days by publication date.
    date_term = f"AND ({today.year}/{since.month:02d}/{since.day:02d}:{today.year}/{today.month:02d}/{today.day:02d}[dp])"
    pubmed_query = f"{query} {date_term}"
    pmids = search_pubmed(pubmed_query, retmax=30)
    articles = fetch_articles(pmids[:20])

    lines = [
        f"# 植物外泌体/植物囊泡文献追踪（{since.isoformat()} ~ {today.isoformat()}）",
        "",
        f"> PubMed 检索：`{pubmed_query}`",
        f"> 共返回 {len(articles)} 篇（展示前 {min(len(articles), 20)} 篇）",
        "",
        "## 本周新增文献",
        "",
    ]
    if not articles:
        lines.append("- 本周暂无新增文献")
    else:
        for a in articles:
            lines.append(f"- **{a['title']}**")
            lines.append(f"  - 期刊：{a['journal']}｜年份：{a['year']}｜PMID：{a['pmid']}")
            if a["doi"]:
                lines.append(f"  - DOI：{a['doi']}")
            if a["abstract"]:
                snippet = a["abstract"]
                if len(snippet) > 300:
                    snippet = snippet[:300] + "…"
                lines.append(f"  - 摘要：{snippet}")

    md = "\n".join(lines)

    if llm_available() and articles:
        prompt = f"""你是植物细胞外囊泡/植物外泌体领域的科研助手，擅长把文献列表提炼成可读的周报。
下面是本周 PubMed 检索到的植物外泌体/植物囊泡相关文献。请用中文生成「本周文献速览与重点推荐」，要求：
1. 用 2-3 句话概括本周该领域的研究动态；
2. 挑出你认为最值得关注的 3-5 篇，并解释为什么值得关注（方法、机制、应用价值）；
3. 如果有与“皮肤衰老/ECM/胶原/创面修复”特别相关的文献，请单独标注。
不要编造原文没有的信息。

文献列表：
{md}"""
        try:
            insight = llm_complete(
                prompt,
                system="你是专注于植物囊泡与再生医学的科研编辑。",
                max_tokens=2500,
            )
            md = md.replace(
                "## 本周新增文献",
                f"## 本周文献速览与重点推荐（AI 生成）\n\n{insight}\n\n## 本周新增文献",
                1,
            )
        except Exception as exc:
            md += f"\n\n> LLM 摘要生成失败：{exc}\n"

    md += "\n\n---\n\n> 自动生成脚本：`scripts/literature_digest.py`｜数据来源：PubMed E-utilities"
    return md


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--query", default=DEFAULT_QUERY, help="PubMed query base (without date filter)")
    parser.add_argument("--extended", action="store_true", help="Use skin/ECM/aging extended query")
    args = parser.parse_args()

    query = EXTENDED_QUERY if args.extended else args.query
    LITERATURE_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    path = LITERATURE_DIR / f"{today}-plant-exosome.md"
    path.write_text(render_markdown(args.days, query), encoding="utf-8")
    print(f"Literature digest written: {path}")


if __name__ == "__main__":
    main()