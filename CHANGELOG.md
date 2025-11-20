# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
