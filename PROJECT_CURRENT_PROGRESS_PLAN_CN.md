# AI Travel Itinerary Planner 当前进度与后续计划

## 1. 当前项目状态

项目已经完成了从“简单文本生成器”到“基于真实地点的旅行计划工具”的第一轮升级。

目前已经完成：

1. 空输入不会生成行程。
2. 目的地输入接入 Google Places Autocomplete，不再使用本地城市列表限制。
3. 用户必须从 Google Places 候选中选择目的地。
4. 目的地会通过 Place Details 获取标准名称、地址、经纬度和 `place_id`。
5. 删除 `Holiday Type`、`Budget Type`、`Number of People`。
6. 暂时隐藏 `Packing List` 功能入口。
7. `Month of Travel` 已改为准确的 `Travel Start Date`。
8. 增加 `Hotel Name` 输入。
9. 酒店名称接入 Google Places Text Search，可以获取真实酒店地址、坐标、`place_id` 和 Google Maps 链接。
10. `generate_itinerary` 已改为结构化 JSON 输出，并从 JSON 中取 Markdown 展示。
11. 系统会从结构化行程中提取景点和餐厅。
12. 景点和餐厅会通过 Google Places 查询坐标。
13. 页面已增加第一版地图展示和地点 Google Maps 链接。
14. 景点和餐厅会尽量使用 Google Places Photos API 展示图片。

当前项目已经具备这些基础能力：

- 真实目的地校验。
- 真实酒店位置校验。
- 结构化 itinerary 数据。
- 第一版地图点位展示。
- 更可靠的 prompt 防线，避免模型编造目的地。

## 2. 当前页面流程

用户当前使用流程：

1. 输入目的地。
2. 系统调用 Google Places 返回城市候选。
3. 用户从候选中选择目的地。
4. 用户选择旅行开始日期和天数。
5. 用户可选输入酒店名称。
6. 如果输入酒店，系统用 Google Places 查询酒店位置。
7. 用户填写额外偏好。
8. 点击生成行程。
9. 系统生成结构化 itinerary。
10. 页面显示 Markdown 行程。
11. 系统查询酒店、景点、餐厅坐标。
12. 页面显示地图和地点链接。

## 3. 已完成模块

### 3.1 Google Places 目的地自动补全

文件：

- `services/google_maps_service.py`
- `travel_agent.py`

已实现：

- `autocomplete_cities`
- `get_place_details`
- `GOOGLE_MAPS_API_KEY` 检查
- Streamlit 候选选择
- 必须选择候选后才能生成

### 3.2 Google Places 酒店查询

文件：

- `services/google_maps_service.py`
- `travel_agent.py`

已实现：

- `search_hotel`
- 根据 `hotel_name + destination` 搜索酒店
- 保存酒店名称、地址、坐标、`place_id` 和 Google Maps 链接
- 酒店输入可选
- 如果用户输入酒店但无法确认，系统会提示错误并停止生成

### 3.3 结构化 itinerary

文件：

- `agents/generate_itinerary.py`
- `travel_agent.py`

已实现：

- 要求 LLM 返回 JSON
- JSON 中包含 `markdown` 和 `days/items`
- 页面继续显示 Markdown
- state 中保存 `itinerary_data`
- JSON 解析失败时保留文本兜底

### 3.4 地图点位第一版

文件：

- `services/google_maps_service.py`
- `travel_agent.py`

已实现：

- `search_place`
- 从 `itinerary_data.days[].items[]` 提取 `attraction`、`restaurant`、`activity`
- 查询景点和餐厅坐标
- 保存 `map_points`
- 使用 `st.map` 显示地图
- 展示地点 Google Maps 链接列表

## 4. 当前限制

### 4.1 地图展示还比较基础

当前使用 `st.map`，能显示点位，但自定义能力较弱。

缺少：

- 不同日期不同颜色。
- 酒店和景点不同图标。
- hover tooltip。
- 每日路线连线。
- 地图点位点击交互。

后续建议升级到 `pydeck`。

### 4.2 结构化 JSON 仍可能不稳定

虽然 prompt 已要求返回 JSON，但 LLM 仍可能偶尔输出不合法 JSON。

后续可以增强：

- JSON 修复。
- 更严格的 schema 校验。
- 将“生成数据”和“渲染 Markdown”拆成两个步骤。
- 失败时自动重试一次。

### 4.3 景点图片已接入第一版，但展示还可增强

当前已经有：

- Google Places Photos API 图片 URL。
- 每日最多 3 张地点图片展示。
- 图片加载失败不影响主行程。

当前还缺少：

- 图片缓存或代理。
- 图片版权归因展示。
- PDF 中插入图片。

### 4.4 Chat 仍然只是问答

当前 Chat 还不能修改主行程。

后续目标：

- 判断用户是在提问还是要求修改。
- 如果是修改请求，更新 itinerary。
- 修改后重新查询景点坐标和图片。
- 保存版本历史。

## 5. 下一阶段推荐开发顺序

### 阶段 A：地图展示增强

目标：

- 从 `st.map` 升级到 `pydeck`。
- 酒店、景点、餐厅使用不同颜色。
- 不同日期使用不同颜色。
- hover tooltip 显示地点名称、日期、类型。

验收标准：

- 地图可区分酒店、景点、餐厅。
- 用户能看出每天地点分布。
- 地图点位和行程内容一致。

### 阶段 B：图片展示增强

目标：

- 增加图片归因信息。
- 控制每一天图片数量。
- 后续导出 PDF 时带上图片。

验收标准：

- 图片展示更稳定。
- 图片来源更清晰。
- PDF 可以包含主要景点图片。

### 阶段 C：路线优化

目标：

- 使用酒店坐标和景点坐标减少跨区域折返。
- 可以先用经纬度距离做简单排序。
- 后续再接 Google Directions API。

验收标准：

- 每天景点更集中。
- 行程中减少不合理跨城往返。
- 可以生成 Google Maps 路线链接。

### 阶段 D：Chat 动态修改行程

目标：

- 新增 Chat 意图分类。
- 判断用户是问答还是修改请求。
- 修改请求会更新主 itinerary，而不是只回复建议。
- 修改后刷新地图和图片。
- 保存版本历史。

建议新增：

```text
agents/classify_chat_intent.py
agents/revise_itinerary.py
```

验收标准：

- 用户说“第二天不要博物馆，换成购物”，主行程会更新。
- 系统保留上一版行程。
- 修改后地图点位同步刷新。

### 阶段 E：PDF 导出增强

目标：

- PDF 中加入行程、地图链接、景点图片。
- 后续可加入静态地图图片。

验收标准：

- PDF 不只是纯文本。
- 主要景点和地图链接可以一起导出。

## 6. 当前最推荐的下一步

最推荐下一步做：**地图展示增强**。

原因：

- 目的地、酒店、景点坐标和图片都已经接入 Google Places。
- 当前 `st.map` 只能做基础点位展示。
- 升级到 `pydeck` 后，可以区分日期、类型和 tooltip，用户会更容易判断路线是否合理。

建议任务：

1. 引入 `pydeck` 地图层。
2. 为酒店、景点、餐厅设置不同颜色。
3. 为不同日期设置可区分颜色。
4. 增加 tooltip。
5. 保留 Google Maps 链接列表。

## 7. 里程碑状态

### Milestone 1：输入可信

状态：已完成。

### Milestone 2：真实地点

状态：已完成第一版。

包括：

- 目的地 Google Places 查询。
- 目的地坐标。
- 酒店 Google Places 查询。
- 酒店坐标。
- 景点和餐厅坐标。

### Milestone 3：结构化计划

状态：已完成第一版。

包括：

- itinerary JSON。
- Markdown 展示。
- `days/items` 数据。

### Milestone 4：地图和图片

状态：地图第一版已完成，图片第一版已完成。

### Milestone 5：动态修改

状态：待开始。

## 8. 总结

当前项目已经完成了真实目的地、真实酒店、结构化行程、地图点位和景点图片第一版。下一步最自然的是增强地图展示，让旅行计划从基础点位地图升级为可以区分日期、类型和路线分布的地图体验。

Chat 动态修改建议放在图片和地图增强之后，因为它需要在修改行程后重新生成结构化数据、重新查地点、重新刷新地图和图片。
