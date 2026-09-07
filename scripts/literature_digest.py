"""Generate a multi-source plant-extracellular-vesicle literature digest.

Sources:
- PubMed E-utilities
- Europe PMC REST API
- OpenAlex API
- Semantic Scholar API

Papers are deduplicated and persisted to literature/data/papers.jsonl so a
cumulative summary can be generated later.

Usage:
    python scripts/literature_digest.py
    python scripts/literature_digest.py --days 14 --extended
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

from llm import available as llm_available
from llm import llm_complete

ROOT = Path(__file__).resolve().parent.parent
LITERATURE_DIR = ROOT / "literature"
DATA_DIR = LITERATURE_DIR / "data"
PAPERS_JSONL = DATA_DIR / "papers.jsonl"

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
    "wound[Title/Abstract] OR fibrosis[Title/Abstract] OR scar[Title/Abstract] OR "
    "fibroblast[Title/Abstract]"
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


def fetch_json(url: str, timeout: int = 30, retries: int = 3):
    return json.loads(fetch(url, timeout=timeout, retries=retries).decode("utf-8", "ignore"))


def clean(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", " ".join(str(text).split())).strip()


def paper_key(p: dict) -> str:
    if p.get("doi"):
        return "doi:" + p["doi"].lower().replace("https://doi.org/", "")
    if p.get("pmid"):
        return "pmid:" + p["pmid"]
    title = clean(p.get("title", "")).lower()
    if title:
        return "title:" + title
    return "id:" + str(p.get("id", ""))


def merge_dedupe(papers: list[dict]) -> list[dict]:
    seen: set[str] = set()
    result: list[dict] = []
    for p in papers:
        key = paper_key(p)
        if key in seen:
            continue
        seen.add(key)
        result.append(p)
    return result


def search_pubmed(query: str, retmax: int = 20) -> list[dict]:
    params = urllib.parse.urlencode(
        {"db": "pubmed", "term": query, "retmax": retmax, "retmode": "json", "sort": "date"}
    )
    data = fetch_json(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{params}")
    pmids = data["esearchresult"].get("idlist", [])
    if not pmids:
        return []
    params = urllib.parse.urlencode({"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"})
    xml = fetch(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?{params}").decode("utf-8", "ignore")
    import xml.etree.ElementTree as ET
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
            "source": "PubMed",
            "id": clean(pmid_el.text) if pmid_el is not None else "",
            "pmid": clean(pmid_el.text) if pmid_el is not None else "",
            "title": clean(title_el.text) if title_el is not None else "",
            "journal": clean(journal_el.text) if journal_el is not None else "",
            "year": clean(year),
            "date": "",
            "abstract": abstract,
            "doi": clean(doi_el.text) if doi_el is not None else "",
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{clean(pmid_el.text)}/" if pmid_el is not None else "",
        })
    return articles


def search_europepmc(query: str, page_size: int = 20) -> list[dict]:
    q = query.replace("[Title/Abstract]", "").replace("[dp]", "") + f" AND (PUB_YEAR:[{date.today().year - 1} TO {date.today().year}])"
    params = urllib.parse.urlencode({"query": q, "format": "json", "pageSize": page_size, "resultType": "core"})
    data = fetch_json(f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?{params}")
    out = []
    for r in data.get("resultList", {}).get("result", []):
        out.append({
            "source": "Europe PMC",
            "id": r.get("id", ""),
            "pmid": r.get("pmid", ""),
            "title": r.get("title", ""),
            "journal": r.get("journalTitle", ""),
            "year": r.get("pubYear", ""),
            "date": "",
            "abstract": r.get("abstractText", ""),
            "doi": r.get("doi", ""),
            "url": r.get("fullTextUrlList", {}).get("fullTextUrl", [{}])[0].get("url", "") if r.get("fullTextUrlList", {}).get("fullTextUrl") else "",
        })
    return out


def _openalex_abstract(inverted: dict | None) -> str:
    if not inverted:
        return ""
    positions = {}
    for word, idxs in inverted.items():
        for i in idxs:
            positions[i] = word
    return " ".join(positions[i] for i in sorted(positions))


def search_openalex(query: str, from_date: str, to_date: str, per_page: int = 20) -> list[dict]:
    params = urllib.parse.urlencode({
        "search": query,
        "filter": f"from_publication_date:{from_date},to_publication_date:{to_date}",
        "per-page": per_page,
        "mailto": "epiphany_0421@qq.com",
    })
    data = fetch_json(f"https://api.openalex.org/works?{params}")
    out = []
    for w in data.get("results", []):
        source = (w.get("primary_location") or {}).get("source") or {}
        out.append({
            "source": "OpenAlex",
            "id": w.get("id", ""),
            "pmid": "",
            "title": w.get("title", "") or "",
            "journal": source.get("display_name", ""),
            "year": str((w.get("publication_date") or "")[:4]),
            "date": w.get("publication_date", ""),
            "abstract": _openalex_abstract(w.get("abstract_inverted_index")),
            "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
            "url": w.get("doi") or w.get("id", ""),
        })
    return out


def search_semanticscholar(query: str, limit: int = 20) -> list[dict]:
    params = urllib.parse.urlencode({
        "query": query,
        "limit": limit,
        "fields": "title,abstract,year,venue,externalIds,publicationDate,url",
    })
    data = fetch_json(f"https://api.semanticscholar.org/graph/v1/paper/search?{params}")
    out = []
    for p in data.get("data", []):
        ext = p.get("externalIds") or {}
        out.append({
            "source": "Semantic Scholar",
            "id": p.get("paperId", ""),
            "pmid": ext.get("PubMed", ""),
            "title": p.get("title", "") or "",
            "journal": p.get("venue", "") or "",
            "year": str(p.get("year", "") or ""),
            "date": p.get("publicationDate", "") or "",
            "abstract": p.get("abstract", "") or "",
            "doi": ext.get("DOI", ""),
            "url": p.get("url", ""),
        })
    return out


def collect_all(query: str, days: int) -> list[dict]:
    today = date.today()
    since = today - timedelta(days=days)
    from_date = since.isoformat()
    to_date = today.isoformat()

    papers: list[dict] = []
    errors: list[str] = []

    # PubMed
    try:
        papers += search_pubmed(query, retmax=20)
    except Exception as exc:
        errors.append(f"PubMed: {exc}")

    # Europe PMC
    try:
        papers += search_europepmc(query, page_size=20)
    except Exception as exc:
        errors.append(f"Europe PMC: {exc}")

    # OpenAlex
    try:
        papers += search_openalex(query, from_date, to_date, per_page=20)
    except Exception as exc:
        errors.append(f"OpenAlex: {exc}")

    # Semantic Scholar
    s2_query = re.sub(r"\[[^\]]*\]", "", query).strip()
    try:
        papers += search_semanticscholar(s2_query, limit=20)
    except Exception as exc:
        errors.append(f"Semantic Scholar: {exc}")

    deduped = merge_dedupe(papers)
    return deduped, errors


def append_new_papers(papers: list[dict]) -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    known: set[str] = set()
    if PAPERS_JSONL.exists():
        for line in PAPERS_JSONL.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                known.add(paper_key(json.loads(line)))
            except json.JSONDecodeError:
                continue
    new_count = 0
    with PAPERS_JSONL.open("a", encoding="utf-8") as f:
        for p in papers:
            key = paper_key(p)
            if key in known:
                continue
            record = {
                **p,
                "collected_at": date.today().isoformat(),
                "key": key,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            known.add(key)
            new_count += 1
    return new_count


def render_markdown(days: int, query: str, papers: list[dict], errors: list[str]) -> str:
    today = date.today()
    since = today - timedelta(days=days)

    lines = [
        f"# 植物外泌体/植物囊泡文献追踪（{since.isoformat()} ~ {today.isoformat()}）",
        "",
        f"> 检索范围：{query}",
        f"> 数据源：PubMed / Europe PMC / OpenAlex / Semantic Scholar｜去重后 {len(papers)} 篇",
        "",
        "## 本周新增文献",
        "",
    ]
    if not papers:
        lines.append("- 本周暂无新增文献")
    else:
        for a in papers:
            lines.append(f"- **{a['title']}**")
            lines.append(f"  - 来源：{a['source']}｜期刊：{a['journal']}｜年份：{a['year']}")
            pmid = a.get("pmid") or ""
            doi = a.get("doi") or ""
            if pmid:
                lines.append(f"  - PMID：{pmid}（https://pubmed.ncbi.nlm.nih.gov/{pmid}/）")
            if doi:
                lines.append(f"  - DOI：{doi}（https://doi.org/{doi}）")
            if a.get("abstract"):
                snippet = a["abstract"]
                if len(snippet) > 300:
                    snippet = snippet[:300] + "…"
                lines.append(f"  - 摘要：{snippet}")

    md = "\n".join(lines)

    if llm_available() and papers:
        prompt = f"""你是植物细胞外囊泡/植物外泌体领域的科研助手，擅长把多来源文献列表提炼成可读的周报。
下面是本周多个数据库检索到的植物外泌体/植物囊泡相关文献。请用中文生成「本周文献速览与重点推荐」，要求：
1. 用 2-3 句话概括本周该领域的研究动态；
2. 挑出你认为最值得关注的 3-5 篇，并说明研究方法、机制或应用价值；
3. 如果有与“皮肤衰老/ECM/胶原/创面修复/纤维化”特别相关的文献，单独标注。
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

    if errors:
        md += "\n\n## 数据源状态\n\n"
        for e in errors:
            md += f"- ⚠️ {e}\n"

    md += "\n\n---\n\n> 自动生成脚本：`scripts/literature_digest.py`｜数据源：PubMed / Europe PMC / OpenAlex / Semantic Scholar"
    return md


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--query", default=DEFAULT_QUERY, help="PubMed-style query base")
    parser.add_argument("--extended", action="store_true", help="Use skin/ECM/aging extended query")
    args = parser.parse_args()

    query = EXTENDED_QUERY if args.extended else args.query
    papers, errors = collect_all(query, args.days)
    new_count = append_new_papers(papers)
    print(f"Collected {len(papers)} papers (new to storage: {new_count}); errors: {len(errors)}")

    LITERATURE_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    path = LITERATURE_DIR / f"{today}-plant-exosome.md"
    path.write_text(render_markdown(args.days, query, papers, errors), encoding="utf-8")
    print(f"Literature digest written: {path}")


if __name__ == "__main__":
    main()