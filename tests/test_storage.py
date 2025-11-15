"""存储层测试"""
import os

import pytest

from vibe_todo.core.models import Task, TaskStatus
from vibe_todo.storage.repository import TaskRepository


@pytest.fixture
def test_db():
    """测试数据库 fixture"""
    db_path = "test_vibe_todo.db"
    yield db_path
    # 清理测试数据库
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def repository(test_db):
    """Repository fixture"""
    return TaskRepository(db_path=test_db)


class TestTaskRepository:
    """测试 TaskRepository"""

    def test_save_new_task(self, repository):
        task = Task(title="新任务", description="描述")
        saved = repository.save(task)

        assert saved.id is not None
        assert saved.title == "新任务"
        assert saved.description == "描述"

    def test_save_update_task(self, repository):
        task = Task(title="原标题")
        saved = repository.save(task)

        saved.title = "新标题"
        updated = repository.save(saved)

        assert updated.id == saved.id
        assert updated.title == "新标题"

    def test_get_by_id(self, repository):
        task = Task(title="任务")
        saved = repository.save(task)

        retrieved = repository.get_by_id(saved.id)
        assert retrieved is not None
        assert retrieved.id == saved.id
        assert retrieved.title == "任务"

    def test_get_by_id_not_found(self, repository):
        retrieved = repository.get_by_id(999)
        assert retrieved is None

    def test_list_all(self, repository):
        repository.save(Task(title="任务1"))
        repository.save(Task(title="任务2"))

        tasks = repository.list_all()
        assert len(tasks) == 2

    def test_list_all_by_status(self, repository):
        task1 = Task(title="任务1")
        task2 = Task(title="任务2")
        task2.mark_done()

        repository.save(task1)
        repository.save(task2)

        todo_tasks = repository.list_all(status=TaskStatus.TODO)
        assert len(todo_tasks) == 1
        assert todo_tasks[0].title == "任务1"

        done_tasks = repository.list_all(status=TaskStatus.DONE)
        assert len(done_tasks) == 1
        assert done_tasks[0].title == "任务2"

    def test_delete(self, repository):
        task = Task(title="任务")
        saved = repository.save(task)

        assert repository.delete(saved.id) is True
        assert repository.get_by_id(saved.id) is None

    def test_delete_not_found(self, repository):
        assert repository.delete(999) is False

    def test_persistence(self, test_db):
        # 创建任务并保存
        repo1 = TaskRepository(db_path=test_db)
        task = Task(title="持久化测试")
        saved = repo1.save(task)
        task_id = saved.id

        # 新建 repository 实例，验证数据已持久化
        repo2 = TaskRepository(db_path=test_db)
        retrieved = repo2.get_by_id(task_id)

        assert retrieved is not None
        assert retrieved.title == "持久化测试"
