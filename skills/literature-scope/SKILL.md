---
name: literature-scope
description: 管理文献搜索范围（OpenAlex 学科过滤、arXiv 类别限制）
metadata: {"openclaw":{"always":true}}
---

# 文献搜索范围管理

管理 `~/.openclaw/workspace/literature/scope.conf` 中的搜索范围配置。控制文献采集从哪些学科/类别搜索。

## 配置文件

- 路径：`~/.openclaw/workspace/literature/scope.conf`
- 格式：每行 `key=value`，`#` 开头为注释
- 不存在时使用默认值（Computer Science）

## 配置项

### openalex_filter

OpenAlex API 的 filter 参数，控制搜索的学科范围。

常用 OpenAlex Concept ID：

| 学科 | Concept ID | filter 值 |
|------|-----------|-----------|
| Computer Science | C41008148 | `concepts.id:C41008148` |
| Mathematics | C33923547 | `concepts.id:C33923547` |
| Physics | C121332964 | `concepts.id:C121332964` |
| Engineering | C127413603 | `concepts.id:C127413603` |
| Biology | C86803240 | `concepts.id:C86803240` |
| Medicine | C71924100 | `concepts.id:C71924100` |
| Economics | C162324750 | `concepts.id:C162324750` |
| Psychology | C15744967 | `concepts.id:C15744967` |

多学科用 `|` 分隔：`concepts.id:C41008148|concepts.id:C33923547`

也可加年份过滤：`concepts.id:C41008148,publication_year:>2020`

留空则不限制学科。

### arxiv_categories

arXiv 搜索限制的类别，逗号分隔。

常用 arXiv CS 类别：

| 类别 | 说明 |
|------|------|
| cs.IR | Information Retrieval（信息检索） |
| cs.AI | Artificial Intelligence（人工智能） |
| cs.LG | Machine Learning（机器学习） |
| cs.CL | Computation and Language（NLP） |
| cs.CV | Computer Vision（计算机视觉） |
| cs.RO | Robotics（机器人） |
| cs.SE | Software Engineering（软件工程） |
| cs.DB | Databases（数据库） |
| cs.CR | Cryptography and Security（安全） |
| cs.DC | Distributed Computing（分布式） |
| stat.ML | Machine Learning (Statistics)（统计ML） |
| eess.SP | Signal Processing（信号处理） |
| q-bio | Quantitative Biology（定量生物） |

留空则搜索全站（不推荐，会混入大量无关论文）。

## 操作指南

### 查看当前配置

```bash
cat ~/.openclaw/workspace/literature/scope.conf
```

### 修改搜索范围

根据用户要求重写配置文件：

```bash
cat > ~/.openclaw/workspace/literature/scope.conf << 'EOF'
# 文献搜索范围配置
# OpenAlex 学科过滤（留空不限制）
openalex_filter = concepts.id:C41008148

# arXiv 类别限制（逗号分隔，留空搜索全站）
arxiv_categories = cs.IR, cs.AI, cs.LG, cs.CL
EOF
```

### 示例场景

**用户："加上计算机视觉"**
→ 在 arxiv_categories 中加入 `cs.CV`

**用户："我还想看 NLP 和机器学习的论文"**
→ 确认 `cs.CL` 和 `cs.LG` 已在列表中

**用户："搜索范围改成生物信息学"**
→ openalex_filter 改为 `concepts.id:C86803240`，arxiv_categories 改为 `q-bio`

**用户："不限制学科"**
→ openalex_filter 留空，arxiv_categories 留空（提醒用户可能会搜到大量无关论文）

**用户："只搜 arXiv 不搜 OpenAlex"**
→ 这个通过 cron job 的 `--source arxiv` 参数控制，不在 scope.conf 中，需要修改 cron job

## 注意事项

- 修改后展示完整配置让用户确认
- 范围太宽会导致大量无关论文，提醒用户
- 范围太窄可能漏掉相关论文，建议适当宽松
- 配置变更立即生效（下次采集时读取）
