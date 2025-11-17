"""任务导入器"""

import csv
import json
from enum import Enum
from pathlib import Path
from typing import Dict, List, Tuple

from ..core.models import Task
from ..core.service import TaskService
from .formats import DataValidator, dict_to_task


class ImportConflictStrategy(Enum):
    """导入冲突策略"""
    SKIP = "skip"           # 跳过冲突任务
    OVERWRITE = "overwrite"  # 覆盖已存在任务
    CREATE_NEW = "create_new"  # 创建新任务（推荐）


class ImportResult:
    """导入结果"""
    
    def __init__(self):
        self.success_count = 0
        self.skip_count = 0
        self.error_count = 0
        self.errors: List[Tuple[int, str]] = []  # (行号, 错误信息)
    
    def add_success(self):
        self.success_count += 1
    
    def add_skip(self):
        self.skip_count += 1
    
    def add_error(self, line: int, error: str):
        self.error_count += 1
        self.errors.append((line, error))
    
    @property
    def total_count(self) -> int:
        return self.success_count + self.skip_count + self.error_count


class TaskImporter:
    """任务导入器"""
    
    def __init__(self, service: TaskService):
        self.service = service
    
    def import_from_json(
        self,
        input_path: str,
        strategy: ImportConflictStrategy = ImportConflictStrategy.CREATE_NEW
    ) -> ImportResult:
        """
        从 JSON 文件导入任务
        
        Args:
            input_path: 输入文件路径
            strategy: 冲突处理策略
        
        Returns:
            导入结果
        """
        result = ImportResult()
        
        # 读取文件
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            result.add_error(0, f"读取文件失败: {str(e)}")
            return result
        
        # 验证导出数据格式
        errors = DataValidator.validate_export_data(data)
        if errors:
            for error in errors:
                result.add_error(0, error)
            return result
        
        # 导入任务
        tasks_data = data.get("tasks", [])
        for idx, task_data in enumerate(tasks_data, start=1):
            try:
                self._import_task(task_data, strategy, result, idx)
            except Exception as e:
                result.add_error(idx, f"导入失败: {str(e)}")
        
        return result
    
    def import_from_csv(
        self,
        input_path: str,
        strategy: ImportConflictStrategy = ImportConflictStrategy.CREATE_NEW
    ) -> ImportResult:
        """
        从 CSV 文件导入任务
        
        Args:
            input_path: 输入文件路径
            strategy: 冲突处理策略
        
        Returns:
            导入结果
        """
        result = ImportResult()
        
        # 读取文件
        try:
            with open(input_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                
                for idx, row in enumerate(reader, start=2):  # 跳过表头，从第2行开始
                    try:
                        # 转换 CSV 行为任务字典
                        task_data = self._csv_row_to_dict(row)
                        self._import_task(task_data, strategy, result, idx)
                    except Exception as e:
                        result.add_error(idx, f"导入失败: {str(e)}")
        
        except Exception as e:
            result.add_error(0, f"读取文件失败: {str(e)}")
        
        return result
    
    def _csv_row_to_dict(self, row: Dict[str, str]) -> Dict[str, any]:
        """将 CSV 行转换为任务字典"""
        task_data = {
            "title": (row.get("title") or "").strip(),
            "description": (row.get("description") or "").strip() or None,
            "status": (row.get("status") or "").strip(),
            "priority": (row.get("priority") or "").strip(),
            "due_date": (row.get("due_date") or "").strip() or None,
            "tags": [t.strip() for t in (row.get("tags") or "").split(";") if t.strip()],
            "project": (row.get("project") or "").strip() or None,
            "time_spent_minutes": (row.get("time_spent_minutes") or "0").strip(),
        }
        
        # 清理空字符串
        if not task_data["description"]:
            task_data["description"] = None
        if not task_data["due_date"]:
            task_data["due_date"] = None
        if not task_data["project"]:
            task_data["project"] = None
        
        return task_data
    
    def _import_task(
        self,
        task_data: Dict[str, any],
        strategy: ImportConflictStrategy,
        result: ImportResult,
        line: int
    ):
        """导入单个任务"""
        # 验证数据
        errors = DataValidator.validate_task_dict(task_data)
        if errors:
            for error in errors:
                result.add_error(line, error)
            return
        
        # 根据策略处理
        task_id = task_data.get("id")
        
        if strategy == ImportConflictStrategy.CREATE_NEW or not task_id:
            # 创建新任务（忽略原ID）
            task = dict_to_task(task_data)
            self.service.create_task(task)
            result.add_success()
        
        elif strategy == ImportConflictStrategy.SKIP:
            # 检查是否存在
            existing = self.service.get_task(task_id)
            if existing:
                result.add_skip()
            else:
                task = dict_to_task(task_data)
                self.service.create_task(task)
                result.add_success()
        
        elif strategy == ImportConflictStrategy.OVERWRITE:
            # 覆盖已存在的任务
            existing = self.service.get_task(task_id)
            if existing:
                # 更新现有任务
                task = dict_to_task(task_data)
                task.id = existing.id
                self.service.repository.save(task)
                result.add_success()
            else:
                # 创建新任务
                task = dict_to_task(task_data)
                self.service.create_task(task)
                result.add_success()
