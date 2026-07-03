# 智投CRM 全量架构与需求全景文档
> 版本: v2.3  |  日期: 2026-07-03  |  状态: 架构已确认 / 待拆分实施
> 基准文档: telegram-bot-管理系统-需求文档.md + 智投CRM-v2.16-研发交付文档.md
> 注意: 两个基准文档不可修改，本文档为对齐后的全景描述。凡本文档与源文档冲突，以源文档为准。

================================================================================

## 一、系统拓扑：双系统独立架构

系统由两个独立微服务组成，各持独立数据库，仅通过 HTTP API 通信，互不直连对方数据库。

`
┌─ Bot管理系统 (:8081) ────────────────┐      ┌─ CRM系统 (:8080) ─────────────────┐
│ 数据库: PostgreSQL 16 (bot_management)│      │ 数据库: MySQL 8.x (crm)            │
│ 缓存/队列: Redis (Streams)            │      │ 缓存: Redis                       │
│ 搜索: Elasticsearch                   │      │                                   │
│ 对象存储: MinIO                       │      │                                   │
│                                      │      │                                   │
│ [采集] live_capture (多Bot热加载)      │      │ [接收] POST /api/orders/from-bot   │
│   ↓                                  │      │   ↓                               │
│ raw_messages (JSONB存储+去重)         │      │ [接收] POST /api/orders/from-bot   │
│   ├─→ POST /api/orders/from-bot ──→  │      │ 原始消息文本 + 来源信息             │
│   │   转发原始消息                    │      │   ↓                               │
│   │                                  │      │ [NLP提取] nlp_fields (17字段定义)   │
│   ├─→ [转发引擎] → Redis Streams     │      │ NLP提取引擎 → 结构化JSON+紧急度检测  │
│   │   5场景: 群→群/群→Bot/Bot→群/    │      │   ↓                               │
│   │   群→Webhook/关键词路由           │      │ 创建订单 (pending_audit)           │
│   │   format: origin/template/stripped│     │   ↓                               │
│   │   options: edits/deletes/限速/去重│     │ [审核] 客服审核 → 通过/驳回          │
│   └─→ ES 全文搜索索引                │      │   ↓                               │
│                                      │      │ [派单] assign_rules(6权重+3版本)   │
│   │                                  │      │ score = w_region×40 + w_d7×d7       │
│   ├─→ [转发引擎] → Redis Streams     │      │  + w_d14×d14 + w_d30×d30            │
│   │   5场景: 群→群/群→Bot/Bot→群/    │      │  - pFR×filter - pOR×overtime        │
│   │   群→Webhook/关键词路由           │      │ 动态黑名单自动排除                  │
│   │   format: origin/template/stripped│     │   ↓                               │
│   │   options: edits/deletes/限速/去重│     │ [执行] 组长接单→分配投手→投放中     │
│   └─→ ES 全文搜索索引                │      │ SLA六物料追踪→完成/暂停/终止        │
│                                      │      │ 佣金率: n+m/n+m返k/纯数字x          │
│ [消息模板] 欢迎语/关键词回复/定时群发  │      │ 预警分钟: getAlertMinutesForOrder   │
│   定时模式: 一次性/每天/每周/Cron     │      │   6市场(JP/US/BR/EU/SEA/IN)         │
│                                      │      │                                   │
│ [监控仪表盘] 活跃Bot/心跳/限流/错误率  │      │ [业务仪表盘] 订单量/审核率/区域分布 │
│ 消息趋势图/转发日志                   │      │                                   │
│                                      │      │ WebSocket 推送 (4通道):             │
│ 前端 (:8081) + 4角色RBAC+TOTP        │      │ TG消息流/催促通知/派单结果/SLA倒计时│
│ Bot/群聊/转发/消息/模板/仪表盘    │      │ 前端 (:8080) + 3角色RBAC            │
│                                      │      │ 订单/审核/派单/客户/预警/规则/SLA   │
└──────────────────────────────────────┘      └───────────────────────────────────┘
`

---

## 二、数据库与基础设施归属

| 组件 | 归属 | 版本/类型 | 说明 |
|------|------|----------|------|
| PostgreSQL 16 | Bot 系统 | bot_management | Bot 主库：用户/群聊/Bot/消息/规则/模板/审计 |
| MySQL 8.x | CRM 系统 | crm | CRM 主库：订单/客户/团队/派单规则/SLA |
| Redis (Streams) | Bot 系统 | 队列+缓存 | 转发消息队列、去重窗口、速率限制 |
| Redis | CRM 系统 | 缓存 | Session/Token 缓存 |
| Elasticsearch | Bot 系统 | 搜索 | 消息全文搜索 |
| MinIO | Bot 系统 | 对象存储 | 图片/视频/文档等媒体文件 |

两个系统各持独立数据库，互不直连对方数据库。Bot→CRM 仅通过 HTTP API 通信 (POST /api/orders/from-bot)。CRM 不直接查 Bot 的 PostgreSQL。

---

## 三、非功能需求

### 3.1 性能指标（Bot需求文档 §9）

| 指标 | 目标 |
|------|------|
| API 响应 P99 | ≤ 500ms |
| 单 Bot 消息采集吞吐 | ≥ 100 msg/s |
| 转发延迟 | ≤ 1s |
| 消息去重准确率 | 100% |
| Bot 重连恢复 | ≤ 30s |
| 派单推荐计算 | ≤ 500ms (10个团队排序) |
| 页面首屏渲染 | ≤ 1.5s |
| WebSocket 连接稳定 | 99.5% |

### 3.2 安全规范（Bot需求文档 §9）

- Bot Token：AES-256-GCM 加密存储
- API 速率限制：按用户/Bot/IP 分级
- 高危操作二次确认：删除 Bot、退出群聊、批量操作
- TOTP 两步验证（Bot 系统 4 角色）
- 操作审计日志：关键操作留痕

### 3.3 可用性要求（Bot需求文档 §9）

- Bot 异常断开自动恢复
- 消息"至少一次"送达保证
- Redis 持久化 + 消息不丢失
- 按级别配置保留天数 + 自动清理归档

---

## 四、用户角色体系

### 4.1 Bot 系统 — 4 角色（Bot需求文档 §2）

| 角色 | 权限范围 |
|------|---------|
| 超级管理员 | 全部权限：用户管理、Bot CRUD、系统配置 |
| 管理员 | Bot/群聊/转发/模板管理 |
| 运营 | 消息查看、仪表盘、导出 |
| 只读 | 消息查看、仪表盘（只读） |

认证方式：用户名+密码 + TOTP 两步验证。登录日志 + 操作审计。

### 4.2 CRM 系统 — 3 角色（CRM交付文档 §1.2）

| 角色 | Key | 核心职责 | 菜单页签数 |
|------|-----|---------|-----------|
| **客服** | `cs` | 审核订单 / 派单 / 生命周期跟踪 / 客户管理 / 集团管理 / 紧急度修正 / 转单 | 7 |
| **组长** | `leader` | 接单 / 再分配 / 投手管理 / 订单拆分 / 多投手协作 / 接收催促进通知 | 3 |
| **管理员** | `admin` | Bot/NLP 配置 / 派单规则 / 动态黑名单 / 地区优先级 / 预警时间 / 业务字典 / SLA 大盘 / 审计日志 | 8 |

---

## 五、数据模型详情

### 5.1 Bot 系统 — bots 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PK | |
| name | VARCHAR(128) | 显示名称 |
| username | VARCHAR(64) | @bot_username |
| token | TEXT | Bot Token (AES-256-GCM 加密) |
| avatar_url | VARCHAR(512) | |
| owner_uid | VARCHAR(32) | Bot 归属的 Telegram 用户 ID（Bot需求文档 §3.2） |
| status | VARCHAR(20) | active / paused / error / revoked |
| receive_mode | VARCHAR(20) | long_polling（Bot需求文档 §3.2） |
| last_heartbeat | TIMESTAMP | |
| group_tag | VARCHAR(64) | 自定义分组标签（Bot需求文档 §3.2） |
| notes | TEXT | |
| is_deleted | INT DEFAULT 0 | 软删除：消息记录保留 30 天后自动清理（Bot需求文档 §3.1） |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### 5.2 Bot 系统 — raw_messages 表（完整字段，Bot需求文档 §6.2）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PK | |
| bot_id | INT | 采集 Bot ID |
| chat_id | BIGINT | 群聊 ID |
| message_id | INT | Telegram message_id |
| sender | JSONB | 发送者信息 |
| type | VARCHAR(20) | text / photo / video / document |
| content | JSONB | 消息内容 |
| media | JSONB | 媒体文件信息 |
| reply_to | JSONB | 回复消息引用 |
| forward_from | JSONB | 转发来源 |
| bot_command | VARCHAR(64) | Bot 命令 |
| edit_history | JSONB | 编辑历史 |
| timestamp | TIMESTAMP | |
| UNIQUE(bot_id, chat_id, message_id) | | |

### 5.3 Bot 系统 — tg_groups 表（含权限配置，Bot需求文档 §4.3）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PK | |
| chat_id | BIGINT | |
| chat_title | VARCHAR(256) | |
| chat_type | VARCHAR(32) | group / supergroup / channel |
| member_count | INT DEFAULT 0 | |
| tags | VARCHAR(256) | 自定义标签分组 |
| bot_permissions | JSONB | {can_read,can_send,can_delete,can_ban,can_pin,can_invite} 6个boolean |
| auto_reply | JSONB | {enabled, welcome_message, farewell_message, keywords[{trigger,reply}]} |
| forward_config_id | VARCHAR(64) | 该群绑定的转发规则ID（Bot需求文档 §4.3） |
| description | TEXT | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### 5.4 Bot 系统 — forward_rules 表（含 format/edits/deletes，Bot需求文档 §5.3）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL PK | |
| name | VARCHAR(128) | |
| description | TEXT | |
| enabled | INT DEFAULT 1 | |
| source_config | JSONB | {type:bot/group/channel, bot_id, chat_ids} |
| target_config | JSONB | [{type, bot_id, chat_id, **format**:origin/template/stripped, template}] |
| filters | JSONB | {allowed_types, keywords, exclude_keywords, sender_whitelist, sender_blacklist} |
| options | JSONB | {rate_limit, dedup_window_seconds, **forward_edits**:false, **forward_deletes**:false} |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

**5 种转发场景（Bot需求文档 §5.2）：**
1. 群→群：源群消息实时同步到目标群
2. 群→Bot：源群消息转发给指定 Bot 处理
3. Bot→群：Bot 产出内容推送到目标群
4. 群→Webhook：消息推送到外部系统 (ERP等)
5. 关键词路由：含特定关键词走特殊路由（如含"投诉"→优先转发值班经理）。这是独立场景，不同于 filters.keywords（过滤）。

**format 3 种模式（Bot需求文档 §5.3）：**
- origin：原样转发
- template：模板渲染，如 [来自{source_title}] {sender}: {text}
- stripped：纯文本

### 5.5 CRM 系统 — orders 表（完整字段，CRM交付文档 §3.1）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | |
| order_no | VARCHAR(32) | {地区}-{渠道}-{日期}-{序号} |
| status | ENUM | 见 Section 六.6（订单状态机） |
| customer | VARCHAR(128) | |
| region | VARCHAR(8) | MG/YD/JP/ZZ/BR/KR... |
| channel | VARCHAR(8) | TT/FB/GG... |
| product_type | VARCHAR(16) | app/pwa/web |
| product_info | JSON | 产品详细信息（ProductInfo类型） |
| kpi | JSON | {roi_target, cpa_target, budget, daily_budget} |
| balance | DECIMAL(12,2) | |
| consumed | DECIMAL(12,2) | |
| today_consumed | DECIMAL(12,2) | |
| today_roi | DECIMAL(8,4) | |
| bd | VARCHAR(64) | 商务（脱敏字段） |
| bd_id | VARCHAR(32) | |
| cs | VARCHAR(64) | 客服 |
| cs_id | VARCHAR(32) | 客服ID，和cs成对 |
| cooperation_type | VARCHAR(20) | 未知/仅开户/仅代投/开户+代投 |
| timezone | VARCHAR(16) | 数字时区 |
| bg_type | VARCHAR(20) | 未知/有后台/后台截图/无后台仅看面板 |
| commission_format | VARCHAR(12) | n+m / n+m返k / 纯数字x |
| commission_n | INT | n+m 格式中的 n 值（原始输入，用于回溯） |
| commission_m | INT | n+m 格式中的 m 值（原始输入） |
| commission_k | INT | n+m返k 格式中的 k 值（返佣，原始输入） |
| commission_x | INT | 纯数字x 格式中的 x 值（原始输入，用于回溯） |
| commission_internal | VARCHAR(16) | 对内佣金率（自动计算） |
| commission_external | VARCHAR(16) | 对外佣金率（自动计算） |
| team_id | VARCHAR(32) | |
| leader_id | VARCHAR(32) | |
| leader_name | VARCHAR(64) | 组长姓名，和leader_id成对 |
| assigned_pitcher_id | VARCHAR(32) | |
| assigned_pitcher_name | VARCHAR(64) | 投手姓名，和assigned_pitcher_id成对 |
| assigned_team_at | TIMESTAMP | |
| reassign_count | INT DEFAULT 0 | |
| reassign_log | JSON | 再分配日志 |
| rejected_teams | JSON | 曾拒单的团队ID列表 |
| match_score | DECIMAL(6,2) | 派单匹配评分 |
| urgency_level | ENUM | urgent / normal |
| urgency_source | VARCHAR(10) | nlp / manual |
| urgency_reason | VARCHAR(256) | |
| urgency_confidence | DECIMAL(3,2) | 0~1 |
| urgency_modified_by | VARCHAR(64) | |
| urgency_modified_at | TIMESTAMP | |
| wait_minutes | INT | 等待时长（演示性 mock 值） |
| nlp_fields | JSON | NLP 提取的 17 字段完整结果 |
| nlp_confidence | JSON | 各字段置信度 map |
| sub_orders | JSON | 子订单列表 |
| tg_group | JSON | {name, type, bot} |
| tg_messages | JSON | 关联的 TG 消息 |
| internal_messages | JSON | 内部通知 |
| asset_sla | JSON | SLA 物料追踪 |
| urged_count | INT DEFAULT 0 | 催促进次数 |
| ai_call_count | INT DEFAULT 0 | AI 呼叫次数 |
| timeline | JSON | 时间线事件 |
| created_at | TIMESTAMP | |
| created_by | VARCHAR(64) | |
| updated_at | TIMESTAMP | |

---

## 六、核心算法

### 6.1 佣金率自动计算（CRM交付文档 §4.1）

| 格式 | 输入 | 对内佣金率 | 对外佣金率 | 示例 |
|------|------|-----------|-----------|------|
| n+m | 4+1 | n+m = 5.0% | n+m = 5.0% | 4+1 → 对內=对外=5% |
| n+m返k | 4+1返1 | n+m-k = 4.0% | n+m = 5.0% | 4+1返1 → 对内4% 对外5% |
| 纯数字x | 5 | x = 5.0% | x = 5.0% | 5 → 对内=对外=5% |

### 6.2 派单评分算法（CRM交付文档 §4.3）

`
score = w_region × 40 + w_d7 × d7_score + w_d14 × d14_score
      + w_d30 × d30_score - pFR × filter_reject_count
      - pOR × overtime_reject_count
`

默认权重 (V3.2 生效版):
- w_region = 0.4, w_d7 = 0.3, w_d14 = 0.2, w_d30 = 0.5
- pFR = 0.08, pOR = 0.12

### 6.3 预警分钟算法 getAlertMinutesForOrder（CRM交付文档 §4.4）

`
启用市场时间?
  └─ YES → 按订单推广地区匹配市场(JP/US/BR/EU/SEA/IN)
       └─ 匹配到 → 用当地当前时间判断上班/下班 → 返回对应预警分钟
       └─ 未匹配 → fallback 中国时间判断
  └─ NO → 统一用中国时间判断上班/下班 → 返回对应预警分钟
`

上班预警默认: 5 分钟 (可调 1~30)。下班预警默认: 60 分钟 (可调 15~180)。

### 6.4 Bot 订单触发条件（CRM交付文档 §6.1）

- is_order_trigger：TG 消息包含完整订单关键词组合（地区+渠道+预算+KPI+客户名）时才触发
- triggered_order_no 格式：{地区}-{渠道}-{日期}-{序号}，如 MG-TT-20260702-0142

### 6.5 紧急度 NLP 检测规则（CRM交付文档 §6.3）

4 种触发类型 + 判定流程：

| 触发类型 | 示例关键词 | 标记方式 |
|----------|-----------|---------|
| 时间限定语 | "今天必须上线"、"限时"、"尽快"、"紧急" | is_urgent_keyword |
| 余额不足 | "余额不足"、"需要充值"、"马上要停" | is_urgent_keyword |
| 全拒循环 | 3 轮以上全部拒单 | 系统自动判定 |
| 客户 VIP | VIP 客户标记 | 系统自动判定 |

判定流程：
`
TG消息 → NLP提取紧急关键词 → 计算置信度
  └─ 置信度 ≥ 0.85 → 自动标记 urgent (urgency_source='nlp')
  └─ 置信度 < 0.85 → 默认 normal
客服可在详情页人工修正 (urgency_source='manual')
`

### 6.6 订单状态机（CRM交付文档 §1.3）

完整 14 状态 DAG，自 CRM 交付文档 §1.3 逐字提取：

`
pending_audit（待审核）
  → (客服审核通过) → pending_assign（待派单）
  → (驳回) → rejected（已驳回）

pending_assign
  → (系统派单评分排序) → group_assigning（派单中）

group_assigning
  → (组长接单) → leader_accepted（组长已接单）

leader_accepted
  → (组长分配投手) → dispatched（已分配投手）

dispatched
  → configuring（配置中）
  → in_progress（投放中）

in_progress
  → (正常结束) → ended（已结束）
  → (暂停) → paused（手动暂停） / paused_sys（系统自动暂停）
  → (等待素材) → waiting_asset（等待素材） → asset_escalated（素材等待升级）
  → (终止) → terminated（已终止）
`

**状态分类：**
| 状态 | 说明 | 触发方式 |
|------|------|---------|
| pending_audit | Bot 推送后自动创建 | 系统自动 |
| rejected | 客服驳回 | 人工 |
| pending_assign | 客服审核通过 | 人工 |
| group_assigning | 系统评分排序后 | 系统自动 |
| leader_accepted | 组长接单 | 人工 |
| dispatched | 组长分配投手 | 人工 |
| configuring | 投手开始配置 | 人工 |
| in_progress | 配置完成，投放中 | 人工 |
| ended | 正常结束 | 人工/系统 |
| paused | 手动暂停 | 人工 |
| paused_sys | 系统自动暂停（如余额不足） | 系统自动 |
| waiting_asset | 等待素材 | 人工 |
| asset_escalated | 素材等待超时升级 | 系统自动 |
| terminated | 终止 | 人工 |

---

## 七、NLP 字段完整定义

### 7.1 NLP 17 字段 + 置信度（CRM交付文档 §6.2）

| # | field_key | field_label | field_type | 置信度范围 | 必填 |
|---|-----------|-------------|------------|-----------|------|
| 1 | customer_name | 客户名称 | text | 0.80~0.98 | ✓ |
| 2 | bd_name | 商务 | select | 0.85~0.99 | ✓ |
| 3 | coop_type | 合作方式 | select | 0.70~0.95 | ✓ |
| 4 | third_party_type | 第三方类型 | select | 0.60~0.90 | ✗ |
| 5 | cs_no | 客服编号 | text | 0.80~0.95 | ✓ |
| 6 | internal_commission | 对内佣金率 | text | 0.70~0.92 | ✓ |
| 7 | external_commission | 对外佣金率 | text | 0.60~0.88 | ✗ |
| 8 | remark | 备注说明 | text | 0.50~0.85 | ✗ |
| 9 | order_no | 订单编号 | text | 0.95~0.99 | ✓ |
| 10 | platform | 推广平台(TT/FB/GG) | select | 0.90~0.99 | ✓ |
| 11 | carrier | 推广载体(App/PWA/Web) | text | 0.85~0.95 | ✗ |
| 12 | region | 推广地区 | select | 0.90~0.98 | ✓ |
| 13 | timezone | 下户时区 | select | 0.70~0.90 | ✓ |
| 14 | daily_budget | 单线日预算 | number | 0.75~0.95 | ✓ |
| 15 | kpi | KPI | text | 0.60~0.89 | ✓ |
| 16 | site_domain | 域名 | text | 0.50~0.80 | ✗ |
| 17 | link_count | 链接数 | number | 0.40~0.75 | ✗ |

**归属**：nlp_fields 表在 CRM 系统 MySQL 中。NLP 是 CRM 系统的一部分（CRM交付文档 §6），17字段定义、匹配引擎、置信度计算均在 CRM 侧完成。

---

## 八、SLA 六物料 + 升级策略

### 8.1 六物料 SLA 配置（CRM交付文档 §7.1）

| 物料 | 请求方 | 默认超时(分钟) | 触发时机 |
|------|--------|---------------|---------|
| 像素/Pixel ID | BD | 15 | pitcher_accept |
| 包名/Bundle ID | BD | 15 | pitcher_accept |
| 在线表格链接 | BD | 240 | before_invest |
| 广告系列命名规则 | BD | 240 | before_invest |
| 日报截图 | 投手 | 60 | daily_18 |
| 转化事件回传 | 投手 | 1440 | daily_18 |

### 8.2 SLA 升级策略（CRM交付文档 §7.2）

超时后自动触发升级：3 次未接 → 自动升级到主管/系统兜底。重试间隔：30 秒。

---

## 九、跨系统交互协议

### 9.1 Bot → CRM：订单推送（POST /api/orders/from-bot）

```json
{
  "source": {
    "bot_id": 1,
    "chat_id": -1001234567890,
    "message_id": 42,
    "tg_group": {"name": "MG投放群", "type": "supergroup"},
    "sender": {"id": 123456789, "username": "bd_zhang", "display_name": "张三"}
  },
  "raw_text": "MG TT 开户+代投 客户GameStorm Group 日预算500 ROI目标2.0 今天必须上线",
  "trigger_info": {
    "order_no": "MG-TT-20260703-0001",
    "matched_keywords": ["MG", "TT", "开户+代投", "GameStorm Group", "500", "ROI", "2.0"],
    "is_urgent_keyword": true
  },
  "media": [],
  "timestamp": "2026-07-03T10:30:00Z"
}
```

### 9.2 Bot → 外部 Webhook（转发引擎）

不同 target 可独立配置 format（origin / template / stripped），非统一 CRM 订单格式。推送内容取决于该转发规则的 target_config.format。

---

## 十、Bot 系统 API 端点设计

### 10.1 认证（Bot需求文档 §11）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/auth/login | 登录（支持TOTP） |
| POST | /api/v1/auth/logout | 登出 |
| GET | /api/v1/auth/me | 当前用户信息 |

### 10.2 Bot 账号管理（Bot需求文档 §11.1）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/bots | Bot 列表（分页+筛选） |
| POST | /api/v1/bots | 新增 Bot（输入Token→自动拉取头像/名称/username） |
| GET | /api/v1/bots/:id | Bot 详情（含群聊列表+实时状态） |
| PUT | /api/v1/bots/:id | 编辑 Bot 配置 |
| DELETE | /api/v1/bots/:id | 删除 Bot（软删除，消息保留30天后清理） |
| POST | /api/v1/bots/:id/toggle | 启用/禁用 Bot |
| POST | /api/v1/bots/:id/reconnect | 重新连接 Bot |
| POST | /api/v1/bots/import | 批量导入 Bot (JSON/CSV) |

### 10.3 群聊管理（Bot需求文档 §11.2）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/bots/:id/chats | 获取 Bot 下的群聊列表 |
| PUT | /api/v1/bots/:id/chats/:chatId | 配置群聊（permissions/auto_reply） |
| POST | /api/v1/bots/:id/chats/:chatId/toggle | 启用/停用群聊 |
| POST | /api/v1/bots/:id/chats/:chatId/leave | Bot 退出群聊 |
| POST | /api/v1/bots/:id/chats/batch-toggle | 批量启用/停用 |
| GET | /api/v1/bots/:id/chats/sync | 手动同步群聊列表 |

### 10.4 转发规则（Bot需求文档 §11.3）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/forward-rules | 转发规则列表 |
| POST | /api/v1/forward-rules | 创建转发规则 |
| GET | /api/v1/forward-rules/:id | 规则详情 |
| PUT | /api/v1/forward-rules/:id | 修改规则 |
| DELETE | /api/v1/forward-rules/:id | 删除规则 |
| POST | /api/v1/forward-rules/:id/toggle | 启用/暂停规则 |
| GET | /api/v1/forward-rules/:id/logs | 转发日志 |
| POST | /api/v1/forward-rules/test | 测试转发（不实际发送） |

### 10.5 消息查看（Bot需求文档 §11.4）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/messages | 消息列表（分页+筛选） |
| GET | /api/v1/messages/search | 全文搜索（ES） |
| GET | /api/v1/messages/:id | 消息详情 |
| GET | /api/v1/messages/export | 导出消息 |
| GET | /api/v1/messages/stats | 消息统计 |

### 10.6 持久化配置（Bot需求文档 §11.5）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/settings/persistence | 获取持久化配置 |
| PUT | /api/v1/settings/persistence | 更新持久化配置 |

### 10.7 CRM 内部接口（Bot→CRM 通信）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/orders/from-bot | Bot 推送原始消息文本 + 触发信息 + order_no |
| GET | /api/internal/bots/active-config | CRM 向 Bot 系统拉取活跃 Bot 配置 |

---

## 十一、前端页面清单

### 11.1 Bot 系统前端（:8081）

| 页面 | 路由 | 说明 |
|------|------|------|
| 登录 | /login | 用户名+密码+TOTP |
| 仪表盘 | /dashboard | 活跃Bot数/心跳延迟/API限流/错误率/消息趋势图 |
| Bot 管理 | /bots | Bot CRUD + 启停 + 群聊列表 + 状态 |
| 群聊管理 | /bots/:id/chats | 群聊配置 + 权限 + auto_reply + 标签 |
| 转发规则 | /forward-rules | 5场景规则配置 + 日志 |
| 消息查看 | /messages | 消息列表 + ES 搜索 + 导出 |
| 消息模板 | /templates | 欢迎语/关键词回复/定时群发 |
| 用户管理 | /users | 4 角色 RBAC |
| 审计日志 | /audit-log | 操作审计 |
| 系统设置 | /settings | 持久化/保留策略配置 |

### 11.2 CRM 系统前端（:8080）

| 页面 | 路由 | 说明 | 角色 |
|------|------|------|------|
| 订单列表 | /orders | 多条件筛选 + 统计卡 | 客服 |
| 审核中心 | /audit | pending_audit 订单集中审核 | 客服 |
| 待接单池 | /pool | 催促/AI呼叫/转单 | 客服 |
| 客户管理 | /customers | NLP 自动创建 + 关联订单 | 客服 |
| 集团管理 | /group_mgmt | 客户集团归属 | 客服 |
| NLP 字段管理 | /cs/nlp | CRM 本地管理 17 NLP 字段（只读+调优） | 客服 |
| Bot 管理 | /cs/bots | 查看 Bot/群聊状态 | 客服 |
| 组长接单台 | /leader/orders | 接单 + 拆分 + 多投手 | 组长 |
| 投手管理 | /leader/pitchers | 投手配置 | 组长 |
| 规则中心 | /admin/rules | 派单规则(6权重+3版本+黑名单) | 管理员 |
| NLP 字段管理 | /admin/nlp | CRM 本地管理 17 NLP 字段 | 管理员 / 客服 |
| Bot 管理 | /admin/bots | 跳转 :8081 或调 Bot API | 管理员 / 客服 |
| SLA 大盘 | /admin/sla | 六物料超时监控 | 管理员 |
| 预警配置 | /admin/alerts | 上班/下班/6市场预警分钟 | 管理员 |
| 业务字典 | /admin/dict | 集团/渠道/时区等枚举值 | 管理员 |
| 审计日志 | /admin/audit-log | 关键操作审计 | 管理员 |

---

## 十二、前端技术选型

| 技术 | 用途 | 版本 |
|------|------|------|
| Vue 3 | 框架 | 3.x |
| Vite | 构建 | 5.x |
| Element Plus | UI 组件库 | 2.x |
| Pinia | 状态管理 | 2.x |
| Vue Router | 路由 | 4.x |
| Axios | HTTP 客户端 | 1.x |
| Chart.js | 仪表盘图表 | 4.x |
| dayjs | 时区转换 + 日期 | 1.x |

**CSS 变量体系（暗色主题）：**
- --bg-base: #0a0a0a
- --bg-card: #141414
- --cyan: #00d4ff

---

## 十三、消息全生命周期（端到端）

`
1. Telegram群聊用户发消息
2. Bot live_capture 通过 polling 实时捕获
3. 去重检查（Redis 窗口 + DB UNIQUE）
4. 写入 bot_management.raw_messages (JSONB)
5. 媒体文件存入 MinIO，消息记录存文件 URL
6. 异步写 ES 索引
7. 触发条件检查：地区+渠道+预算+KPI+客户名 → is_order_trigger
8. Bot 推送原始消息 + 触发信息 → CRM (POST /api/orders/from-bot)
9. 并行执行（Bot 侧）：
    a. 转发引擎 → 5 种场景 → Redis Streams 异步消费者执行
    b. 关键词自动回复 → Bot 发送到群
10. CRM 接收：NLP 提取引擎读 nlp_fields，匹配 17 字段 + 置信度
11. 紧急度 NLP 检测：4 种触发类型 → 置信度≥0.85 标 urgent → 创建 pending_audit 订单
12. CRM 客服审核中心：NLP字段核对/修改 → 通过 → pending_assign
13. 系统派单：评分算法排序 → 推荐最优团队 → group_assigning
14. 客服待接单池：催促/AI呼叫/转单 → 组长接单台
15. 组长：接单(整单/拆分/多投手) → 分配投手 → dispatched
16. 投手：configuring → in_progress
17. SLA 六物料追踪 + 预警分钟算法 → 超时自动告警升级
18. 结束: ended / paused / paused_sys / waiting_asset / asset_escalated / terminated
19. WebSocket 实时推送: TG消息流/催促通知/派单结果/SLA倒计时
20. 按保留策略定期清理/归档旧消息
`

---

## 十四、数据初始化（CRM交付文档 §10）

### 14.1 业务字典初始值

| 字典 | 初始值 | 来源 |
|------|--------|------|
| groupList | GameStorm Group / ShopFast Holdings / EduTech LLC / FitLife Apps | Admin 可维护 |
| cooperationTypes | 未知 / 仅开户 / 仅代投 / 开户+代投 | 固定 4 选项 |
| timezoneList | 西5区/西6区/西7区/西8区/东5.5区/东7区/东8区/东9区/东10区/UTC/UTC+1/UTC+2/UTC+3 | 固定 13 个 |
| bgTypes | 未知 / 有后台 / 后台截图 / 无后台仅看面板 | 固定 4 选项 |
| commissionFormats | n+m / n+m返k / 纯数字x | 固定 3 种格式 |

### 14.2 派单规则初始版本

| 版本 | 权重 |
|------|------|
| V3.2 (生效版) | w_region=0.4, w_d7=0.3, w_d14=0.2, w_d30=0.5, pFR=0.08, pOR=0.12 |
| V3.3 (草稿版) | 同 V3.2（可编辑） |
| V3.4-mock (模拟版) | w_region=0.5, w_d7=0.2, w_d14=0.2, w_d30=0.6, pFR=0.05, pOR=0.1 |

### 14.3 预警配置默认值

| 配置项 | 默认值 |
|--------|--------|
| 上班时间 | 09:00 → 18:00 |
| 上班预警 | 5 分钟（可调 1~30） |
| 下班预警 | 60 分钟（可调 15~180） |
| 市场时间启用 | true |
| 通知渠道 | TG Bot + AI外呼 + App推送（全启用） |
| 6市场默认 | 各市场 09:00~18:00，下班预警 60 分钟 |

---

## 十五、验收标准

### 15.1 功能验收用例（CRM交付文档 §11.1，关键路径）

| # | 用例 | 角色 | 验收标准 |
|---|------|------|---------|
| 1 | 订单审核通过 | 客服 | 点击审核通过 → 状态变 pending_assign → 系统自动派单到最优团队 |
| 2 | 组长整单接单 | 组长 | 一级池点"接单" → 状态变 leader_accepted → 二级池可见 |
| 3 | 组长拆分接单 | 组长 | 点"接单并指派投手" → 弹窗 → 拆分模式选各产品投手 → 确认 → 子订单生成 |
| 4 | 组长多投手协作 | 组长 | 同一产品选多投手 → 确认 → 主投手+co_pitchers 列表生成 |
| 5 | 催促进团队 | 客服 | 待接单池等待>3分钟 → 点催促进 → 组长端弹出催促进通知 |
| 6 | AI呼叫组长 | 客服 | 等待>3分钟 → 点AI呼叫 → 系统自动外呼组长 |
| 7 | 转单 | 客服 | 双栏弹窗 → 候选团队评分排序 → 选择团队 → 确认转单 |
| 8 | 紧急度修正 | 客服 | 详情页TG面板 → 点"标为紧急"/"标为正常" → 填修正理由 → 更新 |
| 9 | 派单规则配置 | 管理员 | 规则中心 → 修改权重 → 保存 → 版本切换生效 |
| 10 | 动态黑名单 | 管理员 | 新增临时地区黑名单 → 过期自动失效 → 派单算法自动排除 |
| 11 | 预警时间配置 | 管理员 | 配置上班5分钟+下班1小时+6市场时间 → 保存 → 订单预警用对应分钟数 |
| 12 | 客户管理 | 客服 | 客户列表 → 详情 → 跳转关联订单 |
| 13 | 集团管理 | 客服 | 集团新增/编辑 → 同步到 Admin 业务字典 |
| 14 | 商务脱敏 | 投手/组长 | 投手不可见 BD 名和 TG 外部群名，BD 不可见投手身份 |
| 15 | 佣金率计算 | 客服 | 4+1 → 对内=对外=5%；4+1返1 → 对内4%对外5%；5 → 对内=对外=5% |

### 15.2 性能验收

| 指标 | 目标 |
|------|------|
| 派单推荐计算 | ≤ 500ms (10个团队排序) |
| TG 消息推送延迟 | ≤ 2s |
| 页面首屏渲染 | ≤ 1.5s |
| WebSocket 连接稳定 | 99.5% |

### 15.3 安全验收

| 检查项 | 标准 |
|--------|------|
| 商务脱敏 | BD API 返回无投手字段；投手 API 返回无 BD 字段 |
| 权限隔离 | 每角色只能访问自己菜单/API |
| 临时黑名单自动失效 | expires_at 到期后派单算法自动忽略 |
| 审计日志 | 紧急度修正/派单操作/黑名单变更均有 audit log |

---

## 十六、风险与约束

### 16.1 已知技术风险（CRM交付文档 §12.1）

| 风险 | 影响 | 缓解 |
|------|------|------|
| TG Bot API 延迟 | 消息推送延迟 | Bot 本地缓存 + 重试机制 |
| PUSH 报表数据不及时 | 地区优先级评分过时 | 定时同步（建议每 6 小时） |
| 市场时区计算复杂 | 夏令时/冬令时切换 | dayjs timezone 插件自动处理 |
| 子订单拆分性能 | 10+ 产品订单拆分延迟 | 限制单词拆分 ≤ 5 个子订单 |

### 16.2 Non-Goals（明确不做，CRM交付文档 §1.4）

- ✗ 不做独立投手角色视图（投手功能合并到组长分配）
- ✗ 不做 BD 独立视图和大盘（BD 信息通过 TG 群聊 + NLP 提取）
- ✗ 不做主管 Plus 决策界面（改为系统自动 5s 轮询 mock）
- ✗ 不做财务报表模块
- ✗ 不做子订单独立详情页跳转（子订单在主订单详情页内展示）
- ✗ 不做实时数据推送（PUSH 报表数据为 mock/定时导入）

---

## 十七、目录结构（目标态）

`
D:\develop\job	elegram-bot├── bot-management-system/              ← 新建（独立系统）
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py                 ← :8081
│   │   │   ├── config.py
│   │   │   ├── database.py             ← PostgreSQL 连接
│   │   │   ├── redis.py                ← Redis 连接 (Streams)
│   │   │   ├── models/                 ← 10+ 数据模型
│   │   │   ├── api/                    ← REST API 路由
│   │   │   ├── services/               ← 转发/模板引擎
│   │   │   └── middleware/             ← 认证/限流/审计
│   │   └── requirements.txt
│   ├── frontend/                       ← Vue 3 + Element Plus
│   └── docs/
├── crm-system/                         ← 已有
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py                 ← :8080
│   │   │   ├── config.py
│   │   │   ├── database.py             ← MySQL 连接
│   │   │   ├── redis.py                ← Redis 连接
│   │   │   ├── models/
│   │   │   ├── api/               ← NLP提取/佣金/SLA/派单
│   │   │   ├── services/
│   │   │   └── middleware/
│   │   └── requirements.txt
│   ├── frontend/                       ← Vue 3 + Element Plus
│   └── docs/
└── telegram-bot-demo/                  ← 已有（采集层保留，后续可迁移到 bot-management-system）
    ├── live_capture.py                 ← 多 Bot 热加载采集
    └── ...
`

---

## 十八、模块归属速查

| 模块 | 归属 | 数据源 | 说明 |
|------|------|--------|------|
| Bot CRUD/启停/软删除30天 | Bot | PG bots | AES-256-GCM 加密/receive_mode/owner_uid/group_tag |
| 群聊管理/标签/权限/auto_reply/定期同步/退出 | Bot | PG tg_groups | bot_permissions(6bool)+auto_reply(欢迎/告别/关键词) |
| 消息采集+存储去重 | Bot | PG raw_messages | JSONB/reply_to/forward_from/bot_command/edit_history |
| 消息保留策略 | Bot | PG retention_policies | 按级别保留天数+自动清理归档 |
| NLP字段定义(17字段) | CRM | MySQL nlp_fields | 唯一数据源，含完整置信度表（CRM交付文档 §6.2） |
| NLP字段管理页面 | CRM | CRM原生 | CS + Admin 管理（CRM交付文档 §2.1.6） |
| NLP提取引擎 | CRM | 读MySQL nlp_fields | 17字段匹配+置信度计算（CRM交付文档 §6） |
| 紧急度NLP检测 | CRM | NLP提取结果 | 4触发类型/置信度≥0.85标urgent（CRM交付文档 §6.3） |
| 转发引擎(5场景/3format/edits+deletes) | Bot | PG forward_rules | Redis Streams 异步消费 |
| 消息模板/定时群发(一次性/每天/每周/Cron) | Bot | PG message_templates | |
| Bot 仪表盘+告警 | Bot | PG | 24h趋势图/实时状态列表/转发日志滚动/站内+邮件+Bot推送 |
| ES 全文搜索 | Bot | ES | 消息全文搜索（源文档仅 Bot 侧有 ES 需求） |
| Bot 用户管理 | Bot | PG users | 4角色RBAC+TOTP |
| Bot 操作审计日志 | Bot | PG audit_logs | 关键操作留痕 |
| MinIO 媒体存储 | Bot | MinIO | 图片/视频/文档 |
| 推送原始消息+触发信息 | Bot→CRM | POST /api/orders/from-bot | 原始文本+触发信息+order_no+来源信息 |
| 外部Webhook | Bot→外部 | 转发引擎 | 推任意第三方URL |
| 接收Bot推送 | CRM | crm.orders | from-bot端点 |
| 订单审核/派单/生命周期 | CRM | crm.orders | 完整 14 状态 DAG（见 Section 六.6） |
| 派单评分算法 | CRM | assign_rules | 6权重+3版本(active/draft/mock) |
| 动态黑名单 | CRM | team_blacklist | 临时(自动过期)/永久/暂停 |
| 佣金率计算 | CRM | orders.commission_* | 3种格式自动计算 |
| 预警分钟算法 | CRM | alert_config | 上班/下班/6市场时区匹配 |
| SLA六物料+升级 | CRM | sla_config | 15/15/240/240/60/1440分钟+3次升级 |
| 商务脱敏 | CRM | 接口+前端双兜底 | BD↔投手双向不可见 |
| WebSocket推送 | CRM | 4通道 | TG流/催促/派单结果/SLA倒计时 |
| 业务仪表盘 | CRM | crm | 订单量/审核率/区域分布 |
| Bot管理前端 | 双端 | :8081完整；:8080调API | |
| CSS变量体系 | CRM前端 | 暗色主题13变量 | --bg-base:#0a0a0a / --cyan:#00d4ff |
| Chart.js / dayjs | CRM前端 | SLA图+时区转换 | |

---

## 十九、参考文档（不可修改）

以下两份文档为系统需求的唯一权威来源。本文档作为对齐后的全景描述，凡与源文档冲突，以源文档为准。

1. `telegram-bot-管理系统-需求文档.md` — Bot 管理系统需求（4 角色 RBAC, Bot/群聊/转发/消息/仪表盘）
2. `智投CRM-v2.16-研发交付文档.md` — CRM 系统需求（3 角色, 订单审核/派单/生命周期/SLA/佣金/脱敏）
