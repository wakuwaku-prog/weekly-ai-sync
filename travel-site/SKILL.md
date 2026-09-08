# travel-research — 旅行调研与行程网站生成技能（草稿）

> 状态：草稿 v1。验证一轮端到端后复制到 `~/.dsh/skills/travel-research/` 固化复用。
> 定位：一次会话内完成「询问用户 → 三平台调研 → 结构化攻略 → 高德地图补齐 → 生成网站」。

## 触发词

- "帮我规划旅行/做攻略/做行程"
- "想去 X 玩 N 天"
- "做个旅行网站"

## 输入收集（第一步，选项化提问）

必须收集：目的地、天数、出发日期、出发城市、人数、预算档位（穷游/舒适/富游）、内容偏好（可选多项）、节奏（休闲/均衡/特种兵）。

## 调研阶段（第二步）

平台与数量要求：

| 平台 | 最少数量 | 工具 |
|---|---|---|
| 小红书 | 20 篇 | agent-reach（OpenCLI/CDP 或 xhs cookies）；直接访问 `search_result?keyword=` 路由，粗筛 10-20 条再精读 2-3 条 |
| B站 | 5 个视频 | bili-cli 搜索 + `video-to-subtitle-summary` 抓字幕/转写 |
| 抖音/YouTube | 5 个视频 | `video-to-subtitle-summary`（AI-Douyin/TikHub 解析 + faster-whisper 转写），YouTube 优先 yt-dlp 字幕 |
| 补充 | 按需 | exa-search / parallel-web：官网、交通时刻、预约规则、天气 |

产出：
1. `data/raw/` 原始记录（JSONL：平台、URL、标题、作者、正文/字幕、评论摘录）
2. LLM 综合 → `guides/<目的地>.md`（含来源链接与"2 个独立来源交叉验证"标注）
3. 提炼 → `data/research/sources.json`

## 结构化与地图补齐（第三步）

1. 上方攻略提炼出 `pois/hotels/restaurants/experiences` 及逐日行程草案；
2. 高德 Web 服务：
   - `/config/district` 校验目的地；
   - `/geocode/geo` + `/place/text` 回填每个实体的坐标、地址、POI ID；**LLM 生成的名字不可信，坐标必须以高德回填为准**；
   - 逐日 `/direction/driving|walking|transit/integrated` 计算路线（距离/耗时/polyline）；
3. 落盘 `data/trips/trip-<目的地>-<日期>.json`（结构见 PLAN.md §4.3）。

## 生成网站（第四步）

1. 运行 `scripts/build_site.py data/trips/trip-*.json` → `site/`；
2. 网站栏目：行程 / 景点指南 / 当地特色体验 / 餐饮指南 / 出发前准备 / 旅行提醒；
3. 地图：高德 JS API `AMap.Driving` 画每日路线；每个 POI 卡片「跳转高德导航」＝
   `https://uri.amap.com/navigation?to=<lng>,<lat>,<名称>&mode=car&callnative=1`
   （移动端可改用 `androidamap://navi` / `iosamap://path` scheme）；
4. 交互：用户勾选感兴趣景点/项目 → 前端 `AMap.Driving.search(origin, dest, waypoints)` 动态重规划并更新时间轴；
5. 汇报：网站位置 + 调研统计（视频数/帖子数）+ 关键提醒 + 来源。

## 硬规则

- 不下结论给"感觉"：每条攻略信息尽量挂 `sourceIds`；
- 票/价/营业信息标注"规划估算，出发前以官方为准"；
- 不为名店扭曲路线：餐厅是当天区域的顺路候选；
- 一天一个主区域；行程是参考坐标，不是逐小时执行脚本；
- 不保存用户证件、订单号、完整聊天记录；长期偏好写入 `~/.tip-map-memory/MEMORY.md`（记忆文件）供下次复用。