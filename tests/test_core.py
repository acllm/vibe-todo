"""核心模块测试"""

import pytest

from vibe_todo.core.models import Task, TaskStatus
from vibe_todo.core.service import TaskService


class MockRepository:
    """模拟仓储用于测试"""

    def __init__(self):
        self.tasks = {}
        self.next_id = 1

    def save(self, task: Task) -> Task:
        if task.id is None:
            task.id = self.next_id
            self.next_id += 1
        self.tasks[task.id] = task
        return task

    def get_by_id(self, task_id: int):
        return self.tasks.get(task_id)

    def list_all(self, status=None):
        tasks = list(self.tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks

    def delete(self, task_id: int) -> bool:
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False


class TestTask:
    """测试 Task 模型"""

    def test_create_task(self):
        task = Task(title="测试任务", description="描述")
        assert task.title == "测试任务"
        assert task.description == "描述"
        assert task.status == TaskStatus.TODO
        assert task.time_spent == 0

    def test_mark_done(self):
        task = Task(title="测试任务")
        task.mark_done()
        assert task.status == TaskStatus.DONE

    def test_mark_in_progress(self):
        task = Task(title="测试任务")
        task.mark_in_progress()
        assert task.status == TaskStatus.IN_PROGRESS

    def test_add_time(self):
        task = Task(title="测试任务")
        task.add_time(30)
        assert task.time_spent == 30
        task.add_time(45)
        assert task.time_spent == 75

    def test_format_time_spent(self):
        task = Task(title="测试任务")
        task.add_time(30)
        assert task.format_time_spent() == "30m"

        task.add_time(90)
        assert task.format_time_spent() == "2h 0m"

        task.add_time(15)
        assert task.format_time_spent() == "2h 15m"


class TestTaskService:
    """测试 TaskService"""

    @pytest.fixture
    def service(self):
        repository = MockRepository()
        return TaskService(repository)

    def test_create_task(self, service):
        task = service.create_task("新任务", "描述")
        assert task.id == 1
        assert task.title == "新任务"
        assert task.description == "描述"

    def test_get_task(self, service):
        created = service.create_task("任务1")
        retrieved = service.get_task(created.id)
        assert retrieved.id == created.id
        assert retrieved.title == created.title

    def test_list_tasks(self, service):
        service.create_task("任务1")
        service.create_task("任务2")
        tasks = service.list_tasks()
        assert len(tasks) == 2

    def test_list_tasks_by_status(self, service):
        task1 = service.create_task("任务1")
        task2 = service.create_task("任务2")
        service.mark_done(task1.id)

        done_tasks = service.list_tasks(status=TaskStatus.DONE)
        assert len(done_tasks) == 1
        assert done_tasks[0].id == task1.id

        todo_tasks = service.list_tasks(status=TaskStatus.TODO)
        assert len(todo_tasks) == 1
        assert todo_tasks[0].id == task2.id

    def test_update_task(self, service):
        task = service.create_task("原标题")
        updated = service.update_task(task.id, title="新标题", description="新描述")
        assert updated.title == "新标题"
        assert updated.description == "新描述"

    def test_mark_done(self, service):
        task = service.create_task("任务")
        updated = service.mark_done(task.id)
        assert updated.status == TaskStatus.DONE

    def test_mark_in_progress(self, service):
        task = service.create_task("任务")
        updated = service.mark_in_progress(task.id)
        assert updated.status == TaskStatus.IN_PROGRESS

    def test_add_time(self, service):
        task = service.create_task("任务")
        updated = service.add_time(task.id, 60)
        assert updated.time_spent == 60

    def test_delete_task(self, service):
        task = service.create_task("任务")
        assert service.delete_task(task.id) is True
        assert service.get_task(task.id) is None

    def test_get_statistics(self, service):
        task1 = service.create_task("任务1")
        task2 = service.create_task("任务2")
        task3 = service.create_task("任务3")

        service.mark_in_progress(task1.id)
        service.mark_done(task2.id)
        service.add_time(task1.id, 60)
        service.add_time(task2.id, 90)

        stats = service.get_statistics()
        assert stats["total"] == 3
        assert stats["todo"] == 1
        assert stats["in_progress"] == 1
        assert stats["done"] == 1
        assert stats["total_time_minutes"] == 150
        assert stats["total_time_hours"] == 2.5
