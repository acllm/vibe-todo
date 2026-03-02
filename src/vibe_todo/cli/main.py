"""命令行接口 - 使用 Rich 美化输出"""
import re
from datetime import datetime
from itertools import groupby
from typing import Dict, List, Optional

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from ..adapters import TaskFilter
from ..config import get_config
from ..core import Task, TaskPriority, TaskService, TaskStatus
from ..io import ImportConflictStrategy, TaskExporter, TaskImporter
from ..io.formats import ExportFormat
from ..storage.factory import create_repository
from .views import (
    TaskCardView, TaskTimelineView, TaskBoardView,
    get_status_display, get_priority_display
)

console = Console()


def get_service() -> TaskService:
    """获取任务服务实例"""
    repository = create_repository()
    return TaskService(repository)


def sort_and_group_tasks(tasks: List[Task]) -> Dict[TaskStatus, List[Task]]:
    """按状态和优先级对任务进行排序和分组
    
    排序规则：
    1. 先按状态分组：进行中 > 待处理 > 已完成
    2. 每个状态组内按优先级排序：紧急 > 高 > 中 > 低
    
    Args:
        tasks: 任务列表
    
    Returns:
        按状态分组的任务字典，每个组内按优先级排序
    """
    # 先按状态和优先级排序
    sorted_tasks = sorted(
        tasks,
        key=lambda t: (t.status.sort_order(), t.priority.sort_order())
    )

    # 按状态分组（使用列表推导式避免 list() 函数名冲突）
    grouped = {}
    for status, group in groupby(sorted_tasks, key=lambda t: t.status):
        grouped[status] = [task for task in group]

    return grouped


@click.group()
@click.version_option(version="0.2.4")
def cli():
    """Vibe Todo - 简洁实用的任务和工时管理工具"""
    pass


@cli.command()
@click.argument("title")
@click.option("-d", "--description", default="", help="任务描述")
@click.option("-p", "--priority", type=click.Choice(["low", "medium", "high", "urgent"]),
              default="medium", help="优先级")
@click.option("--due", help="截止日期 (格式: YYYY-MM-DD)")
@click.option("-t", "--tags", help="标签 (逗号分隔)")
@click.option("--project", help="项目名称")
def add(title: str, description: str, priority: str, due: str, tags: str, project: str):
    """添加新任务"""
    service = get_service()

    # 解析截止日期
    due_date = None
    if due:
        try:
            due_date = datetime.strptime(due, "%Y-%m-%d")
        except ValueError:
            console.print("[red]✗ 日期格式错误，应为 YYYY-MM-DD[/red]")
            return

    # 解析标签
    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    # 创建任务
    task = service.create_task(
        title=title,
        description=description,
        priority=TaskPriority(priority),
        due_date=due_date,
        tags=tag_list,
        project=project,
    )

    console.print(f"[green]✓ 任务已创建:[/green] [bold]#{task.id}[/bold] {task.title}")


@cli.command()
@click.option("-s", "--status", type=click.Choice(["todo", "in_progress", "done"]), help="按状态筛选")
@click.option("--priority", type=click.Choice(["low", "medium", "high", "urgent"]), help="按优先级筛选")
@click.option("-p", "--project", help="按项目筛选")
@click.option("-t", "--tags", help="按标签筛选（逗号分隔）")
@click.option("--tags-operator", type=click.Choice(["AND", "OR"]), default="OR",
              help="标签筛选逻辑（AND/OR，默认 OR）")
@click.option("--overdue", is_flag=True, help="只显示逾期任务")
@click.option("--due-in-days", type=int, help="只显示指定天数内到期的任务")
@click.option("--view", type=click.Choice(["table", "card", "timeline", "board"]), default="table",
              help="视图类型（table/card/timeline/board，默认 table）")
def list(status: str, priority: str, project: str, tags: str, tags_operator: str,
         overdue: bool, due_in_days: int, view: str):
    """列出所有任务（按状态和优先级分组展示，支持高级筛选）"""
    repo = create_repository()

    # 构建过滤条件
    task_filter = TaskFilter()

    if status:
        task_filter.status = TaskStatus(status)

    if priority:
        task_filter.priority = TaskPriority(priority)

    if project:
        task_filter.project = project

    if tags:
        task_filter.tags = [t.strip() for t in tags.split(",")]
        task_filter.tags_operator = tags_operator

    task_filter.overdue_only = overdue

    if due_in_days is not None:
        task_filter.due_in_days = due_in_days

    # 使用过滤条件
    if task_filter.has_any_filter():
        tasks = repo.filter_tasks(task_filter)
    else:
        tasks = repo.list_all()

    if not tasks:
        console.print("[dim]暂无任务[/dim]")
        return

    # 根据视图类型展示
    if view == "card":
        # 卡片视图
        card_view = TaskCardView()
        card_view.display_list(tasks)
    elif view == "timeline":
        # 时间线视图
        timeline_view = TaskTimelineView()
        timeline_view.display(tasks)
    elif view == "board":
        # 看板视图
        board_view = TaskBoardView()
        board_view.display(tasks)
    else:
        # 默认表格视图
        # 对任务进行分组和排序
        grouped_tasks = sort_and_group_tasks(tasks)

        # 按状态组展示任务
        for task_status in sorted(grouped_tasks.keys(), key=lambda s: s.sort_order()):
            status_tasks = grouped_tasks[task_status]

            # 创建每个状态组的表格
            status_display = get_status_display(task_status)
            table = Table(
                title=f"📋 {status_display} ({len(status_tasks)} 项)",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta",
            )

            # ID 列使用自适应宽度，可以显示完整的 UUID（Notion）或数字 ID（SQLite）
            table.add_column("ID", style="cyan", overflow="fold")
            table.add_column("标题", style="white", no_wrap=False)
            table.add_column("优先级", width=10)
            table.add_column("工时", width=8, style="blue")
            table.add_column("截止日期", width=12)
            table.add_column("标签", style="magenta")

            for task in status_tasks:
                # 工时
                time_str = task.format_time_spent() if task.time_spent > 0 else "-"

                # 截止日期
                if task.due_date:
                    due_date_str = task.due_date.strftime("%Y-%m-%d")
                    if task.is_overdue():
                        due_str = Text(due_date_str, style="red")
                    elif task.days_until_due() is not None and task.days_until_due() <= 3:
                        due_str = Text(due_date_str, style="yellow")
                    else:
                        due_str = due_date_str
                else:
                    due_str = "-"

                # 标签
                tags_str = ", ".join(task.tags) if task.tags else "-"

                # 标题（如果已完成添加删除线）
                title_text = task.title
                if task.status == TaskStatus.DONE:
                    title_text = f"[dim strikethrough]{task.title}[/dim strikethrough]"

                table.add_row(
                    str(task.id),
                    title_text,
                    get_priority_display(task.priority),
                    time_str,
                    due_str,
                    tags_str,
                )

            console.print(table)
            console.print()  # 在每个状态组之间添加空行


@cli.command()
@click.argument("query")
@click.option("-s", "--status", type=click.Choice(["todo", "in_progress", "done"]), help="按状态筛选")
@click.option("--priority", type=click.Choice(["low", "medium", "high", "urgent"]), help="按优先级筛选")
@click.option("-p", "--project", help="按项目筛选")
@click.option("-t", "--tags", help="按标签筛选（逗号分隔）")
@click.option("--tags-operator", type=click.Choice(["AND", "OR"]), default="OR",
              help="标签筛选逻辑（AND/OR，默认 OR）")
@click.option("--overdue", is_flag=True, help="只显示逾期任务")
@click.option("--due-in-days", type=int, help="只显示指定天数内到期的任务")
def search(query: str, status: str, priority: str, project: str, tags: str,
           tags_operator: str, overdue: bool, due_in_days: int):
    """全文搜索任务
    
    支持在标题、描述、标签和项目中搜索关键词，同时可以使用高级筛选条件。
    """
    repo = create_repository()

    # 构建过滤条件
    task_filter = TaskFilter()

    if status:
        task_filter.status = TaskStatus(status)

    if priority:
        task_filter.priority = TaskPriority(priority)

    if project:
        task_filter.project = project

    if tags:
        task_filter.tags = [t.strip() for t in tags.split(",")]
        task_filter.tags_operator = tags_operator

    task_filter.overdue_only = overdue

    if due_in_days is not None:
        task_filter.due_in_days = due_in_days

    # 执行搜索和过滤
    tasks = repo.search_and_filter(query=query, task_filter=task_filter)

    if not tasks:
        console.print(f"[dim]未找到匹配 '{query}' 的任务[/dim]")
        return

    console.print(f"[green]找到 {len(tasks)} 个匹配 '{query}' 的任务:[/green]")
    console.print()

    # 对任务进行分组和排序
    grouped_tasks = sort_and_group_tasks(tasks)

    # 按状态组展示任务
    for task_status in sorted(grouped_tasks.keys(), key=lambda s: s.sort_order()):
        status_tasks = grouped_tasks[task_status]

        # 创建每个状态组的表格
        status_display = get_status_display(task_status)
        table = Table(
            title=f"📋 {status_display} ({len(status_tasks)} 项)",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta",
        )

        # ID 列使用自适应宽度，可以显示完整的 UUID（Notion）或数字 ID（SQLite）
        table.add_column("ID", style="cyan", overflow="fold")
        table.add_column("标题", style="white", no_wrap=False)
        table.add_column("优先级", width=10)
        table.add_column("工时", width=8, style="blue")
        table.add_column("截止日期", width=12)
        table.add_column("标签", style="magenta")

        for task in status_tasks:
            # 工时
            time_str = task.format_time_spent() if task.time_spent > 0 else "-"

            # 截止日期
            if task.due_date:
                due_date_str = task.due_date.strftime("%Y-%m-%d")
                if task.is_overdue():
                    due_str = Text(due_date_str, style="red")
                elif task.days_until_due() is not None and task.days_until_due() <= 3:
                    due_str = Text(due_date_str, style="yellow")
                else:
                    due_str = due_date_str
            else:
                due_str = "-"

            # 标签
            tags_str = ", ".join(task.tags) if task.tags else "-"

            # 标题（如果已完成添加删除线）
            title_text = task.title
            if task.status == TaskStatus.DONE:
                title_text = f"[dim strikethrough]{task.title}[/dim strikethrough]"

            table.add_row(
                str(task.id),
                title_text,
                get_priority_display(task.priority),
                time_str,
                due_str,
                tags_str,
            )

        console.print(table)
        console.print()  # 在每个状态组之间添加空行


@cli.command()
@click.argument("task_id")  # 改为字符串，兼容 SQLite 的整数 ID 和 Notion 的 UUID
def show(task_id: str):
    """显示任务详情"""
    service = get_service()
    task = service.get_task(task_id)

    if not task:
        console.print(f"[red]✗ 任务 #{task_id} 不存在[/red]")
        return

    # 创建详情面板
    details = f"""
[bold cyan]标题:[/bold cyan] {task.title}
[bold cyan]描述:[/bold cyan] {task.description or '(无)'}
[bold cyan]状态:[/bold cyan] {get_status_display(task.status)}
[bold cyan]优先级:[/bold cyan] {get_priority_display(task.priority)}
[bold cyan]工时:[/bold cyan] [blue]{task.format_time_spent()}[/blue]
[bold cyan]截止日期:[/bold cyan] {task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else '(无)'}
[bold cyan]标签:[/bold cyan] {', '.join(task.tags) if task.tags else '(无)'}
[bold cyan]项目:[/bold cyan] {task.project or '(无)'}
[bold cyan]创建时间:[/bold cyan] {task.created_at.strftime('%Y-%m-%d %H:%M')}
[bold cyan]更新时间:[/bold cyan] {task.updated_at.strftime('%Y-%m-%d %H:%M')}
"""

    if task.is_overdue():
        details += "\n[red bold]⚠️  任务已逾期！[/red bold]"
    elif task.days_until_due() is not None and task.days_until_due() <= 3:
        details += f"\n[yellow]⏰ 还有 {task.days_until_due()} 天到期[/yellow]"

    panel = Panel(
        details.strip(),
        title=f"[bold]任务 #{task.id}[/bold]",
        border_style="cyan",
        box=box.ROUNDED,
    )
    console.print(panel)


@cli.command()
@click.argument("task_id")
def edit(task_id: str):
    """交互式编辑任务
    
    逐个字段编辑任务，可以选择跳过不修改的字段。
    """
    service = get_service()
    task = service.get_task(task_id)
    
    if not task:
        console.print(f"[red]✗ 任务 #{task_id} 不存在[/red]")
        return
    
    console.print()
    console.print(f"[bold cyan]编辑任务 #{task.id}[/bold cyan]")
    console.print(f"[dim]按 Enter 保持原值，输入新值修改[/dim]")
    console.print()
    
    # 编辑标题
    new_title = Prompt.ask(
        f"[bold]标题[/bold]",
        default=task.title
    )
    
    # 编辑描述
    new_description = Prompt.ask(
        f"[bold]描述[/bold]",
        default=task.description or "(空)"
    )
    if new_description == "(空)":
        new_description = ""
    
    # 编辑状态
    status_options = ["todo", "in_progress", "done"]
    status_display = {
        "todo": "⭕ 待处理",
        "in_progress": "🔄 进行中",
        "done": "✅ 已完成"
    }
    current_status = task.status.value
    new_status_str = Prompt.ask(
        f"[bold]状态[/bold] [dim](可选: todo, in_progress, done)[/dim]",
        default=current_status,
        choices=status_options,
        show_default=False
    )
    console.print(f"  → {status_display.get(new_status_str, new_status_str)}")
    new_status = TaskStatus(new_status_str)
    
    # 编辑优先级
    priority_options = ["low", "medium", "high", "urgent"]
    priority_display = {
        "low": "🟢 低",
        "medium": "🟡 中",
        "high": "🟠 高",
        "urgent": "🔴 紧急"
    }
    current_priority = task.priority.value
    new_priority_str = Prompt.ask(
        f"[bold]优先级[/bold] [dim](可选: low, medium, high, urgent)[/dim]",
        default=current_priority,
        choices=priority_options,
        show_default=False
    )
    console.print(f"  → {priority_display.get(new_priority_str, new_priority_str)}")
    new_priority = TaskPriority(new_priority_str)
    
    # 编辑截止日期
    current_due = task.due_date.strftime("%Y-%m-%d") if task.due_date else "(无)"
    new_due_str = Prompt.ask(
        f"[bold]截止日期[/bold] [dim](格式: YYYY-MM-DD)[/dim]",
        default=current_due
    )
    new_due = None
    if new_due_str != "(无)":
        try:
            new_due = datetime.strptime(new_due_str, "%Y-%m-%d")
        except ValueError:
            console.print(f"[yellow]⚠  日期格式错误，保持原值[/yellow]")
            new_due = task.due_date
    
    # 编辑标签
    current_tags = ", ".join(task.tags) if task.tags else "(无)"
    new_tags_str = Prompt.ask(
        f"[bold]标签[/bold] [dim](逗号分隔)[/dim]",
        default=current_tags
    )
    new_tags = []
    if new_tags_str != "(无)":
        new_tags = [t.strip() for t in new_tags_str.split(",") if t.strip()]
    
    # 编辑项目
    current_project = task.project or "(无)"
    new_project = Prompt.ask(
        f"[bold]项目[/bold]",
        default=current_project
    )
    if new_project == "(无)":
        new_project = None
    
    # 确认修改
    console.print()
    console.print("[bold]修改预览:[/bold]")
    
    changes = []
    if new_title != task.title:
        changes.append(f"  标题: [yellow]{task.title}[/yellow] → [green]{new_title}[/green]")
    if new_description != task.description:
        old_desc = task.description or "(空)"
        new_desc = new_description or "(空)"
        changes.append(f"  描述: [yellow]{old_desc}[/yellow] → [green]{new_desc}[/green]")
    if new_status != task.status:
        changes.append(f"  状态: [yellow]{status_display[task.status.value]}[/yellow] → [green]{status_display[new_status.value]}[/green]")
    if new_priority != task.priority:
        changes.append(f"  优先级: [yellow]{priority_display[task.priority.value]}[/yellow] → [green]{priority_display[new_priority.value]}[/green]")
    if new_due != task.due_date:
        old_due = task.due_date.strftime("%Y-%m-%d") if task.due_date else "(无)"
        new_due_display = new_due.strftime("%Y-%m-%d") if new_due else "(无)"
        changes.append(f"  截止日期: [yellow]{old_due}[/yellow] → [green]{new_due_display}[/green]")
    if set(new_tags) != set(task.tags):
        old_tags = ", ".join(task.tags) if task.tags else "(无)"
        new_tags_display = ", ".join(new_tags) if new_tags else "(无)"
        changes.append(f"  标签: [yellow]{old_tags}[/yellow] → [green]{new_tags_display}[/green]")
    if new_project != task.project:
        old_project = task.project or "(无)"
        new_project_display = new_project or "(无)"
        changes.append(f"  项目: [yellow]{old_project}[/yellow] → [green]{new_project_display}[/green]")
    
    if not changes:
        console.print("[dim]  没有修改[/dim]")
        console.print()
        console.print("[yellow]⚠  没有任何修改，取消保存[/yellow]")
        return
    
    for change in changes:
        console.print(change)
    
    console.print()
    if Confirm.ask("[bold]确认保存修改？[/bold]"):
        # 更新任务
        task.title = new_title
        task.description = new_description
        task.status = new_status
        task.priority = new_priority
        task.due_date = new_due
        task.tags = new_tags
        task.project = new_project
        
        updated_task = service.update_task(task)
        console.print()
        console.print(f"[green]✓ 任务已更新:[/green] [bold]#{updated_task.id}[/bold] {updated_task.title}")
    else:
        console.print()
        console.print("[dim]已取消[/dim]")


@cli.command()
@click.argument("task_id")  # 改为字符串
def done(task_id: str):
    """标记任务为完成"""
    service = get_service()
    task = service.mark_done(task_id)

    if not task:
        console.print(f"[red]✗ 任务 #{task_id} 不存在[/red]")
        return

    console.print(f"[green]✓ 任务已完成:[/green] [bold]#{task.id}[/bold] {task.title}")


@cli.command()
@click.argument("task_id")  # 改为字符串
def start(task_id: str):
    """标记任务为进行中"""
    service = get_service()
    task = service.mark_in_progress(task_id)

    if not task:
        console.print(f"[red]✗ 任务 #{task_id} 不存在[/red]")
        return

    console.print(f"[green]✓ 任务已开始:[/green] [bold]#{task.id}[/bold] {task.title}")


@cli.command()
@click.argument("task_id")
@click.argument("time_input")
def time(task_id: str, time_input: str):
    """为任务添加工时
    
    支持多种格式：
    - 数字: 90 (分钟)
    - 小时: 1.5h, 2h
    - 组合: 2h30m, 1h15m
    """
    service = get_service()

    # 解析时间输入
    minutes = parse_time_input(time_input)
    if minutes is None:
        console.print(f"[red]✗ 无效的时间格式: {time_input}[/red]")
        console.print("[yellow]支持的格式: 90, 1.5h, 2h30m[/yellow]")
        return

    if minutes <= 0:
        console.print("[red]✗ 工时必须是正数[/red]")
        return

    task = service.add_time(task_id, minutes)

    if not task:
        console.print(f"[red]✗ 任务 #{task_id} 不存在[/red]")
        return

    console.print(f"[green]✓ 已添加 {minutes} 分钟工时到任务 #{task.id}[/green]")
    console.print(f"  [blue]总工时: {task.format_time_spent()}[/blue]")


def parse_time_input(time_str: str) -> Optional[int]:
    """解析时间输入，返回分钟数
    
    支持格式：
    - 90 -> 90 分钟
    - 1.5h -> 90 分钟
    - 2h -> 120 分钟
    - 2h30m -> 150 分钟
    - 1h15m -> 75 分钟
    """

    time_str = time_str.strip().lower()

    # 格式 1: 纯数字（分钟）
    if time_str.isdigit():
        return int(time_str)

    # 格式 2: 小数小时 (1.5h, 2.0h)
    match = re.match(r'^(\d+(?:\.\d+)?)\s*h$', time_str)
    if match:
        hours = float(match.group(1))
        return int(hours * 60)

    # 格式 3: 小时+分钟 (2h30m, 1h15m)
    match = re.match(r'^(\d+)\s*h\s*(\d+)\s*m$', time_str)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        return hours * 60 + minutes

    # 格式 4: 仅分钟 (30m)
    match = re.match(r'^(\d+)\s*m$', time_str)
    if match:
        return int(match.group(1))

    return None


@cli.command()
@click.argument("task_id")  # 改为字符串
def delete(task_id: str):
    """删除任务"""
    service = get_service()

    # 使用 Rich 的确认提示
    if not Confirm.ask(f"[yellow]确认删除任务 #{task_id}？[/yellow]"):
        console.print("[dim]已取消[/dim]")
        return

    if service.delete_task(task_id):
        console.print(f"[green]✓ 任务 #{task_id} 已删除[/green]")
    else:
        console.print(f"[red]✗ 任务 #{task_id} 不存在[/red]")


@cli.command()
def stats():
    """显示统计信息"""
    service = get_service()
    stats = service.get_statistics()

    # 创建统计面板
    stats_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    stats_table.add_column(style="bold cyan")
    stats_table.add_column(style="bold white", justify="right")

    stats_table.add_row("📊 总任务数", str(stats['total']))
    stats_table.add_row("⭕ 待处理", f"[cyan]{stats['todo']}[/cyan]")
    stats_table.add_row("🔄 进行中", f"[yellow]{stats['in_progress']}[/yellow]")
    stats_table.add_row("✅ 已完成", f"[green]{stats['done']}[/green]")
    stats_table.add_row("⏱️  总工时", f"[blue]{stats['total_time_hours']:.1f} 小时[/blue]")

    panel = Panel(
        stats_table,
        title="[bold]任务统计[/bold]",
        border_style="magenta",
        box=box.ROUNDED,
    )
    console.print(panel)


@cli.group()
def config():
    """配置管理"""
    pass


@config.command(name="show")
def config_show():
    """显示当前配置"""
    cfg = get_config()
    backend_type = cfg.get_backend_type()
    backend_config = cfg.get_backend_config()

    info = f"""
[bold cyan]当前后端:[/bold cyan] [yellow]{backend_type}[/yellow]
[bold cyan]配置:[/bold cyan]
"""

    for key, value in backend_config.items():
        # 隐藏敏感信息
        if "token" in key.lower() or "secret" in key.lower():
            value = "*" * 8 + value[-4:] if len(value) > 4 else "****"
        info += f"  [cyan]{key}:[/cyan] {value}\n"

    panel = Panel(
        info.strip(),
        title="[bold]配置信息[/bold]",
        border_style="cyan",
        box=box.ROUNDED,
    )
    console.print(panel)


@config.command(name="set-backend")
@click.argument("backend_type", type=click.Choice(["sqlite", "notion", "microsoft"]))
@click.option("--db-path", help="SQLite 数据库路径")
@click.option("--token", help="Notion Integration Token")
@click.option("--database", help="Notion Database ID")
@click.option("--client-id", help="Microsoft Azure Client ID")
@click.option("--list-id", help="Microsoft To Do List ID")
def config_set_backend(backend_type: str, db_path: str, token: str, database: str,
                       client_id: str, list_id: str):
    """设置后端配置"""
    cfg = get_config()

    if backend_type == "sqlite":
        if not db_path:
            db_path = "vibe_todo.db"
        cfg.set_backend("sqlite", db_path=db_path)
        console.print(f"[green]✓ 已切换到 SQLite 后端: {db_path}[/green]")

    elif backend_type == "notion":
        if not token or not database:
            console.print("[red]✗ Notion 后端需要 --token 和 --database 参数[/red]")
            return
        cfg.set_backend("notion", token=token, database_id=database)
        console.print("[green]✓ 已切换到 Notion 后端[/green]")

    elif backend_type == "microsoft":
        if not client_id:
            console.print("[red]✗ Microsoft To Do 后端需要 --client-id 参数[/red]")
            return
        kwargs = {"client_id": client_id}
        if list_id:
            kwargs["list_id"] = list_id
        cfg.set_backend("microsoft", **kwargs)
        console.print("[green]✓ 已切换到 Microsoft To Do 后端[/green]")
        console.print("[yellow]⚠️  首次使用需要进行 OAuth2 认证[/yellow]")


@cli.command()
def web():
    """启动 Web 服务器"""
    import uvicorn

    from ..web.app import app

    console.print("[green]🚀 启动 Web 服务器...[/green]")
    console.print("[cyan]📍 访问: http://localhost:8000[/cyan]")
    uvicorn.run(app, host="0.0.0.0", port=8000)


@cli.command()
@click.argument("output_path")
@click.option("--format", "-f", type=click.Choice(["json", "csv"]), default="json",
              help="导出格式 (默认: json)")
@click.option("--ids", help="指定要导出的任务ID，用逗号分隔")
def export(output_path: str, format: str, ids: Optional[str]):
    """导出任务到文件"""
    service = get_service()
    exporter = TaskExporter(service)

    # 解析任务ID
    task_ids = None
    if ids:
        task_ids = [tid.strip() for tid in ids.split(",")]

    # 执行导出
    export_format = ExportFormat.JSON if format == "json" else ExportFormat.CSV

    try:
        count = exporter.export_tasks(output_path, export_format, task_ids)
        console.print(f"[green]✓ 成功导出 {count} 个任务到: {output_path}[/green]")
    except Exception as e:
        console.print(f"[red]✗ 导出失败: {str(e)}[/red]")


@cli.command(name="import")
@click.argument("input_path")
@click.option("--format", "-f", type=click.Choice(["json", "csv"]), default="json",
              help="导入格式 (默认: json)")
@click.option("--strategy", "-s",
              type=click.Choice(["skip", "overwrite", "create_new"]),
              default="create_new",
              help="冲突处理策略 (默认: create_new)")
def import_tasks(input_path: str, format: str, strategy: str):
    """从文件导入任务"""
    service = get_service()
    importer = TaskImporter(service)

    # 解析策略
    strategy_map = {
        "skip": ImportConflictStrategy.SKIP,
        "overwrite": ImportConflictStrategy.OVERWRITE,
        "create_new": ImportConflictStrategy.CREATE_NEW,
    }
    conflict_strategy = strategy_map[strategy]

    # 执行导入
    try:
        if format == "json":
            result = importer.import_from_json(input_path, conflict_strategy)
        else:
            result = importer.import_from_csv(input_path, conflict_strategy)

        # 显示结果
        console.print("\n[bold]导入结果:[/bold]")
        console.print(f"  [green]✓ 成功: {result.success_count}[/green]")
        if result.skip_count > 0:
            console.print(f"  [yellow]⊘ 跳过: {result.skip_count}[/yellow]")
        if result.error_count > 0:
            console.print(f"  [red]✗ 错误: {result.error_count}[/red]")
            console.print("\n[bold red]错误详情:[/bold red]")
            for line, error in result.errors[:10]:  # 只显示前10个错误
                console.print(f"  第 {line} 行: {error}")
            if len(result.errors) > 10:
                console.print(f"  ... 还有 {len(result.errors) - 10} 个错误")

    except Exception as e:
        console.print(f"[red]✗ 导入失败: {str(e)}[/red]")


@cli.group()
def batch():
    """批量操作命令"""
    pass


@batch.command(name="done")
@click.argument("task_ids", nargs=-1, required=True)
def batch_done(task_ids):
    """批量标记任务为完成"""
    service = get_service()
    count = service.batch_update_status(list(task_ids), TaskStatus.DONE)
    console.print(f"[green]✓ 成功标记 {count} 个任务为完成[/green]")


@batch.command(name="delete")
@click.argument("task_ids", nargs=-1, required=True)
def batch_delete(task_ids):
    """批量删除任务"""
    service = get_service()

    # 确认删除
    if not Confirm.ask(f"[yellow]确定要删除 {len(task_ids)} 个任务吗？[/yellow]"):
        console.print("[cyan]已取消[/cyan]")
        return

    count = service.batch_delete(list(task_ids))
    console.print(f"[green]✓ 成功删除 {count} 个任务[/green]")


@batch.command(name="tag")
@click.argument("task_ids", nargs=-1, required=True)
@click.argument("tags")
def batch_tag(task_ids, tags: str):
    """批量添加标签（用逗号分隔多个标签）"""
    service = get_service()
    tag_list = [t.strip() for t in tags.split(",")]
    count = service.batch_add_tags(list(task_ids), tag_list)
    console.print(f"[green]✓ 成功为 {count} 个任务添加标签: {', '.join(tag_list)}[/green]")


@batch.command(name="priority")
@click.argument("task_ids", nargs=-1, required=True)
@click.argument("priority_level", type=click.Choice(["low", "medium", "high", "urgent"]))
def batch_priority(task_ids, priority_level: str):
    """批量设置优先级"""
    service = get_service()
    priority_map = {
        "low": TaskPriority.LOW,
        "medium": TaskPriority.MEDIUM,
        "high": TaskPriority.HIGH,
        "urgent": TaskPriority.URGENT,
    }
    count = service.batch_update_priority(list(task_ids), priority_map[priority_level])
    console.print(f"[green]✓ 成功设置 {count} 个任务的优先级为: {priority_level}[/green]")


@batch.command(name="project")
@click.argument("task_ids", nargs=-1, required=True)
@click.argument("project_name")
def batch_project(task_ids, project_name: str):
    """批量设置项目"""
    service = get_service()
    count = service.batch_update_project(list(task_ids), project_name)
    console.print(f"[green]✓ 成功设置 {count} 个任务的项目为: {project_name}[/green]")


if __name__ == "__main__":
    cli()
