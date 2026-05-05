# AI Travel Itinerary Planner 当前进度与后续计划

## 1. 当前版本状态

当前版本已经完成旅行计划核心链路的第一轮重构：

- 目的地使用 Google Places Autocomplete，不再使用本地城市列表。
- 用户必须从 Google Places 候选中选择目的地。
- 目的地会通过 Place Details 获取标准名称、地址、经纬度和 `place_id`。
- 表单已删除 `Holiday Type`、`Budget Type`、`Number of People`。
- 暂时隐藏 `Packing List`，优先做好旅行计划本体。
- `Month of Travel` 已改为 `Travel Start Date`。
- 酒店输入为可选项。
- 输入酒店时，系统会用 Google Places 查询真实酒店位置。
- 不输入酒店时，系统不会发明酒店，也不会围绕酒店规划。
- 行程生成已改为结构化 JSON 数据。
- 页面 Markdown 由程序渲染，不再直接展示模型返回的 JSON 原文。
- 景点、餐厅、活动会通过 Google Places 查询坐标。
- 地图已升级为 `pydeck`，支持颜色、标记、tooltip 和路线连线。
- 真实路线已接入 Google Directions API 第一版，失败时保留直线 fallback。
- 景点图片已接入 Google Places Photos API 第一版。
- Chat 动态修改行程已完成第一版。

## 2. 当前用户流程

1. 用户输入目的地。
2. Google Places 返回目的地候选。
3. 用户选择目的地。
4. 用户选择旅行开始日期和天数。
5. 用户可选输入酒店名称。
6. 用户填写额外偏好。
7. 点击生成行程。
8. 系统校验目的地。
9. 如果填写酒店，系统校验酒店。
10. 系统生成结构化 itinerary。
11. 程序把结构化 itinerary 渲染成 Markdown。
12. 系统查询景点、餐厅、活动坐标。
13. 页面显示行程、地图、地点链接和图片。
14. 用户可以在 Chat 中提问，或直接要求修改行程。
15. 如果 Chat 内容是修改请求，系统会更新主行程并刷新地图和图片。

## 3. 已完成模块

### 3.1 Google Places 目的地自动补全

文件：

- `services/google_maps_service.py`
- `travel_agent.py`

已实现：

- `autocomplete_cities`
- `get_place_details`
- `GOOGLE_MAPS_API_KEY` 检查
- 目的地候选选择
- 未选择候选时不生成

### 3.2 Google Places 酒店查询

文件：

- `services/google_maps_service.py`
- `travel_agent.py`

已实现：

- `search_hotel`
- 酒店输入可选
- 输入酒店时必须能确认真实地点
- 酒店坐标进入 state 和 prompt
- 不输入酒店时不会生成酒店约束

### 3.3 结构化 itinerary

文件：

- `agents/generate_itinerary.py`
- `travel_agent.py`

已实现：

- LLM 返回结构化 JSON。
- JSON 包含 `title`、`summary`、`days/items`。
- 程序负责渲染 Markdown。
- state 保存 `itinerary_data`。
- JSON 解析失败时显示错误提示，不展示 JSON 原文。

### 3.4 地图展示

文件：

- `travel_agent.py`

已实现：

- `pydeck` 地图。
- 每天使用不同颜色。
- 酒店、景点、餐厅、活动使用字母标记。
- hover tooltip 显示地点名称、日期、类型和地址。
- 每日路线连线。
- Google Maps 链接列表作为可点击入口。

说明：`st.pydeck_chart` 不提供点位点击回调，因此地图点位点击弹窗暂时无法原生实现。当前用 hover tooltip + Google Maps 链接列表满足基本交互。

### 3.5 景点图片

文件：

- `services/google_maps_service.py`
- `travel_agent.py`

已实现：

- Google Places Photo URL。
- 按天展示地点图片。
- 每天最多展示 3 张。
- 图片失败不影响行程和地图。

### 3.6 Chat 动态修改行程

文件：

- `agents/classify_chat_intent.py`
- `agents/revise_itinerary.py`
- `travel_agent.py`

已实现：

- `classify_chat_intent` 判断普通问答或修改请求。
- 普通问题继续走原有 `chat_agent`。
- 修改请求调用 `revise_itinerary`。
- 修改后更新 `itinerary` 和 `itinerary_data`。
- 修改后刷新地图点位和图片。
- 保存 `itinerary_versions`。
- 页面显示当前 itinerary version。

## 4. 当前限制

### 4.1 真实路线仍需增强

当前已经接入 Google Directions API，可以用 overview polyline 展示真实路线，并提供每日 Google Maps 路线链接。

仍需增强：

- 支持用户选择 walking / driving / transit 等模式。
- 处理 Directions API 未启用或超额时的更友好提示。
- 展示每段路线的详细步骤。
- 根据距离自动选择交通方式。

### 4.2 JSON 稳定性仍需增强

虽然已去掉 `markdown` 字段并降低 JSON 出错概率，但 LLM 仍可能偶尔输出不合法 JSON。

后续可以增加：

- JSON schema 校验。
- 自动修复 JSON。
- 失败后自动重试。
- 将“生成结构化数据”和“渲染文字说明”拆成两个步骤。

### 4.3 图片归因还未完善

当前已经能显示 Google Places 图片，但还没有完整处理：

- 图片归因。
- 图片缓存或代理。
- PDF 中插入图片。

### 4.4 Chat 动态修改仍需增强

当前 Chat 已经可以修改主行程，但仍需增强：

- 更准确的意图分类。
- 支持撤销到上一版。
- 支持查看版本历史。
- 修改失败时自动重试。
- 修改前可选确认。

## 5. 下一步推荐开发

### 阶段 A：Chat 动态修改增强

目标：

- 增加撤销上一版。
- 增加版本历史查看。
- 修改失败自动重试。
- 修改前可选确认。

验收标准：

- 用户可以恢复上一版。
- 用户可以看到每次修改摘要。

### 阶段 B：路线体验增强

目标：

- 支持选择路线模式。
- 展示每段路线的距离和时间。
- 根据距离建议步行、公交或打车。

验收标准：

- 路线信息不只是总距离和总时间。
- 用户能看到更清楚的交通建议。

### 阶段 C：JSON 稳定性增强

目标：

- 加 JSON schema 校验。
- 失败后自动重试一次。
- 更好地处理模型输出异常。

### 阶段 D：PDF 和图片增强

目标：

- PDF 包含主要景点图片。
- PDF 包含地图链接。
- 图片归因信息更完整。

## 6. 当前最推荐的下一步

最推荐下一步做：**Chat 动态修改增强**。

原因：

- 目的地、酒店、地图、图片、真实路线和 Chat 动态修改第一版都已经完成。
- 当前 Chat 修改还不能撤销，也不能查看版本历史。
- 增加版本历史和撤销会让用户更敢于反复调整行程。

建议实现顺序：

1. 增加版本历史 UI。
2. 增加 Undo Last Revision。
3. 支持查看每次 revision summary。
4. 修改失败时保留当前版本并提示重试。

## 7. 里程碑状态

- Milestone 1：输入可信，已完成。
- Milestone 2：真实地点，已完成第一版。
- Milestone 3：结构化计划，已完成第一版。
- Milestone 4：地图和图片，已完成第一版。
- Milestone 5：动态修改，已完成第一版。
- Milestone 6：真实路线，已完成第一版。
