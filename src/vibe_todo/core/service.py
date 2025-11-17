"""核心业务逻辑服务"""
from typing import List, Optional
from datetime import datetime

from .models import Task, TaskStatus, TaskPriority


class TaskService:
    """任务管理服务"""

    def __init__(self, repository):
        """
        Args:
            repository: 任务仓储接口
        """
        self.repository = repository

    def create_task(
        self,
        title_or_task,  # 可以是标题字符串或Task对象
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        project: Optional[str] = None,
    ) -> Task:
        """创建新任务"""
        # 支持两种调用方式
        if isinstance(title_or_task, Task):
            # 直接传入Task对象
            task = title_or_task
        else:
            # 传入单独的参数
            task = Task(
                title=title_or_task,
                description=description,
                priority=priority,
                due_date=due_date,
                tags=tags or [],
                project=project,
            )
        return self.repository.save(task)

    def get_task(self, task_id: int) -> Optional[Task]:
        """获取指定任务"""
        return self.repository.get_by_id(task_id)

    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """列出任务，可按状态筛选"""
        return self.repository.list_all(status=status)

    def update_task(self, task_id: int, title: Optional[str] = None,
                   description: Optional[str] = None) -> Optional[Task]:
        """更新任务信息"""
        task = self.repository.get_by_id(task_id)
        if not task:
            return None

        if title is not None:
            task.title = title
        if description is not None:
            task.description = description

        return self.repository.save(task)

    def mark_done(self, task_id: int) -> Optional[Task]:
        """标记任务为完成"""
        task = self.repository.get_by_id(task_id)
        if not task:
            return None

        task.mark_done()
        return self.repository.save(task)

    def mark_in_progress(self, task_id: int) -> Optional[Task]:
        """标记任务为进行中"""
        task = self.repository.get_by_id(task_id)
        if not task:
            return None

        task.mark_in_progress()
        return self.repository.save(task)

    def add_time(self, task_id: int, minutes: int) -> Optional[Task]:
        """为任务添加工时"""
        task = self.repository.get_by_id(task_id)
        if not task:
            return None

        task.add_time(minutes)
        return self.repository.save(task)

    def delete_task(self, task_id: int) -> bool:
        """删除任务"""
        return self.repository.delete(task_id)

    def get_statistics(self) -> dict:
        """获取任务统计信息"""
        all_tasks = self.repository.list_all()
        total_time = sum(task.time_spent for task in all_tasks)

        return {
            "total": len(all_tasks),
            "todo": len([t for t in all_tasks if t.status == TaskStatus.TODO]),
            "in_progress": len([t for t in all_tasks if t.status == TaskStatus.IN_PROGRESS]),
            "done": len([t for t in all_tasks if t.status == TaskStatus.DONE]),
            "total_time_minutes": total_time,
            "total_time_hours": total_time / 60,
        }
