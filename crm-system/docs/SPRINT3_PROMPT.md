# Sprint 3: 自动分配引擎

> 项目进度见 docs/PROGRESS.md  
> Sprint 2 已完成: 提取引擎 + 规则配置页面

## 当前状态

- 订单审核通过后只改状态为 assigned，但不分配处理人（assigned_to 为空）
- assign_rules 表 + CRUD API 已存在
- 规则配置页面已实现（提取 + 分配规则 Tab）
- 手动分配接口 POST /api/orders/{id}/assign 已实现
- **缺失**: 自动分配引擎（审核通过后按规则自动分配）

## 本次任务

创建分配引擎，审核通过时自动将订单分配给区域操作员。

---

## 一、后端：新建分配引擎 backend/app/services/assign_service.py

### 核心职责

加载分配规则 -> 匹配订单 -> 返回应分配的 agent ID。

### 支持两种分配策略（v0.1）

**策略 A：按区域分配 (rule_type=region)**

rule_config 格式:
{ "region_id": 1, "agent_ids": [3, 5] }

匹配逻辑：
1. 订单 region_id 等于规则中的 region_id
2. 如果指定了 agent_ids，分配给列表中第一个启用的 agent
3. 如果未指定 agent_ids，查询该区域所有 agent，分配给当前订单数最少的那个

**策略 B：区域负载均衡 (rule_type=load_balance)**

rule_config 格式:
{ "region_id": 1 }

匹配逻辑：
1. 查询该 region_id 下所有 role=agent 且 status=1 的用户
2. 统计每个 agent 当前 assigned + processing 状态的订单数
3. 分配给订单数最少的 agent

### 函数签名

    def auto_assign(db: Session, order: Order) -> int | None:
        """
        按优先级匹配分配规则，返回应分配的 user_id。
        无匹配规则时返回 None。
        """

### 执行流程

1. 加载所有 status=1 的 AssignRule，按 priority DESC 排序
2. 如果 order.region_id 为空，跳过所有规则，返回 None
3. 遍历规则：
   - rule_type=region：如果 region_id 匹配 -> 分配
   - rule_type=load_balance：如果 region_id 匹配 -> 负载均衡
   - rule_type=product / custom：暂不处理，返回 None
4. 返回分配目标 user_id

### 负载均衡辅助函数

    def _get_least_busy_agent(db: Session, region_id: int) -> int | None:
        """查询指定区域中当前订单数最少的 agent"""
        # 查询该区域所有启用 agent
        # 统计每个 agent 当前 assigned + processing 的订单数
        # 返回订单数最少的 agent.id

### 种子规则

首次运行且 assign_rules 为空时自动创建:

    {
        "name": "华东默认分配",
        "rule_type": "region",
        "rule_config": {"region_id": 1, "agent_ids": []},
        "priority": 10,
        "status": 1
    }

---

## 二、后端：修改审核端点集成自动分配

### 修改 backend/app/api/orders.py 的 review 端点

当前 approve 逻辑:

    if review_data.action == "approve":
        new_status = "assigned"
        order.reviewer_id = current_user.id

**改为**:

    from ..services.assign_service import auto_assign

    if review_data.action == "approve":
        new_status = "assigned"
        order.reviewer_id = current_user.id
        db.flush()

        # 自动分配
        if not order.assigned_to:  # 不覆盖已手动预分配的
            assigned_to = auto_assign(db, order)
            if assigned_to:
                order.assigned_to = assigned_to
                log.remark = f"审核通过，自动分配给用户 #{assigned_to}"
            else:
                log.remark = "审核通过，无匹配分配规则，等待手动分配"

注意事项:
1. 文件顶部新增 import: from ..services.assign_service import auto_assign
2. 自动分配不覆盖已有 assigned_to
3. remark 写入 order_log
4. 分配失败不阻塞审核流程

---

## 三、涉及文件清单

| 操作 | 文件 | 说明 |
|------|------|------|
| **新建** | backend/app/services/assign_service.py | 分配引擎 |
| **修改** | backend/app/api/orders.py | 审核端点集成 |
| **不改** | backend/app/api/rules.py | 规则 API 已完成 |
| **不改** | frontend/ | 无需改动 |
| **不改** | 数据库表结构 | — |

---

## 四、验证步骤

### 4.1 准备条件

- 区域 华东 (id=1)
- Agent agent1 (id=3) 属于华东
- 分配规则 华东默认分配 已启用

### 4.2 curl 验证

    # 1. admin 创建华东订单
    POST /api/orders/ { "order_no":"TEST-S3-001", "region_id":1, "customer_name":"test", "total_amount":100 }

    # 2. reviewer 登录并审核通过
    POST /api/orders/<ORDER_ID>/review { "action":"approve" }

    # 3. 验证: status=assigned, assigned_to=agent1的id

    # 4. agent1 登录 -> 订单列表包含该订单

### 4.3 无规则场景

    # 禁用所有规则 -> 审核通过 -> assigned_to 为空 -> 不崩溃

### 4.4 前端构建

    cd D:\develop\job	elegram-bot\crm-systemrontend
    npm run build

---

## 五、验收标准

- [ ] 审核通过华东区域订单 -> 自动分配给 agent1
- [ ] agent1 登录后订单列表能看到该订单
- [ ] 无匹配规则时，订单保持 assigned 但 assigned_to 为空（不崩溃）
- [ ] 规则配置页面分配规则 CRUD 正常
- [ ] 前端构建成功
- [ ] 手动分配功能不受影响

---

## 六、注意事项

- 不要修改 backend/app/api/rules.py
- 不要修改 backend/app/services/extract_service.py
- 不要修改 backend/app/api/messages.py
- 不要修改数据库表结构
- 不要回退 Sprint 1 和 Sprint 2 的任何代码
- 不要修改 frontend/src/api/index.js
- 种子分配规则仅在表为空时插入
- 自动分配失败不应阻塞审核流程
- 前端无需改动，仅确认构建兼容
- 写完 cd frontend && npm run build
