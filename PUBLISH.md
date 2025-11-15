# 发布指南

## 准备工作

### 1. 安装发布工具

```bash
uv pip install build twine
```

### 2. 配置 PyPI 账号

如果还没有 PyPI 账号，先注册：https://pypi.org/account/register/

然后创建 API token：https://pypi.org/manage/account/token/

## 发布到 PyPI

### 1. 清理旧的构建文件

```bash
rm -rf dist/ build/ *.egg-info
```

### 2. 构建包

```bash
python -m build
```

这会在 `dist/` 目录下生成两个文件：
- `vibe_todo-0.1.0-py3-none-any.whl` (wheel 格式)
- `vibe_todo-0.1.0.tar.gz` (源码包)

### 3. 检查包

```bash
twine check dist/*
```

### 4. 上传到 TestPyPI（可选，用于测试）

```bash
twine upload --repository testpypi dist/*
```

然后测试安装：
```bash
pip install --index-url https://test.pypi.org/simple/ vibe-todo
```

### 5. 上传到 PyPI

```bash
twine upload dist/*
```

输入你的 PyPI 用户名和 API token。

### 6. 验证发布

```bash
# 等待几分钟让 PyPI 索引更新
pip install vibe-todo
vibe --version
```

## 发布到 GitHub

### 1. 初始化 Git 仓库（如果还没有）

```bash
git init
git add .
git commit -m "Initial commit"
```

### 2. 创建 GitHub 仓库

访问 https://github.com/new 创建新仓库。

### 3. 推送代码

```bash
git remote add origin https://github.com/acllm/vibe-todo.git
git branch -M main
git push -u origin main
```

### 4. 创建 Release

1. 访问 https://github.com/acllm/vibe-todo/releases/new
2. 创建新的 tag：`v0.1.0`
3. 填写 Release 标题和说明
4. 上传构建好的 wheel 和 tar.gz 文件
5. 发布

## 版本更新流程

### 1. 更新版本号

编辑 `pyproject.toml`，修改 `version = "0.1.1"`

### 2. 更新 CHANGELOG

记录变更内容。

### 3. 提交并打 tag

```bash
git add .
git commit -m "Bump version to 0.1.1"
git tag v0.1.1
git push origin main --tags
```

### 4. 重新构建和发布

```bash
rm -rf dist/
python -m build
twine upload dist/*
```

## 自动化发布（GitHub Actions）

可以创建 `.github/workflows/publish.yml` 来自动化发布流程：

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install build twine
      - name: Build package
        run: python -m build
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

记得在 GitHub 仓库设置中添加 `PYPI_API_TOKEN` secret。

## 注意事项

1. **版本号规范**：遵循语义化版本（Semantic Versioning）
   - 主版本号：不兼容的 API 修改
   - 次版本号：向下兼容的功能性新增
   - 修订号：向下兼容的问题修正

2. **发布前检查**：
   - 确保所有测试通过
   - 更新文档
   - 检查依赖版本
   - 验证 README 中的示例

3. **PyPI 名称**：
   - 包名 `vibe-todo` 在 PyPI 上必须唯一
   - 如果已被占用，需要选择其他名称

4. **安全**：
   - 不要将 API token 提交到代码库
   - 使用环境变量或 secrets 管理敏感信息
