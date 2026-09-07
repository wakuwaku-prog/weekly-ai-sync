"""Generate a cumulative literature summary from all collected papers.

Reads literature/data/papers.jsonl (written by literature_digest.py) and
produces a synthesized markdown report grouped by research themes, with an
optional LLM-written overview.

Usage:
    python scripts/literature_summary.py
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

from llm import available as llm_available
from llm import llm_complete

ROOT = Path(__file__).resolve().parent.parent
LITERATURE_DIR = ROOT / "literature"
PAPERS_JSONL = LITERATURE_DIR / "data" / "papers.jsonl"


THEMES = {
    "皮肤/衰老/ECM/创面/纤维化": [
        "skin", "dermal", "aging", "ageing", "senescence", "extracellular matrix",
        "collagen", "wound", "fibrosis", "fibroblast", "scar", "rejuvenat",
    ],
    "工程化/递送/改造": [
        "hydrogel", "liposome", "hybrid", "engineer", "delivery", "encapsul",
        "nanoparticle", "membrane-fused", "biomimetic", "drug",
    ],
    "植物囊泡机制/基础": [
        "plant", "grape", "ginger", "exosome-like", "extracellular vesicle",
        "nanovesicle", "mirna", "protein", "immune", "anti-inflammatory",
    ],
}


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


def classify(p: dict) -> str:
    text = " ".join([
        p.get("title", ""),
        p.get("abstract", ""),
        p.get("keywords", "") if isinstance(p.get("keywords"), str) else "",
    ]).lower()
    for theme, keywords in THEMES.items():
        if any(k in text for k in keywords):
            return theme
    return "其他 / 未分类"


def render_markdown(papers: list[dict]) -> str:
    today = date.today().isoformat()
    total = len(papers)
    source_counts = Counter(p.get("source", "Unknown") for p in papers)
    dates = [p.get("date") or "" for p in papers if p.get("date")]
    date_range = f"{min(dates)} ~ {max(dates)}" if dates else "暂无日期信息"

    lines = [
        "# 植物外泌体/植物囊泡文献汇总报告",
        "",
        f"> 生成日期：{today}｜累计文献：{total} 篇",
        f"> 来源分布：{', '.join(f'{k} {v}篇' for k, v in source_counts.most_common())}",
        f"> 收录日期范围：{date_range}",
        "",
        "## 主题分组",
        "",
    ]

    grouped: dict[str, list[dict]] = {}
    for p in papers:
        theme = classify(p)
        grouped.setdefault(theme, []).append(p)

    for theme, items in grouped.items():
        lines.append(f"### {theme}（{len(items)} 篇）")
        lines.append("")
        for p in items:
            lines.append(f"- **{p.get('title', '')}**")
            detail = []
            if p.get("source"):
                detail.append(p["source"])
            if p.get("journal"):
                detail.append(p["journal"])
            if p.get("year"):
                detail.append(str(p["year"]))
            if detail:
                lines.append(f"  - {'｜'.join(detail)}")
            doi = p.get("doi") or ""
            pmid = p.get("pmid") or ""
            if doi:
                lines.append(f"  - DOI：{doi}（https://doi.org/{doi}）")
            if pmid:
                lines.append(f"  - PMID：{pmid}（https://pubmed.ncbi.nlm.nih.gov/{pmid}/）")
        lines.append("")

    md = "\n".join(lines)

    if llm_available() and papers:
        # Build a compact corpus preview for the LLM.
        preview = "\n".join(
            f"- ({p.get('source')}) {p.get('title')}｜{p.get('abstract', '')[:200]}"
            for p in papers[:30]
        )
        prompt = f"""你是植物细胞外囊泡/植物外泌体领域的研究编辑。下面是已收集文献的标题和摘要片段，共 {total} 篇。
请用中文生成「综合总结与趋势分析」，要求：
1. 用 3-5 段概括当前领域的主要研究热点、方法学趋势和潜在应用方向；
2. 特别关注与“皮肤衰老 / ECM / 胶原 / 创面修复 / 纤维化”相关的内容；
3. 指出知识空白或可能的研究机会；
4. 不要编造文献中没有的数据。

文献片段：
{preview}"""
        try:
            overview = llm_complete(
                prompt,
                system="你是专注植物囊泡与再生医学的资深科研编辑。",
                max_tokens=3000,
            )
            md = md.replace(
                "## 主题分组",
                f"## 综合总结与趋势分析（AI 生成）\n\n{overview}\n\n## 主题分组",
                1,
            )
        except Exception as exc:
            md += f"\n\n> LLM 汇总生成失败：{exc}\n"

    return md


def main() -> None:
    papers = load_papers()
    if not papers:
        print("No papers found in literature/data/papers.jsonl")
        return
    LITERATURE_DIR.mkdir(parents=True, exist_ok=True)
    out = LITERATURE_DIR / f"{date.today().isoformat()}-literature-summary.md"
    out.write_text(render_markdown(papers), encoding="utf-8")
    print(f"Literature summary written: {out}（{len(papers)} papers）")


if __name__ == "__main__":
    main()