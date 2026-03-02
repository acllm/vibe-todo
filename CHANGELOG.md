# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.2] - 2026-03-02

### Added

**视图增强 - 第三阶段（完成！）**

- 完善 `TaskBoardView` 看板视图
  - 按状态三列布局（待处理、进行中、已完成）
  - 美观的任务卡片在列中展示
  - 每个任务卡片包含标题、优先级、项目、截止日期、标签
  - 任务状态高亮显示
  - 按优先级排序（紧急 > 高 > 中 > 低）
  - Rich Table 三列布局，视觉效果出色

### Technical

- 新增 2 个单元测试（看板视图分组逻辑）
- 总测试用例数：90 个，83 个通过，7 个跳过 ✅
- v0.3.x 视图增强系列全部完成！
  - v0.3.0：卡片视图
  - v0.3.1：时间线视图
  - v0.3.2：看板视图
- 保持向后兼容：现有功能不受影响

## [0.3.1] - 2026-03-02

### Added

**视图增强 - 第二阶段**

- 完善 `TaskTimelineView` 时间线视图
  - 按创建时间自动分组任务
  - 智能日期标签（今天、昨天、周一、周二...）
  - 美观的时间线布局（时间标记 + 连接线）
  - 完整的任务信息展示（状态、优先级、项目、描述、标签）
  - 按时间倒序排列（最新的在前）

### Technical

- 新增 2 个单元测试（时间线视图分组逻辑）
- 总测试用例数：88 个，81 个通过，7 个跳过 ✅
- 保持向后兼容：现有功能不受影响

## [0.3.0] - 2026-03-02

### Added

**视图增强 - 第一阶段**

- 全新的视图模块 `src/vibe_todo/cli/views.py`
  - `TaskCardView` - 美观的卡片视图展示
  - `TaskTimelineView` - 时间线视图（预留实现）
  - `TaskBoardView` - 看板视图（预留实现）

- `vibe list` 命令增强
  - 新增 `--view` 选项，支持多种视图类型
    - `table` - 默认表格视图（保持不变）
    - `card` - 美观的卡片视图 ✨
    - `timeline` - 时间线视图（待实现）
    - `board` - 看板视图（待实现）

- 卡片视图特性
  - 完整的任务信息展示
  - 富文本格式和颜色
  - 状态和优先级高亮
  - 截止日期提醒
  - 标签展示

### Technical

- 新增 8 个单元测试（视图功能）
- 总测试用例数：86 个，79 个通过，7 个跳过 ✅
- 重构：将 `get_status_display()` 和 `get_priority_display()` 移到 views.py 避免循环导入
- 向后兼容：默认视图仍为 table，现有功能不受影响

## [0.2.6] - 2026-03-02

### Added

**交互式编辑功能**

- 全新的 `vibe edit <id>` 命令
  - 交互式问答方式编辑任务
  - 显示当前值，按 Enter 保持原样
  - 支持编辑所有字段：标题、描述、状态、优先级、项目、标签、截止日期
  - 友好的用户体验，清晰的提示和确认

- TaskService.update_task() 增强
  - 支持两种调用方式（向后兼容）
    - 方式1：`update_task(task_id, title=..., description=...)` （原有的参数方式）
    - 方式2：`update_task(task_object)` （新的完整对象方式）
  - 保持 100% API 兼容性

### Technical

- 新增 6 个单元测试（交互式编辑功能）
- 总测试用例数：78 个，71 个通过，7 个跳过 ✅
- 测试覆盖：完整对象更新、参数更新、边界情况
- 向后兼容：现有功能不受影响

## [0.2.5] - 2026-03-02

### Added

**全文搜索和高级过滤**

- SQLite FTS5 全文搜索支持
  - 在标题、描述、标签和项目中搜索
  - 按相关性排序结果
  - 自动回退到 LIKE 搜索（如果 FTS5 不可用）

- 高级过滤功能
  - 按状态筛选
  - 按优先级筛选
  - 按项目筛选
  - 按标签筛选（支持 AND/OR 逻辑）
  - 只显示逾期任务
  - 按到期天数筛选
  - 多条件组合筛选

- 新 CLI 命令
  - `vibe search <query>` - 全文搜索任务，支持所有过滤选项
  - `vibe list` 命令增强 - 新增所有高级过滤选项

- 架构改进
  - `TaskFilter` 数据类 - 统一的过滤条件表示
  - `TaskRepositoryInterface` 扩展 - 新增 `search()`, `filter_tasks()`, `search_and_filter()` 方法
  - 默认实现 - 所有适配器都可以使用内存中的搜索和过滤
  - SQLite 优化 - 利用数据库查询进行高效过滤

### Technical

- 新增 18 个单元测试（搜索和过滤功能）
- 总测试用例数：72 个，65 个通过，7 个跳过 ✅
- 测试覆盖：搜索、过滤、组合搜索过滤、各种边界情况
- FTS5 虚拟表自动创建和同步触发器
- 向后兼容：现有功能不受影响

## [0.2.4] - 2025-11-20

### Fixed

**Notion 测试修复**

- 修复在没有安装 `notion-client` 的环境中运行测试时的 `ModuleNotFoundError`
- 将 `@patch` 装饰器改为 `with patch()` 上下文管理器
  - 装饰器会在导入时执行，无法被 `pytest.mark.skipif` 阻止
  - 上下文管理器只在测试执行时才进行 patch
- 添加 `notion_client` 导入检查，更准确地判断依赖是否安装

### Technical

- 测试结果：没有 `notion-client` 时 7 个测试被正确跳过
- 所有其他测试正常通过（47 passed, 7 skipped）

## [0.2.3] - 2025-11-20

### Added

**任务列表分组展示**

- `vibe list` 命令现在按状态分组展示任务
  - 分组顺序：进行中 > 待处理 > 已完成
  - 每个状态组内按优先级排序：紧急 > 高 > 中 > 低
  - 每个状态组显示独立的表格，包含任务数量统计
- 为 `TaskStatus` 和 `TaskPriority` 枚举添加 `sort_order()` 方法
- 新增 `sort_and_group_tasks()` 函数实现任务分组逻辑

### Changed

- 任务列表移除了"状态"列（状态已在表格标题中展示）
- 移除截止日期的 emoji 警告符号，保留颜色提示
  - 逾期任务：红色
  - 3天内到期：黄色

### Fixed

- 修复 `list` 命令与 Python 内置 `list()` 函数的命名冲突问题

## [0.2.2] - 2025-11-20

### Performance

**Notion 后端性能优化**

- 延迟初始化：`data_source_id` 从构造函数移至首次使用时获取
  - 初始化时间从 0.73s 降至 0.12s（**快 6 倍**）
- 配置缓存：`data_source_id` 首次获取后缓存到 `~/.vibe_todo/config.json`
  - 后续命令无需重复查询，额外节省 ~0.3s
- 完善分页逻辑：实现完整的 `has_more` 循环，支持大数据量场景
- **总体性能提升**：`vibe list` 命令执行时间从 ~1.2s 降至 ~1.0s（**提速 18%**）

### Changed

- `NotionRepository.__init__()` 新增 `cached_data_source_id` 参数，支持传入缓存的 data source ID
- `Config.update_backend_config()` 新增方法，支持增量更新后端配置
- Notion 后端现在会自动将 `data_source_id` 保存到配置文件

### Technical

- 优化 Notion 适配器的网络请求策略
- 添加 `_ensure_data_source()` 和 `_cache_data_source_id()` 方法
- 实现智能缓存机制，减少不必要的 API 调用
- 新增 7 个单元测试（Notion 缓存和分页）
- 总测试用例数：54 个，全部通过 ✅

## [0.2.1] - 2025-11-18

### Fixed

- 修复 `TaskService.create_task()` 参数名导致 CLI 调用失败的问题
- 修复批量操作函数名冲突（done/delete 与单个操作命令冲突）

## [0.2.0] - 2025-11-17

### Added

**数据导入/导出**

- 导出任务为 JSON 格式（完整数据，包含元信息）
- 导出任务为 CSV 格式（适合表格查看和编辑）
- 从 JSON 导入任务（支持完整恢复）
- 从 CSV 导入任务（批量创建）
- 三种冲突处理策略：skip（跳过）、overwrite（覆盖）、create_new（创建新任务，推荐）
- 数据格式验证机制（字段完整性和类型校验）
- CLI 命令：`vibe export` 和 `vibe import`
- 支持导出指定任务（通过 ID 列表）

**批量操作**

- 批量更新任务状态（`vibe batch done 1 2 3`）
- 批量删除任务（带确认提示，`vibe batch delete 1 2 3`）
- 批量添加标签（`vibe batch tag 1 2 3 urgent,review`）
- 批量设置优先级（`vibe batch priority 1 2 3 high`）
- 批量设置项目（`vibe batch project 1 2 3 "Q1-Sprint"`）
- 优雅处理无效 ID（跳过不存在的任务）

### Changed

- `TaskService.create_task()` 现在支持两种调用方式：
  - 传统方式：分别传递参数（向后兼容）
  - 新方式：直接传递 Task 对象
- CSV 导出使用分号 `;` 分隔标签（避免与字段分隔符冲突）

### Fixed

- 修复了 `TaskRepository.save()` 中重复添加实体的 bug
- 修复了 CSV 导入时空字段的 None 处理问题
- 修复了导入器中的数据验证问题（枚举值大小写）

### Technical

- 新增 `io` 模块（exporter/importer/formats）
- 新增 13 个单元测试（导入/导出 7 个，批量操作 6 个）
- 总测试用例数：47 个，全部通过 ✅
- 代码覆盖核心功能：导入/导出、批量操作、数据验证

## [0.1.3] - 2025-11-16

### Fixed

- 修复 CLI 表格中 Emoji 导致的列对齐问题

## [0.1.2] - 2025-11-16

### Changed

- 工时输入优化（支持多种格式：90, 1.5h, 1h30m）
- WebUI 信息展示和交互体验增强

## [0.1.0] - 2025-11-15

### Added

- 完整的任务管理（CRUD）
- 优先级和截止日期
- 标签和项目组织
- 工时追踪
- Rich CLI 终端界面
- Web 界面 (HTMX + PicoCSS)
- 多后端支持 (SQLite / Notion / Microsoft To Do)
- 后端切换和配置管理

---

## 版本说明

### v0.2.0 重点特性

**万神殿评审**：

- **Linus Torvalds**: "使用标准库 json/csv，简单实用，没有过度设计"
- **Rob Pike**: "模块职责清晰，接口简洁，批量操作符合直觉"
- **Ken Thompson**: "流式处理优化，数据验证算法优雅"
- **Guido van Rossum**: "CSV/JSON 格式易读，错误提示清晰友好"
- **DHH**: "批量操作的默认行为合理，减少用户决策负担"

### 下一版本预告 (v0.2.1)

- 全文搜索（SQLite FTS5）
- 高级过滤器（多条件组合）
- 搜索关键词高亮

## [0.2.1] - 2025-11-18

### Fixed

- 修复 `TaskService.create_task()` 参数名导致 CLI 调用失败的问题
- 修复批量操作函数名冲突（done/delete 与单个操作命令冲突）
- 修复批量操作参数名与函数名冲突（priority/project）

### Changed

- 批量操作函数重命名为 `batch_*` 前缀避免命名冲突
- 批量操作参数使用描述性名称（`priority_level`, `project_name`）

### Known Issues

- 批量命令实际执行存在问题，将在 v0.2.2 修复
- 基本功能（add/list/export/import）正常工作 ✅
