# 将 AlphaPilot 上传到 GitHub

## 一、前置准备

1. 安装 Git（若未安装）
2. 注册 GitHub 账号：https://github.com

## 二、在 GitHub 创建仓库

1. 登录 GitHub，点击右上角 + -> New repository
2. Repository name: AlphaPilot
3. Description: LLM-Agent 驱动的自动化量化因子研究平台
4. 选择 Public，不要勾选 Add a README
5. 点击 Create repository

## 三、本地推送

```bash
cd AlphaPilot-v1.1
git init
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git add .
git commit -m "Initial commit: AlphaPilot quant factor research platform"
git branch -M main
git push -u origin main
```

## 四、推送前检查

确保 .gitignore 已包含：.env, data_cache/, factor_db/, output/, node_modules/

## 五、设置仓库

- 在仓库 Settings 添加 Topics: quant, llm, agent, rag, alpha-factor
- README.md 会作为首页展示
- 截图在 docs/screenshots/dashboard.png

## 六、后续更新

```bash
git add .
git commit -m "描述"
git push
```

## 七、认证说明

首次推送若需认证，建议使用 Personal Access Token：
GitHub -> Settings -> Developer settings -> Personal access tokens
