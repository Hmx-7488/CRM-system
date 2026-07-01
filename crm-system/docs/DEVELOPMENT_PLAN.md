# CRM 系统后续开发计划

> 创建日期: 2026-07-01  
> 前置条件: 前后端数据库全链路已打通，基础 CRUD 全部完成  
> 当前阻塞: 401 认证问题 (不影响后续开发，可并行规划)

---

## 一、现状盘点：哪些是壳，哪些是肉

### 已完成（基础设施层）

| 模块 | 内容 | 状态 |
|------|------|------|
| 数据库 | 8 张表 + 模型 + 种子数据 | ✅ |
| 认证 | JWT 登录/权限装饰器 | ✅ |
| 用户管理 | CRUD + 角色 + 区域归属 | ✅ |
| 区域管理 | CRUD | ✅ |
| 产品管理 | CRUD + 手动录入 | ✅ |
| 消息管理 | 列表查看 + 单条提取占位 | ⚠️ 壳有了 |
| 订单管理 | CRUD + 状态流转 + 审核 + 分配 | ⚠️ 手动操作有了 |
| 规则管理 | 提取规则 CRUD + 分配规则 CRUD | ⚠️ 壳有了 |
| 仪表盘 | 概览统计 | ✅ |
| 前端页面 | 全部 9 个页面 | ✅ |

### 未实现（业务逻辑层）

| 功能 | 当前状态 | 缺失内容 |
|------|----------|----------|
| 消息导入 | **不存在** | 从 JSONL 文件批量导入 raw_messages 的 API |
| 提取引擎 | **占位符** | 规则匹配引擎、关键词/正则匹配、字段提取、生成订单 |
| 产品自动识别 | **不存在** | 从消息文本中解析产品名称/规格/单价的逻辑 |
| 自动分配引擎 | **不存在** | 按区域/负载均衡自动分配订单给 agent |
| 规则配置页面 | **不存在** | 前端 RulesConfig.vue 页面 |
| 批量操作 | **不存在** | 批量提取、批量导入 |

---

## 二、开发阶段划分

按依赖关系分 4 个 Sprint，每个 Sprint 应该确保上一阶段验收通过再开始。

```
Sprint 处理依赖关系：

Sprint 0 ──→ Sprint 1 ──→ Sprint 2 ──→ Sprint 3
(修复401)    (消息入库)   (订单+产品    (自动分配
                         自动提取)      + 规则页面)
```

### Sprint 0：修复 401 + 验证全链路

**目标**：确保当前系统稳定可用，所有已有功能跑通。

**任务清单**：
- [ ] 修复 401 未授权问题（按 DEBUG_PROMPT.md 排查）
- [ ] 端到端回归测试：登录 → 查看订单 → 手动创建订单 → 审核 → 分配 → 状态变更
- [ ] 确认所有页面无空白字段
- [ ] 确认 3 个角色权限隔离正常

**验收标准**：
- 用 admin/review/agent 三个账号分别登录，各角色看到的内容符合权限设计
- admin 手动创建订单 → reviewer 审核通过 → admin 分配给 agent → agent 处理完成，全流程走通

---

### Sprint 1：消息入库

**目标**：打通"群聊消息 → 数据库"的链路。

**任务清单**：

#### 1.1 后端：消息导入 API
`POST /api/messages/import`（新建）

```
输入：JSONL 文件上传 或 JSON 数组
处理：
  1. 逐条解析 JSONL
  2. 以 (group_id, message_id) 去重（已有则跳过）
  3. 插入 raw_messages 表
  4. source 字段标记为 'history' 或 'live'
返回：{ imported: N, skipped: M, total: N+M }
```

#### 1.2 前端：消息管理页面增强
`frontend/src/views/MessageList.vue`（修改）

- 新增"导入消息"按钮
- 文件上传组件（`.jsonl` 文件）
- 导入结果提示（导入 N 条，跳过 M 条）
- 消息列表已有，无需改动

#### 1.3 数据流验证
- 从 `telegram-bot-demo/output/` 取一个 JSONL 文件
- 通过前端上传 → 确认 raw_messages 表有数据
- 在消息管理页面看到导入的消息

**涉及文件**：
- 新建：`backend/app/services/import_service.py`
- 修改：`backend/app/api/messages.py`（新增 import 端点）
- 修改：`frontend/src/api/messages.js`（新增 importMessages 函数）
- 修改：`frontend/src/views/MessageList.vue`（新增上传按钮）

**验收标准**：
- 上传 JSONL 文件后，消息管理页面能看到内容
- 重复上传同一文件，消息不重复
- processed=0 的消息可被筛选

---

### Sprint 2：订单自动提取 + 产品自动识别

**目标**：从消息中自动提取订单和产品，这是系统的核心价值。

#### 2.1 后端：提取规则引擎
新建 `backend/app/services/extract_service.py`

```
核心功能：
  1. 加载所有启用的提取规则（按 priority 排序）
  2. 对消息文本逐条匹配：
     - keyword 类型：包含指定关键词则命中
     - regex 类型：正则匹配，提取命名分组
     - sender 类型：来自指定发送者则命中
     - group 类型：来自指定群组则命中
  3. 命中后：从消息文本中提取订单字段
     - customer_name（客户名称）
     - customer_phone（电话）
     - customer_address（地址）
     - product_name（产品名称）→ 匹配 products 表
     - quantity（数量）
     - unit_price（单价）
     - total_amount（总金额）
  4. 生成订单：status=pending_review, source_msg_id=消息ID
  5. 标记消息 processed=1
```

**提取策略**（v0.1 简化版）：
- 先做关键词匹配：消息中包含"订单"、"下单"、"订购"等触发词
- 再用正则提取结构化字段：金额 `¥\d+`、数量 `\d+[件箱个]`、电话 `1\d{10}`
- 提取不到的字段留空，由审核员在审核环节补全

#### 2.2 后端：单条提取接口增强
修改 `POST /api/messages/{id}/extract`（当前是占位符）

```
逻辑：
  1. 获取消息
  2. 调用提取规则引擎
  3. 如果提取成功：创建订单（pending_review），标记消息已处理
  4. 如果提取失败：返回 "no match"，消息保持未处理
返回：{ order_id: N, extracted_fields: {...} } 或 { order_id: null, reason: "no match" }
```

#### 2.3 后端：批量提取接口
新建 `POST /api/messages/batch-extract`

```
输入：无参数（自动处理所有未处理消息）
返回：{ processed: N, created_orders: M, failed: K }
```

#### 2.4 后端：产品自动识别
新建 `backend/app/services/product_extract_service.py`

```
从消息中提取产品信息：
  1. 匹配已存在的产品名（products 表）
  2. 如果发现新产品关键词（如"新品"、"上架"），尝试提取：
     - 产品名称
     - 规格
     - 单价
  3. 自动创建 product（source='auto', status='active'）
```

#### 2.5 前端：消息列表增加操作
修改 `MessageList.vue`

- 每条消息增加"提取"按钮
- 点击后调用 `/api/messages/{id}/extract`
- 成功 → 提示"已生成订单 #xxx"
- 失败 → 提示"未匹配到订单信息"

#### 2.6 前端：规则配置页面
新建 `frontend/src/views/RulesConfig.vue`

- 提取规则 Tab：列表 + 新增/编辑/启用/禁用
- 分配规则 Tab：列表 + 新增/编辑/启用/禁用
- 规则类型下拉：keyword / regex / sender / group
- rule_config 用 JSON 编辑器（textarea 即可，v0.1 不做可视化）
- 路由：`/rules`（admin only）
- 侧边栏增加"规则配置"菜单项

**涉及文件**：
- 新建：`backend/app/services/extract_service.py`
- 新建：`backend/app/services/product_extract_service.py`
- 修改：`backend/app/api/messages.py`（增强 extract + 新增 batch-extract）
- 修改：`backend/app/api/products.py`（新增 batch-extract 端点）
- 修改：`frontend/src/views/MessageList.vue`
- 新建：`frontend/src/views/RulesConfig.vue`
- 修改：`frontend/src/router/index.js`（新增 /rules 路由）
- 修改：`frontend/src/components/AppLayout.vue`（新增菜单项）

**验收标准**：
- 创建一条提取规则（如 keyword: "下单"）→ 上传包含"下单"的消息 → 点击提取 → 生成 pending_review 订单
- 在订单管理页面看到新订单，产品/客户信息已填入
- reviewer 登录 → 待审核列表看到新订单 → 审核通过
- 规则配置页面可增删改查规则

---

### Sprint 3：自动分配引擎

**目标**：审核通过后自动分配订单给处理人，减少 admin 手动操作。

#### 3.1 后端：分配引擎
新建 `backend/app/services/assign_service.py`

```
v0.1 支持两种分配策略：

策略 A: 按区域分配 (rule_type=region)
  rule_config: { "region_id": N, "agent_id": M }
  → 指定区域的订单分配给指定 agent

策略 B: 区域负载均衡 (rule_type=load_balance)
  rule_config: { "region_id": N }
  → 查询该区域所有 agent，分配给当前订单数最少的那个

触发时机：
  方式 1: 订单审核通过时自动触发（在 review approve 逻辑中调用）
  方式 2: 手动触发 POST /api/orders/{id}/assign（已实现）
```

#### 3.2 后端：审核通过自动分配
修改 `POST /api/orders/{id}/review`（approve 逻辑）

```
当前：审核通过后仅改状态为 assigned
改为：审核通过后调用分配引擎 → 自动分配 → 改状态为 assigned
如果无匹配规则：状态保持 assigned，assigned_to 为空，admin 手动分配
```

**涉及文件**：
- 新建：`backend/app/services/assign_service.py`
- 修改：`backend/app/api/orders.py`（review 端点集成分配引擎）

**验收标准**：
- 创建一条分配规则（region: 华东, agent: agent1）
- 审核通过一个华东区域订单 → 自动分配给 agent1
- agent1 登录 → 订单列表看到该订单
- 无匹配规则时，订单保持 assigned 状态但 assigned_to 为空

---

### Sprint 4+（v0.2，需求待确认）

| 功能 | 说明 |
|------|------|
| 订单日报 | 每日汇总统计、自动推送到群聊 |
| Excel 导入导出 | 批量编辑订单、产品 |
| Telegram Bot 查询 | @black1641_bot 查询订单状态 |
| 通知提醒 | 新订单通知审核员、分配通知 agent |
| 主系统对接 | Webhook / API 回调主系统 |

---

## 三、开发顺序依赖图

```
                    ┌──────────────┐
                    │ Sprint 0     │
                    │ 修复401      │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ Sprint 1     │
                    │ 消息导入API  │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
     ┌────────▼─────┐ ┌───▼──────┐     │
     │ 2.1 提取引擎 │ │2.4 产品  │     │
     │ 2.2 单条提取 │ │自动识别  │     │
     │ 2.3 批量提取 │ │          │     │
     └──────┬───────┘ └────┬─────┘     │
            │              │           │
            └──────┬───────┘           │
                   │                   │
          ┌────────▼───────┐  ┌───────▼──────┐
          │ 2.5 消息列表   │  │ 2.6 规则配置 │
          │ 增加提取按钮   │  │ 前端页面     │
          └────────┬───────┘  └──────┬───────┘
                   │                 │
                   └────────┬────────┘
                            │
                   ┌────────▼───────┐
                   │ Sprint 3      │
                   │ 自动分配引擎   │
                   └───────────────┘
```

Sprint 1 是后续所有功能的瓶颈 — 没有消息入库，提取、识别、分配都没有数据源。

---

## 四、给 Claude Code 的开发提示词建议

每个 Sprint 给一个独立的任务提示词，不要一次性丢全部计划。提示词包含：

1. **当前状态说明**（已完成什么、本次要做什么）
2. **具体任务清单**（文件级）
3. **涉及文件路径**（新建/修改）
4. **验收标准**（可执行的 curl/浏览器操作）
5. **不要做的事**（避免回退已完成改动）

建议先给 Sprint 0 的修复提示词（已有 DEBUG_PROMPT.md），修好后逐个给 Sprint 1→2→3。
