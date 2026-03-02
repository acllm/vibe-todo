"""
测试 AI Helper 模块 - 单元测试

覆盖 AI Helper 的所有核心功能：
- 任务分析
- 下一个任务推荐
- 任务建议生成
- 生产力评分
"""
from datetime import datetime, timedelta

import pytest

from src.vibe_todo.core import Task, TaskPriority, TaskStatus
from src.vibe_todo.core.ai_helper import AIHelper, TaskSuggestion, get_ai_helper


class TestAIHelper:
    """测试 AI Helper 核心功能"""

    @pytest.fixture
    def ai_helper(self):
        """创建 AI Helper 实例"""
        return AIHelper()

    @pytest.fixture
    def sample_task(self):
        """创建示例任务"""
        return Task(
            title="完成项目文档",
            description="编写完整的项目文档",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            tags=["文档"],
            project="Vibe Todo"
        )

    def test_analyze_task_basic(self, ai_helper, sample_task):
        """测试基础任务分析"""
        analysis = ai_helper.analyze_task(sample_task)

        assert "suggested_priority" in analysis
        assert "suggested_tags" in analysis
        assert "estimated_time" in analysis
        assert "urgency_score" in analysis
        assert "suggestions" in analysis

    def test_analyze_task_with_pattern_meeting(self, ai_helper):
        """测试会议模式匹配"""
        task = Task(
            title="周一上午10点的团队会议",
            description="讨论项目进展",
            priority=TaskPriority.LOW
        )

        analysis = ai_helper.analyze_task(task)

        # 应该识别为会议模式
        assert analysis["suggested_priority"].sort_order() <= TaskPriority.HIGH.sort_order()
        assert any("会议" in tag for tag in analysis["suggested_tags"])

    def test_analyze_task_with_pattern_code(self, ai_helper):
        """测试代码模式匹配"""
        task = Task(
            title="修复登录功能的 bug",
            description="用户无法正常登录",
            priority=TaskPriority.LOW
        )

        analysis = ai_helper.analyze_task(task)

        # 应该识别为代码模式
        assert analysis["suggested_priority"].sort_order() <= TaskPriority.HIGH.sort_order()
        assert any("开发" in tag or "技术" in tag for tag in analysis["suggested_tags"])

    def test_analyze_task_urgency_overdue(self, ai_helper):
        """测试逾期任务紧急程度"""
        yesterday = datetime.now() - timedelta(days=1)
        task = Task(
            title="逾期任务",
            due_date=yesterday,
            status=TaskStatus.TODO
        )

        analysis = ai_helper.analyze_task(task)

        assert analysis["urgency_score"] == 1.0
        assert analysis["suggested_priority"] == TaskPriority.URGENT

    def test_analyze_task_urgency_today(self, ai_helper):
        """测试今天截止任务紧急程度"""
        today = datetime.now()
        task = Task(
            title="今天截止的任务",
            due_date=today,
            status=TaskStatus.TODO
        )

        analysis = ai_helper.analyze_task(task)

        assert analysis["urgency_score"] >= 0.8
        assert analysis["suggested_priority"].sort_order() <= TaskPriority.HIGH.sort_order()

    def test_suggest_next_task_simple(self, ai_helper):
        """测试简单场景的下一个任务推荐"""
        tasks = [
            Task(
                title="高优先级任务",
                task_id=1,
                priority=TaskPriority.HIGH,
                status=TaskStatus.TODO
            ),
            Task(
                title="中优先级任务",
                task_id=2,
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.TODO
            )
        ]

        next_task = ai_helper.suggest_next_task(tasks)

        # 应该推荐高优先级的任务
        assert next_task is not None
        assert next_task.priority == TaskPriority.HIGH

    def test_suggest_next_task_in_progress_first(self, ai_helper):
        """测试进行中的任务优先"""
        tasks = [
            Task(
                title="进行中的任务",
                task_id=1,
                priority=TaskPriority.MEDIUM,
                status=TaskStatus.IN_PROGRESS
            ),
            Task(
                title="高优先级但未开始",
                task_id=2,
                priority=TaskPriority.HIGH,
                status=TaskStatus.TODO
            )
        ]

        next_task = ai_helper.suggest_next_task(tasks)

        # 应该推荐进行中的任务
        assert next_task is not None
        assert next_task.status == TaskStatus.IN_PROGRESS

    def test_suggest_next_task_with_dependencies(self, ai_helper):
        """测试依赖关系的任务推荐"""
        task1 = Task(
            title="依赖任务 1",
            task_id=1,
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH
        )
        task2 = Task(
            title="主任务（依赖任务 1）",
            task_id=2,
            status=TaskStatus.TODO,
            priority=TaskPriority.URGENT,
            depends_on=["1"]
        )

        tasks = [task1, task2]

        next_task = ai_helper.suggest_next_task(tasks)

        # 应该推荐 task1（因为 task2 依赖 task1，而 task1 未完成）
        assert next_task is not None
        assert next_task.id == 1

    def test_suggest_next_task_all_dependencies_met(self, ai_helper):
        """测试依赖都已满足的情况"""
        task1 = Task(
            title="已完成的依赖",
            task_id=1,
            status=TaskStatus.DONE,
            priority=TaskPriority.MEDIUM
        )
        task2 = Task(
            title="主任务（依赖已完成）",
            task_id=2,
            status=TaskStatus.TODO,
            priority=TaskPriority.URGENT,
            depends_on=["1"]
        )

        tasks = [task1, task2]

        next_task = ai_helper.suggest_next_task(tasks)

        # 应该推荐 task2（依赖都已满足）
        assert next_task is not None
        assert next_task.id == 2

    def test_generate_suggestions_time_of_day_morning(self, ai_helper):
        """测试早晨的建议"""
        suggestions = ai_helper.generate_task_suggestions([], time_of_day="morning")

        # 早晨应该有查看今日待办和处理邮件的建议
        titles = [s.title for s in suggestions]
        assert any("今日待办" in t for t in titles)
        assert any("邮件" in t for t in titles)

    def test_generate_suggestions_time_of_day_afternoon(self, ai_helper):
        """测试下午的建议"""
        suggestions = ai_helper.generate_task_suggestions([], time_of_day="afternoon")

        # 下午应该有专注开发的建议
        titles = [s.title for s in suggestions]
        assert any("开发" in t or "专注" in t for t in titles)

    def test_generate_suggestions_project_momentum(self, ai_helper):
        """测试项目 momentum 保持建议"""
        recent_tasks = [
            Task(title="Vibe Todo 功能1", project="Vibe Todo", created_at=datetime.now()),
            Task(title="Vibe Todo 功能2", project="Vibe Todo", created_at=datetime.now()),
            Task(title="Vibe Todo 功能3", project="Vibe Todo", created_at=datetime.now()),
        ]

        suggestions = ai_helper.generate_task_suggestions(recent_tasks)

        # 应该有继续 Vibe Todo 项目的建议
        titles = [s.title for s in suggestions]
        assert any("Vibe Todo" in t for t in titles)

    def test_productivity_score_basic(self, ai_helper):
        """测试基础生产力分数计算"""
        tasks = [
            Task(
                title="已完成1",
                status=TaskStatus.DONE,
                created_at=datetime.now() - timedelta(days=1),
                time_spent=60
            ),
            Task(
                title="已完成2",
                status=TaskStatus.DONE,
                created_at=datetime.now() - timedelta(days=2),
                time_spent=120
            )
        ]

        result = ai_helper.calculate_productivity_score(tasks, days=7)

        assert "score" in result
        assert "completed" in result
        assert "total_time" in result
        assert result["completed"] == 2
        assert result["total_time"] == 3.0  # 60 + 120 分钟 = 3 小时

    def test_productivity_score_with_overdue(self, ai_helper):
        """测试有逾期任务的生产力分数"""
        yesterday = datetime.now() - timedelta(days=1)
        tasks = [
            Task(
                title="已完成",
                status=TaskStatus.DONE,
                created_at=datetime.now() - timedelta(days=1)
            ),
            Task(
                title="逾期任务",
                status=TaskStatus.TODO,
                due_date=yesterday,
                created_at=datetime.now() - timedelta(days=1)
            )
        ]

        result = ai_helper.calculate_productivity_score(tasks, days=7)

        assert result["overdue"] == 1
        # 逾期应该有惩罚，分数会低一些

    def test_productivity_score_trends(self, ai_helper):
        """测试趋势分析"""
        tasks = [
            Task(
                title="已完成1",
                status=TaskStatus.DONE,
                created_at=datetime.now() - timedelta(days=1),
                time_spent=240  # 4 小时
            ),
            Task(
                title="已完成2",
                status=TaskStatus.DONE,
                created_at=datetime.now() - timedelta(days=2),
                time_spent=180  # 3 小时
            )
        ]

        result = ai_helper.calculate_productivity_score(tasks, days=7)

        assert "trends" in result
        # 应该有正面的趋势分析


class TestTaskSuggestion:
    """测试 TaskSuggestion 数据类"""

    def test_task_suggestion_creation(self):
        """测试任务建议创建"""
        suggestion = TaskSuggestion(
            title="测试建议",
            description="这是一个测试",
            priority=TaskPriority.HIGH,
            tags=["测试", "AI"],
            confidence=0.8,
            reason="测试理由"
        )

        assert suggestion.title == "测试建议"
        assert suggestion.description == "这是一个测试"
        assert suggestion.priority == TaskPriority.HIGH
        assert suggestion.tags == ["测试", "AI"]
        assert suggestion.confidence == 0.8
        assert suggestion.reason == "测试理由"

    def test_task_suggestion_defaults(self):
        """测试任务建议默认值"""
        suggestion = TaskSuggestion(
            title="最小化建议"
        )

        assert suggestion.title == "最小化建议"
        assert suggestion.description == ""
        assert suggestion.priority == TaskPriority.MEDIUM
        assert suggestion.tags == []
        assert suggestion.confidence == 0.5
        assert suggestion.reason == ""


class TestGetAIHelper:
    """测试全局 AI Helper 实例"""

    def test_get_ai_helper_singleton(self):
        """测试获取全局 AI Helper 实例（应该是单例）"""
        helper1 = get_ai_helper()
        helper2 = get_ai_helper()

        assert helper1 is helper2
