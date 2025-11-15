"""Notion 后端适配器"""
from typing import List, Optional
from datetime import datetime

from ..core.models import Task, TaskStatus, TaskPriority
from . import TaskRepositoryInterface


class NotionRepository(TaskRepositoryInterface):
    """Notion 数据库适配器"""
    
    def __init__(self, token: str, database_id: str):
        """
        Args:
            token: Notion Integration Token
            database_id: Notion Database ID
        """
        try:
            from notion_client import Client
        except ImportError:
            raise ImportError("请安装 notion-client: uv pip install notion-client")
        
        self.client = Client(auth=token)
        self.database_id = database_id
        self.data_source_id = None  # 缓存 data source ID
        self._verify_and_get_data_source()
    
    def _verify_and_get_data_source(self):
        """验证数据库是否可访问并获取 data source ID"""
        try:
            # 获取数据库信息
            db_info = self.client.databases.retrieve(database_id=self.database_id)
            
            # 从数据库信息中提取 data_source_id
            # 根据 Notion API 文档，数据库对象可能包含 data_sources 字段
            # 文档地址 https://developers.notion.com/reference/database-retrieve
            if "data_sources" in db_info and isinstance(db_info["data_sources"], list):
                if "id" in db_info["data_sources"][0]:
                    self.data_source_id = db_info["data_sources"][0]["id"]
                else:
                    # 没有单独的 data_source.id，使用 database_id
                    self.data_source_id = self.database_id
            else:
                # 如果没有 data_sources 字段，这是传统数据库，使用 database_id
                self.data_source_id = self.database_id
                
        except Exception as e:
            raise RuntimeError(f"无法访问 Notion 数据库: {e}")
    
    def _task_to_properties(self, task: Task) -> dict:
        """将 Task 转换为 Notion 属性格式"""
        properties = {
            "Name": {
                "title": [{"text": {"content": task.title}}]
            },
            "Description": {
                "rich_text": [{"text": {"content": task.description}}]
            } if task.description else {"rich_text": []},
            "Status": {
                "select": {"name": self._map_status_to_notion(task.status)}
            },
            "Priority": {
                "select": {"name": self._map_priority_to_notion(task.priority)}
            },
            "Time Spent": {
                "number": task.time_spent
            },
        }
        
        # 截止日期
        if task.due_date:
            properties["Due Date"] = {
                "date": {"start": task.due_date.isoformat()}
            }
        
        # 标签
        if task.tags:
            properties["Tags"] = {
                "multi_select": [{"name": tag} for tag in task.tags]
            }
        
        # 项目
        if task.project:
            properties["Project"] = {
                "select": {"name": task.project}
            }
        
        return properties
    
    def _properties_to_task(self, page: dict) -> Task:
        """将 Notion 页面转换为 Task 对象"""
        props = page["properties"]
        
        # 提取标题
        title = ""
        if props.get("Name", {}).get("title"):
            title = props["Name"]["title"][0]["text"]["content"]
        
        # 提取描述
        description = ""
        if props.get("Description", {}).get("rich_text"):
            description = props["Description"]["rich_text"][0]["text"]["content"]
        
        # 提取状态
        status_name = props.get("Status", {}).get("select", {}).get("name", "To Do")
        status = self._map_notion_to_status(status_name)
        
        # 提取优先级
        priority_name = props.get("Priority", {}).get("select", {}).get("name", "Medium")
        priority = self._map_notion_to_priority(priority_name)
        
        # 提取工时
        time_spent = props.get("Time Spent", {}).get("number", 0)
        
        # 提取截止日期
        due_date = None
        if props.get("Due Date", {}).get("date"):
            due_str = props["Due Date"]["date"]["start"]
            due_date = datetime.fromisoformat(due_str.replace("Z", "+00:00"))
        
        # 提取标签
        tags = []
        if props.get("Tags", {}).get("multi_select"):
            tags = [tag["name"] for tag in props["Tags"]["multi_select"]]
        
        # 提取项目
        project = None
        if props.get("Project", {}).get("select"):
            project = props["Project"]["select"]["name"]
        
        # 提取时间戳
        created_at = datetime.fromisoformat(page["created_time"].replace("Z", "+00:00"))
        updated_at = datetime.fromisoformat(page["last_edited_time"].replace("Z", "+00:00"))
        
        return Task(
            task_id=page["id"],
            title=title,
            description=description,
            status=status,
            priority=priority,
            time_spent=time_spent,
            due_date=due_date,
            tags=tags,
            project=project,
            created_at=created_at,
            updated_at=updated_at,
        )
    
    def _map_status_to_notion(self, status: TaskStatus) -> str:
        """映射状态到 Notion"""
        mapping = {
            TaskStatus.TODO: "To Do",
            TaskStatus.IN_PROGRESS: "In Progress",
            TaskStatus.DONE: "Done",
        }
        return mapping[status]
    
    def _map_notion_to_status(self, notion_status: str) -> TaskStatus:
        """映射 Notion 状态到内部状态"""
        mapping = {
            "To Do": TaskStatus.TODO,
            "In Progress": TaskStatus.IN_PROGRESS,
            "Done": TaskStatus.DONE,
        }
        return mapping.get(notion_status, TaskStatus.TODO)
    
    def _map_priority_to_notion(self, priority: TaskPriority) -> str:
        """映射优先级到 Notion"""
        mapping = {
            TaskPriority.LOW: "Low",
            TaskPriority.MEDIUM: "Medium",
            TaskPriority.HIGH: "High",
            TaskPriority.URGENT: "Urgent",
        }
        return mapping[priority]
    
    def _map_notion_to_priority(self, notion_priority: str) -> TaskPriority:
        """映射 Notion 优先级到内部优先级"""
        mapping = {
            "Low": TaskPriority.LOW,
            "Medium": TaskPriority.MEDIUM,
            "High": TaskPriority.HIGH,
            "Urgent": TaskPriority.URGENT,
        }
        return mapping.get(notion_priority, TaskPriority.MEDIUM)
    
    def save(self, task: Task) -> Task:
        """保存或更新任务"""
        properties = self._task_to_properties(task)
        
        if task.id:
            # 更新现有页面
            try:
                page = self.client.pages.update(
                    page_id=task.id,
                    properties=properties
                )
                return self._properties_to_task(page)
            except Exception as e:
                raise RuntimeError(f"更新 Notion 任务失败: {e}")
        else:
            # 创建新页面
            try:
                page = self.client.pages.create(
                    parent={"database_id": self.database_id},
                    properties=properties
                )
                return self._properties_to_task(page)
            except Exception as e:
                raise RuntimeError(f"创建 Notion 任务失败: {e}")
    
    def get_by_id(self, task_id: str) -> Optional[Task]:
        """根据 ID 获取任务"""
        try:
            page = self.client.pages.retrieve(page_id=task_id)
            return self._properties_to_task(page)
        except Exception:
            return None
    
    def list_all(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """列出所有任务，可按状态筛选"""
        # 构建查询参数
        query_params = {
            "data_source_id": self.data_source_id
        }
        
        # 添加过滤器
        if status:
            query_params["filter"] = {
                "property": "Status",
                "select": {
                    "equals": self._map_status_to_notion(status)
                }
            }
        
        # 添加排序
        query_params["sorts"] = [
            {
                "timestamp": "created_time",
                "direction": "descending"
            }
        ]
        
        try:
            # 使用 SDK 的高级 API: data_sources.query()
            response = self.client.data_sources.query(**query_params)
            
            tasks = []
            for page in response.get("results", []):
                tasks.append(self._properties_to_task(page))
            
            return tasks
        except Exception as e:
            raise RuntimeError(f"查询 Notion 任务失败: {e}")
    
    def delete(self, task_id: str) -> bool:
        """删除任务（归档到 Notion）"""
        try:
            self.client.pages.update(
                page_id=task_id,
                archived=True
            )
            return True
        except Exception:
            return False
