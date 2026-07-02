# Sprint 2 第一部分：提取引擎框架 + 规则配置页面

> 项目进度见 `docs/PROGRESS.md`  
> Sprint 1 已完成：消息导入功能已通

## 当前状态

- `extract_rules` / `assign_rules` 表 + CRUD API 已存在（`backend/app/api/rules.py`）
- `POST /api/messages/{id}/extract` 是占位符，只返回 `"extraction queued"`
- 没有提取引擎（没有实际的规则匹配逻辑）
- 前端没有规则配置页面
- 消息管理页没有批量提取按钮

## 本次任务

搭建提取引擎框架和规则配置页面。**具体提取什么字段等产品需求确认后再填，本次只搭框架。**

---

## 一、后端：新建提取引擎 `backend/app/services/extract_service.py`

### 核心职责

加载提取规则 → 匹配消息文本 → 返回提取结果。规则匹配逻辑完整实现，字段提取部分用 `rule_config.field_mapping` 驱动（需求确认后改 JSON 即可，不用改代码）。

### 规则类型与匹配逻辑

| 类型 | rule_config 格式 | 匹配逻辑 |
|------|-----------------|----------|
| `keyword` | `{"keywords": ["下单","订购"]}` | 消息文本包含任一关键词 → 命中 |
| `regex` | `{"pattern": "¥(\\d+)", "field_mapping": {"total_amount": 1}}` | 正则匹配 → 按 field_mapping 提取捕获组 |
| `sender` | `{"sender_ids": [123, 456]}` | 消息发送者 ID 在列表中 → 命中 |
| `group` | `{"group_ids": [-100111]}` | 消息群组 ID 在列表中 → 命中 |

### 函数签名

```python
def run_extraction(db: Session, message: RawMessage) -> dict:
    """
    对一条消息执行所有启用的提取规则。
    
    返回:
      {
        "matched": bool,              # 是否有规则命中
        "triggered_rules": [...],      # 命中的规则名称列表
        "extracted_fields": {...},     # 提取到的字段 dict
      }
    """
```

### 执行流程

1. 加载所有 `status=1` 的 `ExtractRule`，按 `priority DESC` 排序
2. 对每条规则按 `rule_type` 匹配：
   - `keyword`：`any(kw in message.text for kw in rule_config["keywords"])`
   - `regex`：`re.search(pattern, message.text)` → 按 `field_mapping` 提取捕获组
   - `sender`：`message.sender_id in rule_config["sender_ids"]`
   - `group`：`message.group_id in rule_config["group_ids"]`
3. 合并所有命中规则的 `extracted_fields`（后面的覆盖前面的）
4. 返回结果

### 两条预置种子规则

在首次运行时如果 extract_rules 表为空，自动创建两条示例规则：

```python
# 规则 1: 关键词触发
{
    "name": "订单触发词",
    "rule_type": "keyword",
    "rule_config": {"keywords": ["下单", "订购", "来货", "要货"]},
    "priority": 10
}

# 规则 2: 金额提取
{
    "name": "金额提取",
    "rule_type": "regex",
    "rule_config": {
        "pattern": "[¥￥](\\d+(?:\\.\\d{1,2})?)",
        "field_mapping": {"total_amount": 1}
    },
    "priority": 5
}
```

---

## 二、后端：增强提取端点 `backend/app/api/messages.py`

### 替换占位符 `POST /api/messages/{id}/extract`

```python
@router.post("/{message_id}/extract")
async def extract_message(message_id: int, db, current_user):
    msg = db.query(RawMessage).filter(RawMessage.id == message_id).first()
    if not msg:
        raise HTTPException(404, "消息不存在")
    
    result = run_extraction(db, msg)
    
    if not result["matched"]:
        return {
            "code": 0,
            "data": {"matched": False, "reason": "no rule matched"},
            "message": "未匹配到任何规则"
        }
    
    # 创建订单
    fields = result["extracted_fields"]
    order = Order(
        order_no=f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{msg.id}",
        status="pending_review",
        customer_name=fields.get("customer_name"),
        customer_phone=fields.get("customer_phone"),
        customer_address=fields.get("customer_address"),
        quantity=fields.get("quantity"),
        unit_price=fields.get("unit_price"),
        total_amount=fields.get("total_amount"),
        region_id=fields.get("region_id"),
        source_msg_id=msg.id,
        remark=f"自动提取自消息 #{msg.id}"
    )
    db.add(order)
    msg.processed = 1
    db.commit()
    db.refresh(order)
    
    # 写日志
    create_order_log(db, order.id, current_user.id, None, "pending_review", "自动提取")
    
    return {
        "code": 0,
        "data": {
            "order_id": order.id,
            "order_no": order.order_no,
            "matched_rules": result["triggered_rules"],
            "extracted_fields": fields
        },
        "message": "提取成功"
    }
```

注意：文件顶部需要新增 import：
```python
from datetime import datetime
from ..models.order import Order
from ..services.extract_service import run_extraction
from ..services.order_service import create_order_log
```

### 新增批量提取端点 `POST /api/messages/batch-extract`

```python
@router.post("/batch-extract")
async def batch_extract(db, current_user):
    """批量提取所有未处理消息"""
    unprocessed = db.query(RawMessage).filter(
        RawMessage.processed == 0,
        RawMessage.text.isnot(None),
        RawMessage.text != ""
    ).all()
    
    results = {"total": len(unprocessed), "matched": 0, "created_orders": 0, "skipped": 0}
    
    for msg in unprocessed:
        result = run_extraction(db, msg)
        if result["matched"]:
            # 创建订单（复用单条提取逻辑）
            order = Order(
                order_no=f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{msg.id}",
                status="pending_review",
                source_msg_id=msg.id,
                remark=f"批量自动提取"
            )
            # 填充提取字段
            for field, value in result["extracted_fields"].items():
                if hasattr(order, field):
                    setattr(order, field, value)
            db.add(order)
            msg.processed = 1
            results["matched"] += 1
            results["created_orders"] += 1
        else:
            results["skipped"] += 1
    
    db.commit()
    
    return {
        "code": 0,
        "data": results,
        "message": f"处理 {results['total']} 条，生成 {results['created_orders']} 个订单"
    }
```

---

## 三、前端：新建规则 API `frontend/src/api/rules.js`

```javascript
import api from './index'

// 提取规则
export function getExtractRules() {
  return api.get('/api/rules/extract')
}
export function createExtractRule(data) {
  return api.post('/api/rules/extract', data)
}
export function updateExtractRule(id, data) {
  return api.put(`/api/rules/extract/${id}`, data)
}

// 分配规则
export function getAssignRules() {
  return api.get('/api/rules/assign')
}
export function createAssignRule(data) {
  return api.post('/api/rules/assign', data)
}
export function updateAssignRule(id, data) {
  return api.put(`/api/rules/assign/${id}`, data)
}
```

---

## 四、前端：新建规则配置页面 `frontend/src/views/RulesConfig.vue`

用 Element Plus 的 `el-tabs` 分两个 Tab。

### 提取规则 Tab

- `el-table` 列：名称、类型(keyword/regex/sender/group)、优先级、状态(启用/禁用)、操作(编辑)
- "新增规则"按钮 → `el-dialog` 表单：
  - 名称 (el-input)
  - 类型 (el-select: keyword/regex/sender/group)
  - 规则配置 (el-input type="textarea"，JSON 格式，rows=8，placeholder 给示例)
  - 优先级 (el-input-number)
- 编辑对话框同上，预填数据
- 状态列用 `el-switch` 控制启用/禁用

### 分配规则 Tab

- `el-table` 列：名称、类型(region/load_balance/product/custom)、优先级、状态、操作
- 新增/编辑对话框（结构同提取规则）

### 规则配置 placeholder 示例

提取规则类型为 `keyword` 时 placeholder：
```json
{"keywords": ["下单", "订购", "来货"]}
```

提取规则类型为 `regex` 时 placeholder：
```json
{"pattern": "[¥￥](\\d+(?:\\.\\d{1,2})?)", "field_mapping": {"total_amount": 1}}
```

---

## 五、前端：路由 + 菜单 + 消息页增强

### 5.1 路由 (`frontend/src/router/index.js`)

在 children 数组中新增：
```javascript
{
  path: 'rules',
  name: 'RulesConfig',
  component: () => import('../views/RulesConfig.vue'),
  meta: { roles: ['admin'] }
}
```

### 5.2 侧边栏菜单 (`frontend/src/components/AppLayout.vue`)

在区域管理菜单项之前新增：
```html
<el-menu-item v-if="isAdmin" index="/rules">
  <el-icon><Setting /></el-icon>
  <template #title>规则配置</template>
</el-menu-item>
```

`Setting` 图标已在 `@element-plus/icons-vue` 中，script 中补充 import：
```javascript
import { ..., Setting } from '@element-plus/icons-vue'
```

### 5.3 消息管理页 (`frontend/src/views/MessageList.vue`)

在 "导入消息" 按钮旁边新增"批量提取"按钮：
```html
<el-button type="warning" @click="handleBatchExtract" :loading="batchExtracting">
  批量提取
</el-button>
```

并新增函数：
```javascript
import { batchExtract } from '../api/messages'  // 需先在 messages.js 中新增

const batchExtracting = ref(false)

const handleBatchExtract = async () => {
  try {
    await ElMessageBox.confirm('将对所有未处理消息执行提取，确定继续？', '确认批量提取')
  } catch { return }
  
  batchExtracting.value = true
  try {
    const res = await batchExtract()
    ElMessage.success(`处理 ${res.data.total} 条，生成 ${res.data.created_orders} 个订单`)
    fetchMessages()
  } catch (error) { /* 拦截器已处理 */ }
  finally { batchExtracting.value = false }
}
```

---

## 六、前端：`frontend/src/api/messages.js` 新增

```javascript
export function batchExtract() {
  return api.post('/api/messages/batch-extract')
}
```

---

## 七、涉及文件清单

| 操作 | 文件 | 说明 |
|------|------|------|
| **新建** | `backend/app/services/extract_service.py` | 提取引擎 |
| **修改** | `backend/app/api/messages.py` | 替换 extract 占位符 + 新增 batch-extract |
| **新建** | `frontend/src/api/rules.js` | 规则 API 封装 |
| **新建** | `frontend/src/views/RulesConfig.vue` | 规则配置页面 |
| **修改** | `frontend/src/router/index.js` | 新增 /rules 路由 (admin) |
| **修改** | `frontend/src/components/AppLayout.vue` | 新增"规则配置"菜单项 |
| **修改** | `frontend/src/api/messages.js` | 新增 batchExtract |
| **修改** | `frontend/src/views/MessageList.vue` | 新增"批量提取"按钮 |
| **不改** | `backend/app/api/rules.py` | 规则 CRUD API 已完成 |
| **不改** | 数据库表结构 | — |

---

## 八、验证步骤

### 1. 后端验证

```powershell
$token = (Invoke-RestMethod -Uri http://localhost:8080/api/auth/login -Method POST -Body '{"username":"admin","password":"admin123"}' -ContentType "application/json").data.token
$headers = @{Authorization="Bearer $token"}

# 1. 查看预置规则
Invoke-RestMethod -Uri http://localhost:8080/api/rules/extract -Headers $headers
# 预期：返回 2 条种子规则

# 2. 单条提取（假设有已导入的消息）
Invoke-RestMethod -Uri http://localhost:8080/api/messages/1/extract -Method POST -Headers $headers
# 如果消息包含"下单"等关键词 → 返回 order_id
# 如果不包含 → 返回 "no rule matched"

# 3. 批量提取
Invoke-RestMethod -Uri http://localhost:8080/api/messages/batch-extract -Method POST -Headers $headers
# 预期：返回处理统计
```

### 2. 前端验证

```bash
cd frontend && npm run build
```
访问 `http://localhost:8080` → admin 登录：
- 侧边栏出现"规则配置"（仅 admin 可见）
- 规则配置页 → 提取规则 Tab → 看到 2 条预置规则
- 可新增/编辑规则
- 消息管理页 → 出现"批量提取"按钮

### 3. 端到端验证

1. 前端导入一条包含"下单"关键词的消息
2. 点击"批量提取" → 生成订单
3. reviewer 登录 → 待审核列表看到新订单

---

## 九、注意事项

- **不要修改** `backend/app/api/rules.py`（规则 CRUD 已完成）
- **不要修改** 数据库表结构
- **不要回退** Sprint 1 的消息导入代码
- **不要修改** `frontend/src/api/index.js` 拦截器
- `field_mapping` 是开放 JSON，提取引擎只负责把匹配到的值塞进对应字段名，不做字段名校验
- 预置种子规则只在首次创建（表为空时），避免重复插入
- 写完 `cd frontend && npm run build`
