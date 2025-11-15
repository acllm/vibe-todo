"""核心领域模型"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List


class TaskStatus(Enum):
    """任务状态"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(Enum):
    """任务优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task:
    """任务模型 - 兼容 Notion、Microsoft To Do 等服务"""

    def __init__(
        self,
        title: str,
        description: str = "",
        status: TaskStatus = TaskStatus.TODO,
        time_spent: int = 0,  # 单位：分钟
        task_id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        # 扩展字段：兼容主流 Todo 服务
        due_date: Optional[datetime] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        tags: Optional[List[str]] = None,
        project: Optional[str] = None,  # 项目/列表名称
    ):
        self.id = task_id
        self.title = title
        self.description = description
        self.status = status
        self.time_spent = time_spent
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.due_date = due_date
        self.priority = priority
        self.tags = tags or []
        self.project = project
    
    @staticmethod
    def _get_now_aware() -> datetime:
        """获取当前时间（带时区信息）"""
        return datetime.now(timezone.utc)
    
    @staticmethod
    def _make_aware(dt: datetime) -> datetime:
        """确保 datetime 对象带时区信息"""
        if dt.tzinfo is None:
            # 假设 naive datetime 是本地时间，转换为 UTC
            return dt.replace(tzinfo=timezone.utc)
        return dt

    def mark_done(self):
        """标记任务为完成"""
        self.status = TaskStatus.DONE
        self.updated_at = datetime.now()

    def mark_in_progress(self):
        """标记任务为进行中"""
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now()

    def add_time(self, minutes: int):
        """增加工时（分钟）"""
        if minutes > 0:
            self.time_spent += minutes
            self.updated_at = datetime.now()

    def format_time_spent(self) -> str:
        """格式化工时显示"""
        hours = self.time_spent // 60
        minutes = self.time_spent % 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    
    def is_overdue(self) -> bool:
        """检查是否逾期"""
        if self.due_date and self.status != TaskStatus.DONE:
            # 统一处理时区问题
            now = self._get_now_aware()
            due = self._make_aware(self.due_date)
            return now > due
        return False
    
    def days_until_due(self) -> Optional[int]:
        """距离截止日期的天数"""
        if self.due_date:
            # 统一处理时区问题
            now = self._get_now_aware()
            due = self._make_aware(self.due_date)
            delta = due - now
            return delta.days
        return None

    def __repr__(self):
        return f"<Task {self.id}: {self.title} ({self.status.value})>"
