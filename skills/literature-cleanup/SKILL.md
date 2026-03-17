---
name: literature-cleanup
description: 清理文献工作流数据文件（data.md、seen-ids.md、seen-pushed-ids.md、pending-push-ids.md）
metadata: {"openclaw":{"always":true}}
---

# 文献数据清理

清理 `~/.openclaw/workspace/literature/` 下的工作流数据文件。

## 数据文件说明

| 文件 | 作用 | 清空影响 |
|------|------|----------|
| `data.md` | 采集到的论文列表 | 日报推送无数据，需重新采集 |
| `seen-ids.md` | 已搜索过的论文 ID | 下次采集会重新搜到之前的论文 |
| `seen-pushed-ids.md` | 已推送过的论文 ID | 已推送的论文会被再次推送 |
| `pending-push-ids.md` | 待确认推送的 ID | 清除未确认的推送状态 |
| `archive-*.md` | data.md 的历史归档 | 丢失历史数据 |

## 操作指南

### 全部重置（推荐用于测试后清理）

清空所有数据文件，回到初始状态：

```bash
cd ~/.openclaw/workspace/literature
echo -n > data.md
echo -n > seen-ids.md
echo -n > seen-pushed-ids.md
echo -n > pending-push-ids.md
rm -f archive-*.md
```

清理后用 `ls -la` 确认文件状态。

### 只清空采集数据（保留推送记录）

```bash
cd ~/.openclaw/workspace/literature
echo -n > data.md
echo -n > seen-ids.md
rm -f archive-*.md
```

### 只清空推送记录（重新推送已有数据）

```bash
cd ~/.openclaw/workspace/literature
echo -n > seen-pushed-ids.md
echo -n > pending-push-ids.md
```

### 删除 data.md 中的特定条目

用户说"删掉 data.md 中关于 XXX 的论文"时，用 `sed` 删除匹配行：

```bash
sed -i '/关键词/d' ~/.openclaw/workspace/literature/data.md
```

### 删除 seen-ids.md 中的特定 ID

让某篇论文可以被重新搜索到：

```bash
sed -i '/arxiv:XXXX.XXXXX/d' ~/.openclaw/workspace/literature/seen-ids.md
```

## 注意事项

- **操作前先展示当前文件内容**，让用户确认要清理的范围
- **清理 seen-ids.md 会导致下次采集重新搜到这些论文**，这通常是期望的行为
- **keywords.md 不在清理范围内**，关键词由 `literature-keywords` Skill 管理
- 如果用户只说"清理数据"，默认执行全部重置
