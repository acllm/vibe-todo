"""测试批量操作功能"""

import pytest

from vibe_todo.core import Task, TaskStatus, TaskPriority, TaskService
from vibe_todo.storage.repository import TaskRepository


@pytest.fixture
def service():
    """创建测试服务"""
    repository = TaskRepository(":memory:")
    return TaskService(repository)


@pytest.fixture
def sample_tasks(service):
    """创建示例任务"""
    tasks = []
    for i in range(5):
        task = service.create_task(
            f"任务{i+1}",
            description=f"描述{i+1}",
            priority=TaskPriority.MEDIUM,
            tags=[f"tag{i+1}"],
        )
        tasks.append(task)
    return tasks


class TestBatchOperations:
    """测试批量操作"""
    
    def test_batch_update_status(self, service, sample_tasks):
        """测试批量更新状态"""
        # 批量标记为完成
        task_ids = [str(task.id) for task in sample_tasks[:3]]
        count = service.batch_update_status(task_ids, TaskStatus.DONE)
        
        assert count == 3
        
        # 验证状态已更新
        for task_id in task_ids:
            task = service.get_task(task_id)
            assert task.status == TaskStatus.DONE
        
        # 验证其他任务未受影响
        task4 = service.get_task(str(sample_tasks[3].id))
        assert task4.status == TaskStatus.TODO
    
    def test_batch_delete(self, service, sample_tasks):
        """测试批量删除"""
        task_ids = [str(task.id) for task in sample_tasks[:2]]
        count = service.batch_delete(task_ids)
        
        assert count == 2
        
        # 验证任务已删除
        for task_id in task_ids:
            assert service.get_task(task_id) is None
        
        # 验证其他任务仍存在
        remaining_tasks = service.list_tasks()
        assert len(remaining_tasks) == 3
    
    def test_batch_add_tags(self, service, sample_tasks):
        """测试批量添加标签"""
        task_ids = [str(task.id) for task in sample_tasks[:3]]
        new_tags = ["urgent", "review"]
        count = service.batch_add_tags(task_ids, new_tags)
        
        assert count == 3
        
        # 验证标签已添加
        for task_id in task_ids:
            task = service.get_task(task_id)
            assert "urgent" in task.tags
            assert "review" in task.tags
            # 原有标签应该保留
            assert len(task.tags) >= 2
    
    def test_batch_update_priority(self, service, sample_tasks):
        """测试批量更新优先级"""
        task_ids = [str(task.id) for task in sample_tasks[:4]]
        count = service.batch_update_priority(task_ids, TaskPriority.HIGH)
        
        assert count == 4
        
        # 验证优先级已更新
        for task_id in task_ids:
            task = service.get_task(task_id)
            assert task.priority == TaskPriority.HIGH
    
    def test_batch_update_project(self, service, sample_tasks):
        """测试批量设置项目"""
        task_ids = [str(task.id) for task in sample_tasks]
        project_name = "Q1 Sprint"
        count = service.batch_update_project(task_ids, project_name)
        
        assert count == 5
        
        # 验证项目已设置
        for task_id in task_ids:
            task = service.get_task(task_id)
            assert task.project == project_name
    
    def test_batch_operations_with_invalid_ids(self, service, sample_tasks):
        """测试批量操作包含无效ID"""
        valid_ids = [str(sample_tasks[0].id)]
        invalid_ids = ["9999", "invalid"]
        task_ids = valid_ids + invalid_ids
        
        # 批量删除应该只删除有效的任务
        count = service.batch_delete(task_ids)
        assert count == 1
        
        # 有效任务应该被删除
        assert service.get_task(valid_ids[0]) is None
        
        # 其他任务仍然存在
        remaining = service.list_tasks()
        assert len(remaining) == 4
