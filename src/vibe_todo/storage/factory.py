"""仓储工厂 - 根据配置创建对应的仓储实例"""
from typing import Union
from .repository import TaskRepository
from ..adapters import TaskRepositoryInterface
from ..config import get_config


def create_repository() -> TaskRepositoryInterface:
    """
    根据配置创建仓储实例
    
    Returns:
        TaskRepositoryInterface: 仓储实例（SQLite/Notion/Microsoft）
    """
    config = get_config()
    backend_type = config.get_backend_type()
    
    if backend_type == "sqlite":
        # SQLite 本地存储
        backend_config = config.get_backend_config("sqlite")
        db_path = backend_config.get("db_path", "vibe_todo.db")
        return TaskRepository(db_path=db_path)
    
    elif backend_type == "notion":
        # Notion 后端
        from ..adapters.notion_adapter import NotionRepository
        backend_config = config.get_backend_config("notion")
        
        token = backend_config.get("token")
        database_id = backend_config.get("database_id")
        cached_data_source_id = backend_config.get("data_source_id")  # 获取缓存的 data_source_id
        
        if not token or not database_id:
            raise ValueError(
                "Notion 后端需要配置 token 和 database_id。\n"
                "请运行: vibe config set-backend notion --token <token> --database <id>"
            )
        
        return NotionRepository(
            token=token, 
            database_id=database_id,
            cached_data_source_id=cached_data_source_id
        )
    
    elif backend_type == "microsoft":
        # Microsoft To Do 后端
        from ..adapters.microsoft_adapter import MicrosoftRepository
        backend_config = config.get_backend_config("microsoft")
        
        client_id = backend_config.get("client_id")
        list_id = backend_config.get("list_id")
        
        if not client_id:
            raise ValueError(
                "Microsoft To Do 后端需要配置 client_id。\n"
                "请运行: vibe config set-backend microsoft --client-id <id>"
            )
        
        return MicrosoftRepository(client_id=client_id, list_id=list_id)
    
    else:
        raise ValueError(
            f"未知的后端类型: {backend_type}。\n"
            f"支持的类型: sqlite, notion, microsoft"
        )
