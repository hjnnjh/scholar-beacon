#!/usr/bin/env python3
"""
推送准备脚本 — 解析 data.md → 筛选未推送条目 → 写入 pending-push-ids.md → stdout 输出摘要。

两阶段提交第一步：只写 pending（中间态），不写 seen-pushed-ids。

用法：
  uv run python3 daily-push-prepare.py \
    --data-file data.md \
    --pushed-file seen-pushed-ids.md \
    --pending-file pending-push-ids.md \
    --max-items 10
"""

import argparse
import re
import sys
from pathlib import Path


def load_ids(path: str) -> set[str]:
    """加载 ID 集合。"""
    p = Path(path)
    if not p.exists():
        return set()
    ids = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            ids.add(line)
    return ids


def parse_data_md(path: str) -> list[dict]:
    """解析 data.md 中的表格行，返回条目列表。"""
    p = Path(path)
    if not p.exists():
        return []

    items = []
    current_date = ""
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        # 检测日期分节
        date_match = re.match(r"^## (\d{4}-\d{2}-\d{2})", line)
        if date_match:
            current_date = date_match.group(1)
            continue

        # 跳过表头和分隔线
        if line.startswith("| 标题") or line.startswith("|---"):
            continue

        # 解析表格行
        if line.startswith("|") and line.endswith("|"):
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) >= 6:
                items.append(
                    {
                        "title": cols[0].replace("\\|", "|"),
                        "authors": cols[1].replace("\\|", "|"),
                        "year": cols[2],
                        "source": cols[3],
                        "citationCount": cols[4],
                        "id": cols[5],
                        "date": current_date,
                    }
                )
    return items


def main():
    parser = argparse.ArgumentParser(description="推送准备（两阶段第一步）")
    parser.add_argument("--data-file", required=True, help="data.md 路径")
    parser.add_argument("--pushed-file", required=True, help="seen-pushed-ids.md 路径")
    parser.add_argument("--pending-file", required=True, help="pending-push-ids.md 路径")
    parser.add_argument(
        "--max-items", type=int, default=10, help="最大推送条目数（默认 10）"
    )
    args = parser.parse_args()

    pushed_ids = load_ids(args.pushed_file)
    # 也排除上次 pending 中的 ID（避免重复推送）
    pending_ids = load_ids(args.pending_file)
    exclude_ids = pushed_ids | pending_ids

    all_items = parse_data_md(args.data_file)
    if not all_items:
        print("[INFO] data.md 中无数据", file=sys.stderr)
        print("今日无新文献需要推送。")
        sys.exit(0)

    # 筛选未推送条目
    new_items = [item for item in all_items if item["id"] not in exclude_ids]
    if not new_items:
        print("[INFO] 无未推送条目", file=sys.stderr)
        print("今日无新文献需要推送。")
        sys.exit(0)

    # 取最新的 max_items 条（data.md 追加写入，末尾最新）
    to_push = new_items[-args.max_items :]

    # 写入 pending-push-ids.md
    pending_path = Path(args.pending_file)
    pending_path.parent.mkdir(parents=True, exist_ok=True)
    pending_content = "\n".join(item["id"] for item in to_push) + "\n"
    pending_path.write_text(pending_content, encoding="utf-8")
    print(
        f"[INFO] 已写入 {len(to_push)} 条到 pending-push-ids.md", file=sys.stderr
    )

    # stdout 输出摘要供 Agent 格式化
    print(f"今日有 {len(to_push)} 篇新文献待推送：\n")
    for i, item in enumerate(to_push, 1):
        print(f"{i}. **{item['title']}**")
        print(f"   作者: {item['authors']}")
        print(f"   年份: {item['year']} | 来源: {item['source']} | 引用数: {item['citationCount']}")
        print(f"   采集日期: {item['date']} | ID: {item['id']}")
        print()

    print("请将以上文献格式化为 Telegram 简报后发送给用户。")


if __name__ == "__main__":
    main()
