"""测试交互式编辑功能"""
import pytest
from datetime import datetime, timedelta
from src.vibe_todo.core.models import Task, TaskStatus, TaskPriority
from src.vibe_todo.core.service import TaskService
from src.vibe_todo.storage.repository import TaskRepository
import tempfile
import os


@pytest.fixture
def temp_db():
    """创建临时数据库"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except Exception:
        pass


@pytest.fixture
def repo(temp_db):
    """创建测试用的仓储"""
    return TaskRepository(db_path=temp_db)


@pytest.fixture
def service(repo):
    """创建测试用的服务"""
    return TaskService(repo)


@pytest.fixture
def sample_task(service):
    """创建一个示例任务"""
    task = Task(
        title="原始任务",
        description="原始描述",
        status=TaskStatus.TODO,
        priority=TaskPriority.MEDIUM,
        tags=["tag1", "tag2"],
        project="原始项目",
        due_date=datetime.now() + timedelta(days=7)
    )
    return service.create_task(task)


class TestUpdateTask:
    """测试 TaskService.update_task 方法"""
    
    def test_update_task_with_object(self, service, sample_task):
        """测试通过 Task 对象完整更新"""
        # 修改任务
        sample_task.title = "更新后的标题"
        sample_task.description = "更新后的描述"
        sample_task.status = TaskStatus.IN_PROGRESS
        sample_task.priority = TaskPriority.HIGH
        sample_task.tags = ["newtag1", "newtag2"]
        sample_task.project = "新项目"
        sample_task.due_date = datetime.now() + timedelta(days=14)
        
        # 更新
        updated = service.update_task(sample_task)
        
        # 验证
        assert updated is not None
        assert updated.id == sample_task.id
        assert updated.title == "更新后的标题"
        assert updated.description == "更新后的描述"
        assert updated.status == TaskStatus.IN_PROGRESS
        assert updated.priority == TaskPriority.HIGH
        assert set(updated.tags) == {"newtag1", "newtag2"}
        assert updated.project == "新项目"
        # 由于 datetime 的精度问题，我们只检查日期部分
        assert updated.due_date.date() == (datetime.now() + timedelta(days=14)).date()
    
    def test_update_task_with_parameters(self, service, sample_task):
        """测试通过参数部分更新（向后兼容）"""
        # 只更新标题和描述
        updated = service.update_task(
            sample_task.id,
            title="只更新标题",
            description="只更新描述"
        )
        
        # 验证：标题和描述更新了，但其他字段保持原样
        assert updated is not None
        assert updated.title == "只更新标题"
        assert updated.description == "只更新描述"
        assert updated.status == TaskStatus.TODO  # 保持原样
        assert updated.priority == TaskPriority.MEDIUM  # 保持原样
        assert set(updated.tags) == {"tag1", "tag2"}  # 保持原样
        assert updated.project == "原始项目"  # 保持原样
    
    def test_update_task_nonexistent(self, service):
        """测试更新不存在的任务"""
        result = service.update_task(99999, title="不存在的任务")
        assert result is None
    
    def test_update_task_updated_at(self, service, sample_task):
        """测试更新时 updated_at 被正确更新"""
        original_updated_at = sample_task.updated_at
        
        # 等待一小会儿确保时间不同
        import time
        time.sleep(0.01)
        
        # 更新
        updated = service.update_task(sample_task.id, title="测试更新时间")
        
        # 验证 updated_at 被更新了
        assert updated.updated_at > original_updated_at
    
    def test_update_task_only_title(self, service, sample_task):
        """测试只更新标题"""
        original_description = sample_task.description
        
        updated = service.update_task(sample_task.id, title="只改标题")
        
        assert updated.title == "只改标题"
        assert updated.description == original_description  # 描述保持不变
    
    def test_update_task_only_description(self, service, sample_task):
        """测试只更新描述"""
        original_title = sample_task.title
        
        updated = service.update_task(sample_task.id, description="只改描述")
        
        assert updated.title == original_title  # 标题保持不变
        assert updated.description == "只改描述"
