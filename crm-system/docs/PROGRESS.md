# CRM 系统开发进度总览

> 最后更新: 2026-07-01 17:00
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
| Phase 5: Sprint 0 验收 | ✅ 完成 | 2026-07-01 15:50 |
| Phase 6: Sprint 1 消息入库 | ✅ 完成 | 2026-07-01 16:00 |
| Phase 7: Sprint 2 智能提取/分配 | ✅ 完成 | 2026-07-01 16:55 |
| Phase 8: Sprint 3 自动分配引擎 | ✅ 完成 | 2026-07-01 17:00 |

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
- `PUT /api/rules/extract/{id}` — 更新提取规则
- `GET/POST /api/rules/assign` — 分配规则
- `PUT /api/rules/assign/{id}` — 更新分配规则
- `POST /api/messages/import` — 消息导入
- `POST /api/messages/{id}/extract` — 单条消息提取
- `POST /api/messages/batch-extract` — 批量消息提取

### 3.2 前端 (Vue 3 + Element Plus)

`frontend/src/` 目录结构：

- `main.js` — 入口，注入 router 到 API 层和 store
- `App.vue` — 根组件
- `router/index.js` — 路由配置 + 守卫 (角色权限检查)
- `store/auth.js` — Pinia 认证状态 (token持久化到localStorage)
- `api/` — Axios 封装 (index.js实例+拦截器; auth/users/orders/products/regions/messages/dashboard/rules各模块)
- `views/` — 页面组件: Login, Dashboard, OrderList, OrderDetail, OrderReview, ProductList, MessageList, UserList, RegionList, RulesConfig
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

## Phase 5: Sprint 0 验收 ✅

### 401 问题 — 已解决

**根因**：
1. Vite HMR 模块热替换时 axios 实例被重建，`baseURL` 上下文丢失
2. API 端点缺少尾部斜杠，FastAPI 307 重定向丢失 Authorization header

**解决方案**：前端 build 产物由 FastAPI 统一提供，所有 API 端点加尾部斜杠。

### 端到端业务流程 — 全链路跑通

```
admin 创建订单 → pending_review
  ↓
reviewer 审核通过 → assigned
  ↓
admin 分配给 agent1 → assigned (assigned_to=3)
  ↓
agent1 开始处理 → processing
  ↓
agent1 完成订单 → completed
```

操作日志完整记录 4 条状态变更。

### 页面字段完整性 — 无空白字段

| 页面 | 关键字段 | 状态 |
|------|----------|------|
| 订单列表 | product_name, region_name, assigned_user, reviewer_user | ✅ |
| 用户列表 | region_name, status(整数 1/0) | ✅ |
| 产品列表 | name, spec, category, unit_price, status | ✅ |
| 区域列表 | name, code | ✅ |
| 仪表盘 | total_orders, pending_review, processing, completed_today, region_stats | ✅ |

### 角色权限隔离 — 正常

| 能力 | admin | reviewer | agent |
|------|-------|----------|-------|
| 用户管理 | ✅ | 403 | 403 |
| 区域管理 | ✅ | ✅ | ✅ |
| 订单列表 | ✅ 全部 | ✅ 全部 | ✅ 仅自己的 |
| 产品列表 | ✅ | ✅ | ✅ |
| 消息列表 | ✅ | ✅ | ✅ |
| 仪表盘 | ✅ | ✅ | ✅ |
| 创建订单 | ✅ | ✅ | 403 |
| 审核订单 | 403 | ✅ | 403 |
| 分配订单 | ✅ | ✅ | 403 |

### 修复的额外问题

- `backend/app/api/orders.py` 分配接口：允许 `assigned` 状态下重新分配（之前只允许 `pending_review`，导致审核通过后无法分配）

---

## Phase 6: Sprint 1 消息入库 ✅

**目标**：实现 JSONL 文件上传 → 解析 → 去重 → 入库的完整链路。

### 新建文件

| 文件 | 说明 |
|------|------|
| `backend/app/services/import_service.py` | JSONL 解析 + 格式自动检测 + 字段映射 + 去重 + 批量入库 |

### 修改文件

| 文件 | 修改内容 |
|------|----------|
| `backend/app/api/messages.py` | 新增 `POST /api/messages/import` 端点 |
| `frontend/src/api/messages.js` | 新增 `importMessages()` 函数 |
| `frontend/src/views/MessageList.vue` | 新增"导入消息"按钮 + 对话框 + 文件选择 + 导入逻辑 |

### 支持的 JSONL 格式

| 格式 | 来源 | 检测条件 |
|------|------|----------|
| 格式 A | dump_messages.py (Telethon 历史) | JSON 有 `sender` 字段 |
| 格式 B | live_capture.py (Bot API 实时) | JSON 有 `from_user` 字段 |

### 验证结果

```
导入测试：imported=3, skipped=0, errors=0
  - 格式 A × 2：sender_name 正确解析，group_name 回退为 chat_{chat_id}
  - 格式 B × 1：sender_name 正确解析，group_name 取 chat_title

去重测试：imported=0, skipped=3, errors=0（重复导入全部跳过）

消息列表：3 条消息正确显示
```

---

## Phase 7: Sprint 2 提取引擎 + 规则配置 ✅

**目标**：搭建提取引擎框架，实现关键词/正则/发送者/群组四种规则匹配，创建规则配置前端页面。

### 新建文件

| 文件 | 说明 |
|------|------|
| `backend/app/services/extract_service.py` | 提取引擎：规则加载 → 匹配 → 字段提取，含种子规则自动创建 |
| `frontend/src/api/rules.js` | 规则 API 封装 (提取规则 + 分配规则 CRUD) |
| `frontend/src/views/RulesConfig.vue` | 规则配置页面：双 Tab (提取/分配)，新增/编辑/启禁用 |

### 修改文件

| 文件 | 修改内容 |
|------|----------|
| `backend/app/api/messages.py` | 替换 extract 占位符为真实提取逻辑 + 新增 `POST /api/messages/batch-extract` |
| `backend/app/api/rules.py` | 规则列表 API 移除 status 过滤（支持显示禁用规则） |
| `frontend/src/router/index.js` | 新增 `/rules` 路由 (admin only) |
| `frontend/src/components/AppLayout.vue` | 新增"规则配置"菜单项 + Setting 图标 |
| `frontend/src/api/messages.js` | 新增 `batchExtract()` 函数 |
| `frontend/src/views/MessageList.vue` | 新增"批量提取"按钮 + 确认对话框 |

### 提取引擎规则类型

| 类型 | 匹配逻辑 | field_mapping |
|------|----------|---------------|
| `keyword` | `any(kw in text for kw in keywords)` | 无（仅触发） |
| `regex` | `re.search(pattern, text)` | 按捕获组索引提取字段 |
| `sender` | `sender_id in sender_ids` | 无（仅触发） |
| `group` | `group_id in group_ids` | 无（仅触发） |

### 验证结果

```
单条提取测试：
  消息 "我要下单买苹果" → 匹配关键词规则 → 创建 order_id=4 ✅

批量提取测试：
  31 条未处理消息 → 0 条匹配（无触发词）→ 正确跳过 ✅

规则 API：
  GET /api/rules/extract → 返回 1 条关键词规则 ✅
  GET /api/rules/assign  → 返回 1 条区域分配规则 ✅

前端构建：RulesConfig-499df9fb.js 生成 ✅
```

---

## Phase 8: Sprint 3 自动分配引擎 ✅

**目标**：审核通过订单时按分配规则自动分配给区域操作员。

### 新建文件

| 文件 | 说明 |
|------|------|
| `backend/app/services/assign_service.py` | 分配引擎：区域分配 + 负载均衡，含种子规则自动创建 |

### 修改文件

| 文件 | 修改内容 |
|------|----------|
| `backend/app/api/orders.py` | 审核端点集成 auto_assign：approve 后自动分配 + remark 记录 |

### 分配策略

| 策略 | rule_type | 匹配逻辑 |
|------|-----------|----------|
| 按区域分配 | `region` | region_id 匹配 → 分配给 agent_ids 中第一个可用 agent；agent_ids 为空时走负载均衡 |
| 区域负载均衡 | `load_balance` | region_id 匹配 → 查询该区域所有 agent → 分配给订单数最少的 |

### 验证结果

```
端到端测试 (order #7):
  admin 创建华东订单 → pending_review ✅
  reviewer 审核通过 → assigned, assigned_to=3 (agent1) ✅
  日志记录: "审核通过，自动分配给用户 #3" ✅
  agent1 登录 → 订单列表可见该订单 ✅

无规则测试 (order #8):
  禁用所有规则 → 审核通过 → assigned, assigned_to=None ✅ (不崩溃)
  日志记录: "审核通过，无匹配分配规则，等待手动分配" ✅
```

---

## Phase 9: 后续规划

> 详细开发计划见 [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)

### Sprint 完成状态

| Sprint | 目标 | 状态 |
|--------|------|------|
| Sprint 0 | 修复 401 + 全链路验证 | ✅ |
| Sprint 1 | 消息入库 (JSONL → raw_messages) | ✅ |
| Sprint 2 | 订单自动提取 + 规则配置页面 | ✅ |
| Sprint 3 | 自动分配引擎 | ✅ |
| Sprint 4+ | v0.2 (日报/Excel/Bot/主系统对接) | ⬜ |

### 9.1 待开发功能 (v0.1 剩余)

- [x] 消息导入接口 (`POST /api/messages/import`) — Sprint 1
- [x] 订单自动提取逻辑 (提取规则匹配 → 生成订单) — Sprint 2
- [x] 自动分配引擎 (审核通过 → 按规则分配 agent) — Sprint 3
- [ ] 产品自动识别逻辑 (从消息中提取产品名称/规格/单价)
- [ ] 订单日志完整记录 (order_logs 表已建，需确保所有状态变更都写入)

### 9.2 v0.2 规划

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
| 验收流程 | [VERIFICATION.md](VERIFICATION.md) | Sprint 1+2 完整验收清单 |
| API 验证手册 | [API_VERIFICATION_GUIDE.md](API_VERIFICATION_GUIDE.md) | 后端 API 验证详细步骤（0 基础可操作） |
| Sprint 3 提示词 | [SPRINT3_PROMPT.md](SPRINT3_PROMPT.md) | 自动分配引擎开发指令 |
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
