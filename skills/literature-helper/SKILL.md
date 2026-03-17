---
name: literature-helper
description: 学术文献自动搜索、Zotero 写入、AI 摘要与定时推送工具集
metadata: {"openclaw":{"requires":{"bins":["uv"],"env":["ZOTERO_API_KEY","ZOTERO_LIBRARY_ID"]}}}
---

# 文献助手工具集

学术文献全自动工作流：Semantic Scholar / arXiv 搜索 → 去重 → Zotero 写入 → AI 摘要 → Telegram 推送。

## 环境变量

| 变量 | 必需 | 说明 |
|------|------|------|
| `ZOTERO_API_KEY` | 是 | Zotero API 密钥（https://www.zotero.org/settings/keys） |
| `ZOTERO_LIBRARY_ID` | 是 | Zotero 用户库 ID |
| `ZOTERO_COLLECTION_KEY` | 否 | 写入的目标 Collection |

## 数据目录

所有工作数据位于 `~/.openclaw/workspace/literature/`：

| 文件 | 说明 |
|------|------|
| `keywords.md` | 搜索关键词（每行一个，# 注释） |
| `data.md` | 采集数据（Markdown 表格，按日期分节） |
| `seen-ids.md` | 已采集论文 ID（防重复搜索） |
| `seen-pushed-ids.md` | 已推送论文 ID（防重复推送） |
| `pending-push-ids.md` | 待确认推送 ID（两阶段中间态） |

## 脚本调用

### 采集（搜索 + 写入管道）

```bash
cd {baseDir}
uv run python3 collect-search.py \
  --keywords-file ~/.openclaw/workspace/literature/keywords.md \
  --seen-file ~/.openclaw/workspace/literature/seen-ids.md \
  --limit 20 \
| uv run python3 collect-write.py \
  --data-file ~/.openclaw/workspace/literature/data.md \
  --seen-file ~/.openclaw/workspace/literature/seen-ids.md
```

`collect-search.py` 支持 `--source [both|semantic_scholar|arxiv]` 参数选择搜索来源。

### 推送准备（两阶段第一步）

```bash
cd {baseDir}
uv run python3 daily-push-prepare.py \
  --data-file ~/.openclaw/workspace/literature/data.md \
  --pushed-file ~/.openclaw/workspace/literature/seen-pushed-ids.md \
  --pending-file ~/.openclaw/workspace/literature/pending-push-ids.md \
  --max-items 10
```

脚本输出文献摘要到 stdout，请将其格式化为用户友好的 Telegram 简报后发送。

### 推送验证（两阶段第二步）

```bash
cd {baseDir}
uv run python3 daily-push-verify.py \
  --pending-file ~/.openclaw/workspace/literature/pending-push-ids.md \
  --pushed-file ~/.openclaw/workspace/literature/seen-pushed-ids.md \
  --push-job-id <literature-daily-push 的 job ID>
```

## Cron 配置

| Job | 调度 | 说明 |
|-----|------|------|
| `literature-collect` | `0 8,20 * * *` | 搜索+去重+Zotero写入 |
| `literature-daily-push` | `0 9 * * *` | 准备摘要+AI格式化+推送 |
| `literature-push-verify` | `5 9 * * *` | 验证推送状态 |
