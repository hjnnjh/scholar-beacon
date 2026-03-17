---
name: literature-zotero
description: 审批并将采集的论文写入 Zotero 文献库（查看待审、按 ID 写入、Zotero 自动去重）
metadata: {"openclaw":{"requires":{"bins":["uv"],"env":["ZOTERO_API_KEY","ZOTERO_LIBRARY_ID"]}}}
---

# 文献入库审批

将采集到的论文（`data.md`）写入 Zotero 文献库。需要用户确认后才写入。

## 工作流

1. 用户说"看看最近采集的论文"或"有什么新论文" → 展示 data.md 中最近的论文
2. 用户挑选后说"把第 1、3、5 篇加入 Zotero"或"把 arxiv:XXXX.XXXXX 加入文献库" → 调用写入脚本
3. 脚本自动对 Zotero 去重（已存在的不重复写入），写入后回复结果

## 操作指南

### 查看最近采集的论文

```bash
cat ~/.openclaw/workspace/literature/data.md
```

展示时按日期分节，每篇论文显示标题、作者、来源、ID。让用户挑选要加入 Zotero 的。

### 写入 Zotero

用户确认后，执行：

```bash
export PATH=$HOME/.local/bin:$PATH
cd ~/.openclaw/skills/literature-helper
uv run python3 zotero-write.py \
  --data-file ~/.openclaw/workspace/literature/data.md \
  --ids "论文ID1" "论文ID2" "论文ID3"
```

ID 格式为 data.md 表格最后一列，如 `arxiv:2603.13228` 或 Semantic Scholar 的 paperId。

### 示例对话

用户："看看最近的论文"
→ 读取 data.md，列出最近采集的论文，编号展示

用户："把 1、3、5 加入 Zotero"
→ 根据编号找到对应 ID，调用 zotero-write.py

用户："把所有 LLM 相关的加入文献库"
→ 从 data.md 中筛选标题含 LLM 的论文 ID，调用 zotero-write.py

## 注意事项

- **必须等用户明确指定**后才调用写入脚本，不要自动写入
- 脚本内置 Zotero 去重（按 DOI 和标题），已存在的条目会自动跳过
- 写入的条目会带 `auto-collected` 和 `user-approved` 标签
- 如果用户说"全部加入"，先展示列表让用户确认数量再执行
