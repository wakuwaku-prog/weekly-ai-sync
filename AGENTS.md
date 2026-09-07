# AGENTS.md — 每周信息同步系统

## 项目目标

搭建一个“每周信息同步”系统。每周自动/半自动抓取、筛选、总结信息，并以静态网站的形式呈现。

当前先实现第一期：**AI 领域每周热点同步**。

第二期（后续再展开）：**植物外泌体方向文献同步**。

---

## 已确定方案

- **呈现方式**：静态网站（本机先通过脚本生成，后续可部署到 GitHub Pages / Cloudflare Pages / Vercel）
- **触发方式**：每周末由 Agent 执行生成（不依赖云端定时任务）
- **信息来源**：中英文都要，覆盖一手英文源（GitHub / arXiv / HF / HN / Reddit）和中文科技媒体
- **输出语言**：中文

## 第一期内容范围：AI 每周热点

每周覆盖：

1. **AI 热点**
   - 好用的 Skill、插件、功能
   - 新的 Agent / MCP / 工具链工作流
   - 重要的模型、产品、框架发布

2. **GitHub 上关于 AI 的近期热门**
   - GitHub Trending 中的 AI 相关仓库
   - 近期高 Star / 高关注 AI 项目
   - 说明用途、技术栈、为什么值得关注

3. **AI 助力生物医药科研**
   - 新的工作流、Skill、工具、平台
   - AI 用于结构生物学 / 药物设计 / 组学分析 / 文献挖掘 / 实验自动化等方向
   - 观察是否有可以复用到自己科研工作中的内容

**每期输出**：
- 本周热点总结（中文）
- 与用户工作相关的“可应用建议”
- 信息来源链接
- 下周关注点

---

## 用户画像（初步假设，待确认）

- 用户科研方向：生物医药；重点关注植物外泌体/植物囊泡及其医学应用（第二期会细化）
- 使用 AI 的目的：提升文献调研、实验设计、数据分析和日常工作流效率
- “可应用建议”将优先围绕上述方向筛选

## 目录结构

```text
AGENTS.md
weekly/
  YYYY-MM-DD-ai-weekly.md     # 每期周报
scripts/
  build_site.py               # Markdown 周报 -> 静态网站
site/
  index.html                  # 生成后的站点入口（可部署）
```

## 建议执行流程

1. **收集**
   - 使用联网搜索与聚合源抓取本周内容
   - 候选来源：
     - GitHub Trending、GitHub Topic（AI、bioinformatics、drug-discovery）
     - Hugging Face Daily Papers / Trending Models
     - Hacker News、Reddit（r/MachineLearning、r/bioinformatics、r/LLMDevs）
     - arXiv（cs.AI、cs.LG、q-bio）、PubMed / bioRxiv
     - AI Agent / MCP / 插件生态
     - 中文科技媒体（机器之心、量子位等）
   - 可用 Skill：`agent-reach`、`exa-search`、`parallel-web`、`github-research`、`academic-search`、`literature-search`、`pubmed` 等
   - 回退数据源（试运行已验证）：`gh search repos` / GitHub Trending 页面、Hugging Face `/api/trending` 与 `/api/daily_papers`、arXiv API、PubMed E-utilities、HN Algolia

2. **筛选与去重**
   - 保留“有实际使用价值”或“对科研工作有启发”的内容
   - 过滤纯营销/低信息量内容

3. **总结**
   - 每期生成 Markdown 周报到 `weekly/YYYY-MM-DD-ai-weekly.md`
   - 周报结构：
     ```markdown
     # AI 每周热点同步（YYYY-MM-DD ~ YYYY-MM-DD）

     ## 1. AI 热点动态
     ## 2. 好用的 Skill / 插件 / 功能
     ## 3. GitHub 热门 AI 项目
     ## 4. AI + 生物医药科研
     ## 5. 可应用到我自己工作的建议
     ## 6. 下周关注
     ## 7. 附录：全部链接
     ```

4. **生成静态网站**
   - 运行 `python scripts/build_site.py`
   - 输出到 `site/`，可在浏览器直接打开 `site/index.html`

5. **每周执行节奏**
   - 周五/周末：Agent 抓取并生成周报
   - 生成后向用户汇报要点和网站位置
   - 根据用户反馈调整来源和筛选偏好

---

## 工具与配置备忘

- **Agent Reach**：已安装到 `C:\Users\epiph\.agent-reach-venv\Scripts\agent-reach.exe`（v1.5.0），已加入用户 PATH；若当前进程不识别，请用完整路径。
- **mcporter + Exa MCP**：已全局安装 mcporter，Exa 已注册到 `C:\Users\epiph\.mcporter\mcporter.json`，并配置了 `Accept: application/json, text/event-stream` 请求头（本环境必需）。
  - 搜索示例：`mcporter call exa.web_search_exa query="..." numResults=5`
  - 读网页示例：`mcporter call exa.web_fetch_exa urls='["https://..."]'`
- **内置 web_search 工具**：目前仍需要 `DEEPSEEK_API_KEY`。两种方式：
  1. 在启动 DSH / 当前终端前设置环境变量 `DEEPSEEK_API_KEY`；
  2. 在 DSH Web UI（默认 http://127.0.0.1:3080）的 Models / 凭据页面填写该 Key。
- DSH 原生还支持其他搜索 API：`web-search-exa`（需 `EXA_API_KEY`）和 `web-search-perplexity`（需 `PERPLEXITY_API_KEY`），可通过配置 overlay 切换 `searchProvider`。
- 暂时不依赖内置 web_search 也可以工作：Exa MCP 搜索已经通过 mcporter 可用，无需额外 Key。
- **yt-dlp**：已补 `--js-runtimes node` 配置。
- **Agent Reach 全渠道安装状态（2026-09-07）**：
  - ✅ 可用：GitHub、YouTube、V2EX、RSS、Exa、Jina 网页阅读、B站（bili-cli 基础搜索/热门/排行）
  - ✅ 已安装但待配置：OpenCLI（需装 Chrome 扩展）、twitter-cli（需 Cookie）、小红书/雪球（需 Cookie）、小宇宙（需 Groq Key）
  - 手动步骤：
    1. 安装 OpenCLI 扩展：https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk
    2. 需要时配置登录：`agent-reach configure twitter-cookies`、`agent-reach configure xhs-cookies`、`agent-reach configure --from-browser chrome --platform xueqiu`
    3. 小宇宙需要免费 Groq Key：`agent-reach configure groq-key`（去 https://console.groq.com 获取）

## 邮件自动推送配置

- **自动抓取脚本**：`scripts/generate_auto_report.py`（无 Key 聚合 GitHub Trending / HF / arXiv / PubMed，生成 `auto-*.md`）
- **邮件发送脚本**：`scripts/send_email.py`（QQ SMTP，SSL 465）
- **自动工作流**：`.github/workflows/auto-weekly-email.yml`（每周日 09:00 北京时间自动运行）
- 需要配置 GitHub Secrets：
  - `SMTP_USER` = `epiphany_0421@qq.com`
  - `SMTP_AUTH_CODE` = QQ 邮箱授权码（不是登录密码）
  - `MAIL_TO` = `epiphany_0421@qq.com`
- QQ 邮箱开启方法：设置 → 账户 → 开启 SMTP 服务 → 生成授权码
- 当前待办：收到用户的 SMTP 授权码后，配置 Secret 并测试发送

## 当前状态与待办

- [x] 确定呈现方式：静态网站
- [x] 确定触发方式：每周末由 Agent 执行
- [x] 确定信息来源：中英文都要
- [x] 搭建基础静态站生成脚本
- [x] 生成第一期 AI 周报（2026-09-07 试运行，已补中文来源）
- [x] 创建 GitHub 仓库 `weekly-ai-sync`（https://github.com/wakuwaku-prog/weekly-ai-sync），已改为公开
- [x] 部署到 GitHub Pages：https://wakuwaku-prog.github.io/weekly-ai-sync/
- [ ] 确定“可应用到自己工作中”的判断标准（用户工作背景：生物医药科研为主）
- [ ] 第二期“植物外泌体文献”的具体检索方向，等待用户补充

---

## 约定

- 默认输出语言：中文
- 所有周报先落盘为 Markdown，保留可追溯来源
- 内容强调“可应用性”，不只是罗列信息
- 后续如有新的决定，优先更新本文件同步