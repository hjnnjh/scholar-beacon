#!/usr/bin/env python3
"""
Zotero 写入脚本 — 按 ID 从 data.md 查找条目，去重后写入 Zotero。

用户通过 literature-zotero Skill 审批后，由 Agent 调用此脚本。

用法：
  uv run python3 zotero-write.py --data-file data.md --ids "arxiv:2603.13228" "arxiv:2603.13227"
  uv run python3 zotero-write.py --data-file data.md --all-pending --pushed-file seen-pushed-ids.md
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from pyzotero import zotero


def parse_data_md(path: str) -> dict[str, dict]:
    """解析 data.md，返回 {id: {title, authors, year, source, citationCount}} 字典。"""
    p = Path(path)
    if not p.exists():
        return {}

    items = {}
    current_date = ""
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        date_match = re.match(r"^## (\d{4}-\d{2}-\d{2})", line)
        if date_match:
            current_date = date_match.group(1)
            continue

        if line.startswith("| 标题") or line.startswith("|---"):
            continue

        if line.startswith("|") and line.endswith("|"):
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) >= 6:
                nid = cols[5]
                items[nid] = {
                    "title": cols[0].replace("\\|", "|"),
                    "authors": cols[1].replace("\\|", "|"),
                    "year": cols[2],
                    "source": cols[3],
                    "citationCount": cols[4],
                    "date": current_date,
                }
    return items


def check_zotero_exists(zot, title: str, doi: str) -> bool:
    """检查 Zotero 中是否已存在该论文。"""
    if doi:
        try:
            results = zot.items(q=doi, qmode="everything", limit=1)
            if results:
                return True
        except Exception:
            pass

    if title:
        try:
            query = title[:60]
            results = zot.items(q=query, qmode="titleCreatorYear", limit=3)
            for r in results:
                r_title = r.get("data", {}).get("title", "")
                if r_title.lower().strip() == title.lower().strip():
                    return True
        except Exception:
            pass

    return False


def write_items_to_zotero(
    items: list[dict],
    zot,
    collection_key: str | None = None,
) -> tuple[list[str], list[str]]:
    """批量写入 Zotero，返回 (成功标题列表, 失败标题列表)。"""
    if not items:
        return [], []

    success = []
    fail = []

    batch_size = 50
    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        zotero_items = []
        batch_titles = []

        for item in batch:
            template = zot.item_template("journalArticle")
            template["title"] = item.get("title", "")
            template["date"] = item.get("year", "")
            template["url"] = item.get("url", "")
            template["DOI"] = item.get("doi", "")
            template["abstractNote"] = item.get("abstract", "")

            # 作者
            authors_str = item.get("authors", "")
            if authors_str:
                creators = []
                for name in authors_str.replace(" et al.", "").split(", "):
                    name = name.strip()
                    if not name:
                        continue
                    parts = name.rsplit(" ", 1)
                    if len(parts) == 2:
                        creators.append(
                            {
                                "creatorType": "author",
                                "firstName": parts[0],
                                "lastName": parts[1],
                            }
                        )
                    else:
                        creators.append(
                            {
                                "creatorType": "author",
                                "firstName": "",
                                "lastName": name,
                            }
                        )
                template["creators"] = creators

            # 标签
            tags = [{"tag": "auto-collected"}, {"tag": "user-approved"}]
            source = item.get("source", "")
            if source:
                tags.append({"tag": f"source:{source}"})
            template["tags"] = tags

            if collection_key:
                template["collections"] = [collection_key]

            zotero_items.append(template)
            batch_titles.append(item.get("title", "unknown"))

        try:
            resp = zot.create_items(zotero_items)
            if isinstance(resp, dict):
                for idx_str in resp.get("success", {}):
                    success.append(batch_titles[int(idx_str)])
                for idx_str in resp.get("unchanged", {}):
                    success.append(batch_titles[int(idx_str)])
                for idx_str, err in resp.get("failed", {}).items():
                    print(
                        f"[WARN] 写入失败 ({batch_titles[int(idx_str)]}): {err}",
                        file=sys.stderr,
                    )
                    fail.append(batch_titles[int(idx_str)])
            else:
                success.extend(batch_titles)
        except Exception as e:
            print(f"[WARN] Zotero 批量写入异常: {e}", file=sys.stderr)
            fail.extend(batch_titles)

    return success, fail


def main():
    parser = argparse.ArgumentParser(description="按 ID 将论文写入 Zotero")
    parser.add_argument("--data-file", required=True, help="data.md 路径")
    parser.add_argument("--ids", nargs="*", default=[], help="要写入的论文 ID 列表")
    parser.add_argument(
        "--zotero-library-id",
        default=os.environ.get("ZOTERO_LIBRARY_ID", ""),
        help="Zotero Library ID",
    )
    parser.add_argument(
        "--zotero-api-key",
        default=os.environ.get("ZOTERO_API_KEY", ""),
        help="Zotero API Key",
    )
    parser.add_argument(
        "--zotero-collection",
        default=os.environ.get("ZOTERO_COLLECTION_KEY", ""),
        help="Zotero Collection Key（可选）",
    )
    args = parser.parse_args()

    if not args.ids:
        print("[INFO] 未指定 ID，退出", file=sys.stderr)
        print("请指定要写入 Zotero 的论文 ID。")
        sys.exit(0)

    if not args.zotero_library_id or not args.zotero_api_key:
        print("[ERROR] 未配置 Zotero API", file=sys.stderr)
        sys.exit(1)

    # 解析 data.md
    all_items = parse_data_md(args.data_file)
    if not all_items:
        print("[ERROR] data.md 为空或无法解析", file=sys.stderr)
        sys.exit(1)

    # 查找请求的 ID
    to_write = []
    not_found = []
    for nid in args.ids:
        if nid in all_items:
            item = all_items[nid]
            item["normalized_id"] = nid
            to_write.append(item)
        else:
            not_found.append(nid)

    if not_found:
        print(f"[WARN] 未在 data.md 中找到: {', '.join(not_found)}", file=sys.stderr)

    if not to_write:
        print("未找到任何匹配的论文。")
        sys.exit(0)

    # Zotero 去重
    zot = zotero.Zotero(args.zotero_library_id, "user", args.zotero_api_key)
    new_items = []
    skipped = []
    for item in to_write:
        if check_zotero_exists(zot, item.get("title", ""), item.get("doi", "")):
            skipped.append(item.get("title", ""))
            print(
                f"[INFO] 已存在，跳过: {item.get('title', '')[:50]}",
                file=sys.stderr,
            )
        else:
            new_items.append(item)

    # 写入
    if new_items:
        success, fail = write_items_to_zotero(
            new_items, zot, args.zotero_collection or None
        )
        print(f"\nZotero 写入结果：", file=sys.stderr)
        print(f"  成功: {len(success)}", file=sys.stderr)
        if fail:
            print(f"  失败: {len(fail)}", file=sys.stderr)
        if skipped:
            print(f"  已存在跳过: {len(skipped)}", file=sys.stderr)

        # stdout 输出供 Agent 回复用户
        result_parts = []
        if success:
            result_parts.append(f"{len(success)} 篇已写入 Zotero")
        if skipped:
            result_parts.append(f"{len(skipped)} 篇已存在跳过")
        if fail:
            result_parts.append(f"{len(fail)} 篇写入失败")
        print("、".join(result_parts) + "。")

        if success:
            print("\n写入成功：")
            for t in success:
                print(f"  - {t}")
    else:
        print(f"所有 {len(skipped)} 篇论文已存在于 Zotero，无需写入。")


if __name__ == "__main__":
    main()
