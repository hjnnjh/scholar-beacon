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
git clone https://github.com/huangjinnan/scholar-beacon.git
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

## 7. 配置 Cron Jobs

参考 examples/cron-jobs.json 中的示例，在 ~/.openclaw/cron/jobs.json 中添加三个定时任务。
注意：需要停止 Gateway 后编辑 jobs.json，编辑完成后重启。
push-verify 任务中的 push-job-id 需要替换为 daily-push 任务的实际 ID。

## 8. 清理

rm -rf /tmp/scholar-beacon

## 9. 验证

openclaw skills list --eligible | grep literature

安装完成后告诉我结果。
```

---

## Notes

- If your server is NOT behind a proxy, remove all `https_proxy` / `http_proxy` prefixes.
- The Zotero integration is optional. Without it, the workflow still collects and pushes papers — just without Zotero library sync.
- Cron job delivery channel (Telegram/Discord) needs to be configured based on your setup.
