================================================================================
  Telegram CRM 系统 — 需求与架构文档
  版本: v0.1  |  日期: 2026-07-01  |  状态: 需求已确认/待开发
================================================================================

## 一、项目背景

### 1.1 目标
将 Telegram 群聊中的订单信息自动提取并纳入 CRM 管理，实现订单录入、审核、
分配、生命周期跟踪的全流程线上化。

### 1.2 已有基础
- Telegram 群聊消息拉取已完成 (dump_messages.py / live_capture.py)
- 群聊消息以 JSON Lines 格式存于本地，可被 CRM 系统消费

### 1.3 技术栈
  后端:       Python + FastAPI
  前端:       Vue 3 + Element Plus
  数据库:     MySQL (本地)
  ORM:        SQLAlchemy
  消息源:     Telegram Bot API + Telethon (已有)

---

## 二、功能模块 (本期范围: 1-4)

  [1] 订单智能录入    — 从群聊消息自动提取订单字段，生成待审核订单
  [2] 订单智能分配    — 按区域 (及后续扩展指标) 将审核通过的订单分配处理人
  [3] 产品智能录入    — 从群聊消息自动识别并入库新产品
  [4] 生命周期管理     — 订单状态流转与产品上下架管理
  [5] 订单日报管理    — 待定
  [6] 订单信息管理    — 待定
  [7] 智能机器人      — 待定

---

## 三、用户角色

  角色            权限范围
  ──────────────────────────────────────────────────────────
  管理员 (admin)    用户管理、区域管理、产品库维护、系统配置、全部数据可见
  审核员 (reviewer) 查看待提取/待审核订单、审核通过或驳回、跨区域可见
  区域操作员 (agent) 仅可见本区域订单、更新订单状态 (处理中->已发货等)

  
  为什么最少需要这 3 个角色:
    - 少管理员: 用户增删、区域调整、产品库维护、规则配置无人能做，系统死锁。
    - 少审核员: 群聊自动提取的订单字段可能有错(漏字段、格式异常)，
      无审核直接进流程会导致后续分配和处理全链错误。
    - 少区域操作员: 分配按区域执行，用户无区域归属则无法认领和处理订单。

  每个用户必须属于一个区域 (region)，区域是分配规则的基础维度。


---

## 四、订单状态生命周期

  待提取 -> 待审核 -> 已分配 -> 处理中 -> 已完成
    |        |        |         |
    |        |        |         +--> 已取消
    |        |        +--> 已取消
    |        +--> 已驳回
    +-- (跳过，待提取不可见给审核员)

  状态说明:
    待提取(pending_extract)  群消息已拉取，尚未经过提取处理
    待审核(pending_review)   字段提取完成，等待审核员确认/驳回/补全
    已驳回(rejected)         审核不通过，附带驳回原因
    已分配(assigned)         审核通过，已分配区域操作员
    处理中(processing)       操作员已接单，正在处理
    已完成(completed)        订单完成
    已取消(cancelled)        订单取消

---

## 五、数据模型 (核心表)

### 5.1 用户表 (users)
  id              INT PRIMARY KEY AUTO_INCREMENT
  username        VARCHAR(64) UNIQUE
  password_hash   VARCHAR(256)
  display_name    VARCHAR(64)
  role            ENUM('admin','reviewer','agent')
  region_id       INT FK -> regions.id
  status          TINYINT DEFAULT 1
  created_at      DATETIME
  updated_at      DATETIME

### 5.2 区域表 (regions)
  id              INT PRIMARY KEY AUTO_INCREMENT
  name            VARCHAR(64) UNIQUE
  code            VARCHAR(16) UNIQUE
  description     VARCHAR(256)
  status          TINYINT DEFAULT 1

### 5.3 产品表 (products)
  id              INT PRIMARY KEY AUTO_INCREMENT
  name            VARCHAR(256)
  spec            VARCHAR(128)          -- 规格
  category        VARCHAR(64)           -- 品类
  unit_price      DECIMAL(10,2)         -- 单价
  unit            VARCHAR(16)           -- 单位 (箱/件/个)
  source          ENUM('manual','auto') -- 来源: 手动录入 / 自动提取
  source_msg_id   INT FK -> raw_messages.id  -- 来源消息
  status          ENUM('active','inactive')
  created_at      DATETIME
  updated_at      DATETIME

### 5.4 原始消息表 (raw_messages)
  id              INT PRIMARY KEY AUTO_INCREMENT
  group_name      VARCHAR(128)
  group_id        BIGINT
  message_id      INT
  sender_id       BIGINT
  sender_name     VARCHAR(128)
  text            TEXT
  raw_json        JSON                  -- 原始消息完整 JSON
  source          ENUM('history','live')
  received_at     DATETIME
  processed       TINYINT DEFAULT 0     -- 是否已提取

### 5.5 订单表 (orders)
  id              INT PRIMARY KEY AUTO_INCREMENT
  order_no        VARCHAR(32) UNIQUE    -- 订单编号
  status          ENUM('pending_extract','pending_review','rejected',
                       'assigned','processing','completed','cancelled')
  customer_name   VARCHAR(128)
  customer_phone  VARCHAR(32)
  customer_address VARCHAR(512)
  product_id      INT FK -> products.id
  quantity        INT
  unit_price      DECIMAL(10,2)
  total_amount    DECIMAL(12,2)
  region_id       INT FK -> regions.id
  assigned_to     INT FK -> users.id
  reviewer_id     INT FK -> users.id    -- 审核人
  reject_reason   VARCHAR(512)          -- 驳回原因
  source_msg_id   INT FK -> raw_messages.id
  remark          TEXT
  created_at      DATETIME
  updated_at      DATETIME

### 5.6 订单日志表 (order_logs)
  id              INT PRIMARY KEY AUTO_INCREMENT
  order_id        INT FK -> orders.id
  operator_id     INT FK -> users.id
  from_status     VARCHAR(32)
  to_status       VARCHAR(32)
  remark          VARCHAR(512)
  created_at      DATETIME

### 5.7 提取规则表 (extract_rules)
  id              INT PRIMARY KEY AUTO_INCREMENT
  name            VARCHAR(128)
  rule_type       ENUM('keyword','regex','sender','group')
  rule_config     JSON                  -- 规则配置 JSON
  priority        INT DEFAULT 0
  status          TINYINT DEFAULT 1
  created_at      DATETIME

### 5.8 分配规则表 (assign_rules)
  id              INT PRIMARY KEY AUTO_INCREMENT
  name            VARCHAR(128)
  rule_type       ENUM('region','load_balance','product','custom')
  rule_config     JSON
  priority        INT DEFAULT 0
  status          TINYINT DEFAULT 1
  created_at      DATETIME

---

## 六、API 设计概要

### 6.1 认证
  POST /api/auth/login          登录 (返回 JWT token)
  POST /api/auth/logout         登出
  GET  /api/auth/me             当前用户信息

### 6.2 用户管理 (admin)
  GET    /api/users             用户列表
  POST   /api/users             创建用户
  PUT    /api/users/{id}        编辑用户
  DELETE /api/users/{id}        禁用用户

### 6.3 区域管理 (admin)
  GET    /api/regions           区域列表
  POST   /api/regions           创建区域
  PUT    /api/regions/{id}      编辑区域

### 6.4 原始消息
  GET    /api/messages          消息列表 (分页, 支持过滤)
  POST   /api/messages/import   手动导入消息 (JSONL 文件)
  POST   /api/messages/{id}/extract  对单条消息执行提取

### 6.5 订单管理
  GET    /api/orders            订单列表 (按角色过滤: agent 看本区域, reviewer/admin 看全部)
  GET    /api/orders/{id}       订单详情
  POST   /api/orders            手动创建订单
  PUT    /api/orders/{id}       更新订单
  POST   /api/orders/{id}/review    审核 (reviewer)
  POST   /api/orders/{id}/assign    分配 (admin/reviewer)
  POST   /api/orders/{id}/status    状态变更

### 6.6 产品管理
  GET    /api/products          产品列表
  POST   /api/products          创建产品
  PUT    /api/products/{id}     编辑产品
  POST   /api/products/batch-extract  批量从消息提取产品

### 6.7 规则管理 (admin)
  GET    /api/rules/extract     提取规则列表
  POST   /api/rules/extract     创建提取规则
  PUT    /api/rules/extract/{id} 编辑提取规则
  GET    /api/rules/assign      分配规则列表
  POST   /api/rules/assign      创建分配规则
  PUT    /api/rules/assign/{id} 编辑分配规则

### 6.8 仪表盘
  GET    /api/dashboard/summary     概览统计
  GET    /api/dashboard/orders      订单统计 (按状态/区域/时间)

---

## 七、前端页面结构

  /login                    登录页
  /dashboard                仪表盘 (概览统计)
  /orders                   订单列表 (含筛选、搜索)
  /orders/:id               订单详情
  /orders/review            待审核列表 (reviewer 专属)
  /products                 产品管理
  /messages                 原始消息列表
  /rules                    规则配置 (提取规则 + 分配规则)
  /users                    用户管理 (admin)
  /regions                  区域管理 (admin)

---

## 八、项目目录结构

  D:\develop\job\telegram-bot\crm-system\
    backend/
      app/
        __init__.py
        main.py              FastAPI 入口
        config.py            配置 (数据库连接、JWT 密钥等)
        models/              SQLAlchemy 模型
        schemas/             Pydantic 请求/响应模型
        api/                 API 路由 (auth, orders, products, ...)
        services/            业务逻辑层
        utils/               工具函数 (JWT, 密码哈希)
      requirements.txt
      alembic/               数据库迁移
      .env                   环境变量

    frontend/
      src/
        views/               页面组件
        components/          通用组件
        api/                 API 调用封装
        router/              路由配置
        store/               Pinia 状态管理
        utils/               工具函数
      package.json
      vite.config.js

    docs/
      REQUIREMENTS.md        本文件

    telegram-bot-demo/       已有的消息拉取模块 (相对路径引用)

---

## 九、环境配置 (.env)

  MYSQL_HOST=127.0.0.1
  MYSQL_PORT=3306
  MYSQL_USER=root
  MYSQL_PASSWORD=123456
  MYSQL_DATABASE=crm
  JWT_SECRET_KEY=<随机生成>
  JWT_EXPIRE_HOURS=24
  TELEGRAM_OUTPUT_DIR=../telegram-bot-demo/output

---

## 十、后续规划 (v0.2+)

  - 订单日报管理 (每日汇总统计、自动推送)
  - 订单信息管理 (批量编辑、Excel 导入导出)
  - 智能机器人 (Telegram Bot 查询订单状态、通知提醒)
  - 分配规则扩展 (负载均衡、产品类型匹配)
  - 订单与主系统对接 (Webhook / API 回调)
  - 操作日志审计 (完整操作记录)

================================================================================
