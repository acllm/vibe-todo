"""命令行接口 - 使用 Rich 美化输出"""
import click
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.prompt import Confirm

from ..core import TaskService, TaskStatus, TaskPriority
from ..storage.factory import create_repository
from ..config import get_config

console = Console()


def get_service() -> TaskService:
    """获取任务服务实例"""
    repository = create_repository()
    return TaskService(repository)


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


@click.group()
@click.version_option(version="0.1.0")
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
@click.option("-p", "--project", help="按项目筛选")
@click.option("--overdue", is_flag=True, help="只显示逾期任务")
def list(status: str, project: str, overdue: bool):
    """列出所有任务"""
    service = get_service()

    status_filter = None
    if status:
        status_filter = TaskStatus(status)

    tasks = service.list_tasks(status=status_filter)
    
    # 项目筛选
    if project:
        tasks = [t for t in tasks if t.project == project]
    
    # 逾期筛选
    if overdue:
        tasks = [t for t in tasks if t.is_overdue()]

    if not tasks:
        console.print("[dim]暂无任务[/dim]")
        return

    # 创建表格
    table = Table(
        title="📋 任务列表",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )
    
    # ID 列使用自适应宽度，可以显示完整的 UUID（Notion）或数字 ID（SQLite）
    table.add_column("ID", style="cyan", overflow="fold")
    table.add_column("标题", style="white", no_wrap=False)
    table.add_column("状态", width=12)
    table.add_column("优先级", width=10)
    table.add_column("工时", width=8, style="blue")
    table.add_column("截止日期", width=12)
    table.add_column("标签", style="magenta")
    
    for task in tasks:
        # 工时
        time_str = task.format_time_spent() if task.time_spent > 0 else "-"
        
        # 截止日期
        due_str = "-"
        if task.due_date:
            due_str = task.due_date.strftime("%Y-%m-%d")
            if task.is_overdue():
                due_str = f"[red]{due_str} ⚠️[/red]"
            elif task.days_until_due() is not None and task.days_until_due() <= 3:
                due_str = f"[yellow]{due_str}[/yellow]"
        
        # 标签
        tags_str = ", ".join(task.tags) if task.tags else "-"
        
        # 标题（如果已完成添加删除线）
        title_text = task.title
        if task.status == TaskStatus.DONE:
            title_text = f"[dim strikethrough]{task.title}[/dim strikethrough]"
        
        table.add_row(
            str(task.id),
            title_text,
            get_status_display(task.status),
            get_priority_display(task.priority),
            time_str,
            due_str,
            tags_str,
        )
    
    console.print(table)


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
@click.argument("task_id")  # 改为字符串
@click.argument("minutes", type=int)
def time(task_id: str, minutes: int):
    """为任务添加工时（分钟）"""
    service = get_service()
    task = service.add_time(task_id, minutes)
    
    if not task:
        console.print(f"[red]✗ 任务 #{task_id} 不存在[/red]")
        return
    
    console.print(f"[green]✓ 已添加 {minutes} 分钟工时到任务 #{task.id}[/green]")
    console.print(f"  [blue]总工时: {task.format_time_spent()}[/blue]")


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


if __name__ == "__main__":
    cli()
