# Vibe Todo 使用示例

## 基础用法

### 添加和管理任务

```bash
# 添加简单任务
vibe add "学习 Python"

# 添加完整信息的任务
vibe add "学习 Python 高级特性" \
  -d "装饰器、生成器、上下文管理器" \
  -p high \
  --due 2025-12-01 \
  -t "学习,Python" \
  --project "技术提升"

# 查看所有任务
vibe list

# 查看特定状态的任务
vibe list -s todo
vibe list -s in_progress
vibe list -s done

# 查看逾期任务
vibe list --overdue

# 查看任务详情
vibe show <task-id>

# 开始任务
vibe start <task-id>

# 完成任务
vibe done <task-id>

# 删除任务
vibe delete <task-id>
```

### 工时管理（灵活输入）

#### CLI 多格式支持

Vibe Todo 支持多种直观的时间输入格式，内部统一存储为分钟（保证精度）：

```bash
# 方式 1: 直接输入分钟数
vibe time <task-id> 90          # 添加 90 分钟

# 方式 2: 使用小时（小数）
vibe time <task-id> 1.5h        # 添加 1.5 小时 = 90 分钟
vibe time <task-id> 2h          # 添加 2 小时 = 120 分钟
vibe time <task-id> 0.25h       # 添加 15 分钟

# 方式 3: 组合格式（小时+分钟）
vibe time <task-id> 2h30m       # 添加 2 小时 30 分钟 = 150 分钟
vibe time <task-id> 1h15m       # 添加 1 小时 15 分钟 = 75 分钟

# 方式 4: 仅分钟（带单位）
vibe time <task-id> 45m         # 添加 45 分钟
vibe time <task-id> 30m         # 添加 30 分钟

# 查看统计（含总工时）
vibe stats
```

**特性**：
- 🔤 大小写不敏感：`1.5H` 和 `1.5h` 等价
- 🔄 空格容忍：`2h 30m` 和 `2h30m` 都支持
- ⚠️ 友好错误提示：无效格式会显示支持的示例

#### WebUI 快捷操作

在 Web 界面中，每个任务提供快捷工时按钮：

```
[+15min] [+30min] [+1h] [+2h]  [自定义: ___ 分钟] [添加]
```

- ⚡ **一键添加**：常用时间段无需输入
- 🎯 **精确控制**：自定义输入框支持任意分钟数
- 📱 **移动友好**：大按钮易于点击

#### 使用场景

**场景 1: 番茄钟工作法**
```bash
vibe time <id> 25m      # 一个番茄钟
vibe time <id> 5m       # 短暂休息
```

**场景 2: 标准工作时间**
```bash
vibe time <id> 4h       # 半天工作
vibe time <id> 8h       # 一天工作
```

**场景 3: 精确计费**
```bash
vibe time <id> 1h45m    # 客户咨询：1小时45分钟
vibe time <id> 0.5h     # 会议：半小时
```

#### 设计原则

**数据完整性优先**：
- 内部存储：分钟（精度 1 分钟）
- 外部显示：格式化为 `Xh Ym`
- 支持碎片化任务（15分钟、30分钟）和长周期任务（数小时）

**用户体验优化**：
- 多种输入格式满足不同习惯
- CLI 灵活输入 + WebUI 快捷按钮
- 无需数据迁移，向后兼容

### 实际工作流示例

```bash
# 早上开始工作
vibe add "实现用户登录功能" -p high --project "Web 项目"
vibe start 1

# 工作 2 小时后记录
vibe time 1 2h

# 午休后继续，再工作 1.5 小时
vibe time 1 1.5h

# 完成任务
vibe done 1

# 查看今日工作统计
vibe stats
```

---

## 多后端使用场景

## 场景 1: 本地开发，使用 SQLite

```bash
# 默认配置，无需额外设置
vibe add "学习 Python" -p high
vibe list
```

## 场景 2: 个人知识管理，同步到 Notion

### 步骤 1: 准备 Notion 数据库

在 Notion 中创建一个数据库模板：

| Name | Status | Priority | Due Date | Tags | Time Spent |
|------|--------|----------|----------|------|------------|
| Title | Select | Select | Date | Multi-select | Number |

### 步骤 2: 获取凭证

```bash
# Integration Token: secret_xxx
# Database ID: xxx (从 URL 中获取)
```

### 步骤 3: 配置并使用

```bash
# 配置 Notion 后端
vibe config set-backend notion \
  --token secret_xxx \
  --database xxx

# 添加任务（会自动同步到 Notion）
vibe add "阅读《深入理解计算机系统》" \
  -d "CSAPP 第3章" \
  -p high \
  --due 2025-12-25 \
  -t "学习,计算机" \
  --project "技术阅读"

# 查看任务（从 Notion 读取）
vibe list

# 在 Notion 中修改任务后，CLI 也能看到更新
vibe show 1
```

### 优势
- ✅ 在 Notion 中可视化管理任务
- ✅ 利用 Notion 的笔记和关联功能
- ✅ 可以在手机上使用 Notion App 查看

## 场景 3: 团队协作，使用 Microsoft To Do

### 步骤 1: 注册 Azure 应用

1. 访问 https://portal.azure.com
2. 创建应用，获取 Client ID
3. 配置权限：Tasks.ReadWrite

### 步骤 2: 配置并认证

```bash
# 配置 Microsoft 后端
vibe config set-backend microsoft --client-id xxx

# 首次使用会弹出浏览器进行认证
vibe list

# 添加任务（同步到 Microsoft To Do）
vibe add "准备季度总结" \
  -p urgent \
  --due 2025-11-30 \
  -t "工作,汇报"

# 在 Microsoft To Do App 中也能看到
```

### 优势
- ✅ 与 Outlook、Teams 集成
- ✅ 跨平台同步（Windows、iOS、Android、Web）
- ✅ 企业环境友好

## 场景 4: 混合使用

```bash
# 开发任务用 SQLite（快速、离线）
vibe config set-backend sqlite
vibe add "修复 Bug #123" -p high

# 个人学习计划用 Notion（笔记丰富）
vibe config set-backend notion --token xxx --database xxx
vibe add "学习 Rust" --project "技术学习"

# 工作任务用 Microsoft（团队协作）
vibe config set-backend microsoft --client-id xxx
vibe add "项目评审" -p urgent
```

## 数据迁移

### 从 SQLite 导出到 Notion

```bash
# TODO: 实现数据迁移工具
vibe migrate --from sqlite --to notion \
  --token xxx --database xxx
```

## 注意事项

### Notion
- ⚠️ API 限制：每秒 3 次请求
- ⚠️ Database 需要预先创建好属性
- ⚠️ Token 需要妥善保管

### Microsoft To Do  
- ⚠️ 首次使用需要浏览器认证
- ⚠️ Token 有效期约 1 小时，自动刷新
- ⚠️ 不支持工时字段（这是 Microsoft To Do 的限制）

### 通用
- ⚠️ 网络问题会导致操作失败
- ⚠️ 建议定期备份重要数据
- ⚠️ 不同后端的 task_id 格式不同，切换后端会丢失 ID 映射
