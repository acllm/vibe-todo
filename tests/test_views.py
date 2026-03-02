"""测试视图功能（卡片视图、时间线视图、看板视图）"""
import pytest
from datetime import datetime, timedelta
from src.vibe_todo.core.models import Task, TaskStatus, TaskPriority
from src.vibe_todo.cli.views import TaskCardView, TaskTimelineView, TaskBoardView


@pytest.fixture
def sample_tasks():
    """创建示例任务列表"""
    tasks = [
        Task(
            task_id=1,
            title="完成项目文档",
            description="编写完整的 API 文档和用户指南",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            tags=["文档", "重要"],
            project="Vibe Todo",
            due_date=datetime.now() + timedelta(days=2),
            time_spent=120,
            created_at=datetime.now() - timedelta(days=3),
            updated_at=datetime.now() - timedelta(hours=2)
        ),
        Task(
            task_id=2,
            title="修复登录 bug",
            description="用户反馈的登录超时问题",
            status=TaskStatus.TODO,
            priority=TaskPriority.URGENT,
            tags=["bug", "高优先级"],
            project="Vibe Todo",
            due_date=datetime.now() + timedelta(days=1),
            created_at=datetime.now() - timedelta(days=1),
            updated_at=datetime.now() - timedelta(minutes=30)
        ),
        Task(
            task_id=3,
            title="代码审查",
            description="审查新功能的 PR",
            status=TaskStatus.DONE,
            priority=TaskPriority.MEDIUM,
            tags=["审查"],
            project="Vibe Todo",
            time_spent=60,
            created_at=datetime.now() - timedelta(days=5),
            updated_at=datetime.now() - timedelta(days=2)
        )
    ]
    return tasks


class TestTaskCardView:
    """测试任务卡片视图"""
    
    def test_create_card_view(self):
        """测试创建卡片视图"""
        view = TaskCardView()
        assert view is not None
    
    def test_render_single_card(self, sample_tasks):
        """测试渲染单个任务卡片"""
        view = TaskCardView()
        task = sample_tasks[0]
        
        # 渲染卡片（不实际打印，只测试生成）
        result = view.render_task(task)
        
        # 验证结果包含关键信息
        assert task.title in result
        assert "进行中" in result or "IN_PROGRESS" in result
        assert "高" in result or "HIGH" in result
        assert "Vibe Todo" in result
    
    def test_render_card_list(self, sample_tasks):
        """测试渲染任务卡片列表"""
        view = TaskCardView()
        
        # 渲染列表
        result = view.render_list(sample_tasks)
        
        # 验证包含所有任务
        assert sample_tasks[0].title in result
        assert sample_tasks[1].title in result
        assert sample_tasks[2].title in result
    
    def test_card_view_with_empty_list(self):
        """测试空列表的卡片视图"""
        view = TaskCardView()
        result = view.render_list([])
        assert "暂无任务" in result or "empty" in result.lower()


class TestTaskTimelineView:
    """测试任务时间线视图"""
    
    def test_create_timeline_view(self):
        """测试创建时间线视图"""
        view = TaskTimelineView()
        assert view is not None
    
    def test_render_timeline(self, sample_tasks):
        """测试渲染时间线"""
        view = TaskTimelineView()
        result = view.render(sample_tasks)
        
        # 验证包含任务
        for task in sample_tasks:
            assert task.title in result


class TestTaskBoardView:
    """测试任务看板视图"""
    
    def test_create_board_view(self):
        """测试创建看板视图"""
        view = TaskBoardView()
        assert view is not None
    
    def test_render_board(self, sample_tasks):
        """测试渲染看板"""
        view = TaskBoardView()
        result = view.render(sample_tasks)
        
        # 验证包含状态列
        assert "待处理" in result or "TODO" in result
        assert "进行中" in result or "IN_PROGRESS" in result
        assert "已完成" in result or "DONE" in result
        
        # 验证包含任务
        for task in sample_tasks:
            assert task.title in result
