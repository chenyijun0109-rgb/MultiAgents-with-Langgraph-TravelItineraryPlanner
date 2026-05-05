# AI Travel Itinerary Planner 当前进度与后续计划

## 1. 当前状态

当前版本已经完成真实地点、酒店、结构化行程、地图和图片的第一轮升级。

已完成：

1. 空输入不会生成行程。
2. 目的地输入接入 Google Places Autocomplete，不再使用本地城市列表。
3. 用户必须从 Google Places 候选中选择目的地。
4. 目的地通过 Place Details 获取名称、地址、经纬度和 `place_id`。
5. 删除 `Holiday Type`、`Budget Type`、`Number of People`。
6. 暂时隐藏 `Packing List`。
7. `Month of Travel` 改为 `Travel Start Date`。
8. 增加 `Hotel Name` 输入。
9. 酒店接入 Google Places Text Search。
10. 行程生成改为结构化 JSON + Markdown 展示。
11. 从结构化行程中提取景点、餐厅、活动。
12. 景点和餐厅接入 Google Places 坐标查询。
13. 地图从 `st.map` 升级为 `pydeck`。
14. 地图支持按日期着色、类型标记、hover tooltip 和每日路线连线。
15. Google Places Photos API 第一版已接入，页面会展示主要地点图片。

## 2. 酒店逻辑说明

酒店是可选输入。

如果用户已经订好酒店并输入酒店名称：

- 系统会用 `酒店名 + 目的地` 查询真实酒店。
- 保存酒店地址、经纬度、`place_id` 和 Google Maps 链接。
- 行程生成会围绕酒店位置规划，尽量从酒店出发或回到酒店附近。
- 地图路线会把酒店作为每天路线的起止参考点。

如果用户没有输入酒店：

- 系统不会发明酒店。
- 系统不会围绕酒店规划。
- 行程会根据城市区域、景点集中度和用户偏好安排。
- 地图路线只连接每天的景点、餐厅和活动点位。

## 3. 当前页面流程

1. 用户输入目的地。
2. Google Places 返回目的地候选。
3. 用户选择目的地。
4. 用户选择开始日期和旅行天数。
5. 用户可选输入酒店名称。
6. 用户填写额外偏好。
7. 点击生成行程。
8. 系统校验目的地和可选酒店。
9. 系统生成结构化 itinerary。
10. 页面显示 Markdown 行程。
11. 系统查询景点、餐厅、活动坐标。
12. 页面显示 `pydeck` 地图、路线连线、地点链接和地点图片。

## 4. 已完成模块

### 4.1 Google Places 目的地自动补全

文件：

- `services/google_maps_service.py`
- `travel_agent.py`

已实现：

- `autocomplete_cities`
- `get_place_details`
- `GOOGLE_MAPS_API_KEY` 检查
- 目的地候选选择
- 未选择候选时不生成

### 4.2 Google Places 酒店查询

文件：

- `services/google_maps_service.py`
- `travel_agent.py`

已实现：

- `search_hotel`
- 酒店输入可选
- 输入酒店时必须能确认真实地点
- 酒店坐标进入 state 和 prompt

### 4.3 结构化 itinerary

文件：

- `agents/generate_itinerary.py`
- `travel_agent.py`

已实现：

- LLM 返回 JSON。
- JSON 包含 `markdown` 和 `days/items`。
- 页面显示 Markdown。
- state 保存 `itinerary_data`。
- JSON 解析失败时保留文本兜底。

### 4.4 地图展示增强

文件：

- `travel_agent.py`

已实现：

- `pydeck` 地图。
- 每天使用不同颜色。
- 酒店、景点、餐厅、活动使用字母标记。
- hover tooltip 显示地点名称、日期、类型和地址。
- 每日路线连线。
- 保留 Google Maps 链接列表作为可点击入口。

说明：Streamlit 原生 `st.pydeck_chart` 不提供地图点位点击回调，因此当前“点击交互”先通过地点链接列表完成。后续如需要地图点位点击弹窗，需要 Streamlit custom component 或前端框架支持。

### 4.5 景点图片

文件：

- `services/google_maps_service.py`
- `travel_agent.py`

已实现：

- Google Places Photo URL。
- 地点图片按天展示。
- 每天最多展示 3 张。
- 图片失败不影响行程和地图。

## 5. 当前限制

### 5.1 路线还不是 Google Directions 真路线

当前路线连线是点到点的直线连接，不是 Google Maps 的真实步行、公交或驾车路线。

后续可以接入：

- Google Directions API
- Google Routes API

### 5.2 行程 JSON 仍可能偶尔不稳定

LLM 仍可能输出不合法 JSON。

后续可以增强：

- JSON schema 校验。
- JSON 修复。
- 失败后自动重试。
- 将“生成结构化数据”和“渲染 Markdown”拆成两个 agent。

### 5.3 图片归因还未完善

当前展示 Google Places 图片 URL，但还没有做完整图片归因展示。

后续需要考虑：

- 图片归因。
- 图片缓存或代理。
- PDF 中插入图片。

### 5.4 Chat 仍然只是问答

当前 Chat 还不能修改主行程。

后续目标：

- 判断用户是在提问还是修改行程。
- 修改请求更新 itinerary。
- 修改后刷新地图和图片。
- 保存版本历史。

## 6. 下一步推荐开发

### 阶段 A：真实路线

目标：

- 接入 Google Directions API 或 Routes API。
- 将直线连线升级为真实路线。
- 生成每日 Google Maps 路线链接。

验收标准：

- 每日路线不只是直线。
- 能看到真实出行路径或打开 Google Maps 路线。

### 阶段 B：Chat 动态修改行程

目标：

- 新增 Chat 意图分类。
- 区分普通问答和行程修改。
- 修改请求会更新主 itinerary。
- 修改后重新生成地图和图片。
- 保存版本历史。

建议新增：

```text
agents/classify_chat_intent.py
agents/revise_itinerary.py
```

### 阶段 C：图片和 PDF 增强

目标：

- 图片归因。
- PDF 包含景点图片。
- PDF 包含地图链接或静态地图。

## 7. 当前最推荐的下一步

最推荐下一步做：**Chat 动态修改行程**。

原因：

- 输入、地点、酒店、地图、图片已经具备第一版。
- 用户接下来最需要的是“这份计划不满意时能继续改”。
- Chat 修改会让项目从一次性生成器变成可交互的旅行计划助手。

建议实现顺序：

1. 增加 itinerary 版本历史。
2. 新增 Chat 意图分类。
3. 修改请求调用 `revise_itinerary`。
4. 更新主 itinerary 和 `itinerary_data`。
5. 重新生成 `map_points` 和图片。

## 8. 里程碑状态

- Milestone 1：输入可信，已完成。
- Milestone 2：真实地点，已完成第一版。
- Milestone 3：结构化计划，已完成第一版。
- Milestone 4：地图和图片，已完成第一版。
- Milestone 5：动态修改，待开始。
