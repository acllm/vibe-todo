"""数据格式定义和验证"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from ..core.models import Task, TaskStatus, TaskPriority


class ExportFormat(Enum):
    """导出格式"""
    JSON = "json"
    CSV = "csv"


class DataValidator:
    """数据验证器"""
    
    REQUIRED_FIELDS = ["title", "status", "priority"]
    VALID_STATUSES = {s.value for s in TaskStatus}
    VALID_PRIORITIES = {p.value for p in TaskPriority}
    
    @classmethod
    def validate_task_dict(cls, data: Dict[str, Any]) -> List[str]:
        """
        验证任务字典数据
        
        返回错误列表，空列表表示验证通过
        """
        errors = []
        
        # 检查必需字段
        for field in cls.REQUIRED_FIELDS:
            if field not in data or not data[field]:
                errors.append(f"缺少必需字段: {field}")
        
        # 验证状态
        if "status" in data and data["status"] not in cls.VALID_STATUSES:
            errors.append(f"无效的状态: {data['status']}")
        
        # 验证优先级
        if "priority" in data and data["priority"] not in cls.VALID_PRIORITIES:
            errors.append(f"无效的优先级: {data['priority']}")
        
        # 验证日期格式
        if "due_date" in data and data["due_date"]:
            try:
                datetime.fromisoformat(data["due_date"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                errors.append(f"无效的日期格式: {data['due_date']}")
        
        # 验证工时
        if "time_spent_minutes" in data:
            try:
                minutes = int(data["time_spent_minutes"])
                if minutes < 0:
                    errors.append("工时不能为负数")
            except (ValueError, TypeError):
                errors.append(f"无效的工时: {data['time_spent_minutes']}")
        
        return errors
    
    @classmethod
    def validate_export_data(cls, data: Dict[str, Any]) -> List[str]:
        """验证导出数据格式"""
        errors = []
        
        if "version" not in data:
            errors.append("缺少版本信息")
        
        if "tasks" not in data:
            errors.append("缺少任务数据")
        elif not isinstance(data["tasks"], list):
            errors.append("任务数据必须是列表")
        
        return errors


def task_to_dict(task: Task) -> Dict[str, Any]:
    """将 Task 对象转换为字典"""
    return {
        "id": str(task.id),
        "title": task.title,
        "description": task.description or "",
        "status": task.status.value,
        "priority": task.priority.value,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "tags": task.tags or [],
        "project": task.project or "",
        "time_spent_minutes": task.time_spent,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }


def dict_to_task(data: Dict[str, Any]) -> Task:
    """将字典转换为 Task 对象（不包含 ID）"""
    due_date = None
    if data.get("due_date"):
        due_date_str = data["due_date"].replace("Z", "+00:00")
        due_date = datetime.fromisoformat(due_date_str)
    
    return Task(
        title=data["title"],
        description=data.get("description") or "",
        status=TaskStatus(data["status"]),
        priority=TaskPriority(data["priority"]),
        due_date=due_date,
        tags=data.get("tags") or [],
        project=data.get("project") or None,
        time_spent=int(data.get("time_spent_minutes", 0)),
    )
