# Vibe Todo

一个简洁实用的 Todo 任务和工时管理工具，提供 Web 界面和命令行两种使用方式，**支持多后端存储**。

## ✨ 特性

- 📝 **任务管理**：创建、编辑、完成、删除任务
- ⏱️  **工时追踪**：记录任务工作时长
- 🎨 **优先级管理**：低/中/高/紧急四个级别
- 📅 **截止日期**：智能提醒逾期任务
- 🏷️ **标签系统**：灵活的任务分类
- 📁 **项目管理**：按项目组织任务
- 🌐 **Web 界面**：使用 HTMX + Jinja2 + PicoCSS 构建的现代化界面
- 💻 **精美 CLI**：使用 Rich 库打造的专业终端UI
- 🔌 **多后端支持**：
  - 🗄️  **SQLite** - 本地存储
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

## License

MIT
