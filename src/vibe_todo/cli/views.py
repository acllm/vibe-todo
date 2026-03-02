"""
任务视图模块

提供不同的任务展示方式：
- 卡片视图：美观的卡片形式展示
- 时间线视图：按时间顺序展示
- 看板视图：按状态分组展示
"""
from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
from datetime import datetime

from ..core.models import Task, TaskStatus, TaskPriority


console = Console()


def get_status_display(status: TaskStatus) -> Text:
    """获取状态的富文本显示"""
    status_map = {
        TaskStatus.TODO: ("⭕ 待处理", "cyan"),
        TaskStatus.IN_PROGRESS: ("🔄 进行中", "yellow"),
        TaskStatus.DONE: ("✅ 已完成", "green"),
    }
    text, color = status_map[status]
    return Text(text, style=color)


def get_priority_display(priority: TaskPriority) -> Text:
    """获取优先级的富文本显示"""
    priority_map = {
        TaskPriority.LOW: ("🟢 低", "green"),
        TaskPriority.MEDIUM: ("🟡 中", "yellow"),
        TaskPriority.HIGH: ("🟠 高", "orange1"),
        TaskPriority.URGENT: ("🔴 紧急", "red bold"),
    }
    text, color = priority_map[priority]
    return Text(text, style=color)


class TaskCardView:
    """任务卡片视图"""
    
    def render_task(self, task: Task) -> str:
        """渲染单个任务卡片（返回字符串用于测试）"""
        # 构建卡片内容
        lines = []
        
        # 标题
        title = task.title
        if task.status == TaskStatus.DONE:
            title = f"[dim strikethrough]{title}[/dim strikethrough]"
        lines.append(f"[bold]{title}[/bold]")
        lines.append("")
        
        # 状态和优先级
        status_display = get_status_display(task.status)
        priority_display = get_priority_display(task.priority)
        lines.append(f"状态: {status_display} | 优先级: {priority_display}")
        
        # 项目
        if task.project:
            lines.append(f"项目: [cyan]{task.project}[/cyan]")
        
        # 描述
        if task.description:
            lines.append("")
            lines.append(f"[dim]{task.description}[/dim]")
        
        # 标签
        if task.tags:
            lines.append("")
            tags_str = " ".join([f"[magenta]#{tag}[/magenta]" for tag in task.tags])
            lines.append(f"标签: {tags_str}")
        
        # 截止日期
        if task.due_date:
            lines.append("")
            due_date_str = task.due_date.strftime("%Y-%m-%d")
            if task.is_overdue():
                due_str = f"[red]截止: {due_date_str} (逾期)[/red]"
            elif task.days_until_due() is not None and task.days_until_due() <= 3:
                due_str = f"[yellow]截止: {due_date_str}[/yellow]"
            else:
                due_str = f"截止: {due_date_str}"
            lines.append(due_str)
        
        # 工时
        if task.time_spent > 0:
            time_str = task.format_time_spent()
            lines.append(f"工时: [blue]{time_str}[/blue]")
        
        # ID
        lines.append("")
        lines.append(f"[dim]ID: {task.id}[/dim]")
        
        return "\n".join(lines)
    
    def display_task(self, task: Task):
        """显示单个任务卡片"""
        card_content = self.render_task(task)
        panel = Panel(
            card_content,
            border_style="blue",
            padding=(1, 2)
        )
        console.print(panel)
    
    def render_list(self, tasks: List[Task]) -> str:
        """渲染任务卡片列表（返回字符串用于测试）"""
        if not tasks:
            return "暂无任务"
        
        result = []
        for task in tasks:
            result.append(self.render_task(task))
            result.append("---")
        
        return "\n".join(result)
    
    def display_list(self, tasks: List[Task]):
        """显示任务卡片列表"""
        if not tasks:
            console.print("[dim]暂无任务[/dim]")
            return
        
        for task in tasks:
            self.display_task(task)
            console.print()


class TaskTimelineView:
    """任务时间线视图（预留实现）"""
    
    def render(self, tasks: List[Task]) -> str:
        """渲染时间线（返回字符串用于测试）"""
        if not tasks:
            return "暂无任务"
        
        result = ["时间线视图:"]
        for task in tasks:
            result.append(f"- {task.title}")
        
        return "\n".join(result)
    
    def display(self, tasks: List[Task]):
        """显示时间线"""
        console.print(self.render(tasks))


class TaskBoardView:
    """任务看板视图（预留实现）"""
    
    def render(self, tasks: List[Task]) -> str:
        """渲染看板（返回字符串用于测试）"""
        if not tasks:
            return "暂无任务"
        
        result = ["看板视图:"]
        result.append("待处理 | 进行中 | 已完成")
        
        for task in tasks:
            result.append(f"- {task.title} ({get_status_display(task.status)})")
        
        return "\n".join(result)
    
    def display(self, tasks: List[Task]):
        """显示看板"""
        console.print(self.render(tasks))
