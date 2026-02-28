# 发布流程 - Release Process

> "稳定可落地才行"
> — Chao

## 🎯 发布原则

1. **质量第一** - 不发布未经验证的代码
2. **可追溯** - 每个版本都有清晰的变更记录
3. **可回滚** - 发布问题可以快速回滚
4. **小步快跑** - 频繁发布，每次改动小而可控

---

## 📋 完整发布流程

### 阶段 1: 开发完成 (Development Complete)

- [ ] 功能开发完成
- [ ] 所有测试通过（单元测试 + 集成测试）
- [ ] 代码检查通过（ruff check）
- [ ] 文档已更新（README / CHANGELOG）
- [ ] 手动验证核心功能

### 阶段 2: 发布准备 (Release Preparation)

- [ ] 从 feature 分支创建 release 分支
- [ ] 更新版本号（pyproject.toml / CLI）
- [ ] 更新 CHANGELOG.md
- [ ] 运行完整测试套件
- [ ] 生成覆盖率报告
- [ ] 最终代码检查

### 阶段 3: 质量门禁 (Quality Gate)

**必须 100% 通过才能继续：**

- [ ] 所有单元测试通过 ✅
- [ ] 核心模块覆盖率 >90% ✅
- [ ] 集成测试通过 ✅
- [ ] 代码检查无 error ✅
- [ ] 关键功能手动验证 ✅

### 阶段 4: 发布执行 (Release Execution)

- [ ] 合并 release 分支到 main
- [ ] 创建 Git tag (`vX.Y.Z`)
- [ ] 推送到远程仓库
- [ ] （可选）PyPI 发布
- [ ] 发布公告

### 阶段 5: 发布后 (Post-release)

- [ ] 监控发布后的状态
- [ ] 收集用户反馈
- [ ] 记录发布总结
- [ ] 规划下一个版本

---

## 🔖 版本号规范

遵循语义化版本 (Semantic Versioning):

```
vMAJOR.MINOR.PATCH
  │     │     │
  │     │     └─ Bug fixes, small improvements
  │     └─────── New features, backwards compatible
  └───────────── Breaking changes
```

**示例**:
- `v0.3.0` - 新功能（AI 辅助）
- `v0.3.1` - Bug 修复，测试完善
- `v0.4.0` - 新的大功能
- `v1.0.0` - 正式版

---

## 📝 CHANGELOG 规范

每个版本必须更新 CHANGELOG.md，格式：

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- 新功能描述

### Fixed
- 修复描述

### Changed
- 变更描述

### Deprecated
- 即将废弃的功能

### Removed
- 已移除的功能
```

**原则**:
- 每个变更都有清晰描述
- 对用户可见的变更必须记录
- 包含日期和版本号

---

## 🛠️ 发布检查清单 (Release Checklist)

### 发布前 (Pre-release)

- [ ] 代码已合并到 feature 分支
- [ ] `git status` 干净，无未提交改动
- [ ] 本地 main 分支已更新 (`git pull`)
- [ ] 创建 release 分支 (`git checkout -b release/vX.Y.Z`)
- [ ] 更新版本号
  - [ ] pyproject.toml
  - [ ] src/vibe_todo/cli/main.py (click.version_option)
- [ ] 更新 CHANGELOG.md
- [ ] 运行完整测试 `pytest`
- [ ] 运行代码检查 `ruff check .`
- [ ] 生成覆盖率报告（如需要）
- [ ] 手动验证关键功能
- [ ] 提交 release 分支 (`git commit -m "Prepare release vX.Y.Z"`)

### 发布中 (During release)

- [ ] 切换到 main 分支 (`git checkout main`)
- [ ] 合并 release 分支 (`git merge --no-ff release/vX.Y.Z`)
- [ ] 创建 Git tag (`git tag -a vX.Y.Z -m "Release vX.Y.Z"`)
- [ ] 推送到远程 (`git push && git push --tags`)
- [ ] （可选）PyPI 发布 (`python -m build && twine upload dist/*`)

### 发布后 (Post-release)

- [ ] 验证 GitHub Release 页面正常
- [ ] （可选）验证 PyPI 包可用
- [ ] 删除本地 release 分支 (`git branch -d release/vX.Y.Z`)
- [ ] 删除远程 release 分支（如适用）
- [ ] 记录发布笔记
- [ ] 庆祝！🎉

---

## 🔄 分支策略

```
main (稳定分支，随时可发布)
  │
  └── release/vX.Y.Z (发布准备分支)
  │     │
  │     └── 从 feature 分支合并，准备发布
  │
  └── feature/xxx (功能开发分支)
  │
  └── fix/xxx (Bug 修复分支)
```

**规则**:
- `main` 分支始终是稳定的
- 所有发布从 `release/vX.Y.Z` 分支合并
- 功能开发在 `feature/` 分支
- Bug 修复在 `fix/` 分支

---

## 🚨 紧急修复流程 (Hotfix)

如果发现严重问题需要紧急修复：

1. **从 main 创建 hotfix 分支**
   ```bash
   git checkout main
   git pull
   git checkout -b hotfix/xxx
   ```

2. **修复问题**
   - 写测试（先写测试！）
   - 修复问题
   - 确保所有测试通过

3. **准备发布**
   - 更新版本号（PATCH 版本 +1）
   - 更新 CHANGELOG
   - 提交 hotfix 分支

4. **发布**
   - 合并到 main
   - 创建 tag `vX.Y.Z+1`
   - 推送

---

## 📊 发布模板 (Release Template)

每次发布使用以下模板：

### Release Title
```
Release vX.Y.Z - [简短描述]
```

### Release Notes
```markdown
## 🌟 亮点

- 主要功能 1
- 主要功能 2

## 📝 变更

### Added
- 新增...

### Fixed
- 修复...

### Changed
- 变更...

## 🛡️ 质量

- ✅ 所有测试通过
- ✅ 覆盖率 >90%
- ✅ 代码检查通过

## 📦 下载

PyPI: https://pypi.org/project/vibe-todo/X.Y.Z/
GitHub: https://github.com/acllm/vibe-todo/releases/tag/vX.Y.Z
```

---

## 🎯 v0.3.0 发布计划 (当前)

### 当前状态
- ✅ 功能开发完成 (AI Helper)
- ✅ 测试覆盖完成
- ✅ 文档更新完成
- ⏳ 待验证测试通过
- ⏳ 待合并到 main

### 发布步骤
1. 验证测试通过（安装依赖，运行 pytest）
2. 创建 release/v0.3.0 分支
3. 最终检查和准备
4. 合并到 main
5. 创建 tag v0.3.0
6. 推送并发布

---

## 💡 最佳实践

1. **发布频率** - 小版本频繁发布，大版本谨慎发布
2. **发布时间** - 避开周五下午和节假日
3. **回滚计划** - 每个发布都想好如果出问题怎么回滚
4. **沟通** - 发布前告知相关人员，发布后通知
5. **学习** - 每次发布后总结经验教训

---

**最后更新**: 2026-02-28  
**版本**: v1.0  
**负责人**: Nova 🌟
