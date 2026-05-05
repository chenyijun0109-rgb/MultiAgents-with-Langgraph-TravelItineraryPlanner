# AI Travel Itinerary Planner 当前进度与后续计划

## 1. 当前版本总结

当前项目已经从“文本行程生成器”升级为“基于真实地点、地图、图片、路线和动态修改的旅行计划工具”。

当前已完成：

- 目的地使用 Google Places Autocomplete。
- 目的地必须从 Google Places 候选中选择。
- 目的地通过 Place Details 获取名称、地址、经纬度和 `place_id`。
- 表单已删除 `Holiday Type`、`Budget Type`、`Number of People`。
- 暂时隐藏 `Packing List`。
- `Month of Travel` 已改为 `Travel Start Date`。
- 酒店输入为可选项。
- 输入酒店时，系统会查询真实酒店位置。
- 不输入酒店时，系统不会发明酒店，也不会围绕酒店规划。
- 行程生成已改为结构化 JSON。
- 页面 Markdown 由程序渲染，不直接展示模型 JSON 原文。
- 景点、餐厅、活动会通过 Google Places 查询坐标。
- 地图已升级为 `pydeck`。
- 地图支持颜色、标记、tooltip 和路线展示。
- 真实路线已接入 Google Directions API 第一版。
- Google Directions 失败时保留直线 fallback。
- 地点图片已接入 Google Places Photos API 第一版。
- Chat 可以区分普通问答和修改请求。
- Chat 修改请求会更新主行程，并刷新地图和图片。
- 已保存 itinerary 版本历史。
- JSON schema 校验已完成第一版。
- 生成和修改行程失败时会自动重试一次。
- PDF 已支持行程文本、路线链接、地点链接和主要地点图片。

## 2. 当前用户流程

1. 用户输入目的地。
2. Google Places 返回目的地候选。
3. 用户选择目的地。
4. 用户选择旅行开始日期和旅行天数。
5. 用户可选输入酒店名称。
6. 用户填写额外偏好。
7. 用户点击生成行程。
8. 系统校验目的地。
9. 如果填写酒店，系统校验酒店。
10. 系统生成结构化 itinerary。
11. 程序把结构化 itinerary 渲染成 Markdown。
12. 系统查询景点、餐厅、活动坐标。
13. 系统生成每日真实路线。
14. 页面显示行程、地图、路线链接、地点链接和地点图片。
15. 用户可以通过 Chat 提问或要求修改行程。
16. 修改行程后，系统重新生成结构化 itinerary、地图、路线和图片。
17. 用户可以导出包含路线链接和图片的 PDF。

## 3. 已完成模块清单

### 3.1 输入与校验

完成内容：

- 空输入拦截。
- 目的地 Google Places Autocomplete。
- 目的地 Place Details 校验。
- 酒店 Google Places Text Search。
- 酒店可选逻辑。
- 无酒店时不发明酒店、不围绕酒店规划。

相关文件：

- `travel_agent.py`
- `services/google_maps_service.py`
- `agents/generate_itinerary.py`

### 3.2 结构化行程

完成内容：

- LLM 返回结构化 JSON。
- JSON 包含 `title`、`summary`、`days/items`。
- 程序渲染 Markdown。
- state 保存 `itinerary_data`。
- schema 校验。
- 失败自动重试一次。

相关文件：

- `agents/itinerary_schema.py`
- `agents/generate_itinerary.py`
- `agents/revise_itinerary.py`

### 3.3 地图与真实路线

完成内容：

- Google Places 查询景点、餐厅、活动坐标。
- `pydeck` 地图。
- 不同日期不同颜色。
- 酒店、景点、餐厅、活动字母标记。
- hover tooltip。
- Google Directions API 真实路线。
- Directions 失败时直线 fallback。
- 每日 Google Maps 路线链接。

相关文件：

- `travel_agent.py`
- `services/google_maps_service.py`

### 3.4 图片

完成内容：

- Google Places Photos API 图片 URL。
- 页面按天展示地点图片。
- 每天最多展示 3 张。
- 图片失败不影响行程和地图。

相关文件：

- `services/google_maps_service.py`
- `travel_agent.py`

### 3.5 Chat 动态修改

完成内容：

- Chat 意图分类。
- 普通问题走原有问答。
- 修改请求调用 `revise_itinerary`。
- 修改后更新 `itinerary` 和 `itinerary_data`。
- 修改后刷新地图、路线和图片。
- 保存 itinerary version。
- 页面显示当前版本号。

相关文件：

- `agents/classify_chat_intent.py`
- `agents/revise_itinerary.py`
- `travel_agent.py`

### 3.6 PDF 导出

完成内容：

- 导出行程文本。
- 导出每日路线链接。
- 导出地点 Google Maps 链接。
- 导出主要地点图片。
- 图片失败时跳过。

相关文件：

- `utils_export.py`
- `travel_agent.py`

## 4. 当前限制

### 4.1 Chat 版本管理还不完整

当前已经保存版本，但还没有完整 UI 支持：

- 查看版本历史。
- 恢复任意版本。
- 撤销上一版。
- 修改前确认。

### 4.2 路线体验仍可增强

当前 Directions API 已接入，但路线体验还比较基础：

- 没有路线模式选择。
- 没有根据距离自动建议步行、公交或打车。
- 没有展示每段路线步骤。
- 没有展示 Directions API 的版权和 warnings。

### 4.3 PDF 排版还比较基础

当前 PDF 已包含更多内容，但排版仍然简单：

- 没有静态地图图片。
- 图片归因不完整。
- 标题层级和分页还可以优化。
- 中文内容仍可能受 `fpdf` 字体限制影响。

### 4.4 JSON 稳定性仍可增强

当前已完成第一版 schema 校验和自动重试，但仍可以继续增强：

- 使用 Pydantic 或更严格的数据模型。
- 根据错误类型给用户更具体提示。
- 将生成结构化数据和生成文字说明拆成两个步骤。

### 4.5 文档和 README 还未同步

README 仍然描述旧版本功能，需要更新：

- Google Places。
- Google Directions。
- 结构化 itinerary。
- 地图和图片。
- Chat 动态修改。
- 新增环境变量。

## 5. 后续开发计划

### 阶段 A：Chat 版本历史和撤销

目标：

- 增加版本历史 UI。
- 支持恢复上一版。
- 支持恢复任意版本。
- 展示每次修改摘要。

验收标准：

- 用户可以撤销最近一次 Chat 修改。
- 用户可以查看所有 itinerary versions。
- 恢复版本后，地图、路线和图片同步刷新。

### 阶段 B：路线体验增强

目标：

- 增加路线模式选择，例如 walking、driving、transit。
- 展示路线距离和时间。
- 展示 Directions warnings。
- 后续根据距离建议交通方式。

验收标准：

- 用户可以选择出行方式。
- 每日路线信息更清楚。
- API fallback 行为更友好。

### 阶段 C：PDF 排版与地图增强

目标：

- PDF 支持更好的标题层级。
- PDF 支持静态地图图片。
- PDF 支持图片归因。
- 改善中文字体支持。

验收标准：

- PDF 可读性明显提升。
- PDF 不只是链接和文字。
- 图片来源说明更完整。

### 阶段 D：README 和项目文档更新

目标：

- 更新 README。
- 更新运行方式。
- 更新 `.env` 配置说明。
- 说明需要启用的 Google API。
- 说明当前功能和限制。

验收标准：

- 新用户可以按 README 配置并运行项目。
- 文档内容与当前代码一致。

### 阶段 E：JSON 稳定性第二版

目标：

- 引入更严格 schema。
- 对模型输出错误分类。
- 对失败场景给更清晰提示。

验收标准：

- JSON 失败率进一步降低。
- 用户不会看到模型原始输出。

## 6. 当前最推荐的下一步

最推荐下一步做：**Chat 版本历史和撤销**。

原因：

- Chat 动态修改已经完成第一版。
- 当前已经保存版本，但用户还不能使用版本历史。
- 加上撤销后，用户会更放心地反复调整行程。

建议实现顺序：

1. 在页面显示 version history expander。
2. 增加 `Undo Last Revision` 按钮。
3. 增加 `Restore Version` 逻辑。
4. 恢复版本后刷新地图、路线和图片。
5. 保留当前版本号和修改摘要。

## 7. 里程碑状态

- Milestone 1：输入可信，已完成。
- Milestone 2：真实地点，已完成第一版。
- Milestone 3：结构化计划，已完成第一版。
- Milestone 4：地图和图片，已完成第一版。
- Milestone 5：Chat 动态修改，已完成第一版。
- Milestone 6：真实路线，已完成第一版。
- Milestone 7：JSON 稳定性，已完成第一版。
- Milestone 8：PDF 增强，已完成第一版。

## 8. 总结

当前项目已经具备比较完整的旅行计划核心能力。下一步不建议继续堆新功能，而是优先提升“可控性”和“可恢复性”：先把 Chat 修改后的版本历史和撤销做好，再增强路线体验和 PDF 排版。这样项目会更像一个可以持续编辑的旅行计划工具，而不是一次性生成器。
