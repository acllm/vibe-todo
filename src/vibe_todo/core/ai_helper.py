"""
Nova AI Helper - AI 辅助功能模块

提供智能任务建议、优先级推荐、自动分类等功能
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .models import Task, TaskPriority, TaskStatus


class TaskSuggestion:
    """任务建议"""
    def __init__(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        tags: Optional[List[str]] = None,
        confidence: float = 0.5,
        reason: str = ""
    ):
        self.title = title
        self.description = description
        self.priority = priority
        self.tags = tags or []
        self.confidence = confidence
        self.reason = reason


class AIHelper:
    """AI 助手类 - 提供智能任务管理功能"""

    def __init__(self):
        self.task_patterns = self._init_patterns()

    def _init_patterns(self) -> Dict[str, Dict[str, Any]]:
        """初始化任务模式匹配规则"""
        return {
            "meeting": {
                "keywords": ["会议", "meeting", "讨论", "review", "评审"],
                "priority": TaskPriority.HIGH,
                "tags": ["会议", "工作"],
                "default_time": 60  # 默认60分钟
            },
            "report": {
                "keywords": ["报告", "report", "文档", "doc", "总结"],
                "priority": TaskPriority.MEDIUM,
                "tags": ["文档", "工作"],
                "default_time": 90
            },
            "email": {
                "keywords": ["邮件", "email", "回信", "回复"],
                "priority": TaskPriority.LOW,
                "tags": ["邮件", "沟通"],
                "default_time": 15
            },
            "code": {
                "keywords": ["代码", "code", "开发", "dev", "bug", "修复"],
                "priority": TaskPriority.HIGH,
                "tags": ["开发", "技术"],
                "default_time": 120
            },
            "design": {
                "keywords": ["设计", "design", "UI", "原型"],
                "priority": TaskPriority.MEDIUM,
                "tags": ["设计", "产品"],
                "default_time": 90
            },
            "personal": {
                "keywords": ["家人", "朋友", "生日", "纪念日"],
                "priority": TaskPriority.URGENT,
                "tags": ["个人", "生活"],
                "default_time": 30
            }
        }

    def analyze_task(self, task: Task) -> Dict[str, Any]:
        """
        分析任务，返回 AI 分析结果
        
        返回包含：
        - suggested_priority: 建议的优先级
        - suggested_tags: 建议的标签
        - estimated_time: 预估工时（分钟）
        - urgency_score: 紧急程度分数 (0-1)
        - suggestions: 改进建议
        """
        content = f"{task.title} {task.description}".lower()

        result = {
            "suggested_priority": task.priority,
            "suggested_tags": [],
            "estimated_time": 30,
            "urgency_score": 0.0,
            "suggestions": []
        }

        # 模式匹配
        for pattern_name, pattern in self.task_patterns.items():
            if any(keyword in content for keyword in pattern["keywords"]):
                result["suggested_tags"].extend(pattern["tags"])
                result["estimated_time"] = max(result["estimated_time"], pattern["default_time"])

                # 如果是更高优先级，更新建议
                if pattern["priority"].sort_order() < result["suggested_priority"].sort_order():
                    result["suggested_priority"] = pattern["priority"]

        # 去重标签
        result["suggested_tags"] = list(set(result["suggested_tags"]))

        # 计算紧急程度
        if task.due_date:
            days_until = task.days_until_due()
            if days_until is not None:
                if days_until < 0:
                    result["urgency_score"] = 1.0
                elif days_until == 0:
                    result["urgency_score"] = 0.9
                elif days_until <= 2:
                    result["urgency_score"] = 0.7
                elif days_until <= 7:
                    result["urgency_score"] = 0.5
                else:
                    result["urgency_score"] = 0.2

        # 基于紧急程度调整优先级
        if result["urgency_score"] >= 0.9:
            result["suggested_priority"] = TaskPriority.URGENT
        elif result["urgency_score"] >= 0.7:
            if result["suggested_priority"].sort_order() > TaskPriority.HIGH.sort_order():
                result["suggested_priority"] = TaskPriority.HIGH

        # 生成建议
        if task.status == TaskStatus.TODO and result["urgency_score"] > 0.7:
            result["suggestions"].append("这个任务比较紧急，建议优先处理")

        if not task.tags and result["suggested_tags"]:
            result["suggestions"].append(f"建议添加标签: {', '.join(result['suggested_tags'])}")

        if task.priority != result["suggested_priority"]:
            result["suggestions"].append(
                f"建议将优先级从 {task.priority.value} 调整为 {result['suggested_priority'].value}"
            )

        return result

    def suggest_next_task(self, tasks: List[Task]) -> Optional[Task]:
        """
        智能推荐下一个应该处理的任务
        
        考虑因素：
        - 优先级
        - 截止日期
        - 依赖关系
        - 预计工时（先做短任务）
        """
        available_tasks = []

        for task in tasks:
            # 跳过已完成的任务
            if task.status == TaskStatus.DONE:
                continue

            # 检查依赖是否都已完成
            dependencies_met = True
            for dep_id in task.depends_on:
                dep_task = next((t for t in tasks if str(t.id) == dep_id), None)
                if dep_task and dep_task.status != TaskStatus.DONE:
                    dependencies_met = False
                    break

            if not dependencies_met:
                continue

            available_tasks.append(task)

        if not available_tasks:
            return None

        # 打分排序
        scored_tasks = []
        for task in available_tasks:
            analysis = self.analyze_task(task)

            # 综合评分（越高越优先）
            score = 0.0

            # 优先级权重
            priority_weights = {
                TaskPriority.URGENT: 100,
                TaskPriority.HIGH: 75,
                TaskPriority.MEDIUM: 50,
                TaskPriority.LOW: 25
            }
            score += priority_weights.get(task.priority, 50)

            # 紧急程度权重
            score += analysis["urgency_score"] * 50

            # 短任务优先（快速成就感）
            if task.time_spent == 0:  # 还没开始的任务
                score += 10  # 优先处理新任务
            elif task.time_spent < 30:
                score += 5  # 短任务加分

            # 进行中的任务优先
            if task.status == TaskStatus.IN_PROGRESS:
                score += 30

            scored_tasks.append((score, task))

        # 按分数降序排序
        scored_tasks.sort(key=lambda x: x[0], reverse=True)

        return scored_tasks[0][1] if scored_tasks else None

    def generate_task_suggestions(
        self,
        recent_tasks: List[Task],
        time_of_day: Optional[str] = None
    ) -> List[TaskSuggestion]:
        """
        基于历史和上下文生成任务建议
        
        Args:
            recent_tasks: 最近的任务列表
            time_of_day: 时间段（morning/afternoon/evening）
        """
        suggestions = []

        # 默认时间段
        if not time_of_day:
            hour = datetime.now().hour
            if 5 <= hour < 12:
                time_of_day = "morning"
            elif 12 <= hour < 18:
                time_of_day = "afternoon"
            else:
                time_of_day = "evening"

        # 基于时间段的建议
        time_based_suggestions = {
            "morning": [
                TaskSuggestion(
                    "查看今日待办",
                    "快速浏览今天需要完成的任务，制定今日计划",
                    TaskPriority.MEDIUM,
                    ["计划", "日常"],
                    0.8,
                    "早上是规划一天的好时机"
                ),
                TaskSuggestion(
                    "处理邮件",
                    "查看并回复重要邮件",
                    TaskPriority.LOW,
                    ["邮件", "沟通"],
                    0.6,
                    "早上处理邮件不会被打扰"
                )
            ],
            "afternoon": [
                TaskSuggestion(
                    "专注开发",
                    "下午是专注力最好的时间段，适合做需要深度思考的工作",
                    TaskPriority.HIGH,
                    ["开发", "专注"],
                    0.9,
                    "下午专注力最佳"
                )
            ],
            "evening": [
                TaskSuggestion(
                    "今日总结",
                    "回顾今天完成的工作，记录进展和问题",
                    TaskPriority.LOW,
                    ["总结", "反思"],
                    0.7,
                    "晚上适合总结反思"
                )
            ]
        }

        suggestions.extend(time_based_suggestions.get(time_of_day, []))

        # 基于最近任务的补充建议
        project_counts = {}
        tag_counts = {}

        for task in recent_tasks:
            if task.project:
                project_counts[task.project] = project_counts.get(task.project, 0) + 1
            for tag in task.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # 如果某个项目最近活跃，建议继续
        if project_counts:
            top_project = max(project_counts.items(), key=lambda x: x[1])
            if top_project[1] >= 3:
                suggestions.append(
                    TaskSuggestion(
                        f"继续 {top_project[0]} 项目",
                        "这个项目最近很活跃，保持 momentum",
                        TaskPriority.HIGH,
                        [top_project[0], "继续"],
                        0.85,
                        "保持项目 momentum"
                    )
                )

        return suggestions

    def calculate_productivity_score(self, tasks: List[Task], days: int = 7) -> Dict[str, Any]:
        """
        计算生产力分数
        
        返回：
        - score: 总分数 (0-100)
        - completed: 完成的任务数
        - in_progress: 进行中的任务数
        - overdue: 逾期任务数
        - total_time: 总工时（小时）
        - trends: 趋势分析
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        recent_tasks = [
            t for t in tasks
            if t.created_at and t.created_at >= cutoff_date
        ]

        completed = sum(1 for t in recent_tasks if t.status == TaskStatus.DONE)
        in_progress = sum(1 for t in recent_tasks if t.status == TaskStatus.IN_PROGRESS)
        overdue = sum(1 for t in recent_tasks if t.is_overdue())
        total_time = sum(t.time_spent for t in recent_tasks) / 60  # 转换为小时

        # 计算基础分
        score = 0.0

        # 完成率 (最多50分)
        if recent_tasks:
            completion_rate = completed / len(recent_tasks)
            score += completion_rate * 50

        # 工时贡献 (最多30分)
        time_score = min(total_time / 40 * 30, 30)  # 每周40小时满分
        score += time_score

        # 逾期惩罚 (最多扣20分)
        overdue_penalty = min(overdue * 5, 20)
        score -= overdue_penalty

        # 确保分数在 0-100 之间
        score = max(0, min(100, score))

        # 简单趋势分析
        trends = []
        if completed > 0:
            trends.append(f"完成了 {completed} 个任务，很棒！")
        if overdue > 0:
            trends.append(f"有 {overdue} 个任务逾期，需要注意")
        if total_time > 20:
            trends.append(f"投入了 {total_time:.1f} 小时，很充实！")

        return {
            "score": round(score, 1),
            "completed": completed,
            "in_progress": in_progress,
            "overdue": overdue,
            "total_time": round(total_time, 1),
            "trends": trends,
            "period_days": days
        }


# 全局 AI 助手实例
_ai_helper: Optional[AIHelper] = None


def get_ai_helper() -> AIHelper:
    """获取全局 AI 助手实例"""
    global _ai_helper
    if _ai_helper is None:
        _ai_helper = AIHelper()
    return _ai_helper
