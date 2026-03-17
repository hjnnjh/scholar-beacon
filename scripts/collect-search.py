#!/usr/bin/env python3
"""
文献搜索脚本 — 从 OpenAlex + arXiv 搜索论文，过滤已见 ID，输出 JSONL 到 stdout。

用法：
  uv run python3 collect-search.py --keywords-file keywords.md --seen-file seen-ids.md --limit 20
  uv run python3 collect-search.py --keywords-file keywords.md --seen-file seen-ids.md --source arxiv --limit 10
  uv run python3 collect-search.py --keywords-file keywords.md --seen-file seen-ids.md --source openalex --limit 10
"""

import argparse
import json
import sys
import time
from pathlib import Path

import arxiv
import requests

# OpenAlex polite pool: 加邮箱可获得更高速率
OPENALEX_EMAIL = "openclaw-literature@example.com"

# 默认搜索范围配置
DEFAULT_SCOPE = {
    "openalex_filter": "concepts.id:C41008148",  # Computer Science
    "arxiv_categories": ["cs.IR", "cs.AI", "cs.LG", "cs.CL"],
}


def load_scope(path: str | None) -> dict:
    """加载搜索范围配置文件，每行 key=value 格式，# 注释。"""
    scope = DEFAULT_SCOPE.copy()
    if not path:
        return scope
    p = Path(path)
    if not p.exists():
        return scope
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if key == "openalex_filter":
            scope["openalex_filter"] = value
        elif key == "arxiv_categories":
            scope["arxiv_categories"] = [c.strip() for c in value.split(",") if c.strip()]
    return scope


def parse_keywords(path: str) -> list[str]:
    """解析 keywords.md，每行一个关键词，# 开头为注释，空行跳过。"""
    keywords = []
    p = Path(path)
    if not p.exists():
        print(f"[WARN] 关键词文件不存在: {path}", file=sys.stderr)
        return keywords
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        keywords.append(line)
    return keywords


def load_seen_ids(path: str) -> set[str]:
    """加载已见 ID 集合（每行一个 ID）。"""
    p = Path(path)
    if not p.exists():
        return set()
    ids = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            ids.add(line)
    return ids


def normalize_arxiv_id(entry_id: str) -> str:
    """从 arXiv entry URL 提取 ID，如 http://arxiv.org/abs/2301.12345v1 -> arxiv:2301.12345"""
    raw = entry_id.split("/")[-1]
    if "v" in raw:
        raw = raw[: raw.rfind("v")]
    return f"arxiv:{raw}"


def search_openalex(keyword: str, limit: int, openalex_filter: str = "") -> list[dict]:
    """通过 OpenAlex API 搜索论文。"""
    url = "https://api.openalex.org/works"
    params = {
        "search": keyword,
        "per_page": min(limit, 50),
        "sort": "relevance_score:desc",
        "mailto": OPENALEX_EMAIL,
    }
    if openalex_filter:
        params["filter"] = openalex_filter
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[WARN] OpenAlex 搜索失败 ({keyword}): {e}", file=sys.stderr)
        return []

    results = []
    for work in data.get("results", []):
        # OpenAlex ID 格式: https://openalex.org/W1234567890
        openalex_id = work.get("id", "")
        if not openalex_id:
            continue
        # 提取短 ID
        nid = f"openalex:{openalex_id.split('/')[-1]}"

        # 作者
        authorships = work.get("authorships") or []
        author_names = []
        for a in authorships[:5]:
            name = a.get("author", {}).get("display_name", "")
            if name:
                author_names.append(name)
        authors = ", ".join(author_names)
        if len(authorships) > 5:
            authors += " et al."

        # DOI
        doi = work.get("doi", "") or ""
        if doi.startswith("https://doi.org/"):
            doi = doi[len("https://doi.org/"):]

        # abstract: OpenAlex 返回 inverted index 格式，需要重建
        abstract = ""
        abstract_index = work.get("abstract_inverted_index")
        if abstract_index:
            try:
                word_positions = []
                for word, positions in abstract_index.items():
                    for pos in positions:
                        word_positions.append((pos, word))
                word_positions.sort()
                abstract = " ".join(w for _, w in word_positions)[:500]
            except Exception:
                pass

        results.append(
            {
                "normalized_id": nid,
                "title": work.get("display_name", ""),
                "authors": authors,
                "year": work.get("publication_year"),
                "abstract": abstract,
                "doi": doi,
                "url": work.get("primary_location", {}).get("landing_page_url", "")
                or openalex_id,
                "citationCount": work.get("cited_by_count", 0),
                "source": "openalex",
            }
        )
    return results


def search_arxiv(keyword: str, limit: int, arxiv_categories: list[str] | None = None) -> list[dict]:
    """通过 arXiv API 搜索论文，按相关性排序。"""
    try:
        client = arxiv.Client()
        if arxiv_categories:
            cat_filter = " OR ".join(f"cat:{c}" for c in arxiv_categories)
            cs_query = f"({keyword}) AND ({cat_filter})"
        else:
            cs_query = keyword
        search = arxiv.Search(
            query=cs_query,
            max_results=min(limit, 50),
            sort_by=arxiv.SortCriterion.Relevance,
        )
        results = []
        for paper in client.results(search):
            nid = normalize_arxiv_id(paper.entry_id)
            authors = ", ".join(str(a) for a in paper.authors[:5])
            if len(paper.authors) > 5:
                authors += " et al."
            results.append(
                {
                    "normalized_id": nid,
                    "title": paper.title,
                    "authors": authors,
                    "year": paper.published.year if paper.published else None,
                    "abstract": (paper.summary or "")[:500],
                    "doi": paper.doi or "",
                    "url": paper.entry_id,
                    "citationCount": 0,
                    "source": "arxiv",
                }
            )
        return results
    except Exception as e:
        print(f"[WARN] arXiv 搜索失败 ({keyword}): {e}", file=sys.stderr)
        return []


def main():
    parser = argparse.ArgumentParser(description="文献搜索 → JSONL stdout")
    parser.add_argument("--keywords-file", required=True, help="关键词文件路径")
    parser.add_argument("--seen-file", required=True, help="已见 ID 文件路径")
    parser.add_argument(
        "--source",
        choices=["both", "openalex", "arxiv"],
        default="both",
        help="搜索来源（默认 both）",
    )
    parser.add_argument(
        "--limit", type=int, default=20, help="每个关键词每个来源的最大结果数"
    )
    parser.add_argument(
        "--scope-file",
        default=None,
        help="搜索范围配置文件路径（默认读取 ~/.openclaw/workspace/literature/scope.conf）",
    )
    args = parser.parse_args()

    # 加载搜索范围
    scope_file = args.scope_file
    if not scope_file:
        default_scope_path = Path.home() / ".openclaw" / "workspace" / "literature" / "scope.conf"
        if default_scope_path.exists():
            scope_file = str(default_scope_path)
    scope = load_scope(scope_file)
    print(f"[INFO] 搜索范围: openalex_filter={scope['openalex_filter']}, arxiv_categories={scope['arxiv_categories']}", file=sys.stderr)

    keywords = parse_keywords(args.keywords_file)
    if not keywords:
        print("[WARN] 无关键词，退出", file=sys.stderr)
        sys.exit(0)

    seen_ids = load_seen_ids(args.seen_file)
    output_ids: set[str] = set()  # 本次输出内去重
    count = 0

    for kw in keywords:
        # OpenAlex
        if args.source in ("both", "openalex"):
            papers = search_openalex(kw, args.limit, scope["openalex_filter"])
            for p in papers:
                nid = p["normalized_id"]
                if nid in seen_ids or nid in output_ids:
                    continue
                output_ids.add(nid)
                print(json.dumps(p, ensure_ascii=False))
                count += 1
            time.sleep(0.2)  # OpenAlex polite pool 无严格限制，短暂间隔即可

        # arXiv
        if args.source in ("both", "arxiv"):
            papers = search_arxiv(kw, args.limit, scope["arxiv_categories"])
            for p in papers:
                nid = p["normalized_id"]
                if nid in seen_ids or nid in output_ids:
                    continue
                output_ids.add(nid)
                print(json.dumps(p, ensure_ascii=False))
                count += 1
            time.sleep(1)  # arXiv 速率控制

    print(f"[INFO] 搜索完成，输出 {count} 条新论文", file=sys.stderr)


if __name__ == "__main__":
    main()
