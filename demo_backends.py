#!/usr/bin/env python3
"""
Vibe Todo 多后端演示脚本

展示如何在代码中使用不同的后端
"""

from vibe_todo.core import TaskService, TaskStatus, TaskPriority
from vibe_todo.storage.factory import create_repository
from vibe_todo.config import Config
from datetime import datetime, timedelta


def demo_sqlite():
    """演示 SQLite 后端"""
    print("\n=== SQLite 后端演示 ===\n")
    
    # 创建配置
    config = Config()
    config.set_backend("sqlite", db_path="demo.db")
    
    # 创建服务
    repository = create_repository()
    service = TaskService(repository)
    
    # 添加任务
    task1 = service.create_task(
        title="学习 Python 高级特性",
        description="装饰器、生成器、上下文管理器",
        priority=TaskPriority.HIGH,
        due_date=datetime.now() + timedelta(days=7),
        tags=["学习", "Python"],
        project="技术提升"
    )
    print(f"✓ 创建任务: {task1.title}")
    
    # 列出任务
    tasks = service.list_tasks()
    print(f"\n当前有 {len(tasks)} 个任务:")
    for task in tasks:
        print(f"  - [{task.status.value}] {task.title}")
    
    # 统计
    stats = service.get_statistics()
    print(f"\n统计信息:")
    print(f"  总任务: {stats['total']}")
    print(f"  待处理: {stats['todo']}")


def demo_notion():
    """演示 Notion 后端（需要配置）"""
    print("\n=== Notion 后端演示 ===\n")
    print("请先配置 Notion:")
    print("  vibe config set-backend notion --token <token> --database <id>")
    print("\n然后修改此脚本取消注释以下代码:\n")
    
    # 取消注释以下代码使用 Notion
    # config = Config()
    # config.set_backend(
    #     "notion",
    #     token="your_integration_token",
    #     database_id="your_database_id"
    # )
    # 
    # repository = create_repository()
    # service = TaskService(repository)
    # 
    # task = service.create_task(
    #     title="Notion 同步测试",
    #     description="这个任务会出现在 Notion 中",
    #     priority=TaskPriority.MEDIUM,
    #     tags=["测试", "Notion"]
    # )
    # print(f"✓ 任务已同步到 Notion: {task.id}")


def demo_microsoft():
    """演示 Microsoft To Do 后端（需要配置）"""
    print("\n=== Microsoft To Do 后端演示 ===\n")
    print("请先配置 Microsoft To Do:")
    print("  vibe config set-backend microsoft --client-id <id>")
    print("\n然后修改此脚本取消注释以下代码:\n")
    
    # 取消注释以下代码使用 Microsoft To Do
    # config = Config()
    # config.set_backend(
    #     "microsoft",
    #     client_id="your_client_id"
    # )
    # 
    # repository = create_repository()  # 会触发 OAuth2 认证
    # service = TaskService(repository)
    # 
    # task = service.create_task(
    #     title="Microsoft To Do 同步测试",
    #     priority=TaskPriority.HIGH,
    #     due_date=datetime.now() + timedelta(days=1),
    #     tags=["测试", "Microsoft"]
    # )
    # print(f"✓ 任务已同步到 Microsoft To Do: {task.id}")


def demo_backend_switch():
    """演示后端切换"""
    print("\n=== 后端切换演示 ===\n")
    
    config = Config()
    
    # 使用 SQLite
    config.set_backend("sqlite", db_path="backend1.db")
    repo1 = create_repository()
    service1 = TaskService(repo1)
    task1 = service1.create_task("SQLite 任务")
    print(f"✓ SQLite: 创建任务 #{task1.id}")
    
    # 切换到另一个 SQLite 数据库
    config.set_backend("sqlite", db_path="backend2.db")
    repo2 = create_repository()
    service2 = TaskService(repo2)
    task2 = service2.create_task("另一个数据库的任务")
    print(f"✓ SQLite2: 创建任务 #{task2.id}")
    
    # 验证数据隔离
    tasks1 = service1.list_tasks()
    tasks2 = service2.list_tasks()
    print(f"\n数据隔离验证:")
    print(f"  backend1.db: {len(tasks1)} 个任务")
    print(f"  backend2.db: {len(tasks2)} 个任务")


if __name__ == "__main__":
    print("Vibe Todo 多后端演示")
    print("=" * 50)
    
    # 演示 SQLite
    demo_sqlite()
    
    # 演示后端切换
    demo_backend_switch()
    
    # Notion 和 Microsoft 需要配置后使用
    demo_notion()
    demo_microsoft()
    
    print("\n" + "=" * 50)
    print("演示完成！")
    print("\n提示: 使用 'vibe config show' 查看当前配置")
