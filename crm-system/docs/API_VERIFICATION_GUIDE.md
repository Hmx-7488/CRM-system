# 后端 API 验证 — 详细操作手册

> 适用对象：0 基础用户，不需要任何编程知识
> 前提：MySQL 和 FastAPI 后端已在运行
> 操作环境：Windows PowerShell（系统自带，无需安装）

---

## 第零步：确认后端正在运行

打开一个新的 PowerShell 窗口（Win+R → 输入 powershell → 回车），执行：

`powershell
Invoke-RestMethod -Uri http://localhost:8080/health
`

**预期看到**：返回一串 JSON，包含 {"status":"ok"} 或类似内容。

如果提示 Unable to connect 或 Connection refused，说明后端没启动。请先启动：
`powershell
cd D:\develop\job\telegram-bot\crm-system\backend
uvicorn app.main:app --reload --port 8080
`

---

## 第一步：登录获取 Token

Token 是你操作 API 的"通行证"。每次测试前都要先登录拿到 token。

**执行以下命令**（逐条复制粘贴到 PowerShell，按回车）：

`powershell
 = '{"username":"admin","password":"admin123"}'
`

这条命令把账号密码存到变量 $body 里，还没有发送。继续：

`powershell
 = Invoke-RestMethod -Uri http://localhost:8080/api/auth/login -Method POST -Body  -ContentType "application/json"
`

这条命令向服务器发送登录请求。$res 是服务器的回复。

`powershell

`

**预期看到**：类似这样的输出
`
code data                 message
---- ----                 -------
   0 @{token=eyJhbG...; user=} ok
`

提取 token，存到 $token 变量：

`powershell
 = .data.token
`

查看 token 是否正确获取：
`powershell

`

**预期**：一长串英文数字混合的字符串，以 eyJ 开头。如果不是，说明前几步有问题。

最后创建请求头（后续每个 API 请求都要带）：
`powershell
 = @{Authorization="Bearer "}
`

验证 headers 正确：
`powershell

`

**预期**：显示 Authorization 键和 Bearer eyJ... 的值。

---

## 第二步：验证消息导入

### 2.1 查看当前消息列表

`powershell
Invoke-RestMethod -Uri "http://localhost:8080/api/messages/?page=1&size=20" -Headers 
`

**预期**：返回 JSON，data.items 是一个数组，data.total 是总数。
- 如果还没导入过数据：data.total = 0，data.items = []
- 如果已经导入过：能看到之前的消息记录

### 2.2 导入测试数据

准备 JSONL 内容（这是模拟 test_import.jsonl 的内容）：

`powershell
 = @'
{"id":1,"date":"2026-07-01T10:00:00+00:00","text":"老板，来两箱苹果","sender":{"id":100,"first_name":"张三","last_name":null,"username":"zhangsan"},"chat_id":-100111}
{"id":2,"date":"2026-07-01T10:01:00+00:00","text":"橘子多少钱一斤","sender":{"id":200,"first_name":"李四","last_name":null},"chat_id":-100111}
{"message_id":3,"date":"2026-07-01T10:02:00+00:00","text":"今天有什么新鲜货","from_user":{"id":300,"first_name":"王五","last_name":null,"is_bot":false},"chat_id":-100111,"chat_title":"测试群"}
'@
`

构造导入请求体：

`powershell
 = @{content=; source="history"} | ConvertTo-Json
`

发送导入请求：

`powershell
 = Invoke-RestMethod -Uri http://localhost:8080/api/messages/import -Method POST -Body  -Headers  -ContentType "application/json"
`

查看结果：
`powershell

`

**预期**：data.imported = 3，data.skipped = 0，data.errors = 0
`json
{
  "code": 0,
  "data": {
    "imported": 3,
    "skipped": 0,
    "errors": 0,
    "total": 3
  },
  "message": "导入 3 条，跳过 0 条"
}
`

**如果 imported=0 且 skipped=3**：说明之前已经导入过了，去重生效。这是正常的也是正确的行为。

### 2.3 验证消息列表（导入后）

`powershell
 = Invoke-RestMethod -Uri "http://localhost:8080/api/messages/?page=1&size=20" -Headers 
.data.total
`

**预期**：返回 >= 3

查看第一条消息的发送者名称：
`powershell
.data.items[0].sender_name
`

**预期**：非空字符串（张三 / 李四 / 王五 之一）

查看全部：
`powershell
.data.items | Format-Table id, sender_name, text, source, processed
`

**预期**：3 条消息，sender_name 非空，text 为中文，source=history，processed=0

---

## 第三步：验证提取规则

### 3.1 查看提取规则

首次访问时应自动创建 2 条种子规则：

`powershell
 = Invoke-RestMethod -Uri http://localhost:8080/api/rules/extract -Headers 
.data | Format-Table id, name, rule_type, priority, status
`

**预期**：至少显示 2 条规则（订单触发词 / 金额提取）

### 3.2 新增一条 keyword 规则

创建一条匹配"苹果"和"橘子"的规则：

`powershell
 = @{
    name = "测试触发词"
    rule_type = "keyword"
    rule_config = @{keywords = @("苹果","橘子")} | ConvertTo-Json -Compress
    priority = 8
} | ConvertTo-Json -Depth 3
`

注意：
ule_config 必须是 JSON 字符串格式，不是对象。

`powershell
 = Invoke-RestMethod -Uri http://localhost:8080/api/rules/extract -Method POST -Body  -Headers  -ContentType "application/json"

`

**预期**：返回新规则的 id（数字）和 status=1

### 3.3 查看分配规则

`powershell
Invoke-RestMethod -Uri http://localhost:8080/api/rules/assign -Headers 
`

**预期**：返回规则列表（可能为空或含种子规则）

---

## 第四步：验证消息提取

### 4.1 单条消息提取

对第 1 条消息（"老板，来两箱苹果"）执行提取：

`powershell
 = Invoke-RestMethod -Uri http://localhost:8080/api/messages/1/extract -Method POST -Headers 

`

**预期**（取决于"测试触发词"是否启用）：

**场景 A** — 规则匹配成功：
`json
{
  "code": 0,
  "data": {
    "order_id": 5,
    "order_no": "ORD20260701...",
    "matched_rules": ["测试触发词"],
    "extracted_fields": {}
  },
  "message": "提取成功"
}
`
→ order_id 是一个数字，说明订单已创建。去浏览器刷新订单管理页面能看到新订单。

**场景 B** — 无匹配规则：
`json
{
  "code": 0,
  "data": {
    "matched": false,
    "reason": "no rule matched"
  },
  "message": "未匹配到任何规则"
}
`
→ 说明没有启用的规则能匹配这条消息。去规则配置页面检查"测试触发词"是否 status=1。

### 4.2 批量提取

处理所有未处理消息：

`powershell
 = Invoke-RestMethod -Uri http://localhost:8080/api/messages/batch-extract -Method POST -Headers 

`

**预期**：
`json
{
  "code": 0,
  "data": {
    "total": 2,
    "matched": 2,
    "created_orders": 2,
    "skipped": 0
  },
  "message": "处理 2 条，生成 2 个订单"
}
`

- 	otal：未处理的消息总数
- matched：命中规则的消息数
- created_orders：实际生成的订单数
- skipped：未命中的消息数

---

## 第五步：验证订单

### 5.1 查看所有订单

`powershell
 = Invoke-RestMethod -Uri "http://localhost:8080/api/orders/?page=1&size=20" -Headers 
.data.items | Format-Table id, order_no, status, customer_name, product_name, region_name, assigned_user
`

**预期**：看到提取生成的订单，status=pending_review，source_msg_id 不为空。

### 5.2 查看仪表盘统计

`powershell
Invoke-RestMethod -Uri http://localhost:8080/api/dashboard/summary -Headers 
`

**预期**：total_orders、pending_review 等统计数字正确。

---

## 第六步：端到端流程（完整验证）

### 6.1 admin 创建手动订单

`powershell
 = '{"order_no":"MANUAL-001","region_id":1,"customer_name":"手动客户","product_id":1,"quantity":10,"unit_price":50,"total_amount":500}'
Invoke-RestMethod -Uri http://localhost:8080/api/orders/ -Method POST -Body  -Headers  -ContentType "application/json"
`

记下返回的 order id。

### 6.2 reviewer 登录

`powershell
 = '{"username":"review","password":"review123"}'
 = Invoke-RestMethod -Uri http://localhost:8080/api/auth/login -Method POST -Body  -ContentType "application/json"
 = .data.token
 = @{Authorization="Bearer "}
`

### 6.3 reviewer 审核通过

替换 <ORDER_ID> 为实际订单 ID：

`powershell
 = '{"action":"approve"}'
Invoke-RestMethod -Uri "http://localhost:8080/api/orders/<ORDER_ID>/review" -Method POST -Body  -Headers  -ContentType "application/json"
`

**预期**：status 变为 assigned，reviewer_id 不为空

### 6.4 admin 分配订单

切换回 admin token：

`powershell
 = '{"assigned_to":3}'
Invoke-RestMethod -Uri "http://localhost:8080/api/orders/<ORDER_ID>/assign" -Method POST -Body  -Headers  -ContentType "application/json"
`

**预期**：status=assigned，assigned_to=3（agent1 的 id）

### 6.5 agent1 登录查看

`powershell
 = '{"username":"agent1","password":"agent123"}'
 = Invoke-RestMethod -Uri http://localhost:8080/api/auth/login -Method POST -Body  -ContentType "application/json"
 = .data.token
 = @{Authorization="Bearer "}
`

查看订单列表：
`powershell
Invoke-RestMethod -Uri "http://localhost:8080/api/orders/?page=1&size=20" -Headers 
`

**预期**：看到分配给自己的订单。

### 6.6 agent1 更新订单状态

`powershell
 = '{"status":"processing"}'
Invoke-RestMethod -Uri "http://localhost:8080/api/orders/<ORDER_ID>/status" -Method POST -Body  -Headers  -ContentType "application/json"
`

**预期**：status 变为 processing。

继续改为已完成：

`powershell
 = '{"status":"completed"}'
Invoke-RestMethod -Uri "http://localhost:8080/api/orders/<ORDER_ID>/status" -Method POST -Body  -Headers  -ContentType "application/json"
`

**预期**：status 变为 completed。

### 6.7 查看订单日志

`powershell
Invoke-RestMethod -Uri "http://localhost:8080/api/orders/<ORDER_ID>/logs" -Headers 
`

**预期**：看到多条日志（创建 → 审核 → 分配 → 处理 → 完成），每条包含 from_status、to_status、operator_name。

---

## 常见错误及处理

### 错误：The remote server returned an error: (401) Unauthorized

**原因**：token 过期或没有登录

**解决**：重新执行第一步获取 token。

### 错误：The remote server returned an error: (403) Forbidden

**原因**：当前角色的权限不够

**解决**：
- 规则 API 需要 admin 角色
- 审核 API 需要 reviewer 角色
- 分配 API 需要 admin 或 reviewer 角色

### 错误：The remote server returned an error: (404) Not Found

**原因**：ID 不存在（消息/订单/规则已被删除或输错）

**解决**：先执行列表 API 确认正确的 ID。

### 错误：The remote server returned an error: (422) Unprocessable Entity

**原因**：请求体格式不对（JSON 字段名写错、类型不匹配）

**解决**：检查 Body 中字段名是否与 API 定义一致。

### 错误：Connection refused / Unable to connect

**原因**：后端没有在 8080 端口运行

**解决**：确认 uvicorn 在运行，看到 Uvicorn running on http://127.0.0.1:8080 字样。

---

## 快速验证脚本（一键运行）

如果你已经熟悉流程，可以复制以下全部命令一次性粘贴到 PowerShell：

`powershell
# ========== 登录 ==========
 = '{"username":"admin","password":"admin123"}'
 = Invoke-RestMethod -Uri http://localhost:8080/api/auth/login -Method POST -Body  -ContentType "application/json"
 = .data.token
 = @{Authorization="Bearer "}
Write-Host "=== Token obtained ==="

# ========== 导入消息 ==========
 = @'
{"id":1,"date":"2026-07-01T10:00:00+00:00","text":"老板，来两箱苹果","sender":{"id":100,"first_name":"张三","last_name":null,"username":"zhangsan"},"chat_id":-100111}
{"id":2,"date":"2026-07-01T10:01:00+00:00","text":"橘子多少钱一斤","sender":{"id":200,"first_name":"李四","last_name":null},"chat_id":-100111}
{"message_id":3,"date":"2026-07-01T10:02:00+00:00","text":"今天有什么新鲜货","from_user":{"id":300,"first_name":"王五","last_name":null,"is_bot":false},"chat_id":-100111,"chat_title":"测试群"}
'@
 = @{content=; source="history"} | ConvertTo-Json
 = Invoke-RestMethod -Uri http://localhost:8080/api/messages/import -Method POST -Body  -Headers  -ContentType "application/json"
Write-Host "=== Import: imported= skipped= ==="

# ========== 查看消息 ==========
 = Invoke-RestMethod -Uri "http://localhost:8080/api/messages/?page=1&size=20" -Headers 
Write-Host "=== Messages: total= ==="

# ========== 查看规则 ==========
 = Invoke-RestMethod -Uri http://localhost:8080/api/rules/extract -Headers 
Write-Host "=== Extract Rules: 0 rules ==="

# ========== 批量提取 ==========
 = Invoke-RestMethod -Uri http://localhost:8080/api/messages/batch-extract -Method POST -Headers 
Write-Host "=== Batch Extract: total= matched= orders= ==="

# ========== 查看订单 ==========
 = Invoke-RestMethod -Uri "http://localhost:8080/api/orders/?page=1&size=20" -Headers 
Write-Host "=== Orders: total= ==="

Write-Host "
=== ALL TESTS DONE ==="
`

每行 Write-Host 输出会告诉你该步骤的结果。如果全部显示合理的数字，验证通过。
