"""Notion 适配器配置缓存测试

注意：
- 这些测试通过 mock 模拟 notion-client 的行为
- 如果 notion-client 未安装，整个测试文件会被跳过
- 测试不会实际连接 Notion API
- 安装可选依赖: uv pip install -e ".[notion]"
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock, create_autospec

# 尝试导入，如果失败则跳过整个模块
try:
    from vibe_todo.adapters.notion_adapter import NotionRepository
    # 尝试导入 notion_client 来检查是否安装
    import notion_client
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    # 创建一个占位符，避免后续引用错误
    NotionRepository = None

pytestmark = pytest.mark.skipif(
    not NOTION_AVAILABLE,
    reason="notion-client not installed (optional dependency)"
)


class TestNotionCaching:
    """测试 Notion 适配器的缓存机制"""
    
    def test_init_with_cached_data_source_id(self):
        """测试使用缓存的 data_source_id 初始化"""
        with patch('notion_client.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # 使用缓存的 data_source_id
            cached_id = "cached-data-source-123"
            repo = NotionRepository(
                token="test_token",
                database_id="test_db_id",
                cached_data_source_id=cached_id
            )
            
            # 验证：使用缓存后不应该调用 databases.retrieve
            assert repo.data_source_id == cached_id
            assert repo._verified is True
            mock_client.databases.retrieve.assert_not_called()
    
    def test_init_without_cache(self):
        """测试不使用缓存的初始化"""
        with patch('notion_client.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # 不使用缓存
            repo = NotionRepository(
                token="test_token",
                database_id="test_db_id",
                cached_data_source_id=None
            )
            
            # 验证：未使用缓存时不会立即验证
            assert repo.data_source_id is None
            assert repo._verified is False
            mock_client.databases.retrieve.assert_not_called()
    
    def test_lazy_data_source_retrieval(self):
        """测试延迟获取 data_source_id"""
        with patch('notion_client.Client') as mock_client_class, \
             patch('vibe_todo.config.get_config') as mock_get_config:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_get_config.return_value = Mock()
            
            # 模拟 databases.retrieve 返回
            mock_db_info = {
                "data_sources": [{"id": "retrieved-data-source-456"}]
            }
            mock_client.databases.retrieve.return_value = mock_db_info
            
            # 创建仓储（不使用缓存）
            repo = NotionRepository(
                token="test_token",
                database_id="test_db_id",
                cached_data_source_id=None
            )
            
            # 手动调用 _ensure_data_source
            repo._ensure_data_source()
            
            # 验证：应该调用了 databases.retrieve
            mock_client.databases.retrieve.assert_called_once_with(
                database_id="test_db_id"
            )
            assert repo.data_source_id == "retrieved-data-source-456"
            assert repo._verified is True
    
    def test_cache_data_source_id(self):
        """测试缓存 data_source_id 到配置"""
        with patch('notion_client.Client') as mock_client_class, \
             patch('vibe_todo.config.get_config') as mock_get_config:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # 模拟配置对象
            mock_config = Mock()
            mock_get_config.return_value = mock_config
            
            # 模拟 databases.retrieve 返回
            mock_db_info = {
                "data_sources": [{"id": "new-data-source-789"}]
            }
            mock_client.databases.retrieve.return_value = mock_db_info
            
            # 创建仓储并触发缓存
            repo = NotionRepository(
                token="test_token",
                database_id="test_db_id",
                cached_data_source_id=None
            )
            repo._ensure_data_source()
            
            # 验证：应该调用了 update_backend_config
            mock_config.update_backend_config.assert_called_once_with(
                "notion",
                data_source_id="new-data-source-789"
            )
    
    def test_ensure_data_source_idempotent(self):
        """测试 _ensure_data_source 的幂等性"""
        with patch('notion_client.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # 使用缓存
            repo = NotionRepository(
                token="test_token",
                database_id="test_db_id",
                cached_data_source_id="cached-id"
            )
            
            # 多次调用 _ensure_data_source
            repo._ensure_data_source()
            repo._ensure_data_source()
            repo._ensure_data_source()
            
            # 验证：不应该调用 databases.retrieve
            mock_client.databases.retrieve.assert_not_called()
    
    def test_fallback_to_database_id(self):
        """测试当没有 data_sources 字段时回退到 database_id"""
        with patch('notion_client.Client') as mock_client_class, \
             patch('vibe_todo.config.get_config') as mock_get_config:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_get_config.return_value = Mock()
            
            # 模拟没有 data_sources 的返回
            mock_db_info = {
                "id": "test_db_id",
                "title": [{"plain_text": "Test Database"}]
            }
            mock_client.databases.retrieve.return_value = mock_db_info
            
            repo = NotionRepository(
                token="test_token",
                database_id="test_db_id",
                cached_data_source_id=None
            )
            repo._ensure_data_source()
            
            # 验证：应该使用 database_id 作为 data_source_id
            assert repo.data_source_id == "test_db_id"


class TestNotionPagination:
    """测试 Notion 适配器的分页功能"""
    
    def test_list_all_with_pagination(self):
        """测试分页查询所有任务"""
        with patch('notion_client.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # 模拟分页响应
            page1_response = {
                "results": [
                    {"id": "task1", "properties": self._mock_task_properties("Task 1"), 
                     "created_time": "2024-01-01T00:00:00Z", "last_edited_time": "2024-01-01T00:00:00Z"},
                    {"id": "task2", "properties": self._mock_task_properties("Task 2"),
                     "created_time": "2024-01-01T00:00:00Z", "last_edited_time": "2024-01-01T00:00:00Z"},
                ],
                "has_more": True,
                "next_cursor": "cursor_123"
            }
            page2_response = {
                "results": [
                    {"id": "task3", "properties": self._mock_task_properties("Task 3"),
                     "created_time": "2024-01-01T00:00:00Z", "last_edited_time": "2024-01-01T00:00:00Z"},
                ],
                "has_more": False,
                "next_cursor": None
            }
            
            mock_client.data_sources.query.side_effect = [page1_response, page2_response]
            
            repo = NotionRepository(
                token="test_token",
                database_id="test_db_id",
                cached_data_source_id="cached-id"
            )
            
            tasks = repo.list_all()
            
            # 验证：应该获取了所有页的任务
            assert len(tasks) == 3
            assert tasks[0].title == "Task 1"
            assert tasks[1].title == "Task 2"
            assert tasks[2].title == "Task 3"
            
            # 验证：调用了两次 query（两页）
            assert mock_client.data_sources.query.call_count == 2
            
            # 验证第二次调用包含了 cursor
            second_call_kwargs = mock_client.data_sources.query.call_args_list[1][1]
            assert second_call_kwargs["start_cursor"] == "cursor_123"
    
    @staticmethod
    def _mock_task_properties(title: str):
        """创建模拟的任务属性"""
        return {
            "Name": {"title": [{"text": {"content": title}}]},
            "Description": {"rich_text": []},
            "Status": {"select": {"name": "To Do"}},
            "Priority": {"select": {"name": "Medium"}},
            "Time Spent": {"number": 0},
            "Due Date": {"date": None},
            "Tags": {"multi_select": []},
            "Project": {"select": None},
        }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
