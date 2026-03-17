#!/usr/bin/env python3
"""
文献写入脚本 — 管道接收 JSONL → 追加 data.md → 更新 seen-ids.md。

不写入 Zotero，Zotero 写入由用户通过 literature-zotero Skill 手动审批。

用法：
  uv run python3 collect-search.py ... | uv run python3 collect-write.py \
    --data-file data.md --seen-file seen-ids.md
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def read_jsonl_stdin() -> list[dict]:
    """从 stdin 读取 JSONL。"""
    items = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"[WARN] 无法解析行: {e}", file=sys.stderr)
    return items


def archive_if_needed(data_file: Path, max_chars: int = 15000):
    """data.md 超过阈值时归档为 archive-YYYY-MM.md。"""
    if not data_file.exists():
        return
    content = data_file.read_text(encoding="utf-8")
    if len(content) <= max_chars:
        return

    now = datetime.now()
    archive_name = f"archive-{now.strftime('%Y-%m')}.md"
    archive_path = data_file.parent / archive_name

    # 追加到归档文件
    existing = ""
    if archive_path.exists():
        existing = archive_path.read_text(encoding="utf-8")
    archive_path.write_text(existing + content, encoding="utf-8")

    # 清空 data.md（保留表头注释）
    data_file.write_text(
        "# 文献采集数据\n\n> 自动生成，请勿手动编辑。历史数据见 archive-*.md\n\n",
        encoding="utf-8",
    )
    print(f"[INFO] data.md 已归档到 {archive_name}", file=sys.stderr)


def append_data_md(items: list[dict], data_file: Path):
    """追加条目到 data.md，按日期分节。"""
    if not items:
        return

    today = datetime.now().strftime("%Y-%m-%d")
    section_header = f"\n## {today}\n\n| 标题 | 作者 | 年份 | 来源 | 引用数 | ID |\n|------|------|------|------|--------|----|\n"

    # 读取现有内容
    content = ""
    if data_file.exists():
        content = data_file.read_text(encoding="utf-8")
    else:
        content = "# 文献采集数据\n\n> 自动生成，请勿手动编辑。历史数据见 archive-*.md\n\n"

    # 检查今天的分节是否已存在
    if f"## {today}" not in content:
        content += section_header

    # 追加表格行
    rows = []
    for item in items:
        title = item.get("title", "").replace("|", "\\|")[:80]
        authors = item.get("authors", "").replace("|", "\\|")[:40]
        year = str(item.get("year", ""))
        source = item.get("source", "")
        citations = str(item.get("citationCount", 0))
        nid = item.get("normalized_id", "")
        rows.append(f"| {title} | {authors} | {year} | {source} | {citations} | {nid} |")

    content += "\n".join(rows) + "\n"
    data_file.write_text(content, encoding="utf-8")


def update_seen_ids(ids: list[str], seen_file: Path):
    """追加 ID 到 seen-ids.md。"""
    if not ids:
        return
    existing = ""
    if seen_file.exists():
        existing = seen_file.read_text(encoding="utf-8")
    new_lines = "\n".join(ids) + "\n"
    seen_file.write_text(existing + new_lines, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="JSONL stdin → data.md + seen-ids.md")
    parser.add_argument("--data-file", required=True, help="data.md 路径")
    parser.add_argument("--seen-file", required=True, help="seen-ids.md 路径")
    args = parser.parse_args()

    items = read_jsonl_stdin()
    if not items:
        print("[INFO] 无输入数据，退出", file=sys.stderr)
        sys.exit(0)

    print(f"[INFO] 接收到 {len(items)} 条论文", file=sys.stderr)

    data_path = Path(args.data_file)
    seen_path = Path(args.seen_file)

    # 确保父目录存在
    data_path.parent.mkdir(parents=True, exist_ok=True)
    seen_path.parent.mkdir(parents=True, exist_ok=True)

    # 归档检查
    archive_if_needed(data_path)

    # 追加 data.md
    append_data_md(items, data_path)
    print(f"[INFO] data.md 已更新 (+{len(items)} 条)", file=sys.stderr)

    # 更新 seen-ids
    all_ids = [item["normalized_id"] for item in items if item.get("normalized_id")]
    update_seen_ids(all_ids, seen_path)
    print(f"[INFO] seen-ids.md 已更新 (+{len(all_ids)} 条)", file=sys.stderr)

    # stdout 输出摘要供 Agent 使用
    print(f"采集完成：{len(items)} 篇新论文已写入 data.md。")


if __name__ == "__main__":
    main()
