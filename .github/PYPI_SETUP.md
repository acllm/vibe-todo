# GitHub Actions + PyPI 可信发布配置指南

本文档说明如何配置 GitHub Actions 自动发布到 PyPI。

## 📋 配置步骤

### 1. 配置 PyPI 可信发布（Trusted Publishing）

这是**最重要**的一步，必须先完成才能自动发布。

#### 1.1 访问 PyPI

登录 https://pypi.org/ 并访问：
https://pypi.org/manage/account/publishing/

#### 1.2 添加新的 Trusted Publisher

点击 "Add a new pending publisher" 并填写：

```
PyPI Project Name:     vibe-todo
Owner:                 acllm              # 你的 GitHub 用户名或组织名
Repository name:       vibe-todo
Workflow name:         publish.yml
Environment name:      pypi
```

> **注意**：如果项目首次发布，选择 "Add a new pending publisher"。  
> 如果项目已存在，选择 "Add a new publisher"。

#### 1.3 确认配置

点击 "Add" 完成配置。PyPI 会记住这个配置，后续发布时会自动验证。

### 2. 验证 GitHub Actions 配置

确认 `.github/workflows/publish.yml` 文件已创建并包含正确的配置。

关键配置项：

```yaml
permissions:
  id-token: write  # 必需：用于 OIDC 认证

environment:
  name: pypi       # 必须与 PyPI 配置匹配
```

### 3. 测试发布流程

#### 3.1 本地测试

```bash
# 确保所有测试通过
pytest tests/ -v

# 构建测试
python -m build
twine check dist/*
```

#### 3.2 推送标签触发发布

```bash
# 更新版本号（如 0.1.3）
vim pyproject.toml

# 提交并打标签
git add pyproject.toml
git commit -m "chore: bump version to 0.1.3"
git tag -a v0.1.3 -m "Release v0.1.3"

# 推送（会触发 GitHub Actions）
git push origin main --tags
```

#### 3.3 监控工作流

访问 https://github.com/acllm/vibe-todo/actions 查看：

- ✅ Test 任务（运行测试）
- ✅ Build 任务（构建包）
- ✅ Publish to PyPI 任务（发布）
- ✅ Create GitHub Release 任务（创建 Release）

### 4. 验证发布成功

```bash
# 等待 1-2 分钟让 PyPI 索引更新
pip install --upgrade vibe-todo

# 检查版本
pip show vibe-todo

# 测试命令
vibe --version
```

---

## 🔍 工作流详解

### 触发条件

```yaml
on:
  push:
    tags:
      - 'v*.*.*'  # 仅在推送 v 开头的语义化版本标签时触发
```

示例：
- ✅ `v0.1.2` - 触发
- ✅ `v1.0.0` - 触发
- ❌ `0.1.2` - 不触发（缺少 v 前缀）
- ❌ `release-0.1.2` - 不触发（格式不匹配）

### 任务流程

```
┌─────────┐
│  Test   │  运行所有测试，确保代码质量
└────┬────┘
     │
     ▼
┌─────────┐
│  Build  │  构建 wheel 和 tar.gz
└────┬────┘
     │
     ▼
┌─────────────────┐
│ Publish to PyPI │  使用 OIDC 发布到 PyPI
└────┬────────────┘
     │
     ▼
┌──────────────────────┐
│ Create GitHub Release│  创建 Release 并附加构建文件
└──────────────────────┘
```

### 可信发布的安全性

**传统方式（API Token）**：
```yaml
env:
  TWINE_USERNAME: __token__
  TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
```
❌ 需要手动管理 token  
❌ token 可能泄露  
❌ 需要定期轮换  

**可信发布（OIDC）**：
```yaml
permissions:
  id-token: write
```
✅ 无需管理 token  
✅ 自动轮换凭证  
✅ GitHub 和 PyPI 双重验证  
✅ 更细粒度的权限控制  

---

## 🚨 常见问题

### Q1: PyPI 发布失败，提示 "Invalid or non-existent authentication information"

**原因**：PyPI 可信发布配置不正确。

**解决**：
1. 检查 PyPI 配置中的仓库名、工作流名称是否完全匹配
2. 确认 `environment: pypi` 配置正确
3. 等待几分钟让 PyPI 配置生效

### Q2: 首次发布失败，提示 "Project does not exist"

**原因**：项目首次发布需要使用 "pending publisher"。

**解决**：
在 PyPI 配置时选择 "Add a new pending publisher" 而不是 "Add a new publisher"。

### Q3: 测试通过但构建失败

**原因**：依赖问题或 `pyproject.toml` 配置错误。

**解决**：
```bash
# 本地测试构建
python -m build
twine check dist/*
```

### Q4: GitHub Actions 显示 "permission denied"

**原因**：缺少必要的权限配置。

**解决**：
确认工作流包含：
```yaml
permissions:
  id-token: write      # PyPI 发布
  contents: write      # 创建 Release
```

### Q5: 标签推送了但没有触发工作流

**原因**：
1. 标签格式不匹配（必须是 `v*.*.*`）
2. GitHub Actions 未启用

**解决**：
```bash
# 检查标签格式
git tag -l

# 重新打标签
git tag -d v0.1.3
git tag -a v0.1.3 -m "Release v0.1.3"
git push origin v0.1.3 --force
```

---

## 📚 相关资源

- **PyPI 可信发布文档**: https://docs.pypi.org/trusted-publishers/
- **GitHub OIDC 文档**: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect
- **PyPI 官方 Action**: https://github.com/pypa/gh-action-pypi-publish
- **语义化版本规范**: https://semver.org/

---

## ✅ 配置完成检查清单

- [ ] PyPI 账号已创建
- [ ] PyPI 可信发布已配置（Owner/Repo/Workflow/Environment 正确）
- [ ] `.github/workflows/publish.yml` 已创建
- [ ] GitHub Actions 已启用
- [ ] 本地测试通过（`pytest tests/ -v`）
- [ ] 本地构建成功（`python -m build`）
- [ ] 首次推送标签测试（推荐先用 `v0.0.1-test`）

配置正确后，每次推送版本标签都会自动发布到 PyPI！🎉
