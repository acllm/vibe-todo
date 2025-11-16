"""Web 应用接口"""
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..core import TaskService, TaskStatus
from ..storage.factory import create_repository

app = FastAPI(title="Vibe Todo")

# 配置模板目录
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


def get_service() -> TaskService:
    """获取任务服务实例"""
    repository = create_repository()
    return TaskService(repository)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页：任务列表"""
    service = get_service()
    tasks = service.list_tasks()
    stats = service.get_statistics()

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "tasks": tasks, "stats": stats}
    )


@app.post("/tasks", response_class=HTMLResponse)
async def create_task(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    priority: str = Form("medium"),
    due_date: str = Form(None),
    tags: str = Form(""),
    project: str = Form("")
):
    """创建新任务"""
    from ..core import TaskPriority
    from datetime import datetime
    
    service = get_service()
    
    # 解析截止日期
    due_date_obj = None
    if due_date:
        try:
            due_date_obj = datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            pass
    
    # 解析标签
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    
    task = service.create_task(
        title=title,
        description=description,
        priority=TaskPriority(priority),
        due_date=due_date_obj,
        tags=tag_list,
        project=project if project else None
    )

    # 返回任务列表片段（HTMX 会替换页面内容）
    tasks = service.list_tasks()
    stats = service.get_statistics()
    return templates.TemplateResponse(
        "partials/task_list.html",
        {"request": request, "tasks": tasks, "stats": stats}
    )


@app.post("/tasks/{task_id}/done", response_class=HTMLResponse)
async def mark_done(request: Request, task_id: str):
    """标记任务为完成"""
    service = get_service()
    task = service.mark_done(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 返回更新后的任务列表
    tasks = service.list_tasks()
    stats = service.get_statistics()
    return templates.TemplateResponse(
        "partials/task_list.html",
        {"request": request, "tasks": tasks, "stats": stats}
    )


@app.post("/tasks/{task_id}/start", response_class=HTMLResponse)
async def mark_in_progress(request: Request, task_id: str):
    """标记任务为进行中"""
    service = get_service()
    task = service.mark_in_progress(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    tasks = service.list_tasks()
    stats = service.get_statistics()
    return templates.TemplateResponse(
        "partials/task_list.html",
        {"request": request, "tasks": tasks, "stats": stats}
    )


@app.post("/tasks/{task_id}/todo", response_class=HTMLResponse)
async def mark_todo(request: Request, task_id: str):
    """标记任务为待处理（暂停）"""
    service = get_service()
    task = service.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    from ..core import TaskStatus
    task.status = TaskStatus.TODO
    service.repository.save(task)

    tasks = service.list_tasks()
    stats = service.get_statistics()
    return templates.TemplateResponse(
        "partials/task_list.html",
        {"request": request, "tasks": tasks, "stats": stats}
    )


@app.delete("/tasks/{task_id}", response_class=HTMLResponse)
async def delete_task(request: Request, task_id: str):
    """删除任务"""
    service = get_service()
    success = service.delete_task(task_id)

    if not success:
        raise HTTPException(status_code=404, detail="任务不存在")

    tasks = service.list_tasks()
    stats = service.get_statistics()
    return templates.TemplateResponse(
        "partials/task_list.html",
        {"request": request, "tasks": tasks, "stats": stats}
    )


@app.post("/tasks/{task_id}/time", response_class=HTMLResponse)
async def add_time(request: Request, task_id: str, minutes: int = Form(...)):
    """添加工时"""
    service = get_service()
    task = service.add_time(task_id, minutes)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    tasks = service.list_tasks()
    stats = service.get_statistics()
    return templates.TemplateResponse(
        "partials/task_list.html",
        {"request": request, "tasks": tasks, "stats": stats}
    )


@app.get("/tasks/filter/{status}", response_class=HTMLResponse)
async def filter_tasks(request: Request, status: str):
    """按状态筛选任务"""
    service = get_service()

    status_filter = None if status == "all" else TaskStatus(status)
    tasks = service.list_tasks(status=status_filter)
    stats = service.get_statistics()

    return templates.TemplateResponse(
        "partials/task_list.html",
        {"request": request, "tasks": tasks, "stats": stats, "current_filter": status}
    )
