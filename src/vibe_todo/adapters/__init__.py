"""仓储抽象接口"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..core.models import Task, TaskStatus


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
