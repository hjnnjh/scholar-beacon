---
name: literature-review
description: 智能审查采集的论文，识别并清理与研究方向无关的文献
metadata: {"openclaw":{"always":true}}
---

# 文献智能审查

审查 `data.md` 中采集到的论文，利用你的理解能力判断哪些与用户的研究方向无关，协助用户清理。

## 审查流程

### 第一步：了解研究方向

读取关键词文件，理解用户关注的研究领域：

```bash
cat ~/.openclaw/workspace/literature/keywords.md
```

### 第二步：读取采集数据

```bash
cat ~/.openclaw/workspace/literature/data.md
```

### 第三步：逐篇判断相关性

对 data.md 中的每篇论文，根据标题、作者、来源等信息，判断它与用户关键词所代表的研究方向是否相关。

**判断标准：**
- **相关**：标题明确涉及关键词所指的研究领域（如关键词是"generative recommendation"，推荐系统+生成模型的论文就是相关的）
- **边缘相关**：主题相近但不是核心方向（如关键词是"LLM4Rec"，一篇纯 LLM 论文没提推荐系统）
- **无关**：完全不沾边（如物理学、纯数学、生物医学、地球科学等论文混入了 CS 搜索结果）

### 第四步：向用户汇报

将审查结果分组展示：

```
📋 文献审查报告

🔍 关键词：generative recommendation, LLM4Rec, ...

✅ 相关论文（X 篇）：
1. 论文标题 — 简述相关原因

⚠️ 边缘相关（X 篇）：
1. 论文标题 — 简述为何边缘

❌ 建议移除（X 篇）：
1. 论文标题 [ID] — 简述为何无关
2. ...

请确认是否移除标记为 ❌ 的论文？
```

### 第五步：执行清理

用户确认后，调用清理脚本：

```bash
export PATH=$HOME/.local/bin:$PATH
cd ~/.openclaw/skills/literature-helper
uv run python3 cleanup-irrelevant.py \
  --data-file ~/.openclaw/workspace/literature/data.md \
  --seen-file ~/.openclaw/workspace/literature/seen-ids.md \
  --ids "ID1" "ID2" "ID3"
```

如果用户说"也把边缘相关的删了"，把那些 ID 也加上。

### 可选：保留 seen-ids

如果用户说"删了但别再搜到"，加 `--keep-seen` 参数：

```bash
uv run python3 cleanup-irrelevant.py ... --keep-seen
```

这样 seen-ids.md 中的记录不会被删除，下次采集不会再搜到这些论文。

## 响应用户指令的方式

| 用户说 | 你做 |
|--------|------|
| "审查一下最近的文献" | 执行完整审查流程 |
| "删掉无关的论文" | 审查 → 展示无关论文 → 确认后清理 |
| "把物理学的论文都删了" | 从 data.md 筛选物理学论文 → 确认后清理 |
| "只保留推荐系统相关的" | 审查 → 把非推荐系统的标记为移除 → 确认后清理 |
| "这些论文哪些值得看" | 审查 → 按相关性排序推荐 |

## 注意事项

- **必须等用户确认后才执行清理**，不要自动删除
- 如果论文数量很多（>50），可以先按日期分批审查
- 审查结果要简洁，每篇论文一行，说明判断理由
- 清理后用 `wc -l` 展示剩余数据量
