# Python Multi-Platform Publisher Assistant

一个 **纯 Python** 的「多平台发布助手」，集成 **PySide6 桌面 UI + Playwright 自动化 + SQLite 账号管理**，用于统一管理多平台账号，并通过浏览器缓存保持登录状态执行发布任务。

> 当前已完成：✅ 小红书（Xiaohongshu）发布流程  
> 后续计划：Temu / TikTok / Shopee / Amazon 等平台逐步接入  
> 终极目标：升级为 **MCP 模式**，通过 **AI Agent** 自动生成/编排发布任务并执行。

---

## ✨ Features

### 1) 账号管理（SQLite + ORM）
- 添加 / 编辑 / 删除账号
- 多平台支持：Xiaohongshu / Temu / TikTok / Shopee / Amazon（可扩展）
- 列表表格展示账号
- 选择账号后右侧显示详情
-（可选）敏感字段加密（密码/Token）

### 2) 自动化发布（Playwright for Python）
- 选择平台与账号后执行发布任务
- 非 headless，便于人工观察、处理验证码
- **使用浏览器缓存目录保持登录状态**（不做 cookies 表管理）
- 日志实时输出到 UI
- 任务异步执行，不阻塞界面

### 3) 设置（可选）
- Playwright 缓存路径配置
- 发布模板管理
- 浏览器启动参数配置

---

## 🧱 Tech Stack

- **Python** 3.10+
- **UI**：PySide6（优先）
- **Automation**：Playwright (Python)
- **DB**：SQLite
- **ORM**：SQLAlchemy / SQLModel（可选其一）
- 结构：MVC / MVVM（UI 与逻辑分离）

---

## 📁 Project Structure

> 目录结构以“清晰可扩展”为目标，每个平台自动化逻辑独立模块化。

