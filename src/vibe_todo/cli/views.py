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
    """任务时间线视图"""
    
    def _group_tasks_by_date(self, tasks: List[Task], date_field: str = 'created_at') -> dict:
        """按日期分组任务
        
        Args:
            tasks: 任务列表
            date_field: 使用哪个日期字段分组（'created_at', 'updated_at', 'due_date'）
        
        Returns:
            按日期分组的任务字典 {date: [tasks]}
        """
        from collections import defaultdict
        groups = defaultdict(list)
        
        for task in tasks:
            # 获取日期
            if date_field == 'due_date' and task.due_date:
                task_date = task.due_date.date()
            elif date_field == 'updated_at':
                task_date = task.updated_at.date()
            else:  # created_at (default)
                task_date = task.created_at.date()
            
            groups[task_date].append(task)
        
        # 按日期排序
        sorted_groups = dict(sorted(groups.items(), reverse=True))  # 最新的在前
        return sorted_groups
    
    def _get_date_label(self, date) -> str:
        """获取日期的友好标签"""
        from datetime import datetime, timedelta
        
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        if date == today:
            return "今天"
        elif date == yesterday:
            return "昨天"
        else:
            # 计算相差天数
            delta = today - date
            if delta.days < 7:
                weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
                return weekdays[date.weekday()]
            else:
                return date.strftime("%Y-%m-%d")
    
    def render(self, tasks: List[Task]) -> str:
        """渲染时间线（返回字符串用于测试）"""
        if not tasks:
            return "暂无任务"
        
        # 按创建时间分组
        groups = self._group_tasks_by_date(tasks, 'created_at')
        
        result = ["📅 时间线视图"]
        result.append("")
        
        for date, date_tasks in groups.items():
            date_label = self._get_date_label(date)
            result.append(f"[bold cyan]{date_label}[/bold cyan] ({date.strftime('%Y-%m-%d')})")
            
            # 按时间排序（最新的在前）
            sorted_tasks = sorted(date_tasks, key=lambda t: t.created_at, reverse=True)
            
            for task in sorted_tasks:
                status_display = get_status_display(task.status)
                priority_display = get_priority_display(task.priority)
                
                # 时间线标记
                time_str = task.created_at.strftime("%H:%M")
                result.append(f"  {time_str} │ {task.title}")
                result.append(f"         │ {status_display} | {priority_display}")
                
                if task.project:
                    result.append(f"         │ 项目: {task.project}")
                
                if task.description:
                    result.append(f"         │ {task.description[:50]}..." if len(task.description) > 50 else f"         │ {task.description}")
                
                result.append("         │")
            
            result.append("")
        
        return "\n".join(result)
    
    def display(self, tasks: List[Task]):
        """显示时间线"""
        if not tasks:
            console.print("[dim]暂无任务[/dim]")
            return
        
        # 按创建时间分组
        groups = self._group_tasks_by_date(tasks, 'created_at')
        
        console.print("📅 [bold]时间线视图[/bold]")
        console.print()
        
        for date, date_tasks in groups.items():
            date_label = self._get_date_label(date)
            
            # 日期标题
            console.print(f"[bold cyan]{date_label}[/bold cyan] ({date.strftime('%Y-%m-%d')})")
            
            # 按时间排序（最新的在前）
            sorted_tasks = sorted(date_tasks, key=lambda t: t.created_at, reverse=True)
            
            for task in sorted_tasks:
                status_display = get_status_display(task.status)
                priority_display = get_priority_display(task.priority)
                
                # 时间线标记
                time_str = task.created_at.strftime("%H:%M")
                
                # 任务标题（如果已完成添加删除线）
                title_text = task.title
                if task.status == TaskStatus.DONE:
                    title_text = f"[dim strikethrough]{title_text}[/dim strikethrough]"
                
                console.print(f"  [dim]{time_str}[/dim] │ {title_text}")
                console.print(f"         │ {status_display} | {priority_display}")
                
                if task.project:
                    console.print(f"         │ 项目: [cyan]{task.project}[/cyan]")
                
                if task.description:
                    desc_text = task.description[:50] + "..." if len(task.description) > 50 else task.description
                    console.print(f"         │ [dim]{desc_text}[/dim]")
                
                if task.tags:
                    tags_str = " ".join([f"[magenta]#{tag}[/magenta]" for tag in task.tags])
                    console.print(f"         │ 标签: {tags_str}")
                
                console.print("         │")
            
            console.print()


class TaskBoardView:
    """任务看板视图"""
    
    def _group_tasks_by_status(self, tasks: List[Task]) -> dict:
        """按状态分组任务
        
        Returns:
            按状态分组的任务字典 {status: [tasks]}
        """
        from collections import defaultdict
        groups = defaultdict(list)
        
        # 确保三个状态列都存在（即使没有任务）
        groups[TaskStatus.TODO] = []
        groups[TaskStatus.IN_PROGRESS] = []
        groups[TaskStatus.DONE] = []
        
        for task in tasks:
            groups[task.status].append(task)
        
        # 每个状态组内按优先级排序
        for status in groups:
            groups[status] = sorted(groups[status], key=lambda t: t.priority.sort_order())
        
        return groups
    
    def _render_mini_card(self, task: Task) -> str:
        """渲染小型任务卡片（用于看板）"""
        lines = []
        
        # 标题（如果已完成添加删除线）
        title_text = task.title
        if task.status == TaskStatus.DONE:
            title_text = f"[dim strikethrough]{title_text}[/dim strikethrough]"
        
        lines.append(f"[bold]{title_text}[/bold]")
        
        # 优先级
        priority_display = get_priority_display(task.priority)
        lines.append(f"{priority_display}")
        
        # 项目
        if task.project:
            lines.append(f"[cyan]{task.project}[/cyan]")
        
        # 截止日期
        if task.due_date:
            due_date_str = task.due_date.strftime("%m-%d")
            if task.is_overdue():
                lines.append(f"[red]📅 {due_date_str}[/red]")
            elif task.days_until_due() is not None and task.days_until_due() <= 3:
                lines.append(f"[yellow]📅 {due_date_str}[/yellow]")
            else:
                lines.append(f"📅 {due_date_str}")
        
        # 标签
        if task.tags:
            tags_str = " ".join([f"[magenta]#{tag}[/magenta]" for tag in task.tags[:2]])  # 最多显示2个标签
            if len(task.tags) > 2:
                tags_str += f" [dim]+{len(task.tags)-2}[/dim]"
            lines.append(tags_str)
        
        # ID
        lines.append(f"[dim]ID: {task.id}[/dim]")
        
        return "\n".join(lines)
    
    def render(self, tasks: List[Task]) -> str:
        """渲染看板（返回字符串用于测试）"""
        if not tasks:
            return "暂无任务"
        
        # 按状态分组
        groups = self._group_tasks_by_status(tasks)
        
        result = ["📋 看板视图"]
        result.append("")
        
        # 按状态顺序显示
        status_order = [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.DONE]
        
        for status in status_order:
            status_display = get_status_display(status)
            status_tasks = groups[status]
            
            result.append(f"[bold]{status_display}[/bold] ({len(status_tasks)} 项)")
            
            for task in status_tasks:
                result.append(f"  • {task.title}")
                result.append(f"    {get_priority_display(task.priority)}")
                if task.project:
                    result.append(f"    {task.project}")
            
            result.append("")
        
        return "\n".join(result)
    
    def display(self, tasks: List[Task]):
        """显示看板"""
        if not tasks:
            console.print("[dim]暂无任务[/dim]")
            return
        
        # 按状态分组
        groups = self._group_tasks_by_status(tasks)
        
        console.print("📋 [bold]看板视图[/bold]")
        console.print()
        
        # 使用 Rich Table 创建三列看板
        from rich.table import Table
        
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
        
        # 三列：待处理、进行中、已完成
        status_order = [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.DONE]
        
        for status in status_order:
            status_display = get_status_display(status)
            status_tasks = groups[status]
            table.add_column(f"{status_display} ({len(status_tasks)})", no_wrap=False)
        
        # 找到最大的任务数，确定行数
        max_tasks = max(len(groups[status]) for status in status_order)
        
        # 逐行添加任务
        for i in range(max_tasks):
            row = []
            for status in status_order:
                status_tasks = groups[status]
                if i < len(status_tasks):
                    task = status_tasks[i]
                    # 创建小型卡片面板
                    mini_card = self._render_mini_card(task)
                    panel = Panel(mini_card, box=box.SQUARE, padding=(0, 1))
                    row.append(panel)
                else:
                    row.append("")
            
            table.add_row(*row)
        
        console.print(table)
