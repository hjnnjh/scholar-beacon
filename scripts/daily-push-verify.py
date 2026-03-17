#!/usr/bin/env python3
"""
推送验证脚本 — 检查推送 job 的 deliveryStatus → delivered 则 commit pending 到 seen-pushed-ids → 清空 pending。

两阶段提交第二步。

用法：
  uv run python3 daily-push-verify.py \
    --pending-file pending-push-ids.md \
    --pushed-file seen-pushed-ids.md \
    --push-job-id <literature-daily-push job ID>
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def check_delivery_status(job_id: str) -> bool:
    """检查指定 cron job 最近一次运行的 deliveryStatus。"""
    # OpenClaw cron 日志位于 ~/.openclaw/cron/runs/{job_id}.jsonl
    run_log = Path.home() / ".openclaw" / "cron" / "runs" / f"{job_id}.jsonl"
    if not run_log.exists():
        print(f"[WARN] Cron 日志不存在: {run_log}", file=sys.stderr)
        return False

    # 读取最后一行（最新的运行记录）
    try:
        lines = run_log.read_text(encoding="utf-8").strip().splitlines()
        if not lines:
            print(f"[WARN] 日志为空: {run_log}", file=sys.stderr)
            return False

        last_line = lines[-1]
        data = json.loads(last_line)
        status = data.get("deliveryStatus", "")
        delivered = data.get("delivered", False)
        print(f"[INFO] Job {job_id} 最新状态: deliveryStatus={status}, delivered={delivered}", file=sys.stderr)
        return status == "delivered" or delivered is True
    except Exception as e:
        print(f"[WARN] 解析日志失败 ({run_log}): {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="推送验证（两阶段第二步）")
    parser.add_argument("--pending-file", required=True, help="pending-push-ids.md 路径")
    parser.add_argument("--pushed-file", required=True, help="seen-pushed-ids.md 路径")
    parser.add_argument("--push-job-id", required=True, help="推送 job 的 ID")
    args = parser.parse_args()

    pending_path = Path(args.pending_file)
    pushed_path = Path(args.pushed_file)

    # 读取 pending IDs
    if not pending_path.exists():
        print("[INFO] 无 pending 文件，无需验证", file=sys.stderr)
        print("无待验证的推送。")
        sys.exit(0)

    pending_content = pending_path.read_text(encoding="utf-8").strip()
    if not pending_content:
        print("[INFO] pending 为空，无需验证", file=sys.stderr)
        print("无待验证的推送。")
        sys.exit(0)

    pending_ids = [
        line.strip()
        for line in pending_content.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    if not pending_ids:
        print("无待验证的推送。")
        sys.exit(0)

    # 检查推送状态
    delivered = check_delivery_status(args.push_job_id)

    if delivered:
        # Commit: 追加 pending 到 seen-pushed-ids
        existing = ""
        if pushed_path.exists():
            existing = pushed_path.read_text(encoding="utf-8")
        new_content = existing + "\n".join(pending_ids) + "\n"
        pushed_path.write_text(new_content, encoding="utf-8")
        print(f"[INFO] 已确认推送 {len(pending_ids)} 条", file=sys.stderr)
        print(f"推送验证通过：{len(pending_ids)} 篇文献已确认送达。")
    else:
        print(
            f"[WARN] 推送未确认送达，丢弃 {len(pending_ids)} 条 pending",
            file=sys.stderr,
        )
        print(f"推送验证失败：{len(pending_ids)} 篇文献未确认送达，将在下次推送时重试。")

    # 清空 pending（无论成功失败）
    pending_path.write_text("", encoding="utf-8")


if __name__ == "__main__":
    main()
