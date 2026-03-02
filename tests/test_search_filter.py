"""搜索和过滤功能测试"""
import os
import tempfile
from datetime import datetime, timedelta

import pytest

from src.vibe_todo.adapters import TaskFilter
from src.vibe_todo.core.models import Task, TaskPriority, TaskStatus
from src.vibe_todo.storage.repository import TaskRepository


@pytest.fixture
def temp_db():
    """创建临时数据库"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def repo(temp_db):
    """创建测试用的仓储"""
    return TaskRepository(db_path=temp_db)


@pytest.fixture
def sample_tasks(repo):
    """创建一些示例任务"""
    tasks = [
        Task(
            title="完成项目文档",
            description="编写完整的项目 README 文档",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            tags=["文档", "重要"],
            project="Vibe Todo",
            due_date=datetime.now() + timedelta(days=1)
        ),
        Task(
            title="修复 bug",
            description="修复搜索功能中的问题",
            status=TaskStatus.TODO,
            priority=TaskPriority.URGENT,
            tags=["bug", "搜索"],
            project="Vibe Todo",
            due_date=datetime.now() - timedelta(days=1)  # 逾期
        ),
        Task(
            title="学习 Python",
            description="学习 Python 高级特性",
            status=TaskStatus.DONE,
            priority=TaskPriority.LOW,
            tags=["学习", "Python"],
            project="个人发展",
        ),
        Task(
            title="购物清单",
            description="买牛奶、面包、鸡蛋",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            tags=["生活", "购物"],
            project="生活",
            due_date=datetime.now() + timedelta(days=2)
        ),
    ]

    for task in tasks:
        repo.save(task)

    return tasks


class TestTaskFilter:
    """测试 TaskFilter 类"""

    def test_empty_filter(self):
        """测试空过滤条件"""
        filter = TaskFilter()
        assert not filter.has_any_filter()

    def test_has_filter(self):
        """测试有过滤条件"""
        filter = TaskFilter(status=TaskStatus.TODO)
        assert filter.has_any_filter()

        filter = TaskFilter(priority=TaskPriority.HIGH)
        assert filter.has_any_filter()

        filter = TaskFilter(project="Test")
        assert filter.has_any_filter()

        filter = TaskFilter(tags=["tag1"])
        assert filter.has_any_filter()

        filter = TaskFilter(overdue_only=True)
        assert filter.has_any_filter()

        filter = TaskFilter(due_in_days=3)
        assert filter.has_any_filter()


class TestSearchFunctionality:
    """测试搜索功能"""

    def test_search_by_title(self, repo, sample_tasks):
        """测试按标题搜索"""
        results = repo.search("文档")
        assert len(results) == 1
        assert "文档" in results[0].title

    def test_search_by_description(self, repo, sample_tasks):
        """测试按描述搜索"""
        results = repo.search("Python")
        assert len(results) == 1
        assert "Python" in results[0].description

    def test_search_by_tags(self, repo, sample_tasks):
        """测试按标签搜索"""
        results = repo.search("bug")
        assert len(results) >= 1
        assert any("bug" in task.tags for task in results)

    def test_search_by_project(self, repo, sample_tasks):
        """测试按项目搜索"""
        results = repo.search("个人发展")
        assert len(results) == 1
        assert results[0].project == "个人发展"

    def test_search_no_results(self, repo, sample_tasks):
        """测试搜索无结果"""
        results = repo.search("不存在的关键词")
        assert len(results) == 0


class TestFilterFunctionality:
    """测试过滤功能"""

    def test_filter_by_status(self, repo, sample_tasks):
        """测试按状态过滤"""
        filter = TaskFilter(status=TaskStatus.TODO)
        results = repo.filter_tasks(filter)
        assert len(results) == 2
        assert all(task.status == TaskStatus.TODO for task in results)

    def test_filter_by_priority(self, repo, sample_tasks):
        """测试按优先级过滤"""
        filter = TaskFilter(priority=TaskPriority.URGENT)
        results = repo.filter_tasks(filter)
        assert len(results) == 1
        assert results[0].priority == TaskPriority.URGENT

    def test_filter_by_project(self, repo, sample_tasks):
        """测试按项目过滤"""
        filter = TaskFilter(project="Vibe Todo")
        results = repo.filter_tasks(filter)
        assert len(results) == 2
        assert all(task.project == "Vibe Todo" for task in results)

    def test_filter_by_tags_or(self, repo, sample_tasks):
        """测试按标签 OR 过滤"""
        filter = TaskFilter(tags=["文档", "bug"], tags_operator="OR")
        results = repo.filter_tasks(filter)
        assert len(results) == 2

    def test_filter_by_tags_and(self, repo, sample_tasks):
        """测试按标签 AND 过滤"""
        filter = TaskFilter(tags=["文档", "重要"], tags_operator="AND")
        results = repo.filter_tasks(filter)
        assert len(results) == 1

    def test_filter_overdue(self, repo, sample_tasks):
        """测试只显示逾期任务"""
        filter = TaskFilter(overdue_only=True)
        results = repo.filter_tasks(filter)
        assert len(results) == 1
        assert results[0].is_overdue()

    def test_filter_due_in_days(self, repo, sample_tasks):
        """测试按到期天数过滤"""
        filter = TaskFilter(due_in_days=2)
        results = repo.filter_tasks(filter)
        assert len(results) >= 1
        assert all(
            task.due_date and task.days_until_due() is not None
            and 0 <= task.days_until_due() <= 2
            for task in results
        )

    def test_multiple_filters(self, repo, sample_tasks):
        """测试多条件组合过滤"""
        filter = TaskFilter(
            status=TaskStatus.TODO,
            priority=TaskPriority.URGENT,
            project="Vibe Todo"
        )
        results = repo.filter_tasks(filter)
        assert len(results) == 1
        assert results[0].title == "修复 bug"


class TestSearchAndFilter:
    """测试搜索和过滤组合"""

    def test_search_with_filter(self, repo, sample_tasks):
        """测试搜索和过滤组合"""
        filter = TaskFilter(status=TaskStatus.IN_PROGRESS)
        results = repo.search_and_filter(query="文档", task_filter=filter)
        assert len(results) == 1
        assert results[0].status == TaskStatus.IN_PROGRESS
        assert "文档" in results[0].title

    def test_filter_only(self, repo, sample_tasks):
        """测试只过滤不搜索"""
        filter = TaskFilter(status=TaskStatus.DONE)
        results = repo.search_and_filter(query=None, task_filter=filter)
        assert len(results) == 1
        assert results[0].status == TaskStatus.DONE

    def test_search_only(self, repo, sample_tasks):
        """测试只搜索不过滤"""
        results = repo.search_and_filter(query="购物", task_filter=None)
        assert len(results) == 1
        assert "购物" in results[0].title
