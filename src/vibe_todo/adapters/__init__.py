"""仓储抽象接口"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from ..core.models import Task, TaskPriority, TaskStatus


@dataclass
class TaskFilter:
    """任务过滤条件"""
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    project: Optional[str] = None
    tags: Optional[List[str]] = None
    tags_operator: str = "OR"  # "AND" 或 "OR"
    overdue_only: bool = False
    due_in_days: Optional[int] = None

    def has_any_filter(self) -> bool:
        """检查是否有任何过滤条件"""
        return any([
            self.status is not None,
            self.priority is not None,
            self.project is not None,
            self.tags is not None,
            self.overdue_only,
            self.due_in_days is not None,
        ])


class TaskRepositoryInterface(ABC):
    """任务仓储接口 - 所有后端适配器都需要实现此接口"""

    @abstractmethod
    def save(self, task: Task) -> Task:
        """保存或更新任务"""
        pass

    @abstractmethod
    def get_by_id(self, task_id) -> Optional[Task]:
        """根据 ID 获取任务"""
        pass

    @abstractmethod
    def list_all(self, status: Optional[TaskStatus] = None) -> List[Task]:
        """列出所有任务，可按状态筛选"""
        pass

    @abstractmethod
    def delete(self, task_id) -> bool:
        """删除任务"""
        pass

    def search(self, query: str) -> List[Task]:
        """全文搜索任务
        
        Args:
            query: 搜索关键词
            
        Returns:
            匹配的任务列表
        """
        # 默认实现：简单的字符串匹配
        all_tasks = self.list_all()
        query_lower = query.lower()
        return [
            task for task in all_tasks
            if query_lower in task.title.lower()
            or query_lower in task.description.lower()
            or any(query_lower in tag.lower() for tag in task.tags)
            or (task.project and query_lower in task.project.lower())
        ]

    def filter_tasks(self, task_filter: TaskFilter) -> List[Task]:
        """高级过滤任务
        
        Args:
            task_filter: 过滤条件
            
        Returns:
            符合条件的任务列表
        """
        # 默认实现：在内存中过滤
        tasks = self.list_all()

        if task_filter.status:
            tasks = [t for t in tasks if t.status == task_filter.status]

        if task_filter.priority:
            tasks = [t for t in tasks if t.priority == task_filter.priority]

        if task_filter.project:
            tasks = [t for t in tasks if t.project == task_filter.project]

        if task_filter.tags:
            if task_filter.tags_operator == "AND":
                tasks = [t for t in tasks if all(tag in t.tags for tag in task_filter.tags)]
            else:  # OR
                tasks = [t for t in tasks if any(tag in t.tags for tag in task_filter.tags)]

        if task_filter.overdue_only:
            tasks = [t for t in tasks if t.is_overdue()]

        if task_filter.due_in_days is not None:
            tasks = [
                t for t in tasks
                if t.due_date and t.days_until_due() is not None
                and 0 <= t.days_until_due() <= task_filter.due_in_days
            ]

        return tasks

    def search_and_filter(self, query: Optional[str] = None, task_filter: Optional[TaskFilter] = None) -> List[Task]:
        """组合搜索和过滤
        
        Args:
            query: 搜索关键词（可选）
            task_filter: 过滤条件（可选）
            
        Returns:
            匹配的任务列表
        """
        if query:
            tasks = self.search(query)
        else:
            tasks = self.list_all()

        if task_filter and task_filter.has_any_filter():
            # 需要先获取所有任务再过滤，因为 search 可能已经过滤了
            if query:
                # 如果有搜索，先过滤 search 结果
                filtered_tasks = []
                all_tasks = {t.id: t for t in self.list_all()}
                for task in tasks:
                    full_task = all_tasks.get(task.id, task)
                    # 临时替换为完整任务进行过滤
                    filtered = self._filter_single_task(full_task, task_filter)
                    if filtered:
                        filtered_tasks.append(task)
                tasks = filtered_tasks
            else:
                tasks = self.filter_tasks(task_filter)

        return tasks

    def _filter_single_task(self, task: Task, task_filter: TaskFilter) -> bool:
        """过滤单个任务（内部辅助方法）"""
        if task_filter.status and task.status != task_filter.status:
            return False

        if task_filter.priority and task.priority != task_filter.priority:
            return False

        if task_filter.project and task.project != task_filter.project:
            return False

        if task_filter.tags:
            if task_filter.tags_operator == "AND":
                if not all(tag in task.tags for tag in task_filter.tags):
                    return False
            else:
                if not any(tag in task.tags for tag in task_filter.tags):
                    return False

        if task_filter.overdue_only and not task.is_overdue():
            return False

        if task_filter.due_in_days is not None:
            if not (task.due_date and task.days_until_due() is not None
                   and 0 <= task.days_until_due() <= task_filter.due_in_days):
                return False

        return True
