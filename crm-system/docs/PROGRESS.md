# CRM 系统开发进度总览

> 最后更新: 2026-07-01 15:30  
> 项目路径: `D:\develop\job\telegram-bot\crm-system`  
> 相关模块: `D:\develop\job\telegram-bot\telegram-bot-demo` (消息拉取)

---

## 总体进度

| 阶段 | 状态 | 完成日期 |
|------|------|----------|
| Phase 1: Telegram 消息拉取 | ✅ 完成 | 2026-06-30 |
| Phase 2: 需求分析与架构设计 | ✅ 完成 | 2026-07-01 上午 |
| Phase 3: CRM 系统全栈搭建 | ✅ 完成 | 2026-07-01 中午 |
| Phase 4: Bug 修复 (字段显示 + 登录跳转 + 部署架构) | ✅ 完成 | 2026-07-01 15:10 |
| Phase 5: 剩余 401 问题 | 🔴 待修复 | — |
| Phase 6: 智能提取/分配业务逻辑 | ⬜ 未开始 | — |

---

## Phase 1: Telegram 消息拉取 ✅

**目标**：从 Telegram 群聊拉取消息，作为 CRM 系统的数据源。

### 1.1 Bot 与 API 凭证

| 项目 | 值 |
|------|-----|
| Bot 名称 | @black1641_bot (My Test-Bot) |
| Bot Token | `8701600313:AAG1Nn4slTkRcFj7Edhn1IfID5rDNzUQPf0` |
| API ID | `36194093` |
| API Hash | `3624610135cd16e4338ad860116c61cc` |
| App 名称 | MsgExport |
| App 简称 | bbmsgdump20250630 |
| 两步验证密码 | `hmx7654321` |
| 目标群组 | `https://t.me/+dF6hjsXHiV5iNjA9` |
| 账号手机号 | `+86 16670022097` |

### 1.2 脚本文件 (`telegram-bot-demo/`)

| 文件 | 功能 | 状态 |
|------|------|------|
| `bot.py` | Telethon 客户端配置与基础连接 | ✅ 完成 |
| `dump_messages.py` | 历史消息批量拉取 (JSON Lines 输出) | ✅ 完成 |
| `live_capture.py` | 实时消息捕获 (持续运行) | ✅ 完成，已测试通过 |

### 1.3 实时捕获验证
- Bot 加入群聊后开启 live_capture.py
- 在群聊中发送测试消息，确认能实时捕获
- 消息以 JSON Lines 格式保存，每条一行

---

## Phase 2: 需求分析与架构设计 ✅

### 2.1 核心功能模块 (本期 1-4)

1. **订单智能录入** — 从群聊消息自动提取订单字段，生成待审核订单
2. **订单智能分配** — 按区域将审核通过的订单分配给处理人
3. **产品智能录入** — 从群聊消息自动识别并入库新产品
4. **订单和产品生命周期管理** — 订单状态流转 + 产品上下架
5. 订单日报管理 — 待定 (v0.2)
6. 订单信息管理 — 待定 (v0.2)
7. 智能机器人 — 待定 (v0.2)

### 2.2 技术栈

| 层级 | 技术选型 |
|------|----------|
| 后端 | Python 3.11+ / FastAPI / SQLAlchemy / PyMySQL |
| 前端 | Vue 3 (Composition API) / Element Plus / Vite / Pinia / Vue Router / Axios |
| 数据库 | MySQL (本地, root/123456, 库名 crm) |
| 认证 | JWT (python-jose + passlib bcrypt) |
| 消息源 | Telethon (已有 telegram-bot-demo) |

### 2.3 用户角色 (3 个)

| 角色 | 权限范围 |
|------|----------|
| admin (管理员) | 用户管理、区域管理、产品库维护、系统配置、全部数据可见 |
| reviewer (审核员) | 查看待提取/待审核订单、审核通过或驳回、跨区域可见 |
| agent (区域操作员) | 仅可见本区域订单、更新订单状态 |

每个用户必须属于一个区域。

### 2.4 订单状态生命周期

```
待提取 -> 待审核 -> 已分配 -> 处理中 -> 已完成
  |        |        |         |
  |        |        |         +--> 已取消
  |        |        +--> 已取消
  |        +--> 已驳回
  +-- (跳过，待提取仅系统可见)
```

### 2.5 数据库表 (8 张)

`users` / `regions` / `products` / `raw_messages` / `orders` / `order_logs` / `extract_rules` / `assign_rules`

详细字段见 REQUIREMENTS.md 第五章。

---

## Phase 3: CRM 系统全栈搭建 ✅

### 3.1 后端 (FastAPI)

`backend/app/` 目录结构：

- `main.py` — FastAPI 入口 + SPA 中间件
- `config.py` — 环境变量配置
- `database.py` — 数据库连接 (PyMySQL)
- `models/` — SQLAlchemy 模型 (8 张表: user, region, product, raw_message, order, extract_rules, assign_rules; order_logs 内嵌于 order.py)
- `schemas/` — Pydantic 请求/响应模型
- `api/` — API 路由 (auth, users, regions, products, messages, orders, dashboard, rules)
- `services/` — 业务逻辑 (auth_service, order_service)
- `utils/` — 工具函数 (security, deps)

**已实现 API**：
- `POST /api/auth/login` — 登录
- `GET /api/auth/me` — 当前用户信息
- `GET/POST/PUT /api/users` — 用户管理 (admin)
- `GET/POST/PUT /api/regions` — 区域管理 (admin)
- `GET/POST/PUT /api/products` — 产品管理
- `GET /api/messages` — 消息列表
- `GET/POST/PUT /api/orders` — 订单管理
- `POST /api/orders/{id}/review` — 审核
- `POST /api/orders/{id}/assign` — 分配
- `POST /api/orders/{id}/status` — 状态变更
- `GET /api/dashboard/summary` — 仪表盘统计
- `GET/POST /api/rules/extract` — 提取规则
- `GET/POST /api/rules/assign` — 分配规则

### 3.2 前端 (Vue 3 + Element Plus)

`frontend/src/` 目录结构：

- `main.js` — 入口，注入 router 到 API 层和 store
- `App.vue` — 根组件
- `router/index.js` — 路由配置 + 守卫 (角色权限检查)
- `store/auth.js` — Pinia 认证状态 (token持久化到localStorage)
- `api/` — Axios 封装 (index.js实例+拦截器; auth/users/orders/products/regions/messages/dashboard各模块)
- `views/` — 页面组件: Login, Dashboard, OrderList, OrderDetail, OrderReview, ProductList, MessageList, UserList, RegionList
- `components/AppLayout.vue` — 主布局 (侧边栏 + 顶栏 + 角色菜单过滤)

### 3.3 种子数据

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | admin |
| review | review123 | reviewer |
| agent1 | agent123 | agent |

预置区域：华东、华南、华北、西南

### 3.4 初始部署架构 (已废弃)

```
浏览器 ──→ localhost:5173 (Vite dev server)
               │
               └── /api/* ──→ proxy ──→ localhost:8080 (FastAPI)
```

**问题**：Vite HMR 导致 axios baseURL 丢失，请求直连 8080；307 重定向丢失 Authorization header。

---

## Phase 4: Bug 修复 ✅

### 一、后端 API 返回关联实体名称

**问题**：订单管理页面"产品"、"区域"、"处理人"列显示空白。后端只返回外键 ID，前端模板用名称字段渲染。

**修复**：

`backend/app/api/orders.py` — 在 `list_orders`、`get_order`、`create_order`、`update_order` 返回字典中新增（保留原 ID 字段）：

```python
"product_name": order.product.name if order.product else None,
"region_name": order.region.name if order.region else None,
"assigned_user": order.assigned_user.display_name if order.assigned_user else None,
"reviewer_user": order.reviewer.display_name if order.reviewer else None,
```

`backend/app/api/users.py` — 在 `list_users` 返回字典中新增：

```python
"region_name": user.region.name if user.region else None,
```

### 二、前端 UserList.vue status 字段类型修复

**问题**：后端返回 `status` 为整数 (1/0)，前端模板按字符串 `'active'`/`'inactive'` 比较导致显示错误。

**修复**：`frontend/src/views/UserList.vue` — 所有 status 比较从字符串改为整数 `1`/`0`

### 三、前端登录后被踢回登录页 — 方向 B (SPA 统一端口)

**问题现象**：登录成功后点击侧边栏任意菜单，页面被踢回 `/login`，提示"登录已过期"。

**根因**：
1. Vite HMR 模块热替换时 axios 实例被重建，`baseURL` 上下文丢失，请求直连 `localhost:8080` 绕过代理
2. API 端点缺少尾部斜杠（如 `/api/orders`），FastAPI 返回 307 重定向到 `/api/orders/`，重定向过程中浏览器丢弃 Authorization header

**解决方案**：把前端 build 产物挂到 FastAPI，统一从 `:8080` 端口提供，彻底消除 Vite 代理层。

修改涉及文件：
- `frontend/src/api/index.js` — baseURL 设为 `''`
- `frontend/src/store/auth.js` — 移除 router 直接导入，改用 `setStoreRouter()` 延迟注入
- `frontend/src/main.js` — 调用 `setStoreRouter(router)`
- `frontend/src/api/*.js` — 所有列表端点加尾部斜杠 (orders/users/products/regions/messages)
- `backend/app/main.py` — 新增 `SPAMiddleware` + `/assets` StaticFiles 挂载

### 四、当前部署架构

```
浏览器 ──→ localhost:8080 (FastAPI)
               │
               ├── /api/*          → FastAPI 路由
               ├── /assets/*       → StaticFiles
               ├── /health         → 健康检查
               └── 其他路径         → SPAMiddleware → index.html (Vue SPA)
```

**不再使用** Vite dev server (`:5173`) + proxy 代理。

**前端修改后需重建**：`cd frontend && npm run build`，后端 `--reload` 自动检测变化。

### 五、全局字段排查结果

| 页面 | 列/字段 | 状态 |
|------|---------|------|
| OrderList.vue | product_name, region_name, assigned_user | ✅ |
| OrderDetail.vue | 同上 + reviewer_user | ✅ |
| OrderReview.vue | product_name | ✅ |
| UserList.vue | region_name, status | ✅ |
| MessageList.vue | group_name, sender_name | ✅ |
| ProductList.vue | status (字符串) | ✅ |
| Dashboard.vue | region_stats.region_name | ✅ |
| RegionList.vue | name, code | ✅ |

---

## Phase 5: 剩余问题 🔴

### 当前报错

登录后跳转到消息管理页面时，Console 报错：

```
GET http://localhost:8080/api/messages/?page=1&size=20 401 (Unauthorized)
```

**可能原因**：
- Token 在 localStorage 中存在但已过期
- Pinia store 初始化时 token 恢复逻辑存在竞态条件
- SPAMiddleware 与 StaticFiles 的 middleware 注册顺序导致某些请求路由异常
- 前端 dist 构建产物可能未包含最新的请求拦截器代码

**状态**：已写出排查提示词 → DEBUG_PROMPT.md，交给 Claude 排查。**尚未解决**。

---

## Phase 6: 后续规划

> 详细开发计划见 [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)

### Sprint 0-3 概述

| Sprint | 目标 | 依赖 |
|--------|------|------|
| Sprint 0 | 修复 401 + 全链路验证 | 无 |
| Sprint 1 | 消息入库 (JSONL → raw_messages) | Sprint 0 |
| Sprint 2 | 订单自动提取 + 产品自动识别 + 规则配置页面 | Sprint 1 |
| Sprint 3 | 自动分配引擎 | Sprint 2 |
| Sprint 4+ | v0.2 (日报/Excel/Bot/主系统对接) | Sprint 3 | ⬜

### 6.1 待开发功能 (v0.1 剩余)

- [ ] 消息导入接口 (`POST /api/messages/import`)
- [ ] 订单自动提取逻辑 (调用提取规则匹配 raw_messages → 生成订单)
- [ ] 产品自动识别逻辑 (从消息中提取产品名称/规格/单价)
- [ ] 分配规则引擎 (v0.1 为手动分配，后续扩展自动分配)
- [ ] 订单日志完整记录 (order_logs 表已建，需确保所有状态变更都写入)

### 6.2 v0.2 规划

- [ ] 订单日报管理 (每日汇总统计)
- [ ] 订单信息管理 (批量编辑、Excel 导入导出)
- [ ] 智能机器人 (Telegram Bot 查询订单状态、通知提醒)
- [ ] 分配规则扩展 (负载均衡、产品类型匹配)
- [ ] 主系统对接 (Webhook / API 回调)
- [ ] 操作日志审计

---

## 文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 需求与架构 | [REQUIREMENTS.md](REQUIREMENTS.md) | 完整的需求规格、数据模型、API 设计 |
| Claude 开发提示词 | [CLAUDE_PROMPT.md](CLAUDE_PROMPT.md) | 给 Claude 的全栈搭建指令 |
| Bug 修复提示词 | [BUGFIX_PROMPT.md](BUGFIX_PROMPT.md) | 字段显示问题修复指令 |
| 调试提示词 | [DEBUG_PROMPT.md](DEBUG_PROMPT.md) | 401 登录跳转问题排查指令 |
| 团队角色配置 | [team/](team/) | TEAM_LEAD.md / BACKEND_AGENT.md / FRONTEND_AGENT.md |

---

## 环境速查

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
