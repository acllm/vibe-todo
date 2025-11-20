# Vibe Todo

一个简洁实用的 Todo 任务和工时管理工具，提供 Web 界面和命令行两种使用方式，**支持多后端存储**。

## ✨ 特性

- 📝 **任务管理**：创建、编辑、完成、删除任务
- ⏱️ **工时追踪**：记录任务工作时长
- 🎨 **优先级管理**：低/中/高/紧急四个级别
- 📅 **截止日期**：智能提醒逾期任务
- 🏷️ **标签系统**：灵活的任务分类
- 📁 **项目管理**：按项目组织任务
- 🌐 **Web 界面**：使用 HTMX + Jinja2 + PicoCSS 构建的现代化界面
- 💻 **精美 CLI**：使用 Rich 库打造的专业终端 UI
- 🔌 **多后端支持**：
  - 🗄️ **SQLite** - 本地存储
  - 📓 **Notion** - 同步到 Notion 数据库
  - ✅ **Microsoft To Do** - 同步到 Microsoft To Do

## 🚀 快速开始

### 安装

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 基础安装
uv pip install -e ".[dev]"

# 安装 Notion 支持
uv pip install -e ".[notion]"

# 安装 Microsoft To Do 支持
uv pip install -e ".[microsoft]"

# 安装所有后端支持
uv pip install -e ".[all]"
```

### 使用 Web 界面

```bash
vibe web
# 访问 http://localhost:8000
```

### 使用 CLI

#### 基础操作

```bash
# 添加任务（支持完整参数）
vibe add "完成项目文档" -d "编写 README" -p high --due 2025-12-20 -t "文档,重要" --project "Vibe Todo"

# 列出所有任务（精美表格显示）
vibe list

# 按状态筛选
vibe list -s todo
vibe list -s in_progress

# 按项目筛选
vibe list -p "Vibe Todo"

# 显示逾期任务
vibe list --overdue

# 查看任务详情
vibe show 1

# 开始任务
vibe start 1

# 添加工时
vibe time 1 30  # 添加30分钟

# 完成任务
vibe done 1

# 删除任务
vibe delete 1

# 查看统计
vibe stats
```

#### 数据导入/导出 (v0.2.0+)

```bash
# 导出任务
vibe export tasks.json              # 导出为JSON
vibe export tasks.csv --format csv  # 导出为CSV
vibe export tasks.json --ids 1,2,3  # 导出指定任务

# 导入任务
vibe import tasks.json                            # 从JSON导入
vibe import tasks.csv --format csv                # 从CSV导入
vibe import tasks.json --strategy create_new      # 导入策略
```

#### 批量操作 (v0.2.0+)

```bash
# 批量标记完成
vibe batch done 1 2 3

# 批量删除（带确认）
vibe batch delete 1 2 3

# 批量添加标签
vibe batch tag 1 2 3 urgent,review

# 批量设置优先级
vibe batch priority 1 2 3 high

# 批量设置项目
vibe batch project 1 2 3 "Q1-Sprint"
```

#### 后端配置

```bash
# 查看当前配置
vibe config show

# 使用 SQLite（默认）
vibe config set-backend sqlite --db-path vibe_todo.db

# 切换到 Notion
vibe config set-backend notion \
  --token secret_xxx \
  --database xxx

# 切换到 Microsoft To Do
vibe config set-backend microsoft \
  --client-id xxx
```

## 📖 多后端配置指南

### Notion 配置

1. **创建 Integration**

   - 访问 https://www.notion.so/my-integrations
   - 创建新的 Integration，获取 Token

2. **创建 Database**

   - 在 Notion 中创建一个数据库
   - 添加以下属性：
     - Name (title)
     - Description (text)
     - Status (select: To Do, In Progress, Done)
     - Priority (select: Low, Medium, High, Urgent)
     - Due Date (date)
     - Tags (multi-select)
     - Project (select)
     - Time Spent (number)

3. **连接 Database**

   - 在数据库页面，点击右上角 "..." → "Add connections"
   - 选择你创建的 Integration
   - 复制数据库 ID（URL 中的一段字符）

4. **配置 Vibe Todo**
   ```bash
   vibe config set-backend notion \
     --token secret_xxx \
     --database database_id
   ```

### Microsoft To Do 配置

1. **注册 Azure AD 应用**

   - 访问 https://portal.azure.com
   - Azure Active Directory → App registrations → New registration
   - 设置 Redirect URI: `http://localhost`
   - 添加 API 权限：`Tasks.ReadWrite`
   - 复制 Application (client) ID

2. **配置 Vibe Todo**

   ```bash
   vibe config set-backend microsoft --client-id xxx
   ```

3. **首次认证**
   - 运行任意命令时会弹出浏览器进行 OAuth2 认证
   - 授权后 token 会缓存到本地

## 开发

### 运行测试

```bash
pytest
```

### 代码检查

```bash
ruff check .
```

## 技术栈

- **后端**: FastAPI + SQLAlchemy
- **前端**: HTMX + Jinja2 + PicoCSS
- **CLI**: Click
- **数据库**: SQLite
- **测试**: pytest

## 架构

项目采用简洁的分层架构：

- `core/`: 核心领域模型和业务逻辑
- `storage/`: 数据持久化层
- `web/`: Web 接口（FastAPI + HTMX）
- `cli/`: 命令行接口（Click）

## 📊 项目状态

**当前版本**: v0.2.2  
**开发状态**: ✅ 稳定 (Stable)  
**测试覆盖**: 54 个测试用例全部通过

### 已实现功能

#### v0.2.2 (2025-11-20)

- ⚡ **性能优化**：Notion 后端延迟初始化 + 配置缓存，`vibe list` 提速 18%

#### v0.2.0 (2025-11-17)

- ✅ **数据导入/导出**：JSON/CSV 格式，支持冲突策略
- ✅ **批量操作**：批量标记完成、删除、添加标签、设置优先级/项目

#### v0.1.x

- ✅ 完整的任务管理（CRUD）
- ✅ 优先级和截止日期
- ✅ 标签和项目组织
- ✅ 工时追踪
- ✅ Rich CLI 终端界面
- ✅ Web 界面 (HTMX + PicoCSS)
- ✅ 多后端支持 (SQLite / Notion / Microsoft To Do)
- ✅ 后端切换和配置管理

### 路线图

查看完整的技术架构和未来规划：[ARCHITECTURE.md](ARCHITECTURE.md)

#### 下一步 (v0.2.1 - v0.3.0)

- 🔄 全文搜索和高级过滤（FTS5）
- 💡 交互式任务编辑
- 💡 看板和日历视图
- 💡 深色模式

#### 中期规划 (v0.3.0 - v0.4.0)

- 💡 交互式任务编辑
- 💡 看板和日历视图
- 💡 深色模式
- 🔮 Google Tasks / Todoist 集成

#### 长期愿景 (v0.5.0+)

- 🌟 AI 辅助（自动分类、优先级建议）
- 🌟 协作功能（多用户、评论）
- 🌟 实时同步和离线模式

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

### 如何贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交改动 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

### 开发指南

```bash
# 克隆仓库
git clone https://github.com/yourusername/vibe-todo.git
cd vibe-todo

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装开发依赖
uv pip install -e ".[dev,all]"

# 运行测试
pytest

# 代码检查
ruff check .
```

### 行为准则

请遵循友好、尊重、包容的开源社区准则。

## 📄 License

MIT License - 详见 [LICENSE](LICENSE) 文件
