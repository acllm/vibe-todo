# 多后端架构设计

## 概述

Vibe Todo 已准备好支持多后端架构，可以将任务同步到 Notion 和 Microsoft To Do。

## 当前架构

```
┌─────────────┐
│   CLI/Web   │
└──────┬──────┘
       │
┌──────▼──────┐
│TaskService  │ (业务逻辑层)
└──────┬──────┘
       │
┌──────▼──────┐
│TaskRepository│ (SQLite)
└─────────────┘
```

## 目标架构：Adapter 模式

```
┌─────────────┐
│   CLI/Web   │
└──────┬──────┘
       │
┌──────▼──────────────────────┐
│      TaskService            │ (业务逻辑层)
└──────┬──────────────────────┘
       │
┌──────▼──────────────────────┐
│  TaskRepositoryInterface    │ (抽象接口)
└──────┬──────────────────────┘
       │
       ├─► SQLiteRepository     (本地存储)
       ├─► NotionRepository     (Notion API)
       └─► MicrosoftRepository  (Microsoft To Do API)
```

## 实现步骤

### Phase 1: 抽象仓储接口（已完成）

当前 `TaskRepository` 已实现以下接口：
- `save(task)` - 保存或更新
- `get_by_id(id)` - 获取单个任务
- `list_all(status)` - 列出任务
- `delete(id)` - 删除任务

### Phase 2: 创建 Notion Adapter

#### 字段映射

| Vibe Todo | Notion Database Property |
|-----------|-------------------------|
| title | Title (title) |
| description | Description (rich_text) |
| status | Status (select: To Do/In Progress/Done) |
| priority | Priority (select: Low/Medium/High/Urgent) |
| due_date | Due Date (date) |
| tags | Tags (multi_select) |
| project | Project (relation or select) |
| time_spent | Time Spent (number, minutes) |

#### 实现文件

```python
# src/vibe_todo/adapters/notion_adapter.py

from notion_client import Client
from ..core.models import Task, TaskStatus, TaskPriority
from typing import List, Optional

class NotionRepository:
    def __init__(self, token: str, database_id: str):
        self.client = Client(auth=token)
        self.database_id = database_id
    
    def save(self, task: Task) -> Task:
        # 转换为 Notion API 格式
        properties = {
            "Name": {"title": [{"text": {"content": task.title}}]},
            "Status": {"select": {"name": task.status.value}},
            # ... 其他字段
        }
        
        if task.id:
            # 更新
            self.client.pages.update(task.id, properties=properties)
        else:
            # 创建
            page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            task.id = page["id"]
        
        return task
    
    def get_by_id(self, task_id: str) -> Optional[Task]:
        # 从 Notion 获取并转换
        pass
    
    # ... 实现其他方法
```

### Phase 3: 创建 Microsoft To Do Adapter

#### 字段映射

| Vibe Todo | Microsoft To Do |
|-----------|-----------------|
| title | title |
| description | body.content |
| status | status (notStarted/inProgress/completed) |
| priority | importance (low/normal/high) |
| due_date | dueDateTime |
| tags | categories[] |
| time_spent | *扩展属性* |

#### 实现文件

```python
# src/vibe_todo/adapters/microsoft_adapter.py

from msal import PublicClientApplication
import requests
from ..core.models import Task, TaskStatus, TaskPriority
from typing import List, Optional

class MicrosoftRepository:
    def __init__(self, client_id: str, list_id: str = "tasks"):
        self.client_id = client_id
        self.list_id = list_id
        self.token = None
        self._authenticate()
    
    def _authenticate(self):
        # 使用 MSAL 进行 OAuth2 认证
        app = PublicClientApplication(self.client_id)
        result = app.acquire_token_interactive(
            scopes=["Tasks.ReadWrite"]
        )
        self.token = result["access_token"]
    
    def save(self, task: Task) -> Task:
        headers = {"Authorization": f"Bearer {self.token}"}
        
        body = {
            "title": task.title,
            "body": {"content": task.description},
            "status": self._map_status(task.status),
            "importance": self._map_priority(task.priority),
            # ... 其他字段
        }
        
        if task.id:
            # 更新
            url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{self.list_id}/tasks/{task.id}"
            response = requests.patch(url, json=body, headers=headers)
        else:
            # 创建
            url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{self.list_id}/tasks"
            response = requests.post(url, json=body, headers=headers)
            task.id = response.json()["id"]
        
        return task
    
    # ... 实现其他方法
```

### Phase 4: 配置管理

创建配置文件支持多后端：

```yaml
# config.yaml
backend:
  type: sqlite  # 或 notion, microsoft
  
  sqlite:
    db_path: vibe_todo.db
  
  notion:
    token: secret_xxx
    database_id: xxx
  
  microsoft:
    client_id: xxx
    list_id: tasks
```

### Phase 5: 工厂模式创建仓储

```python
# src/vibe_todo/storage/factory.py

def create_repository(config):
    backend_type = config.get("backend", {}).get("type", "sqlite")
    
    if backend_type == "sqlite":
        return TaskRepository(config["sqlite"]["db_path"])
    elif backend_type == "notion":
        from ..adapters.notion_adapter import NotionRepository
        return NotionRepository(
            token=config["notion"]["token"],
            database_id=config["notion"]["database_id"]
        )
    elif backend_type == "microsoft":
        from ..adapters.microsoft_adapter import MicrosoftRepository
        return MicrosoftRepository(
            client_id=config["microsoft"]["client_id"]
        )
    else:
        raise ValueError(f"Unknown backend: {backend_type}")
```

## 所需依赖

### Notion
```bash
uv pip install notion-client
```

### Microsoft To Do
```bash
uv pip install msal requests
```

## 使用示例

```bash
# 配置使用 Notion
vibe config set-backend notion --token <token> --database <id>

# 配置使用 Microsoft To Do
vibe config set-backend microsoft --client-id <id>

# 切换回本地
vibe config set-backend sqlite
```

## 注意事项

1. **API 限制**: Notion 和 Microsoft 都有 API 调用频率限制
2. **认证**: Microsoft 需要 OAuth2 流程，需要用户授权
3. **字段兼容**: 某些字段可能无法完全映射（如工时追踪）
4. **离线支持**: 建议实现本地缓存 + 云同步机制

## 下一步

1. ✅ 扩展核心模型支持新字段（已完成）
2. ✅ 更新 CLI 支持新字段（已完成）
3. ⏳ 实现 Notion Adapter
4. ⏳ 实现 Microsoft To Do Adapter
5. ⏳ 添加配置管理
6. ⏳ 实现同步机制
