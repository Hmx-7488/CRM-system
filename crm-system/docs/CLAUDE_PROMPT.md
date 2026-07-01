# CRM 系统继续开发提示词

> 项目当前状态见 [PROGRESS.md](PROGRESS.md)。Phase 1-4 已完成，Phase 5 待修复，Phase 6 未开始。

================================================================================
  项目路径: D:\develop\job\telegram-bot\crm-system
  需求文档: D:\develop\job\telegram-bot\crm-system\docs\REQUIREMENTS.md
  进度文档: D:\develop\job\telegram-bot\crm-system\docs\PROGRESS.md
================================================================================

## 0. 当前状态 (先读这个)

### 已完成
- ✅ Phase 1: Telegram 消息拉取 (telegram-bot-demo/)
- ✅ Phase 2: 需求分析与架构设计
- ✅ Phase 3: CRM 系统全栈搭建 (后端 32 个 py 文件, 前端 23 个 vue/js 文件)
- ✅ Phase 4: Bug 修复 (字段显示 + 登录跳转)

### 当前部署架构
```
浏览器 ──→ localhost:8080 (FastAPI)
               ├── /api/*          → FastAPI 路由
               ├── /assets/*       → StaticFiles
               └── 其他路径         → SPAMiddleware → index.html (Vue SPA)
```
前端 build 产物挂在 FastAPI 上，不再使用 Vite dev server。

### 待修复 🔴
- **Phase 5: 401 Unauthorized 错误** — 登录后跳转页面时部分请求返回 401
  - 报错: `GET http://localhost:8080/api/messages/?page=1&size=20 401`
  - 排查提示词: [DEBUG_PROMPT.md](DEBUG_PROMPT.md)

### 未开始 ⬜
- **Phase 6**: 智能提取/分配业务逻辑开发

## 1. 优先任务：修复 401 问题

严格按 [DEBUG_PROMPT.md](DEBUG_PROMPT.md) 的 6 步流程排查，不跳过任何步骤。

关键提示：
- 当前架构是 SPA 统一端口 (8080)，不存在 Vite proxy，请求 URL `localhost:8080` 是正确的
- 先确认 `frontend/dist/` 是最新构建 (npm run build)
- 先用 PowerShell curl 验证后端 API 带 token 是否正常
- 重点关注路由守卫与响应拦截器的竞态问题（见 DEBUG_PROMPT.md 可能性 5）

## 2. 技术约束 (不变)

- 后端: Python 3.11+, FastAPI, SQLAlchemy, PyMySQL
- 前端: Vue 3 (Composition API), Element Plus, Vite, Pinia, Vue Router, Axios
- 数据库: MySQL root/123456@127.0.0.1:3306/crm
- 认证: JWT (python-jose + passlib bcrypt)
- 所有 API 返回格式: {"code": 0, "data": ..., "message": "ok"}

## 3. 待开发功能 (Phase 6, 修复 401 后)

### 3.1 消息导入接口
`POST /api/messages/import` — 从 JSONL 文件批量导入消息到 raw_messages 表

### 3.2 订单自动提取
- 实现提取规则匹配引擎：从 raw_messages 中匹配关键词/正则，提取订单字段
- `POST /api/messages/{id}/extract`：对单条消息执行提取，生成 pending_extract 订单
- 批量提取：遍历未处理消息，调用规则引擎

### 3.3 产品自动识别
- 从消息中识别产品名称/规格/单价，自动创建 product 记录
- `POST /api/products/batch-extract`

### 3.4 分配规则引擎
- v0.1 为手动分配（已实现 POST /api/orders/{id}/assign）
- 后续扩展：自动按区域分配、负载均衡分配

### 3.5 订单日志完善
- 确保所有状态变更都写入 order_logs 表

## 4. 环境速查

```bash
# 后端启动
cd D:\develop\job\telegram-bot\crm-system\backend
uvicorn app.main:app --reload --port 8080

# 前端构建 (修改前端代码后)
cd D:\develop\job\telegram-bot\crm-system\frontend
npm run build

# 数据库
MySQL: root / 123456 @ 127.0.0.1:3306 / crm

# 登录
http://localhost:8080
admin / admin123
```

## 5. 参考文件

| 文档 | 路径 | 用途 |
|------|------|------|
| 需求与架构 | [REQUIREMENTS.md](REQUIREMENTS.md) | 完整数据模型 + API 设计 |
| 进度总览 | [PROGRESS.md](PROGRESS.md) | 项目当前状态 |
| 401 排查 | [DEBUG_PROMPT.md](DEBUG_PROMPT.md) | 401 问题详细排查步骤 |
| 消息拉取模块 | `../telegram-bot-demo/` | 已有的消息源 |

## 6. 注意事项

- 不要删除或修改 `D:\develop\job\telegram-bot\telegram-bot-demo` 下任何文件
- 不要回退已完成改动 (见 DEBUG_PROMPT.md "已完成的改动")
- 前端代码修改后必须 `npm run build`，后端 `--reload` 不会自动检测 dist 变化
- 密码必须 bcrypt 哈希
- 不要重新创建数据库或重置种子数据
