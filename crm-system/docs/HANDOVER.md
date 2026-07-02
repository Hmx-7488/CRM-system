# CRM 系统接手文档

> 最后更新: 2026-07-01 17:10  
> 写给接手此项目的人，10 分钟内了解全貌。

---

## 一、项目一句话描述

**从 Telegram 群聊消息自动提取订单，审核后按区域自动分配给操作员处理的 CRM 系统。**

---

## 二、核心架构

```
Telegram 群聊
    │
    ├── Telethon (dump_messages.py)     → JSONL 历史消息文件
    └── Bot API (live_capture.py)       → JSONL 实时消息流
              │
              ▼
    ┌─────────────────────────┐
    │  FastAPI 后端 (:8080)    │
    │  ├── 消息导入 API        │
    │  ├── 提取引擎 (规则匹配)  │
    │  ├── 分配引擎 (自动分配)  │
    │  ├── 订单/产品/用户 CRUD │
    │  └── 前端 SPA 托管       │
    └──────────┬──────────────┘
               │
    ┌──────────▼──────────────┐
    │  MySQL (crm, 8张表)      │
    └─────────────────────────┘
               │
    ┌──────────▼──────────────┐
    │  Vue 3 前端              │
    │  ├── admin: 全部功能     │
    │  ├── reviewer: 审核      │
    │  └── agent: 仅自己订单   │
    └─────────────────────────┘
```

**部署方式**: 前端 build 产物由 FastAPI 统一在 `:8080` 端口提供，无需 Nginx，无需 Vite dev server。

---

## 三、技术栈速览

| 层 | 技术 | 版本 |
|----|------|------|
| 后端 | Python + FastAPI + SQLAlchemy + PyMySQL | 3.11+ |
| 前端 | Vue 3 + Element Plus + Vite + Pinia + Axios | — |
| 数据库 | MySQL | 8.x |
| 消息源 | Telethon + python-telegram-bot | — |
| 认证 | JWT (python-jose + passlib bcrypt) | — |

---

## 四、目录结构

```
D:\develop\job\telegram-bot\
├── telegram-bot-demo/          # 消息拉取脚本（独立项目）
│   ├── bot.py                  # Telethon 客户端配置
│   ├── dump_messages.py        # 历史消息批量导出 (JSONL)
│   └── live_capture.py         # 实时消息捕获
│
└── crm-system/                 # CRM 主系统
    ├── backend/
    │   └── app/
    │       ├── main.py           # FastAPI 入口 + SPA 中间件
    │       ├── config.py         # 配置
    │       ├── database.py       # 数据库连接
    │       ├── models/           # SQLAlchemy 模型 (8 张表)
    │       │   ├── user.py       # users
    │       │   ├── region.py     # regions
    │       │   ├── product.py    # products
    │       │   ├── order.py      # orders + order_logs
    │       │   ├── raw_message.py# raw_messages
    │       │   ├── extract_rules.py  # extract_rules
    │       │   └── assign_rules.py   # assign_rules
    │       ├── schemas/          # Pydantic 模型
    │       ├── api/              # 路由
    │       │   ├── auth.py       # 登录 + 用户信息
    │       │   ├── users.py      # 用户 CRUD
    │       │   ├── regions.py    # 区域 CRUD
    │       │   ├── products.py   # 产品 CRUD
    │       │   ├── messages.py   # 消息列表 + 导入 + 提取 + 批量提取
    │       │   ├── orders.py     # 订单 CRUD + 审核 + 分配 + 状态
    │       │   ├── dashboard.py  # 仪表盘统计
    │       │   └── rules.py      # 提取/分配规则 CRUD
    │       ├── services/         # 业务逻辑
    │       │   ├── auth_service.py       # 认证
    │       │   ├── order_service.py      # 订单日志
    │       │   ├── import_service.py     # 消息导入 (Sprint 1)
    │       │   ├── extract_service.py    # 提取引擎 (Sprint 2)
    │       │   └── assign_service.py     # 分配引擎 (Sprint 3)
    │       └── utils/
    │           ├── security.py   # JWT 工具
    │           └── deps.py       # 依赖注入 (get_db, get_current_user, require_role)
    │
    ├── frontend/
    │   ├── src/
    │   │   ├── main.js           # Vue 入口
    │   │   ├── App.vue           # 根组件
    │   │   ├── router/index.js   # 路由 + 权限守卫
    │   │   ├── store/auth.js     # Pinia 认证状态
    │   │   ├── api/              # Axios 封装
    │   │   │   ├── index.js      # 实例 + 拦截器
    │   │   │   ├── auth.js
    │   │   │   ├── users.js
    │   │   │   ├── orders.js
    │   │   │   ├── products.js
    │   │   │   ├── regions.js
    │   │   │   ├── messages.js   # + importMessages + batchExtract
    │   │   │   ├── dashboard.js
    │   │   │   └── rules.js      # 规则 CRUD (Sprint 2)
    │   │   ├── views/            # 页面
    │   │   │   ├── Login.vue
    │   │   │   ├── Dashboard.vue
    │   │   │   ├── OrderList.vue
    │   │   │   ├── OrderDetail.vue
    │   │   │   ├── OrderReview.vue
    │   │   │   ├── ProductList.vue
    │   │   │   ├── MessageList.vue  # + 导入 + 批量提取按钮
    │   │   │   ├── UserList.vue
    │   │   │   ├── RegionList.vue
    │   │   │   └── RulesConfig.vue  # 规则配置 (Sprint 2)
    │   │   └── components/
    │   │       └── AppLayout.vue # 侧边栏 + 顶栏
    │   └── dist/                 # 前端 build 产物
    │
    └── docs/
        ├── REQUIREMENTS.md       # 需求规格说明书
        ├── DEVELOPMENT_PLAN.md   # 开发计划
        ├── PROGRESS.md           # 进度总览 (开发完成后可删)
        ├── HANDOVER.md           # 本文档
        ├── SPRINT1_PROMPT.md     # Sprint 1 开发提示词
        ├── SPRINT2_PROMPT.md     # Sprint 2 开发提示词
        └── SPRINT3_PROMPT.md     # Sprint 3 开发提示词
```

---

## 五、数据库 (8 张表)

| 表 | 说明 | 关键字段 |
|----|------|----------|
| `users` | 用户 | username, password_hash, role(admin/reviewer/agent), region_id, status(0/1) |
| `regions` | 区域 | name, code |
| `products` | 产品 | name, spec, category, unit_price, status |
| `raw_messages` | 原始消息 | group_id, message_id (联合去重), sender_id, sender_name, text, processed(0/1) |
| `orders` | 订单 | order_no, status, region_id, assigned_to, reviewer_id, product_id, total_amount |
| `order_logs` | 订单日志 | order_id, operator_id, from_status, to_status, remark |
| `extract_rules` | 提取规则 | name, rule_type(keyword/regex/sender/group), rule_config(JSON), priority, status |
| `assign_rules` | 分配规则 | name, rule_type(region/load_balance), rule_config(JSON), priority, status |

### 订单状态生命周期

```
待提取 → 待审核 → 已分配 → 处理中 → 已完成
             ↓       ↓        ↓
           已驳回   已取消    已取消
```

---

## 六、权限模型 (3 角色)

| 能力 | admin | reviewer | agent |
|------|-------|----------|-------|
| 用户管理 | ✅ | ❌ 403 | ❌ 403 |
| 区域管理 | ✅ | ✅ | ✅ |
| 订单列表 | ✅ 全部 | ✅ 全部 | ✅ 仅自己 |
| 产品列表 | ✅ | ✅ | ✅ |
| 消息列表 | ✅ | ✅ | ✅ |
| 仪表盘 | ✅ | ✅ | ✅ |
| 创建订单 | ✅ | ✅ | ❌ 403 |
| 审核订单 | ❌ 403 | ✅ | ❌ 403 |
| 分配订单 | ✅ | ✅ | ❌ 403 |
| 规则配置 | ✅ | ❌ 页面不可见 | ❌ 页面不可见 |

---

## 七、Sprint 完成情况

| Sprint | 目标 | 状态 |
|--------|------|------|
| Sprint 0 | 修复 401 + 全链路验证 | ✅ |
| Sprint 1 | 消息导入 (JSONL → raw_messages) | ✅ |
| Sprint 2 | 提取引擎 + 规则配置页面 | ✅ |
| Sprint 3 | 自动分配引擎 | ✅ |

### 已实现的完整业务流程

```
1. 前端上传 JSONL 文件 → 消息入库 (Sprint 1)
2. 消息批量提取 → 规则匹配 → 生成 pending_review 订单 (Sprint 2)
3. reviewer 审核通过 → 自动分配 agent → assigned 状态 (Sprint 3)
4. agent 处理 → processing → completed
```

### 待开发 (v0.1 剩余)

- [ ] 产品自动识别（从消息文本提取产品名称/规格/单价）
- [ ] 订单日志全面覆盖（review/assign 已有，status 变更部分缺失）

---

## 八、启动指南

### 数据库

```bash
MySQL: root / 123456 @ 127.0.0.1:3306
数据库名: crm
# 表结构和种子数据由 SQLAlchemy create_all 自动创建
```

### 后端

```bash
cd D:\develop\job\telegram-bot\crm-system\backend
pip install fastapi uvicorn sqlalchemy pymysql python-jose passlib bcrypt
uvicorn app.main:app --reload --port 8080
```

### 前端 (修改后需重新构建)

```bash
cd D:\develop\job\telegram-bot\crm-system\frontend
npm run build
# 产物输出到 frontend/dist/, FastAPI 自动服务
```

### 访问

```
http://localhost:8080

测试账号：
  admin   / admin123   (管理员，全部权限)
  review  / review123  (审核员)
  agent1  / agent123   (操作员，华东区域)
```

---

## 九、关键设计决策

### 1. 为什么前端不是独立 dev server
Vite HMR 热替换时 axios 实例被重建导致 `baseURL` 丢失，请求绕过代理直连 8080。加上 FastAPI 307 重定向丢失 Authorization header。最终采用方向 B：前端 build 产物由 FastAPI SPA 中间件统一在 8080 提供服务。

### 2. API 端点尾部斜杠规则
FastAPI 对无尾斜杠的端点返回 307 重定向，导致浏览器丢弃 Authorization header。所以：
- **有尾斜杠的端点**（如 `/api/orders/`）：前端调用必须加尾斜杠
- **无尾斜杠的端点**（如 `/api/rules/extract`、`/api/messages/import`）：前端调用不加尾斜杠

**规则**：看 `@router.get("/")` 还是 `@router.get("/extract")` 来决定前端 URL。

### 3. 提取引擎 field_mapping 设计
提取规则的 `field_mapping` 是开放 JSON，引擎不做字段名校验。新增字段只需改规则 JSON，不用改代码。例如：
```json
{"pattern": "[¥￥](\\d+)", "field_mapping": {"total_amount": 1}}
```

### 4. 种子规则自动创建
提取引擎和分配引擎首次运行时，如果对应规则表为空，自动插入预置规则。后续运行不再重复创建。

---

## 十、常见问题排查

### 前端显示问题
- **字段空白**：检查后端 API 返回的字段名是否和前端模板一致（如 product_name vs product_id）
- **状态显示错误**：检查整数/字符串类型匹配（如 status=1 还是 status='active'）

### 后端问题
- **401 未授权**：检查 token 是否有效、Authorization header 是否正确传递
- **307 重定向**：检查前端调用 URL 的尾斜杠是否匹配后端路由定义
- **导入报错**：检查 JSONL 格式（需有 `sender` 或 `from_user` 字段）

### 前后端通信
- 所有 API 前缀为 `/api/`
- 后端 `--reload` 只检测 Python 文件变化
- 前端代码修改后要 `npm run build` 才能生效
- 静态资源 `/assets/*` 由 FastAPI StaticFiles 直接提供

---

## 十一、下一步工作

1. **产品自动识别**：从消息文本中匹配 products 表已有产品名，或识别"新品"关键词自动入库
2. **通知提醒**：Telegram Bot 推送新订单通知给审核员
3. **Excel 批量操作**：导入导出订单
4. **v0.2 长期**：订单日报、Telegram Bot 查询、主系统对接

---

## 十二、文档索引

| 文档 | 内容 |
|------|------|
| [REQUIREMENTS.md](REQUIREMENTS.md) | 完整需求规格、数据模型、API 设计 |
| [PROGRESS.md](PROGRESS.md) | 开发进度详情（含各 Sprint 修改清单和验证结果） |
| [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) | 原始开发计划 |
| [API_VERIFICATION_GUIDE.md](API_VERIFICATION_GUIDE.md) | API 验证步骤 |
