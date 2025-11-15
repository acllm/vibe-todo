"""Microsoft To Do 后端适配器"""
from typing import List, Optional
from datetime import datetime
import json
import os

from ..core.models import Task, TaskStatus, TaskPriority
from . import TaskRepositoryInterface


class MicrosoftRepository(TaskRepositoryInterface):
    """Microsoft To Do 适配器"""
    
    def __init__(self, client_id: str, list_id: str = None, token_cache_path: str = ".mstodo_token"):
        """
        Args:
            client_id: Azure AD Application (client) ID
            list_id: To Do List ID (默认使用 "tasks" 列表)
            token_cache_path: Token 缓存文件路径
        """
        try:
            from msal import PublicClientApplication
            import requests
        except ImportError:
            raise ImportError("请安装依赖: uv pip install msal requests")
        
        self.client_id = client_id
        self.list_id = list_id
        self.token_cache_path = token_cache_path
        self.token = None
        self.requests = __import__('requests')
        
        # 初始化 MSAL
        self.app = PublicClientApplication(
            client_id=client_id,
            authority="https://login.microsoftonline.com/common"
        )
        
        self._authenticate()
        
        # 如果没有指定 list_id，获取默认列表
        if not self.list_id:
            self.list_id = self._get_default_list_id()
    
    def _authenticate(self):
        """OAuth2 认证"""
        # 尝试从缓存加载 token
        if os.path.exists(self.token_cache_path):
            try:
                with open(self.token_cache_path, 'r') as f:
                    cache_data = json.load(f)
                    self.token = cache_data.get("access_token")
                    # 简单验证 token 是否有效
                    if self._verify_token():
                        return
            except Exception:
                pass
        
        # 需要重新认证
        scopes = ["Tasks.ReadWrite", "User.Read"]
        
        # 先尝试静默获取
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(scopes, account=accounts[0])
            if result and "access_token" in result:
                self.token = result["access_token"]
                self._save_token(result)
                return
        
        # 交互式认证
        result = self.app.acquire_token_interactive(scopes=scopes)
        
        if "access_token" in result:
            self.token = result["access_token"]
            self._save_token(result)
        else:
            raise RuntimeError(f"认证失败: {result.get('error_description', 'Unknown error')}")
    
    def _verify_token(self) -> bool:
        """验证 token 是否有效"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = self.requests.get(
                "https://graph.microsoft.com/v1.0/me",
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def _save_token(self, result: dict):
        """保存 token 到缓存"""
        try:
            with open(self.token_cache_path, 'w') as f:
                json.dump({
                    "access_token": result["access_token"],
                    "expires_at": datetime.now().timestamp() + result.get("expires_in", 3600)
                }, f)
        except Exception:
            pass
    
    def _get_default_list_id(self) -> str:
        """获取默认任务列表 ID"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.requests.get(
            "https://graph.microsoft.com/v1.0/me/todo/lists",
            headers=headers
        )
        
        if response.status_code == 200:
            lists = response.json()["value"]
            # 查找默认的 "Tasks" 列表
            for lst in lists:
                if lst.get("wellknownListName") == "defaultList":
                    return lst["id"]
            # 如果没有找到，返回第一个
            if lists:
                return lists[0]["id"]
        
        raise RuntimeError("无法获取 Microsoft To Do 列表")
    
    def _task_to_mstodo(self, task: Task) -> dict:
        """将 Task 转换为 Microsoft To Do 格式"""
        body = {
            "title": task.title,
            "importance": self._map_priority_to_mstodo(task.priority),
            "status": self._map_status_to_mstodo(task.status),
        }
        
        # 描述
        if task.description:
            body["body"] = {
                "content": task.description,
                "contentType": "text"
            }
        
        # 截止日期
        if task.due_date:
            body["dueDateTime"] = {
                "dateTime": task.due_date.isoformat(),
                "timeZone": "UTC"
            }
        
        # 标签（Microsoft To Do 用 categories）
        if task.tags:
            body["categories"] = task.tags
        
        return body
    
    def _mstodo_to_task(self, mstodo_task: dict) -> Task:
        """将 Microsoft To Do 任务转换为 Task 对象"""
        # 提取基本信息
        title = mstodo_task.get("title", "")
        description = ""
        if mstodo_task.get("body"):
            description = mstodo_task["body"].get("content", "")
        
        # 状态
        status = self._map_mstodo_to_status(mstodo_task.get("status", "notStarted"))
        
        # 优先级
        priority = self._map_mstodo_to_priority(mstodo_task.get("importance", "normal"))
        
        # 截止日期
        due_date = None
        if mstodo_task.get("dueDateTime"):
            due_str = mstodo_task["dueDateTime"]["dateTime"]
            due_date = datetime.fromisoformat(due_str.replace("Z", "+00:00"))
        
        # 标签
        tags = mstodo_task.get("categories", [])
        
        # 时间戳
        created_at = datetime.fromisoformat(
            mstodo_task["createdDateTime"].replace("Z", "+00:00")
        )
        updated_at = datetime.fromisoformat(
            mstodo_task["lastModifiedDateTime"].replace("Z", "+00:00")
        )
        
        # Microsoft To Do 不支持工时，使用扩展属性存储（这里简化处理）
        time_spent = 0
        
        # Microsoft To Do 的项目概念不明确，使用列表名称
        project = None
        
        return Task(
            task_id=mstodo_task["id"],
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
    
    def _map_status_to_mstodo(self, status: TaskStatus) -> str:
        """映射状态到 Microsoft To Do"""
        mapping = {
            TaskStatus.TODO: "notStarted",
            TaskStatus.IN_PROGRESS: "inProgress",
            TaskStatus.DONE: "completed",
        }
        return mapping[status]
    
    def _map_mstodo_to_status(self, mstodo_status: str) -> TaskStatus:
        """映射 Microsoft To Do 状态到内部状态"""
        mapping = {
            "notStarted": TaskStatus.TODO,
            "inProgress": TaskStatus.IN_PROGRESS,
            "completed": TaskStatus.DONE,
        }
        return mapping.get(mstodo_status, TaskStatus.TODO)
    
    def _map_priority_to_mstodo(self, priority: TaskPriority) -> str:
        """映射优先级到 Microsoft To Do"""
        mapping = {
            TaskPriority.LOW: "low",
            TaskPriority.MEDIUM: "normal",
            TaskPriority.HIGH: "high",
            TaskPriority.URGENT: "high",  # Microsoft 只有三级
        }
        return mapping[priority]
    
    def _map_mstodo_to_priority(self, mstodo_priority: str) -> TaskPriority:
        """映射 Microsoft To Do 优先级到内部优先级"""
        mapping = {
            "low": TaskPriority.LOW,
            "normal": TaskPriority.MEDIUM,
            "high": TaskPriority.HIGH,
        }
        return mapping.get(mstodo_priority, TaskPriority.MEDIUM)
    
    def save(self, task: Task) -> Task:
        """保存或更新任务"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        body = self._task_to_mstodo(task)
        
        if task.id:
            # 更新现有任务
            url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{self.list_id}/tasks/{task.id}"
            response = self.requests.patch(url, json=body, headers=headers)
        else:
            # 创建新任务
            url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{self.list_id}/tasks"
            response = self.requests.post(url, json=body, headers=headers)
        
        if response.status_code in [200, 201]:
            return self._mstodo_to_task(response.json())
        else:
            raise RuntimeError(f"保存任务失败: {response.text}")
    
    def get_by_id(self, task_id: str) -> Optional[Task]:
        """根据 ID 获取任务"""
        headers = {"Authorization": f"Bearer {self.token}"}
        url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{self.list_id}/tasks/{task_id}"
        
        response = self.requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return self._mstodo_to_task(response.json())
        return None
    
    def list_all(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """列出所有任务，可按状态筛选"""
        headers = {"Authorization": f"Bearer {self.token}"}
        url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{self.list_id}/tasks"
        
        # Microsoft Graph API 支持 $filter
        if status:
            mstodo_status = self._map_status_to_mstodo(status)
            url += f"?$filter=status eq '{mstodo_status}'"
        
        response = self.requests.get(url, headers=headers)
        
        if response.status_code == 200:
            tasks = []
            for mstodo_task in response.json()["value"]:
                tasks.append(self._mstodo_to_task(mstodo_task))
            return tasks
        else:
            raise RuntimeError(f"查询任务失败: {response.text}")
    
    def delete(self, task_id: str) -> bool:
        """删除任务"""
        headers = {"Authorization": f"Bearer {self.token}"}
        url = f"https://graph.microsoft.com/v1.0/me/todo/lists/{self.list_id}/tasks/{task_id}"
        
        response = self.requests.delete(url, headers=headers)
        return response.status_code == 204
