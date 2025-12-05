## 🎯 **项目目标**

我需要你作为一名高级 Python 架构师，帮我设计并生成一个：

**「Python 多平台发布助手」**

要求：

### ✔ 技术栈

- 后端：纯 Python（不依赖 Node.js，不使用 Django/FastAPI）
- 界面：
  - **PySide6（优先）** 或 **Tkinter（可选）**
  - 结构清晰、支持切换页面、支持线程异步执行任务
- 自动化执行：
  - 使用 **Playwright for Python**（浏览器缓存作为登录状态，不做 Cookies 管理）
- 数据存储：
  - SQLite (本地数据库)
  - ORM 可用 SqlModel / SQLAlchemy
  - 用于账号管理（平台、用户名、密码、备注等）

### ✔ 功能模块

1. **账号管理模块**
   - 添加 / 编辑 / 删除账号
   - 多平台：如 Temu、TikTok、Shopee、Amazon 等
   - 数据加密（可选）
   - 表格显示账号列表
   - 点击选择账号后，右侧显示详情
2. **自动化发布模块（Playwright）**
   - 选择平台和账号
   - 调用对应平台的自动化脚本
   - 自动打开浏览器（非 headless）
   - 使用浏览器缓存保持登录，不做 cookies 表管理
   - 日志窗口实时输出 Playwright 执行过程
   - 任务异步执行，不阻塞 UI
3. **设置模块（可选）**
   - Playwright 缓存路径
   - 发布模板管理
   - 浏览器设置

### ✔ 架构要求

- MVC / MVVM 结构
- 所有 UI 与逻辑分离
- 每个平台自动化脚本独立成模块，例如：

```
publishers/
    temu_publisher.py
    tiktok_publisher.py
    shopee_publisher.py
```

- 每个发布脚本都要暴露一个标准接口，例如：

```
async def publish(account: AccountModel, task_data: dict, logger):
    ...
```

### ✔ 输出要求

请你生成：

1. **完整项目目录结构**
2. **所有主要文件的核心代码**
3. **UI 结构页面示意图 + 事件流程图**
4. **账号管理模块完整代码（含 SQLite 表结构 + CRUD）**
5. **Playwright 自动化发布模块模板（含浏览器缓存目录）**
6. **主界面代码（PySide6）**
7. 后续我只需说“生成 Temu 发布脚本”即可继续往项目扩展