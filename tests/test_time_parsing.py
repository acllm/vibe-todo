"""测试时间输入解析功能"""
import pytest
from vibe_todo.cli.main import parse_time_input


class TestTimeInputParsing:
    """测试各种时间输入格式"""
    
    def test_parse_minutes_number(self):
        """测试纯数字分钟输入"""
        assert parse_time_input("90") == 90
        assert parse_time_input("120") == 120
        assert parse_time_input("15") == 15
        assert parse_time_input("1") == 1
    
    def test_parse_hours_decimal(self):
        """测试小数小时输入"""
        assert parse_time_input("1.5h") == 90
        assert parse_time_input("2h") == 120
        assert parse_time_input("2.0h") == 120
        assert parse_time_input("0.5h") == 30
        assert parse_time_input("0.25h") == 15
    
    def test_parse_hours_with_space(self):
        """测试带空格的小时输入"""
        assert parse_time_input("1.5 h") == 90
        assert parse_time_input("2 h") == 120
    
    def test_parse_combined_format(self):
        """测试组合格式（小时+分钟）"""
        assert parse_time_input("2h30m") == 150
        assert parse_time_input("1h15m") == 75
        assert parse_time_input("3h45m") == 225
        assert parse_time_input("0h30m") == 30
    
    def test_parse_combined_with_space(self):
        """测试带空格的组合格式"""
        assert parse_time_input("2h 30m") == 150
        assert parse_time_input("1h 15m") == 75
        assert parse_time_input("2 h 30 m") == 150
    
    def test_parse_minutes_with_unit(self):
        """测试带单位的分钟输入"""
        assert parse_time_input("45m") == 45
        assert parse_time_input("30m") == 30
        assert parse_time_input("15 m") == 15
    
    def test_case_insensitive(self):
        """测试大小写不敏感"""
        assert parse_time_input("1.5H") == 90
        assert parse_time_input("2H30M") == 150
        assert parse_time_input("45M") == 45
    
    def test_invalid_formats(self):
        """测试无效格式"""
        assert parse_time_input("abc") is None
        assert parse_time_input("1.5") is None  # 缺少单位
        assert parse_time_input("h30m") is None  # 缺少小时数
        assert parse_time_input("2h30") is None  # 分钟缺少单位
        assert parse_time_input("") is None
        assert parse_time_input("  ") is None
    
    def test_edge_cases(self):
        """测试边界情况"""
        assert parse_time_input("0") == 0
        assert parse_time_input("0h") == 0
        assert parse_time_input("0m") == 0
        assert parse_time_input("0h0m") == 0
        
    def test_real_world_examples(self):
        """测试真实使用场景"""
        # 番茄钟
        assert parse_time_input("25m") == 25
        
        # 半小时会议
        assert parse_time_input("0.5h") == 30
        
        # 一天工作时间
        assert parse_time_input("8h") == 480
        
        # 半天工作
        assert parse_time_input("4h") == 240
        
        # 精确记录：2小时45分钟
        assert parse_time_input("2h45m") == 165
