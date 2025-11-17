"""测试导入导出功能"""

import json
import tempfile
from pathlib import Path

import pytest

from vibe_todo.core import Task, TaskStatus, TaskPriority, TaskService
from vibe_todo.storage.repository import TaskRepository
from vibe_todo.io import TaskExporter, TaskImporter, ImportConflictStrategy
from vibe_todo.io.formats import ExportFormat


@pytest.fixture
def service():
    """创建测试服务"""
    repository = TaskRepository(":memory:")
    return TaskService(repository)


@pytest.fixture
def sample_tasks(service):
    """创建示例任务"""
    tasks = [
        Task(
            title="任务1",
            description="描述1",
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH,
            tags=["tag1", "tag2"],
            project="项目A",
        ),
        Task(
            title="任务2",
            description="描述2",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.MEDIUM,
            tags=["tag3"],
            project="项目B",
            time_spent=60,
        ),
    ]
    
    created_tasks = []
    for task in tasks:
        created = service.create_task(task)
        created_tasks.append(created)
    
    return created_tasks


class TestExporter:
    """测试导出器"""
    
    def test_export_to_json(self, service, sample_tasks):
        """测试导出为 JSON"""
        exporter = TaskExporter(service)
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name
        
        try:
            count = exporter.export_to_json(output_path)
            assert count == 2
            
            # 验证文件内容
            with open(output_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            assert data["version"] == "0.2.0"
            assert "export_date" in data
            assert len(data["tasks"]) == 2
            
            task1 = data["tasks"][0]
            # 由于数据库查询顺序可能不确定，验证任务存在即可
            titles = {task["title"] for task in data["tasks"]}
            assert "任务1" in titles
            assert "任务2" in titles
            
            # 验证至少一个任务的字段完整性
            assert task1["status"] in ["todo", "in_progress"]
            assert task1["priority"] in ["high", "medium"]
            assert isinstance(task1["tags"], list)
            assert "project" in task1
        
        finally:
            Path(output_path).unlink(missing_ok=True)
    
    def test_export_to_csv(self, service, sample_tasks):
        """测试导出为 CSV"""
        exporter = TaskExporter(service)
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name
        
        try:
            count = exporter.export_to_csv(output_path)
            assert count == 2
            
            # 验证文件内容
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            assert "任务1" in content
            assert "任务2" in content
            assert "tag1;tag2" in content  # 标签用分号分隔
        
        finally:
            Path(output_path).unlink(missing_ok=True)
    
    def test_export_specific_tasks(self, service, sample_tasks):
        """测试导出指定任务"""
        exporter = TaskExporter(service)
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name
        
        try:
            # 只导出第一个任务
            task_ids = [str(sample_tasks[0].id)]
            count = exporter.export_to_json(output_path, task_ids)
            assert count == 1
            
            with open(output_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            assert len(data["tasks"]) == 1
            assert data["tasks"][0]["title"] == "任务1"
        
        finally:
            Path(output_path).unlink(missing_ok=True)


class TestImporter:
    """测试导入器"""
    
    def test_import_from_json(self, service):
        """测试从 JSON 导入"""
        importer = TaskImporter(service)
        
        # 创建测试数据
        test_data = {
            "version": "0.2.0",
            "export_date": "2025-11-17T12:00:00",
            "backend": "TestRepository",
            "tasks": [
                {
                    "id": "1",
                    "title": "导入任务1",
                    "description": "描述1",
                    "status": "todo",
                    "priority": "high",
                    "due_date": None,
                    "tags": ["tag1"],
                    "project": "测试项目",
                    "time_spent_minutes": 0,
                    "created_at": None,
                    "updated_at": None,
                },
            ],
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            input_path = f.name
        
        try:
            result = importer.import_from_json(input_path)
            # 打印错误信息
            if result.error_count > 0:
                print(f"\n错误数: {result.error_count}")
                for line, error in result.errors:
                    print(f"行 {line}: {error}")
            assert result.success_count == 1
            assert result.error_count == 0
            
            # 验证任务已创建
            tasks = service.list_tasks()
            assert len(tasks) == 1
            assert tasks[0].title == "导入任务1"
        
        finally:
            Path(input_path).unlink(missing_ok=True)
    
    def test_import_from_csv(self, service):
        """测试从 CSV 导入"""
        importer = TaskImporter(service)
        
        # 创建测试 CSV
        csv_content = """title,description,status,priority,due_date,tags,project,time_spent_minutes
导入任务1,描述1,todo,high,,tag1;tag2,测试项目,30
导入任务2,描述2,in_progress,medium,,,60"""
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            input_path = f.name
        
        try:
            result = importer.import_from_csv(input_path)
            if result.error_count > 0:
                print(f"\n错误数: {result.error_count}")
                for line, error in result.errors:
                    print(f"行 {line}: {error}")
            assert result.success_count == 2
            assert result.error_count == 0
            
            # 验证任务已创建
            tasks = service.list_tasks()
            assert len(tasks) == 2
            titles = {task.title for task in tasks}
            assert "导入任务1" in titles
            assert "导入任务2" in titles
            assert tasks[0].tags or tasks[1].tags  # 至少有一个任务有标签
        
        finally:
            Path(input_path).unlink(missing_ok=True)
    
    def test_import_with_validation_errors(self, service):
        """测试导入数据验证"""
        importer = TaskImporter(service)
        
        # 创建包含错误数据的 JSON
        test_data = {
            "version": "0.2.0",
            "tasks": [
                {
                    "title": "",  # 空标题
                    "status": "INVALID",  # 无效状态
                    "priority": "high",
                },
            ],
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            input_path = f.name
        
        try:
            result = importer.import_from_json(input_path)
            assert result.error_count > 0
            assert result.success_count == 0
        
        finally:
            Path(input_path).unlink(missing_ok=True)
    
    def test_import_strategy_create_new(self, service, sample_tasks):
        """测试 CREATE_NEW 策略"""
        importer = TaskImporter(service)
        exporter = TaskExporter(service)
        
        # 先导出
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            export_path = f.name
        
        try:
            exporter.export_to_json(export_path)
            
            # 再导入（应该创建新任务，不是覆盖）
            result = importer.import_from_json(
                export_path, 
                ImportConflictStrategy.CREATE_NEW
            )
            assert result.success_count == 2
            
            # 应该有 4 个任务（原来2个 + 新增2个）
            tasks = service.list_tasks()
            assert len(tasks) == 4
        
        finally:
            Path(export_path).unlink(missing_ok=True)
