"""任务导出器"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..core.models import Task
from ..core.service import TaskService
from .formats import ExportFormat, task_to_dict


class TaskExporter:
    """任务导出器"""
    
    def __init__(self, service: TaskService):
        self.service = service
    
    def export_to_json(
        self,
        output_path: str,
        task_ids: Optional[List[str]] = None
    ) -> int:
        """
        导出任务到 JSON 文件
        
        Args:
            output_path: 输出文件路径
            task_ids: 要导出的任务ID列表，None表示导出全部
        
        Returns:
            导出的任务数量
        """
        # 获取任务
        if task_ids:
            tasks = []
            for task_id in task_ids:
                task = self.service.get_task(task_id)
                if task:
                    tasks.append(task)
        else:
            tasks = self.service.list_tasks()
        
        # 转换为字典
        task_dicts = [task_to_dict(task) for task in tasks]
        
        # 构建导出数据
        export_data = {
            "version": "0.2.0",
            "export_date": datetime.now().isoformat(),
            "backend": self.service.repository.__class__.__name__,
            "tasks": task_dicts,
        }
        
        # 写入文件
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return len(tasks)
    
    def export_to_csv(
        self,
        output_path: str,
        task_ids: Optional[List[str]] = None
    ) -> int:
        """
        导出任务到 CSV 文件
        
        Args:
            output_path: 输出文件路径
            task_ids: 要导出的任务ID列表，None表示导出全部
        
        Returns:
            导出的任务数量
        """
        # 获取任务
        if task_ids:
            tasks = []
            for task_id in task_ids:
                task = self.service.get_task(task_id)
                if task:
                    tasks.append(task)
        else:
            tasks = self.service.list_tasks()
        
        if not tasks:
            return 0
        
        # CSV 字段定义
        fieldnames = [
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "tags",
            "project",
            "time_spent_minutes",
        ]
        
        # 写入文件
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for task in tasks:
                row = {
                    "title": task.title,
                    "description": task.description or "",
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "due_date": task.due_date.isoformat() if task.due_date else "",
                    "tags": ";".join(task.tags) if task.tags else "",
                    "project": task.project or "",
                    "time_spent_minutes": task.time_spent,
                }
                writer.writerow(row)
        
        return len(tasks)
    
    def export_tasks(
        self,
        output_path: str,
        format: ExportFormat = ExportFormat.JSON,
        task_ids: Optional[List[str]] = None
    ) -> int:
        """
        导出任务
        
        Args:
            output_path: 输出文件路径
            format: 导出格式
            task_ids: 要导出的任务ID列表，None表示导出全部
        
        Returns:
            导出的任务数量
        """
        if format == ExportFormat.JSON:
            return self.export_to_json(output_path, task_ids)
        elif format == ExportFormat.CSV:
            return self.export_to_csv(output_path, task_ids)
        else:
            raise ValueError(f"不支持的导出格式: {format}")
