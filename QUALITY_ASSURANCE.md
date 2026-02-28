# 质量保障方案 - Quality Assurance Plan

> "功能演进快不快无所谓，但是功能的完善度跟准确度必须要保障好"
> — Chao (Nova's creator)

## 🎯 核心原则

1. **质量第一** - 不急于添加新功能，确保现有功能稳定可靠
2. **测试防护** - 任何改动都要有对应的测试覆盖
3. **可追溯** - 每个功能都有清晰的测试和验证路径
4. **渐进式演进** - 小步快跑，每次改动都可验证

---

## 🧪 测试策略

### 测试金字塔

```
        ┌─────────────────────┐
        │   E2E Tests (Web)   │  计划中
        └──────────┬──────────┘
        ┌──────────▼──────────┐
        │ Integration Tests   │  ✅ 现有 + 新增 AI 测试
        └──────────┬──────────┘
    ┌──────────────▼──────────────┐
    │      Unit Tests (Core)      │  ✅ 100% 覆盖核心逻辑
    └─────────────────────────────┘
```

### 测试分类

#### 1. 单元测试 (Unit Tests)

**目标**: 覆盖所有核心逻辑，独立可重复

**范围**:
- `src/vibe_todo/core/` - 100% 覆盖
- `src/vibe_todo/io/` - 100% 覆盖
- `src/vibe_todo/storage/` - 90%+ 覆盖

**标准**:
- 每个公共方法至少一个测试
- 边界条件必须测试
- 错误路径必须测试

#### 2. 集成测试 (Integration Tests)

**目标**: 验证各模块间的协作

**范围**:
- CLI 命令集成测试
- 多后端适配器集成
- 导入/导出集成
- AI 功能集成（新增）

#### 3. E2E 测试 (End-to-End)

**目标**: 模拟真实用户场景

**范围**:
- Web 界面完整流程
- CLI 完整工作流
- 跨后端数据迁移

**状态**: 计划中 (v0.3.1+)

---

## 🤖 AI 功能测试方案

### 测试文件结构

```
tests/
├── test_ai_helper.py          # AI Helper 单元测试 (新增)
├── test_ai_cli.py             # AI CLI 集成测试 (新增)
├── test_core.py               # 现有核心测试
├── test_batch.py              # 现有批量操作测试
├── test_io.py                 # 现有 IO 测试
├── test_storage.py            # 现有存储测试
├── test_notion_adapter.py     # 现有 Notion 测试
└── test_time_parsing.py       # 现有时间解析测试
```

### AI Helper 测试用例

#### test_ai_helper.py 大纲

```python
class TestAIHelper:
    """测试 AI Helper 核心功能"""

    def test_analyze_task_basic(self):
        """测试基础任务分析"""

    def test_analyze_task_with_patterns(self):
        """测试模式匹配（会议/报告/代码等）"""

    def test_analyze_task_urgency(self):
        """测试紧急程度计算"""

    def test_suggest_next_task_simple(self):
        """测试简单场景的下一个任务推荐"""

    def test_suggest_next_task_with_dependencies(self):
        """测试依赖关系的任务推荐"""

    def test_suggest_next_task_priority_order(self):
        """测试优先级排序逻辑"""

    def test_generate_suggestions_time_of_day(self):
        """测试时间段感知的建议"""

    def test_generate_suggestions_project_momentum(self):
        """测试项目 momentum 保持"""

    def test_productivity_score_calculation(self):
        """测试生产力分数计算"""

    def test_productivity_score_trends(self):
        """测试趋势分析"""
```

### AI CLI 测试用例

#### test_ai_cli.py 大纲

```python
class TestAICLI:
    """测试 AI CLI 命令集成"""

    def test_cli_ai_analyze(self):
        """测试 ai analyze 命令"""

    def test_cli_ai_next(self):
        """测试 ai next 命令"""

    def test_cli_ai_suggest(self):
        """测试 ai suggest 命令"""

    def test_cli_ai_score(self):
        """测试 ai score 命令"""

    def test_cli_ai_score_with_days(self):
        """测试 ai score --days 参数"""
```

---

## ✅ 质量检查清单

### 每次提交前检查 (Pre-commit Checklist)

- [ ] 运行所有现有测试通过 (`pytest`)
- [ ] 运行代码检查 (`ruff check`)
- [ ] 新功能有对应的单元测试
- [ ] 新功能有对应的集成测试（如适用）
- [ ] 文档已更新（README / 相关文档）
- [ ] 手动验证核心功能正常

### 发布前检查 (Release Checklist)

- [ ] 完整测试套件通过
- [ ] 覆盖度报告达标（核心 >90%）
- [ ] 性能基准测试通过
- [ ] 文档完整且最新
- [ ] CHANGELOG 更新
- [ ] 升级路径测试（如适用）

---

## 📊 代码质量工具

### 已配置工具

1. **pytest** - 测试框架
2. **pytest-cov** - 覆盖率报告
3. **ruff** - 代码检查和格式化

### 常用命令

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=src/vibe_todo --cov-report=html

# 代码检查
ruff check .

# 代码格式化
ruff format .

# 快速检查（测试 + 代码检查）
pytest && ruff check .
```

---

## 🔄 开发工作流

### 标准工作流

1. **创建分支** - 从 `main` 创建功能分支
2. **编写测试** - 先写测试（TDD 风格）
3. **实现功能** - 让测试通过
4. **代码检查** - 运行 `ruff check`
5. **提交代码** - 清晰的 commit message
6. **验证功能** - 手动测试核心场景
7. **创建 PR** - 或直接合并（个人项目）

### 分支策略

```
main (稳定分支)
  │
  └── feature/xxx (功能分支)
  │
  └── fix/xxx (修复分支)
  │
  └── test/xxx (测试增强分支)
```

---

## 📈 质量指标

### 目标指标

| 指标 | 目标 | 说明 |
|------|------|------|
| 核心单元测试覆盖 | >90% | core/ 模块 |
| 集成测试覆盖 | >80% | 主要功能路径 |
| 测试通过率 | 100% | 所有提交必须通过 |
| 代码检查问题 | 0 | 无 error，warn 需评估 |
| 文档完整度 | 100% | 新功能必须有文档 |

### 质量门禁

任何合并到 main 的代码必须满足：

1. ✅ 所有测试通过
2. ✅ 核心模块覆盖率 >90%
3. ✅ 代码检查无 error
4. ✅ 关键功能手动验证通过

---

## 🛡️ 回归测试策略

### 回归测试套件

每次改动后运行：
- 现有所有单元测试
- 关键路径集成测试
- 性能基准测试（如适用）

### 重点回归区域

- 任务 CRUD 操作
- 多后端适配
- 导入/导出功能
- AI 推荐逻辑
- CLI 命令解析

---

## 📝 文档要求

### 代码文档

- 公共 API 必须有 docstring
- 复杂算法必须有注释说明思路
- 测试用例必须描述测试场景

### 用户文档

- 新功能必须更新 README
- 复杂功能必须有使用示例
- 重大变更必须有迁移指南

---

## 🎯 近期行动计划 (v0.3.1)

### 1. 添加 AI 功能测试 (优先级: 🔴 高)
- [ ] 创建 `test_ai_helper.py`
- [ ] 覆盖 AI Helper 所有公共方法
- [ ] 创建 `test_ai_cli.py`
- [ ] 覆盖 AI CLI 所有命令

### 2. 增强现有测试 (优先级: 🟡 中)
- [ ] 新增任务依赖关系测试
- [ ] 新增 AI 字段序列化测试
- [ ] 覆盖边界条件和错误路径

### 3. 完善质量工具 (优先级: 🟡 中)
- [ ] 配置 pre-commit hooks
- [ ] 添加 coverage badge
- [ ] 配置 CI（如果需要）

### 4. 文档完善 (优先级: 🟢 低)
- [ ] 更新 API 文档
- [ ] 添加测试运行指南
- [ ] 添加贡献指南

---

## 💡 质量文化

> "If it's not tested, it doesn't exist."

- 不提交没有测试的代码
- 不合并破坏测试的代码
- 测试是功能的一部分，不是额外工作
- 质量是每个人的责任

---

## 📊 持续改进

每月回顾：
- 测试覆盖率趋势
- Bug 数量和类型
- 测试反馈周期
- 质量指标达成情况

持续优化：
- 优化测试执行速度
- 完善测试数据准备
- 增强测试工具链

---

**最后更新**: 2026-02-28  
**负责人**: Nova 🌟  
**版本**: v1.0
