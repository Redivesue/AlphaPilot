# 将 AlphaPilot 上传到 GitHub 指南

## 一、前置准备

1. **安装 Git**（如未安装）
   ```bash
   # macOS
   brew install git
   ```

2. **注册 GitHub 账号**：https://github.com

3. **配置 Git 用户信息**（首次使用）
   ```bash
   git config --global user.name "你的用户名"
   git config --global user.email "你的邮箱"
   ```

## 二、创建 GitHub 仓库

1. 登录 GitHub，点击右上角 **+** → **New repository**
2. 填写：
   - **Repository name**：`AlphaPilot` 或 `alphapilot-quant-research`
   - **Description**：`LLM-Agent 驱动的自动化量化因子研究平台`
   - 选择 **Public**
   - **不要**勾选 "Add a README file"（本地已有）
3. 点击 **Create repository**

## 三、本地初始化并推送

在项目根目录 `AlphaPilot-v1.1` 下执行：

```bash
# 1. 初始化 Git（若尚未初始化）
git init

# 2. 添加 .gitignore（若不存在，见下方内容）
# 确保 .gitignore 已包含敏感文件和缓存

# 3. 添加所有文件
git add .

# 4. 首次提交
git commit -m "Initial commit: AlphaPilot - LLM-Agent driven quant factor research platform"

# 5. 添加远程仓库（将 YOUR_USERNAME 和 REPO_NAME 替换为你的）
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# 6. 推送到 main 分支
git branch -M main
git push -u origin main
```

## 四、.gitignore 建议

确保项目根目录有 `.gitignore`，至少包含：

```
# Python
__pycache__/
*.py[cod]
*.pyo
.env
.venv/
venv/
*.egg-info/
dist/
build/

# Data & cache
data_cache/
*.pkl
factor_db/chroma/
factor_db/*.db

# Output
output/
*.csv

# Node
frontend/node_modules/
frontend/dist/

# IDE
.idea/
.vscode/
*.swp
.DS_Store
```

## 五、敏感信息

- **切勿**将 `.env` 提交到 GitHub（内含 API Key）
- 提供 `.env.example` 模板供他人参考：
  ```
  OPENAI_API_KEY=your-key-here
  OPENAI_API_BASE=https://api.deepseek.com/v1
  ```

## 六、README 展示效果

- 英文 README：`README.md`
- 中文 README：`README_CN.md`
- 截图已放在 `docs/screenshots/`，README 中已引用，推送后会在 GitHub 项目首页直接展示

## 七、后续更新

```bash
git add .
git commit -m "描述本次修改"
git push
```
