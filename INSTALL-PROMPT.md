# One-Click Install Prompt for LLM Agent

Copy the following prompt and send it to your OpenClaw agent to install Scholar Beacon:

---

```
请帮我安装 Scholar Beacon 文献自动化工作流。按以下步骤执行：

## 1. 安装 uv（如未安装）

which uv || (https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890 curl -LsSf https://astral.sh/uv/install.sh | sh)
export PATH=$HOME/.local/bin:$PATH

## 2. 下载仓库

cd /tmp
git clone https://github.com/hjnnjh/scholar-beacon.git
cd scholar-beacon

## 3. 部署脚本和 Skills

# 核心脚本
mkdir -p ~/.openclaw/skills/literature-helper
cp scripts/*.py scripts/pyproject.toml ~/.openclaw/skills/literature-helper/
cp skills/literature-helper/SKILL.md ~/.openclaw/skills/literature-helper/

# 管理 Skills
for skill in literature-keywords literature-zotero literature-review literature-cleanup literature-scope; do
  mkdir -p ~/.openclaw/skills/$skill
  cp skills/$skill/SKILL.md ~/.openclaw/skills/$skill/
done

## 4. 创建数据目录和配置

mkdir -p ~/.openclaw/workspace/literature
cp examples/keywords.md ~/.openclaw/workspace/literature/
cp examples/scope.conf ~/.openclaw/workspace/literature/

## 5. 安装 Python 依赖

cd ~/.openclaw/skills/literature-helper
https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890 uv sync

## 6. 配置 Zotero API

请问用户获取以下信息，然后写入 openclaw.json 的 skills.entries：
- ZOTERO_API_KEY（从 https://www.zotero.org/settings/keys 获取）
- ZOTERO_LIBRARY_ID（同一页面显示的 userID）
- ZOTERO_COLLECTION_KEY（可选）

需要为 literature-helper 和 literature-zotero 两个 skill 都配置 env。

## 7. 配置推送渠道

询问用户希望通过哪个渠道接收文献日报推送（Discord 或 Telegram），然后获取以下信息：

### 如果用户选择 Discord：
- 询问用户要推送到哪个 Discord 频道
- 获取频道 ID（用户可以在 Discord 中右键频道 → 复制频道 ID）
- 确认该频道已在 openclaw.json 的 channels.discord.guilds.<guild_id>.channels 中设置 allow: true
- 如果频道不在 allowlist 中，帮用户添加

### 如果用户选择 Telegram：
- 询问用户的 Telegram chat ID
- 确认 openclaw.json 中 channels.telegram.enabled 为 true

记录用户选择的渠道和目标 ID，用于下一步配置 Cron Jobs。

## 8. 配置 Cron Jobs

参考 examples/cron-jobs.json 中的示例，在 ~/.openclaw/cron/jobs.json 中添加三个定时任务。

注意事项：
- 需要停止 Gateway 后编辑 jobs.json，编辑完成后重启
- push-verify 任务中的 push-job-id 需要替换为 daily-push 任务的实际 ID
- 每个 job 的 delivery 字段需要根据用户在步骤 7 中选择的渠道配置：
  - Discord: {"mode": "announce"/"silent", "channel": "discord", "to": "<频道ID>"}
  - Telegram: {"mode": "announce"/"silent", "channel": "telegram", "to": "<chat_id>"}
- literature-collect 和 literature-push-verify 使用 silent 模式
- literature-daily-push 使用 announce 模式

## 9. 清理

rm -rf /tmp/scholar-beacon

## 10. 验证

openclaw skills list --eligible | grep literature

安装完成后告诉我结果。
```

---

## Notes

- If your server is NOT behind a proxy, remove all `https_proxy` / `http_proxy` prefixes.
- The Zotero integration is optional. Without it, the workflow still collects and pushes papers — just without Zotero library sync.
- Supported push channels: **Discord** (recommended) and **Telegram**. The agent will ask you to choose during installation.
