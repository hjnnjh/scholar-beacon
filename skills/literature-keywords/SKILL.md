---
name: literature-keywords
description: 管理文献搜索关键词（查看、添加、删除、替换）
metadata: {"openclaw":{"always":true}}
---

# 文献关键词管理

管理 `~/.openclaw/workspace/literature/keywords.md` 中的搜索关键词。这些关键词被文献采集定时任务用于搜索 Semantic Scholar 和 arXiv。

## 关键词文件格式

- 路径：`~/.openclaw/workspace/literature/keywords.md`
- 每行一个关键词
- `#` 开头的行为注释
- 空行跳过

## 操作指南

当用户要求管理关键词时，按以下方式操作：

### 查看当前关键词

```bash
cat ~/.openclaw/workspace/literature/keywords.md
```

### 添加关键词

用户说"添加关键词 XXX"或"我想关注 XXX 方向"时，将关键词追加到文件末尾：

```bash
echo "新关键词" >> ~/.openclaw/workspace/literature/keywords.md
```

支持一次添加多个：

```bash
printf '%s\n' "关键词1" "关键词2" "关键词3" >> ~/.openclaw/workspace/literature/keywords.md
```

### 删除关键词

用户说"删除关键词 XXX"或"不再关注 XXX"时，从文件中移除匹配行：

```bash
sed -i '/^要删除的关键词$/d' ~/.openclaw/workspace/literature/keywords.md
```

### 替换关键词

用户说"把 XXX 改成 YYY"时：

```bash
sed -i 's/^旧关键词$/新关键词/' ~/.openclaw/workspace/literature/keywords.md
```

### 清空并重写

用户说"只保留这些关键词"时，重写整个文件：

```bash
cat > ~/.openclaw/workspace/literature/keywords.md << 'EOF'
# 搜索关键词（每行一个，# 注释）
关键词1
关键词2
EOF
```

## 注意事项

- 每次操作后用 `cat` 展示修改后的完整内容，让用户确认
- 关键词应该是英文学术搜索词（Semantic Scholar 和 arXiv 使用英文搜索效果最好）
- 如果用户给出中文研究方向，帮助翻译为合适的英文学术关键词
- 每个关键词会分别搜索两个来源（Semantic Scholar + arXiv），关键词太多会增加采集时间
- 建议保持 3-10 个关键词
