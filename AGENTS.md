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
- **植物囊泡文献追踪**：`scripts/literature_digest.py`（多来源：PubMed / Europe PMC / OpenAlex / Semantic Scholar + LLM 总结，输出到 `literature/`）
- **文献汇总报告**：`scripts/literature_summary.py`（读取 `literature/data/papers.jsonl`，生成累计汇总报告）
- **论文库页面**：`site/library.html`（列出 `literature/data/papers.jsonl` 中所有文献，支持标题/摘要搜索与原文跳转）
- **邮件发送脚本**：`scripts/send_email.py`（QQ SMTP，SSL 465）
- **自动工作流**：`.github/workflows/auto-weekly-email.yml`（每周日 09:00 北京时间自动运行）
- 需要配置 GitHub Secrets：
  - `SMTP_USER` = `epiphany_0421@qq.com`
  - `SMTP_AUTH_CODE` = QQ 邮箱授权码（不是登录密码）
  - `MAIL_TO` = `epiphany_0421@qq.com`
- QQ 邮箱开启方法：设置 → 账户 → 开启 SMTP 服务 → 生成授权码
- 已配置 SMTP Secrets：`SMTP_USER`、`SMTP_AUTH_CODE`、`MAIL_TO`，测试邮件发送成功
- **LLM 可选增强（已配置）**：
  - `scripts/llm.py` 提供 LLM 调用；自动报告会生成「本周速览与重点推荐（AI 生成）」板块
  - GitHub Secrets：`LLM_PROVIDER=deepseek`、`LLM_API_KEY`、`LLM_MODEL=deepseek-chat`
  - 自动邮件默认发送 LLM 增强后的 `auto-*.md` 摘要；人工精编周报仍保留在网站
  - 未配置 LLM Key 时，自动报告退化为原始聚合，不影响发送

## 当前状态与待办

- [x] 确定呈现方式：静态网站
- [x] 确定触发方式：每周末由 Agent 执行
- [x] 确定信息来源：中英文都要
- [x] 搭建基础静态站生成脚本
- [x] 生成第一期 AI 周报（2026-09-07 试运行，已补中文来源）
- [x] 创建 GitHub 仓库 `weekly-ai-sync`（https://github.com/wakuwaku-prog/weekly-ai-sync），已改为公开
- [x] 部署到 GitHub Pages：https://wakuwaku-prog.github.io/weekly-ai-sync/
- [ ] 确定“可应用到自己工作中”的判断标准（用户工作背景：生物医药科研为主）
- [x] 植物囊泡文献追踪 MVP（多来源 + LLM 总结 + 汇总报告，已上线网站与邮件）
- [ ] 植物外泌体文献检索方向可继续细化（皮肤/ECM/胶原/纤维化等关键词可按需调整）

---

## 约定

- 默认输出语言：中文
- 所有周报先落盘为 Markdown，保留可追溯来源
- 内容强调“可应用性”，不只是罗列信息
- 后续如有新的决定，优先更新本文件同步

---

# 项目二：旅行规划网站（travel-site）

> 详细方案见 `travel-site/PLAN.md`（调研参考 / 构建方案 / 数据模型 / 风险对策），本文档只同步“执行状态与操作记录”。

## 项目目标

用户告知目的地/天数/日期/出发地/人数/预算/偏好 → Agent 调研（小红书 ≥20 帖 + 视频 ≥10 个含字幕评论）→ 整理攻略（行程/酒店位置/交通/特色/美食/项目）→ 高德地图规划线路 + 一键导航 → 生成网站（栏目：行程、景点指南、当地特色体验、餐饮指南、出发前准备、旅行提醒）。

## 关键决策（已定）

- 呈现：静态站（Python 脚本生成 → GitHub Pages/Vercel），与项目一体系一致，**不依赖常驻后端**
- 高德三层：Web 服务预计算路线（`/direction/driving` 等）+ 前端 JS API 画线 + `uri.amap.com/navigation` 一键导航按钮（写入收藏夹官方不支持）
- 参考项目：`hiyeshu/trip-map-builder`（Agent Skill 范式）、`tutu-zzz/zhilv-yuntu`（高德全链路 + LLM 只输出 POI ID、服务层回填真实数据——防幻觉）
- 数据模型：`data/trips/trip-<目的地>-<日期>.json`（meta/sources/pois/hotels/restaurants/experiences/itinerary/tips），来源可追溯（sourceIds）

## Skill / API / 工具配置状态

| 项 | 状态 |
|---|---|
| agent-reach v1.5.0 | ✅ 已装（GitHub/B站/YouTube/Exa 可用） |
| video-to-subtitle-summary | ✅ 已装，**待配 AI-Douyin/TikHub Key**（抖音/小红书视频解析） |
| opencli 1.8.7 | ✅ 已装，**待装 Chrome 扩展**（小红书调研卡点，Extension not connected） |
| bili-cli 0.6.2 / yt-dlp / ffmpeg | ✅ 可用（B站字幕需登录：`bili login` 或 cookie） |
| 高德 Key（Web服务+JS） | ✅ 已配置 `travel-site/.env`（gitignore 保护，勿提交） |
| exa-search (mcporter) | ✅ 可用 |
| 待补 | AI-Douyin Key / TikHub Token、OpenCLI 扩展或 xhs Cookie、B站登录、部署域名白名单 |

## 执行进度

- [x] 2026-09-08 第一轮：方案 + 配置 + 调研种子 + 地图管线 + 网站初版（详见下方记录）
- [x] 2026-09-08 第二轮：真实餐厅/酒店 POI、天气、特色体验栏目、B站转写启动
- [x] 2026-09-08 第三轮：**小红书 79 篇定向采集突破**、行程规范化、来源达标（16视频+79帖）
- [ ] B站 5 视频转写完成 → 写完整攻略 `guides/厦门攻略.md`
- [ ] 前置信息补全（船票时刻、地铁时刻）→ 部署 GitHub Pages/Vercel + 高德域名白名单

## 操作记录（每次执行后追加）

### 2026-09-08 第十三轮（历史版存档 + 手机端地图适配）
- **历史版存档**：当前重设计版快照 → `travel-site/history/2026-09-08-ui-redesign-v1/`（index.html + README，commit dbfab82），Git tag `ui-redesign-2026-09-08` 已推送
- **手机端地图不显示的修复**（pilot_eval 实测定位）：
  - 根因：移动端用 `order:-1` 排地图置顶，但实测 computed order=-1 而渲染顺序不变（环境/浏览器对该写法不可靠），地图实际排在页面底部，手机上"看不到地图界面"
  - 改用 **grid-template-areas** 显式布局：桌面 `"content map"` / 移动 `"map" "content"`，不依赖 order；实测 754px 视口 mapTop=284 < contentTop=624 ✓
  - 容器 `min-height:320px` + `height:46vh`；高德脚本加载失败/未初始化时显示 `#mapnotice` 兜底提示（提示可仍点站导航）；初始化后延迟 resize 重绘
- 已推送：travel-site `4c6f668`、模板 `08af796`；AGENTS 本轮同步
- **提醒用户**：手机建议打开线上 https://wakuwaku-prog.github.io/travel-site/（file:// 或微信 WebView 某些版本可能受限）；高德 JS Key 安全域名需含 `wakuwaku-prog.github.io`
- 遗留：图片帖 OCR / 酒店价格核实 / 船班时刻（可选精修）

### 2026-09-08 第十二轮（前端整体重设计）
- 用户要求优化前端界面（frontend-design skill 指导），重写 HTML_TEMPLATE：
  - **设计系统「潮汐 × 闽南」**：海雾纸底 `#f7f9fb`（非奶油）/ 深海墨蓝 `#12303d` / 潮汐青主色 `#0e7490` / 落日珊瑚点缀 `#e5725c`；宋体标题（Noto Serif SC/Songti SC 回退）+ 系统无衬线正文
  - Hero 页头：大标题 + 副标题 + **meta chips**（游玩/日期/出发/人数/预算/偏好/节奏）+ 底部圆弧纸面过渡
  - 吸顶玻璃 tab 栏（backdrop-blur、移动端横向滚动）；**时间线式行程卡**（D1/D2/D3 徽章 + 主题 + 日期/区域/里程 + 竖向时间线 + 导航小按钮）
  - POI/酒店卡：渐变侧条、hover 轻抬、圆角标签；地图圆角 + **图例浮层**（当日路线/途经点/🏨住宿区域）；顺序导航栏玻璃化
  - 无障碍：focus-visible 轮廓、prefers-reduced-motion；移动端地图置顶吸顶 + 底部固定导航条
- 验证：DOM 快照确认 hero/meta/时间线/图例/住宿圈全部渲染，无占位符残留；travel-site `c69a43b`、模板 `fd73d92` 已推送
- 遗留：图片帖 OCR / 酒店价格核实 / 船班时刻（可选精修）

### 2026-09-08 第十一轮（住宿推荐改为区域级）
- 用户反馈：① 没看到「住宿推荐」栏目（已把栏目**上移到第 2 位**并本地/线上验证）；② 住宿推荐不应绑定具体酒店，要"推荐住哪个区域"
- 数据改为 **5 个区域推荐**（镇海路片区⭐ / 中山路·八市片区 / 环岛路·黄厝靠海片区 / 厦大·白城片区⭐ / 鼓浪屿·码头附近），各带区域坐标、radius、适合人群、价位、推荐理由、候选酒店示例、来源
- 网站：区域卡片（区域名/区位/适合谁/价位/理由/候选示例 + 导航/收藏）；地图用 **AMap.Circle 紫色范围圈** + 🏨 标记常显（可点击导航）
- 已推送：travel-site `9608f29`、模板 `9062b99`；AGENTS 本轮同步
- 遗留：图片帖 OCR / 酒店价格核实 / 船班时刻（可选精修）

### 2026-09-08 第十轮（新增「住宿推荐」栏目）
- 用户指出网站没有展示推荐住宿位置（数据里有 hotels，但无栏目）
- 新增「🏨 住宿推荐」栏目：酒店卡片（名称/区域/价格区间/推荐理由/来源链接 + 🧭高德导航 + ⭐收藏(poiId详情页)按钮）；地图**常显紫色 🏨 住宿标记**（不随每日路线清除、可点击导航）；模板模式回退补齐
- 本地+线上验证通过（2 家酒店卡片与地图标记）;travel-site `25a7c2a`、模板 `79d01a7` 已推送
- 遗留：图片帖 OCR / 酒店价格核实 / 船班时刻（可选精修）

### 2026-09-08 第九轮（研究：点位能否收藏进高德 + 面板精简）
- **用户要求**：① 保留 XML（KML/GPX 分日导出不动）；② 删掉「每日整体路线」区块；③ 研究能否把点位写进高德收藏夹
- **调研结论（官方文档核实）**：高德**不允许第三方静默写入个人收藏夹**（无公开 API）；官方可行路径 = **URI API「地点详情页」** `uri.amap.com/poidetail?poiid=xx&callnative=1` → 打开详情页 → 用户点 ⭐ 收藏（需登录，收藏同步多端，高德帮助中心确认）；另确认「轨迹导入」只解析轨迹线、丢弃地名
- **实现**：
  - 新增 `scripts/amap/poi_favorite.py`：为 pois/hotels/restaurants 带坐标的点反查高德 POI ID（place/around 就近 + place/text 匹配），厦门 20 个点回填成功（鼓浪屿 B0FFFYJ219 等）
  - 「📦 导入路线」面板= ① KML/GPX(分日) ② 逐段导航 ③ **📌 收藏进高德（25 个 ⭐ poi 详情页按钮）**；「每日整体路线」区块已删除
  - 模板仓库脚本与 README 已同步（README 增加 poi_favorite 步骤与官方收藏路径说明）
- 已推送：travel-site `baef55c`、模板 `3c047e6`
- **留给用户的手动步骤**：手机端点收藏按钮→高德详情页点星标收藏（逐点一次确认，官方唯一个人侧路径）
- 遗留：图片帖 OCR / 酒店价格 / 船班时刻（可选精修）

### 2026-09-08 第八轮（优化：带地名线路图 / 逐段导航 / 手机端）
- **用户反馈**：① 高德"轨迹导入"把 KML 当运动轨迹，只画一条线、不显示各景点地名（截图确认）；② 需要"每一段景点的线路图"而非只有起终点；③ 手机端导入麻烦、无法收藏地点/线路
- **方案**（不依赖高德收藏/轨迹导入）：
  - 本站「行程」页地图改为**逐日线路图**：每个景点加**编号圆点 + 名称标注**（AMap.Marker + AMap.Text），点击站点直接唤起高德导航；点地图/当天可切换天
  - 底部新增**「顺序导航」吸底栏**：列出当天所有站点 chips，点站开高德导航，含「上一站/下一站」逐步前进
  - 「📦 导入路线」面板新增**逐段导航**：每一段 `①景点 → ②景点` 各给一个带地名的 uri.amap.com 导航链接；并明确提示高德轨迹导入只显示路线不显示地名的局限
  - `export_routes.py` 生成**分日 KML/GPX**（`trip-xiamen-day<N>.kml/gpx`）+ 总文件；模板脚本已同步
  - 手机端：`@media(max-width:900px)` 地图**置顶吸顶**（42vh）
- 两个仓库已推送：travel-site `54028e8`、`c5d5aa3`；模板 `1134baa`；模板 README 补充说明
- **遗留**：高德不支持第三方写入收藏（官方限制），已通过"本站线路图 + 逐段导航"为用户提供替代；图片帖 OCR / 酒店价格 / 船班时刻（可选精修）

### 2026-09-08 第七轮（新需求：导入高德路线图 + 通用模板项目）
- **行程导入高德做成路线图**：新增 `scripts/amap/export_routes.py`——调用高德 direction API（extensions=all）取每段 polyline，生成 **KML / GPX / routes.json**（含每日路线线串 + 全部点位）；KML 可导入高德 App（我的→收藏→导入），GPX 供两步路/六只脚等；坐标 GCJ-02 说明已写入
- **网站新增「📦 导入路线」面板**（8 栏目）：KML/GPX 下载（部署在 site/export/）+ 高德导入步骤 + 每日整体路线（起终点 uri.amap.com 链接 + 二维码）；厦门站线上已生效（curl 验证）
- **通用模板仓库**：新建 **https://github.com/wakuwaku-prog/travel-planner-kit**（不含厦门数据）——通用版 README / SKILL.md（travel-research 技能）/ docs/schema.md / config.example.json / 脚本（build_site、route_fill、export_routes）/ CI workflow；空数据时 build_site 产出说明页（模板模式）；模板站 https://wakuwaku-prog.github.io/travel-planner-kit/ 已上线（HTTP 200）
- 厦门仓库补 README 指向模板仓库；本次改动均已 push（网络已恢复）
- **后续使用方式**：clone travel-planner-kit → .env 配高德 Key（一次）→ 按 SKILL.md 让 Agent 调研任意目的地 → 三步脚本 → push 即出站；无需再配置
- 遗留：图片帖 OCR / 酒店价格 / 船班时刻（可选精修，不阻塞）

### 2026-09-08 第六轮（目标完成）
- **B站转写 5/5 全部完成**：BV1dbyFBBE9X（厦门人眼中的厦门：笔山洞/龙头山寨郑成功练兵/叶氏麻糍/鲨鱼丸汤/皓月园）要点已合并 → 攻略 **v3 最终版**（`travel-site/guides/厦门-xiamen-攻略.md`）
- **目标达成核对**：小红书 79 篇定向采集 ✅（≥20）｜B站 16 视频种子 + 5 全量转写 ✅（≥10）｜攻略含行程/酒店/交通/特色/美食/项目 ✅｜高德 API 逐日实测路线 + 每点 `uri.amap.com` 一键导航 ✅｜网站 7 栏目（行程/景点/特色体验/餐饮/出发前准备/旅行提醒/资料来源）✅｜线上 https://wakuwaku-prog.github.io/travel-site/ ✅（curl 确认 105 条来源）｜GitHub 参考调研与 skill/API 规划 ✅（PLAN.md）
- **遗留（非阻塞，doc-only）**：① travel-site 仓库 2 个文档提交（攻略v3等）因 github.com 网络抖动未推送，网络恢复后补 `git push`；② 可选精修：图片帖 OCR、酒店价格核实、船班时刻
- 抖音渠道按用户指示跳过（付费）；上海→厦门大交通未做实时比价（示例估算）

### 2026-09-08 第五轮（目标续跑 — v2 重构上线）
- **v2 上线**：行程按 B站视频要点重构为「D1 老城+集美（中山路→八市→集美学村→十里长堤）/ D2 山海环岛（植物园→南普陀→猫街→沙坡尾→白城→演武大桥→环岛路→黄厝）/ D3 鼓浪屿全日（东渡码头→日光岩→菽庄→龙头路→八卦楼→大德记/皓月园）」，高德实测里程（23.7/55.2/13.8km）；线上 https://wakuwaku-prog.github.io/travel-site/ 确认更新（curl 验证）
- **转写 4/5 完成**：BBV1qJ4m1G7Gm（3天2晚，全套行程/美食/住宿）、BV1UCrVBRELu（保姆级：交通/厦大预约/鼓浪屿船票35vs80/集美一日）、BV1apDMBTEED（防坑）、BV12d3NzzEEE（本地人24小店：有生/乌糖/四里沙茶面、明月虾面、阿杰五香、真真海蛎煎等）→ 要点合并进 `data/research/bilibili_notes.md` 与攻略 v2
- **新增**：POI 19 个（新增八市/十里长堤/演武大桥/猫街/铁路公园/日光岩/菽庄/八卦楼/皓月园/东渡码头等）、体验 10 项、预约清单 6 条（船票提前10天/厦大访客中心/南普陀等）
- 脚本：新增 `scripts/restructure_trip.py`（先写文件再跑，避免 heredoc 中文截断问题）
- **下一步**：等第 5 个视频转写（BV1dbyFBBE9X）完成 → 攻略最终版；可选：图片帖 OCR、酒店价格核实、船班时刻

### 2026-09-08 第四轮（目标续跑 — 部署上线）
- **独立部署**：travel-site 拆为独立仓库 `https://github.com/wakuwaku-prog/travel-site`，GitHub Pages 上线 **https://wakuwaku-prog.github.io/travel-site/**（workflow 模式：CI 里跑 `scripts/build_site.py` 后 upload-pages-artifact）
- 部署要点：Pages 需先置为 `build_type=workflow`（DELETE+POST API）才能让 deploy-pages@v4 成功；git 需 `-c http.proxy=` 直连（本机 7890 代理未运行）
- **网站新增「📚 资料来源」面板**：105 条来源（16 视频 + 79 小红书）可回溯展示；线上验收通过（7 栏目 + 三天真实路线 + 导航按钮）
- 注意：**高德 JS API 安全域名白名单**需确认包含 `wakuwaku-prog.github.io`（当前渲染正常，如失效到高德控制台补域名）
- B站转写子代理仍在运行（5 个视频，CPU 较慢）；完成前保留目标激活
- **下一步**：转写完成后合并视频要点出完整攻略 → 补船票/时刻 → 迭代第二版网站

### 2026-09-08 第三轮（目标续跑 — 小红书突破）
- **小红书通道打通**（用户重登后）：search 可用，**8 个关键词采集 79 篇厦门定向帖**（`data/research/xhs_xiamen_seed.json`），含 3天2夜攻略/鼓浪屿导航/16家小破店/住宿推荐/citywalk 等高赞帖；`note <完整URL+xsec_token>` 可读正文（图文帖正文在图片中，仅标题/标签）
- **已精读并吸收**：《厦门3天2夜攻略》（镇海路住宿、十里长堤日落+免费演唱会、植物园西门+观光车、南普陀预约、朱富贵火锅预约、租电驴环岛骑行、防晒防蚊、海鲜问价）→ 已并入 hotel/experiences/tips
- **来源达标**：trip JSON sources = **16 视频 + 79 小红书**（105 条）
- **行程规范化**：每日 3-6 个停靠点（含真实餐厅），高德路线重算（D1 16.3km/79min，D2 51.7km/92min，D3 31.5km/74min）；站点 28.5KB 验收通过
- **B站转写**：子代理仍在运行（已完成 1/5：BV1qJ4m1G7Gm→18KB 文本；预计还需几十分钟）。用户选择：**等转写完成再出完整攻略**
- **Git**：音频/字幕已加入 .gitignore（避免 55MB 误入库），进度已提交 `4311faf`、`3f33929`
- **下一步**：转写完成后 → 写 `guides/厦门攻略.md` 完整版 → 前置信息补全 → 部署

### 2026-09-08 第二轮（目标续跑）
- **环境**：OpenCLI 扩展已连接（v1.0.24，ℹ️ 用户已装 Chrome）；faster-whisper venv 就绪；B站未登录但 **yt-dlp 可匿名下载音频**（绕开字幕登录墙成功）
- **决策**：抖音渠道**跳过**（AI-Douyin/TikHub 需付费），视频源以 B站为主（种子 16 个已够 ≥10）
- **转写**：后台子代理对 5 个关键 B站视频（≈69min）下载+转写中，产出 `data/raw/subtitles/*.txt` + `data/research/bilibili_notes.md`
- **数据**：高德 `place/text` 回填**真实餐厅/酒店**（老溪岸沙茶面、阿忠食坊、百赞姜母鸭、黄则和花生汤、延鹭客栈 等，含坐标/POI ID）；高德天气 API 写入真实预报到 `tips.weather`
- **网站**：新增「🎨 特色体验」栏目（6 栏目齐）；餐饮面板渲染真实餐厅卡片；`site/index.html` 26KB 浏览器验收通过
- **小红书卡点（仍未解）**：search 被 `AUTH_REQUIRED` 拦截、note 详情被风控 `SECURITY_BLOCK`；`login` 报 already_logged_in（Epiphany）但搜索仍失败；feed 通道**已验证可读 25 篇**（`data/research/xhs_feed_seed.json`，通用话题非厦门定向）
- **下一步**：等用户提供小红书分享链接或刷新登录态 → 定向采集 20 篇厦门帖；转写完成后提炼要点并入行程；部署

### 2026-09-08 第一轮
- GitHub 调研：锁定 trip-map-builder / zhilv-yuntu 等 10+ 参考项目；确认“行程导入高德线路”三种做法可行
- 落盘：`travel-site/PLAN.md`、`travel-site/SKILL.md`（travel-research 技能草稿）、`travel-site/config.example.json`
- 收集首次行程参数：**厦门 · 3天（2026-09-18~20 示例）· 上海出发 · 2人 · 舒适 · 自然风光/人文/美食/海岛 · 均衡**
- M0：高德 Key `2525e1…b7ba` 验证通过（geocode / place/text / driving 全 OK），写入 `travel-site/.env`
- M1 部分：`data/research/bilibili_seed.json`（16 个不重复 B站视频，去重按播放量排序）；`data/research/xiamen_pois_raw.json`（12 个 POI 坐标由高德补齐）
- M2：`travel-site/scripts/amap/route_fill.py` 打通——三天逐日驾车路线真实距离/耗时已回写 trip JSON（D1 12.42km/64min，D2 45.16km/82.5min，D3 23.04km/47.2min）
- M3：`travel-site/scripts/build_site.py` → `travel-site/site/index.html`（自包含 18KB）：五栏目 tab + 每日时间轴 + 高德 JS 地图 + 每 POI「高德导航」按钮；浏览器验收通过（file:// 打开）
- 待用户配合（卡点）：① OpenCLI Chrome 扩展安装或 `agent-reach configure xhs-cookies`；② AI-Douyin/TikHub Key；③ 可选 `bili login`

## 执行同步约定

- **每轮执行结束后，将“做了什么 / 改了什么 / 卡在哪 / 下一步”追加到本文件“操作记录”**，并同步更新“执行进度”勾选框
- 配置/凭据只写引用不写明文（Key 存 `travel-site/.env`）；来源链接必须可追溯
- 出错与重试链也记录（如 B站 GBK 编码、yt-dlp cookie 锁、小红书登录墙）