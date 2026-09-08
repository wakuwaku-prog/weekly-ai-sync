# 旅行规划网站 — 构建方案与实施规划

> 状态：规划阶段（v1，2026-09-08）
> 目标：用户说出"想去哪、玩几天、几号出发、从哪出发、几个人、什么预算、偏好什么"→ Agent 调研（小红书/B站/抖音）→ 生成攻略 + 高德地图线路 + 一键导航 → 可视化网站。

---

## 1. GitHub 参考项目调研结论

### 1.1 最关键的两个参考

| 项目 | Stars | 技术栈 | 为什么值得参考 |
|---|---|---|---|
| **[hiyeshu/trip-map-builder](https://github.com/hiyeshu/trip-map-builder)** ⭐212 | HTML/JS | Agent Skill：**规划 → 大众点评/小红书调研 → 单文件交互式地图页**。Leaflet 地图 + 按天时间轴卡片 + **高德 App scheme 一键唤起导航** + 小红书/大众点评链接 | 与我们的需求 90% 重合，是"Agent 调研 + 静态地图页 + 导航跳转"的最短路径范本 |
| **[tutu-zzz/zhilv-yuntu](https://github.com/tutu-zzz/zhilv-yuntu)** ⭐304 | FastAPI + LangChain + ChromaDB + Vue3 + Redis | 完整产品链路：本地 RAG 攻略检索、高德 Web 服务（`/geocode/geo`、`/config/district`、`/place/text`、`/direction/driving`）补坐标/POI/路线，**高德 JS API 虚线箭头路线可视化**，天气、预算拆分、Markdown/PDF 导出 | 回答了"高德线路怎么做"，且其失败降级、缓存、真实性约束（LLM 只输出 POI ID，服务层回填真实数据）的思路可直接抄 |

### 1.2 其他有价值的参考

| 项目 | Stars | 参考点 |
|---|---|---|
| [1sdv/TripStar](https://github.com/1sdv/TripStar)（旅途星辰） | ⭐2224 | Vue AI 文旅应用，一站式攻略的产品形态与栏目设计 |
| [Cooosin/AiClient](https://github.com/Cooosin/AiClient) | ⭐146 | **MCP 服务组合**：小红书搜索 + 高德地图 + 和风天气，即"skill/工具编排"思路 |
| [Ikaros-521/LX_SkyRoam_Agent](https://github.com/Ikaros-521/LX_SkyRoam_Agent) | ⭐123 | AI 攻略生成系统的工作流拆分 |
| [SuperLuJC/PlannerAgent](https://github.com/SuperLuJC/PlannerAgent) | ⭐64 | LangGraph + LangChain 的 Agent 状态机（对话→规划→细化） |
| [alexlmoney83-oss/travel-planning-agent](https://github.com/alexlmoney83-oss/travel-planning-agent) | ⭐51 | LangGraph + MCP + RAG 分层 |
| [Heisenberg-Gao/TravelBird](https://github.com/Heisenberg-Gao/TravelBird) | ⭐22 | 大模型 MCP 旅行助手 |
| [mcxiaoxiao/xiaohongshuCrawler](https://github.com/mcxiaoxiao/xiaohongshuCrawler)、[yangsijie666/xiaohongshu-crawler](https://github.com/yangsijie666/xiaohongshu-crawler) | — | 小红书爬虫兜底方案（**优先用 agent-reach/OpenCLI，爬虫仅作回退**） |
| [ElemeFE/vue-amap](https://github.com/ElemeFE/vue-amap)、[ElemeFE/react-amap](https://github.com/ElemeFE/react-amap) | — | 高德地图的框架封装，若未来上 Vue/React 可参考 |

### 1.3 "行程能否导入高德成线路"——结论

| 需求 | 是否支持 | 实现方式 |
|---|---|---|
| 网页内画出每日路线（含途经点） | ✅ | 高德 **JS API** `AMap.Driving / AMap.Walking / AMap.Transfer / AMap.Polyline`，`AMap.Driving` 原生支持 waypoints；无需后端，前端直接动态重算 |
| 一键跳转高德 App 导航 | ✅ | 高德 **URI API**：`https://uri.amap.com/navigation?from=..&to=..&mode=car&callnative=1`；或 **App scheme**：`androidamap://navi?..`、`iosamap://path?..`（trip-map-builder 已验证） |
| 服务器端预计算路线存入数据 | ✅ | 高德 **Web 服务** `v3/v5 /direction/driving|walking|transit/integrated|bicycling`，返回 polyline 与距离/耗时；v3 驾车途经点上限 16 个 |
| 把行程写入用户高德收藏夹 | ❌ 官方不支持 | 替代：分享链接/二维码、生成 KML/GPX 导出到支持导入的工具；如需"发到手机"可用高德 URI 的 to 参数组合 |
| 地理编码/POI 搜索 | ✅ | Web 服务 `/geocode/geo`、`/place/text`、`/place/around`、`/config/district` |

---

## 2. 总体构建方案

### 2.1 产品形态（与现有工作区体系一致）

延续"**Agent 调研 → 脚本生成 → 静态网站（可部署 GitHub Pages/Vercel）**"的模式，**不依赖常驻后端**：

- 数据在调研时用脚本调用 API 预计算并落盘（JSON），网站是纯前端单页应用（HTML + JS + Leaflet/高德 JS API）。
- 这样部署零成本、可直接手机打开，符合"出发前打开网站看一眼"的用法。
- 若未来要多用户/多行程管理，再按 zhilv-yuntu 的架构补 FastAPI 后端（v2 阶段）。

### 2.2 端到端流程

```
用户输入(目的地/天数/日期/出发地/人数/预算/偏好…)
   ↓ ① Agent 提问收集（选项化，见 PLAN §4.1）
调研阶段（Agent 执行）
   ├─ agent-reach: 小红书 ≥20 帖、B站/抖音/YouTube ≥10 视频（标题+正文/评论 or 字幕）
   ├─ video-to-subtitle-summary: 视频字幕转写 + AI 摘要
   ├─ exa-search / parallel-web: 目的地官网、交通、预约规则等补充
   └─ LLM 综合 → guides/<目的地>.md（含来源链接，可追溯）
结构化阶段（脚本）
   └─ 提炼为 trip-*.json：sources / pois / hotels / restaurants / experiences / itinerary / tips
地图补齐（脚本调用高德 Web 服务）
   ├─ 地理编码 → 所有 POI 得到坐标(与 POI ID)
   ├─ 按天路线：direction API(驾车/步行/公交) → 距离/耗时/polyline
   └─ 包装成 dailyRoutes 存入 JSON
网站生成（build_site.py → site/）
   ├─ 栏目页：行程 / 景点指南 / 当地特色体验 / 餐饮指南 / 出发前准备 / 旅行提醒
   ├─ 地图页：每天路线 + 标记；每个 POI 卡片带「跳转高德导航」
   └─ 交互：用户勾选感兴趣的景点/项目 → 前端用高德 JS API 动态重规划路线并更新时间轴
```

### 2.3 网站栏目（用户要求，全部包含）

1. **行程**：按天时间轴（每天：主题、区域、POI 序列、交通方式、距离/耗时）+ 当日地图路线；支持勾选调整。
2. **景点指南**：每个景点的介绍、开放时间、门票、坐标、来自哪个小红书帖/视频（附链接）、「高德导航」按钮。
3. **当地特色体验**：体验项目清单（含是否需要预约、时长、费用区间、适合人群）。
4. **餐饮指南**：餐厅卡片（类型、人均、推荐菜、避雷备注、是否网红需排队、大众点评关键字 + 高德导航）。
5. **出发前准备**：需提前预约/抢票的景点（含预约入口与时间）、当地交通时刻（船班/地铁/摆渡/机场大巴）、证件与预订清单。
6. **旅行提醒**：必带物品、天气与着装、安全/风俗提醒、紧急联系方式。

### 2.4 技术选型

| 层 | 选型 | 理由 |
|---|---|---|
| 站点 | 静态单页应用（HTML+CSS+JS），多行程由 JS 按 query 参数切换 | 与现有 build_site.py 体系一致，部署简单 |
| 地图 | 高德 JS API 为主；开发期可用 Leaflet + 高德瓦片做无 key 兜底 | JS API 画路线/实时重算最顺；Leaflet 保底 |
| 数据 | JSON（trip-*.json），来源 JSONL（raw/） | 可追溯、可 grep、Git 友好 |
| 调研 | agent-reach + video-to-subtitle-summary + exa-search + LLM | 已装好，见 §3 |
| 生成脚本 | Python（复用现有 scripts 风格） | 与工作区一致 |
| 部署 | GitHub Pages / Vercel 静态托管 | 现有账号即可 |

### 2.5 目录结构（新建 `travel-site/`）

```text
travel-site/
├── PLAN.md                  # 本文档
├── SKILL.md                 # travel-research 技能草稿（规划→调研→建站）
├── config.example.json      # 高德/和风天气/OpenCLI/AI-Douyin 配置模板
├── data/
│   ├── raw/                 # 调研原始记录（JSONL：视频字幕、帖子全文、评论）
│   ├── research/            # 提炼后的结构化调研（sources.json）
│   └── trips/               # 每次行程的 trip-<目的地>-<日期>.json（最终数据源）
├── guides/                  # 攻略 Markdown（人工可读、可追溯来源）
├── scripts/
│   ├── research/            # 调研工作流脚本（agent-reach / 字幕 / 汇总）
│   ├── amap/                # 高德 geocode/poi/route 管线（Python）
│   └── build_site.py        # trip JSON → site/
└── site/                    # 生成后的网站（部署物）
    ├── index.html           # 行程总览 + 六栏目
    ├── map.js / app.js / style.css
```

---

## 3. Skill 与 API 配置规划

### 3.1 本项目要用到的 Skill（多数已装好）

| Skill | 用途 | 状态 |
|---|---|---|
| `agent-reach` | 全网调研路由：小红书 / B站 / 抖音 / YouTube / GitHub / Exa / Jina | ✅ 已装（小红书、抖音需补登录态，见下） |
| `video-to-subtitle-summary` | 视频字幕转写 + AI 摘要（抖音/小红书/B站/YouTube） | ✅ 已装，需配 AI-Douyin 或 TikHub Key |
| `exa-search` | 网页/域名语义搜索补充资料 | ✅ 已装（mcporter+Exa） |
| `parallel-web` | 深度网页调研/结构化抽取 | ✅ 已装（备用） |
| `browser-automation` | OpenCLI/CDP 浏览器控制（小红书/大众点评调研的稳定路径） | ✅ 已装（OpenCLI+扩展待用户装） |
| `markdown-mermaid-writing` | 攻略/流程文档与图表 | ✅ 已装 |
| `frontend-design` | 网站视觉设计（避免模板感） | ✅ 已装 |
| `generate-image` | 可选：封面/OG 图 | ✅ 已装 |
| `liteparse` / `markitdown` | 解析 PDF/网页存档等 | ✅ 已装（备用） |

### 3.2 需要补的配置（按优先级）

| # | 配置项 | 用途 | 获取/操作 |
|---|---|---|---|
| 1 | **高德开放平台 Key**（Web 服务 + JS API 各一，或按服务分别申请） | geocode/POI/路径规划/前端地图 | https://lbs.amap.com 注册 → 控制台创建 Key；JS API 需填**安全域名**（本地可填 `localhost`，部署后填 Pages 域名） |
| 2 | **OpenCLI + Chrome 扩展** | 小红书调研（agent-reach 的小红书走 OpenCLI/浏览器登录态最稳） | 装 `@jackwener/opencli`（`npm i -g`），Chrome 装扩展；或 `agent-reach configure xhs-cookies` |
| 3 | **AI-Douyin API Key / TikHub Token** | 抖音、小红书视频解析下载（字幕 skill 依赖） | https://ai-douyin.top9.cc 注册领额度；或 https://tikhub.io 申请 Token |
| 4 | **和风天气 Key**（可选） | 天气与穿衣提醒栏目 | https://dev.qweather.com 免费注册 |
| 5 | bili-cli / yt-dlp | B站搜索与 YouTube 字幕 | ✅ 已可用（bili-cli 已配置） |
| 6 | 部署域名（可选） | JS API 域名白名单、Pages 绑定 | 可先本地跑，后加 |

### 3.3 建议新建的自有 Skill：`travel-research`

参考 `trip-map-builder` 的技能化做法，把"询问用户 → 三平台调研 → 结构化攻略 → 建站"封装成可复用技能（本项目先放 `travel-site/SKILL.md`，验证稳定后复制到 `~/.dsh/skills/travel-research/`），后续每次出行（第二趟、第三趟…）直接触发，无需重新发明流程。草案见同目录 `SKILL.md`。

### 3.4 高德 API 清单（本项目实际会调用）

| API | 用途 | 频率 |
|---|---|---|
| `GET /geocode/geo` | 地址→经纬度 | 调研时批量 |
| `GET /config/district` | 目的地行政区/城市校验 | 调研时 1 次 |
| `GET /place/text`、`/place/around` | POI 搜索（景点/餐厅/酒店坐标+ID） | 调研时批量 |
| `GET /direction/driving`、`/direction/walking`、`/direction/transit/integrated` | 逐日路线（距离/耗时/polyline） | 调研时按天×段 |
| JS API `AMap.Driving` 等 | 前端画线 + 用户勾选后动态重规划 | 浏览器运行 |
| URI API `uri.amap.com/navigation` | 「跳转高德导航」按钮 | 浏览器运行 |

---

## 4. 具体实施规划

### 4.1 第一步：Agent 提问收集（选项化，拟在建站后每次出行复用）

问题清单（状态：待首次行程执行）：

1. 目的地（城市级，国外也可，但高德导航以国内为主）
2. 玩几天（3 天短途 / 5 天标准 / 7 天深度 / 自定义）
3. 出发日期（yyyy-mm-dd）
4. 出发城市（用于估算大交通）
5. 人数（1 人 / 2 人 / 家庭 / 朋友多人）
6. 预算档位（穷游 / 舒适 / 富游）
7. 内容偏好（自然风光 / 人文历史 / 美食 / 城市休闲 / 海岛度假 / 亲子，可多选）
8. 节奏（休闲 / 均衡 / 特种兵式）

### 4.2 里程碑

| 里程碑 | 内容 | 验收 |
|---|---|---|
| M0 配置 | 高德 Key、OpenCLI+Chrome、AI-Douyin/TikHub、验证 bili-cli | `agent-reach doctor` 全绿 + 一次 geocode 调用成功 |
| M1 调研管线 | 采集 landing 页 + JSONL 落盘 + LLM 综合攻略 | 对一个目的地产出 ≥10 视频 + ≥20 帖子的 `research/sources.json` 与 `guides/*.md` |
| M2 地图管线 | geocode→POI→逐日路线→polyline JSON | 任意两个 POI 能算出路线并渲染在地图上 |
| M3 网站 | 六栏目单页 + 地图 + 勾选重规划 + 高德导航按钮 | 本地 `site/index.html` 通过浏览器验收 |
| M4 端到端首测 | 选一个真实目的地完整跑一遍 | 用户在手机/电脑打开网站按行程可执行 |
| M5 部署与复用 | GitHub Pages/Vercel 上线；固化 `travel-research` skill | 第二条行程复用同一套流程 |

### 4.3 数据模型（trip-*.json 核心结构草案）

```jsonc
{
  "meta": {
    "destination": "大理",
    "dates": ["2026-10-01", "2026-10-02", "2026-10-03"],
    "days": 3,
    "departureCity": "上海",
    "travelers": "2人",
    "budget": "舒适",
    "preferences": ["自然风光", "人文"],
    "sources": { "videos": 12, "posts": 23 },
    "generatedAt": "2026-09-08"
  },
  "sources": [
    { "id": "v01", "platform": "bilibili", "type": "video", "url": "…",
      "title": "…", "author": "…", "status": "字幕已解析", "summary": "…", "used": true }
  ],
  "pois": [
    { "id": "p001", "category": "景点", "name": "洱海生态廊道", "address": "…",
      "lat": 25.75, "lng": 100.18, "poiId": "B0FFF…", "day": 1, "slot": "上午",
      "durationMin": 180, "bookingRequired": false, "ticketPrice": "免费",
      "openHours": "全天", "tags": ["骑行", "日出"], "notes": "…", "sourceIds": ["p03","v05"] }
  ],
  "hotels": [ { "id": "h01", "name": "…", "area": "大理古城", "lat": …, "lng": …,
                "poiId": "…", "priceRange": "¥300-600/晚", "recommend": true, "notes": "…" } ],
  "restaurants": [ { "id": "r01", "name": "…", "type": "白族菜", "avgPrice": 80,
                     "lat": …, "lng": …, "poiId": "…", "dianpingKeyword": "…",
                     "tips": "晚上排队严重", "sourceIds": […] } ],
  "experiences": [ { "id": "e01", "name": "扎染体验", "where": "周城", "durationMin": 120,
                     "price": "¥80-120", "bookingRequired": true, "bookingLink": "…", "bestFor": "亲子/手工" } ],
  "itinerary": [
    { "day": 1, "date": "2026-10-01", "theme": "古城+洱海西线", "area": "大理古城",
      "items": [ { "poiId": "p001", "time": "08:30-11:30", "transport": { "mode": "骑行", "from": "h01", "to": "p001" } } ],
      "dailyRoute": { "mode": "driving", "polylines": ["…"], "distanceKm": 12.4, "durationMin": 40 },
      "notes": "…" }
  ],
  "tips": {
    "weather": { "season": "秋季", "high": 22, "low": 10, "advice": "早晚温差大，带外套" },
    "packing": ["防晒", "外套", "运动鞋"],
    "bookings": [ { "item": "苍山索道", "how": "官方小程序提前3天", "deadline": "出发前3天" } ],
    "transportSchedules": [ { "line": "大理机场-古城大巴", "note": "约40分钟，¥25" } ],
    "safety": ["高原注意防晒补水"],
    "customs": ["白族三月街节庆期间人流大"]
  }
}
```

### 4.4 风险与对策

| 风险 | 对策 |
|---|---|
| 小红书/抖音风控、登录态失效 | agent-reach 多后端 + OpenCLI/CDP 直连（trip-map-builder 经验：**不进搜索框，直接访问搜索结果路由**）；爬虫仓库仅兜底 |
| 高德 JS API 需要域名白名单 | 本地填 `localhost`，部署后更新；开发期 Leaflet 兜底 |
| LLM 编造 POI/价格 | 抄 zhilv-yuntu：**LLM 只输出候选 POI ID/引用来源 ID，坐标、地址、营业信息由高德 API 回填**；价格标注"规划估算" |
| 高德 waypoints 上限（v3 驾车 16 个） | 每天拆段计算、逐段存 polyline；>16 个点的天自动再拆分 |
| 视频/帖子质量参差 | 调研数量要求 ≥10 视频 / ≥20 帖，去重+交叉验证（同一信息至少 2 个独立来源才进入攻略） |
| 静态站无法隐藏 API Key | 个人使用可接受；部署公开站时把 Key 限制 QPS/域名，或 v2 加 FastAPI 代理层 |

---

## 5. 下一步

1. 用户确认方案（或提出调整）；
2. 执行 M0 配置（高德 Key / OpenCLI / AI-Douyin/TikHub，用户提供凭据）；
3. 用户回答 §4.1 的 8 个输入项，开始首个目的地的端到端跑通（M1→M4）。

---

## 6. 执行进度（2026-09-08）

### ✅ 已完成

- **参数收集**：厦门 · 3天（2026-09-18~20 示例日期）· 上海出发 · 2人 · 舒适 · 自然风光/人文/美食/海岛 · 均衡节奏
- **M0 部分**：高德 Key 已验证可用（geocode + place/text + driving direction 全部 OK）
- **M1 部分**：B站调研种子已落盘 `data/research/bilibili_seed.json`（16 个不重复视频，去重按播放量排序）；高德 POI 坐标批量补齐 `data/research/xiamen_pois_raw.json`（12 个点）
- **M2 核心**：`scripts/amap/route_fill.py` 打通——逐日行程两两调用高德 driving API，得到真实距离/耗时写回 trip JSON（D1 12.42km/64min、D2 45.16km/82.5min、D3 23.04km/47.2min）
- **M3 初版**：`scripts/build_site.py` + `site/index.html`（18KB 自包含页）：六栏目 + 每日时间轴 + 高德 JS 地图 + 每 POI「高德导航」URI + tab 切换；浏览器验收通过
- **文档**：PLAN.md / SKILL.md / config.example.json / .env（Key 已 gitignore）

### 🔲 待办（下一轮）

1. **小红书 20 篇**：需 OpenCLI 扩展连接 Chrome（Extension not connected）；或你运行 `agent-reach configure xhs-cookies` 提供 Cookie
2. **抖音 5 个 / B站字幕**：配 AI-Douyin/TikHub Key；B站字幕可 `bili login` 扫码后由 yt-dlp 抓取，或走 faster-whisper 转写
3. 调研后更新 trip JSON（真实餐厅/酒店/价格 + sources 计数达标）→ 重跑 build_site
4. 部署 GitHub Pages / Vercel，配置高德 JS API 域名白名单