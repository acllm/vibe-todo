# 发布指南

## 🚀 自动化发布（推荐）

使用 GitHub Actions 自动化发布到 PyPI。

### 前提条件

1. **配置 PyPI 可信发布（Trusted Publishing）**

   访问 https://pypi.org/manage/account/publishing/ 配置：
   
   - **PyPI Project Name**: `vibe-todo`
   - **Owner**: `acllm`（你的 GitHub 用户名/组织）
   - **Repository**: `vibe-todo`
   - **Workflow**: `publish.yml`
   - **Environment**: `pypi`

   > 优势：无需管理 API Token，更安全

2. **启用 GitHub Actions**

   确保仓库设置中启用了 Actions（默认启用）。

### 发布流程

只需三步即可自动发布到 PyPI：

```bash
# 1. 更新版本号
# 编辑 pyproject.toml，修改 version = "0.1.3"

# 2. 提交并打标签
git add pyproject.toml
git commit -m "chore: bump version to 0.1.3"
git tag -a v0.1.3 -m "Release v0.1.3

✨ 新功能
- 功能描述

🔧 改进
- 改进描述

🐛 修复
- 修复描述"

# 3. 推送标签触发自动发布
git push origin main --tags
```

### 自动化流程说明

当你推送以 `v*.*.*` 格式的标签时，GitHub Actions 会自动：

1. ✅ **运行测试**：确保所有测试通过
2. ✅ **构建包**：生成 wheel 和 tar.gz
3. ✅ **检查包**：使用 twine 验证包的完整性
4. ✅ **发布到 PyPI**：使用可信发布上传包
5. ✅ **创建 GitHub Release**：自动生成 Release 并附加构建文件

### 监控发布状态

访问 https://github.com/acllm/vibe-todo/actions 查看工作流执行状态。

### 验证发布

```bash
# 等待几分钟让 PyPI 索引更新
pip install --upgrade vibe-todo

# 验证版本
vibe --version
```

---

## 🔧 手动发布（备用方案）

如果需要手动发布或本地测试：

### 1. 安装发布工具

```bash
pip install build twine
```

### 2. 配置 PyPI 账号

创建 API token：https://pypi.org/manage/account/token/

### 3. 构建和发布

### 3. 构建和发布

```bash
# 清理旧的构建文件
rm -rf dist/ build/ *.egg-info

# 构建包
python -m build

# 检查包
twine check dist/*

# 上传到 PyPI
twine upload dist/*
```

---

## 📋 版本更新检查清单

发布前确保：

- [ ] 所有测试通过（`pytest tests/ -v`）
- [ ] 更新 `pyproject.toml` 中的版本号
- [ ] 代码已提交到 Git
- [ ] 创建并推送版本标签
- [ ] （自动）GitHub Actions 成功运行
- [ ] （自动）PyPI 包已发布
- [ ] （自动）GitHub Release 已创建
- [ ] 验证新版本可以正常安装

## 🔐 安全最佳实践

### 使用可信发布（推荐）

✅ **优势**：
- 无需管理 API Token
- 自动轮换凭证
- 更安全的权限模型
- GitHub 和 PyPI 原生支持

### 使用 API Token（备用）

如果使用传统的 API Token 方式：

1. 创建范围受限的 token（只针对 `vibe-todo` 项目）
2. 将 token 添加到 GitHub Secrets（`PYPI_API_TOKEN`）
3. 永远不要将 token 提交到代码库
4. 定期轮换 token

## 📊 版本号规范

遵循 [语义化版本](https://semver.org/lang/zh-CN/)：

- **主版本号（Major）**: 不兼容的 API 修改
  - 示例：`v1.0.0` → `v2.0.0`
- **次版本号（Minor）**: 向下兼容的功能性新增
  - 示例：`v0.1.0` → `v0.2.0`
- **修订号（Patch）**: 向下兼容的问题修正
  - 示例：`v0.1.0` → `v0.1.1`

## 🚨 回滚发布

如果发布后发现严重问题：

### 1. PyPI 端（不支持删除）

PyPI 不允许删除已发布的版本，但可以：

```bash
# 发布修复版本
# 将版本号递增（如 0.1.3 → 0.1.4）
```

### 2. GitHub 端

```bash
# 删除远程标签
git push --delete origin v0.1.3

# 删除本地标签
git tag -d v0.1.3

# 在 GitHub 上删除对应的 Release
# 访问 https://github.com/acllm/vibe-todo/releases
```

### 3. 建议用户降级

在 README 或 Release Notes 中通知：

```bash
# 临时回退到上一个稳定版本
pip install vibe-todo==0.1.2
```

## 🔍 故障排查

### GitHub Actions 失败

**测试失败**：
```bash
# 本地运行测试
pytest tests/ -v

# 检查依赖
pip list
```

**构建失败**：
```bash
# 本地构建测试
python -m build
twine check dist/*
```

**PyPI 发布失败**：
- 检查 PyPI 可信发布配置
- 确认包名未被占用
- 检查版本号是否已存在

### 手动触发工作流

如果自动触发失败，可以手动重新运行：

1. 访问 https://github.com/acllm/vibe-todo/actions
2. 选择失败的工作流
3. 点击 "Re-run jobs"

## 📞 获取帮助

- **PyPI 可信发布文档**: https://docs.pypi.org/trusted-publishers/
- **GitHub Actions 文档**: https://docs.github.com/en/actions
- **项目 Issues**: https://github.com/acllm/vibe-todo/issues
