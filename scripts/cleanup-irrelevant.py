#!/usr/bin/env python3
"""
清理无关文献 — 从 data.md 和 seen-ids.md 中移除指定 ID 的论文。

用法：
  uv run python3 cleanup-irrelevant.py \
    --data-file data.md --seen-file seen-ids.md \
    --ids "arxiv:2603.13228" "openalex:W2157098139"

  # 也可从 stdin 读取 ID（每行一个）
  echo -e "arxiv:2603.13228\nopenalex:W2157098139" | \
    uv run python3 cleanup-irrelevant.py \
      --data-file data.md --seen-file seen-ids.md --from-stdin
"""

import argparse
import sys
from pathlib import Path


def remove_from_data_md(data_file: Path, ids_to_remove: set[str]) -> int:
    """从 data.md 中移除指定 ID 的行，返回移除数量。"""
    if not data_file.exists():
        return 0

    lines = data_file.read_text(encoding="utf-8").splitlines()
    new_lines = []
    removed = 0

    for line in lines:
        # 检查表格行是否包含要移除的 ID
        if line.startswith("|") and line.endswith("|"):
            cols = [c.strip() for c in line.split("|")[1:-1]]
            # ID 在最后一列（第 6 列，index 5）
            if len(cols) >= 6 and cols[5] in ids_to_remove:
                removed += 1
                continue
        new_lines.append(line)

    data_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return removed


def remove_from_seen_ids(seen_file: Path, ids_to_remove: set[str]) -> int:
    """从 seen-ids.md 中移除指定 ID，返回移除数量。"""
    if not seen_file.exists():
        return 0

    lines = seen_file.read_text(encoding="utf-8").splitlines()
    new_lines = []
    removed = 0

    for line in lines:
        stripped = line.strip()
        if stripped in ids_to_remove:
            removed += 1
            continue
        new_lines.append(line)

    seen_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return removed


def main():
    parser = argparse.ArgumentParser(description="从 data.md 和 seen-ids.md 移除指定论文")
    parser.add_argument("--data-file", required=True, help="data.md 路径")
    parser.add_argument("--seen-file", required=True, help="seen-ids.md 路径")
    parser.add_argument("--ids", nargs="*", default=[], help="要移除的论文 ID 列表")
    parser.add_argument(
        "--from-stdin", action="store_true", help="从 stdin 读取 ID（每行一个）"
    )
    parser.add_argument(
        "--keep-seen", action="store_true",
        help="保留 seen-ids.md 中的记录（防止下次再搜到）",
    )
    args = parser.parse_args()

    ids = set(args.ids)
    if args.from_stdin:
        for line in sys.stdin:
            line = line.strip()
            if line and not line.startswith("#"):
                ids.add(line)

    if not ids:
        print("[INFO] 未指定要移除的 ID", file=sys.stderr)
        print("请指定要移除的论文 ID。")
        sys.exit(0)

    data_path = Path(args.data_file)
    seen_path = Path(args.seen_file)

    # 从 data.md 移除
    data_removed = remove_from_data_md(data_path, ids)
    print(f"[INFO] data.md: 移除 {data_removed} 条", file=sys.stderr)

    # 从 seen-ids.md 移除（除非 --keep-seen）
    seen_removed = 0
    if not args.keep_seen:
        seen_removed = remove_from_seen_ids(seen_path, ids)
        print(f"[INFO] seen-ids.md: 移除 {seen_removed} 条", file=sys.stderr)

    # stdout 输出结果
    print(f"清理完成：从 data.md 移除 {data_removed} 条", end="")
    if not args.keep_seen:
        print(f"，从 seen-ids.md 移除 {seen_removed} 条。")
    else:
        print("（seen-ids 保留，下次不会再搜到）。")


if __name__ == "__main__":
    main()
