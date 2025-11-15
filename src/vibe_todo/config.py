"""配置管理"""
import os
import json
from pathlib import Path
from typing import Dict, Any


class Config:
    """配置管理器"""
    
    DEFAULT_CONFIG_PATH = Path.home() / ".vibe_todo" / "config.json"
    
    DEFAULT_CONFIG = {
        "backend": {
            "type": "sqlite",
            "sqlite": {
                "db_path": "vibe_todo.db"
            }
        }
    }
    
    def __init__(self, config_path: str = None):
        """
        Args:
            config_path: 配置文件路径，默认为 ~/.vibe_todo/config.json
        """
        self.config_path = Path(config_path) if config_path else self.DEFAULT_CONFIG_PATH
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()
    
    def _save_config(self):
        """保存配置文件"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def get_backend_type(self) -> str:
        """获取当前后端类型"""
        return self.config.get("backend", {}).get("type", "sqlite")
    
    def get_backend_config(self, backend_type: str = None) -> Dict[str, Any]:
        """获取指定后端的配置"""
        if not backend_type:
            backend_type = self.get_backend_type()
        return self.config.get("backend", {}).get(backend_type, {})
    
    def set_backend(self, backend_type: str, **kwargs):
        """设置后端配置"""
        if "backend" not in self.config:
            self.config["backend"] = {}
        
        self.config["backend"]["type"] = backend_type
        self.config["backend"][backend_type] = kwargs
        self._save_config()
    
    def get(self, key: str, default=None):
        """获取配置项"""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    def set(self, key: str, value: Any):
        """设置配置项"""
        keys = key.split(".")
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save_config()


# 全局配置实例
_config = None


def get_config() -> Config:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = Config()
    return _config
