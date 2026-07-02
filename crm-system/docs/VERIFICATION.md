# Sprint 1 + Sprint 2 验收流程

> 用于验证 Claude Code 完成的 Sprint 1（消息入库）和 Sprint 2（提取引擎+规则配置页面）
> 项目路径: `D:\develop\job\telegram-bot\crm-system`

---

## 前置条件

```powershell
# 1. 确保 MySQL 运行中
# 2. 确保后端运行中
cd D:\develop\job\telegram-bot\crm-system\backend
uvicorn app.main:app --reload --port 8080

# 3. 前端已构建（如果刚改过前端代码）
cd D:\develop\job\telegram-bot\crm-system\frontend
npm run build
```

访问 `http://localhost:8080`，使用 admin / admin123 登录。

---

## 第一部分：Sprint 1 — 消息入库验收

### 验收点 1.1：前端导入按钮可见

1. 登录后点击左侧菜单「消息管理」
2. 确认页面顶部有 **「导入消息」** 和 **「批量提取」** 两个按钮
3. 确认消息表格正常显示（如有数据）

### 验收点 1.2：导入 JSONL 文件

**准备测试数据**：项目根目录已有 `test_import.jsonl`（3条测试消息）。

1. 点击「导入消息」按钮 → 弹出对话框
2. 消息来源选择「历史消息 (dump)」
3. 点击文件选择框 → 选择 `D:\develop\job\telegram-bot\crm-system\test_import.jsonl`
4. 点击「开始导入」
5. 预期结果：提示"导入完成：3 条"，页面显示绿色成功提示

### 验收点 1.3：消息列表正确显示

导入完成后消息表格应显示 3 条消息，检查以下字段：

| 字段 | 预期 | 
|------|------|
| sender_name | 张三 / 李四 / 王五（非空） |
| text | 老板，来两箱苹果 / 橘子多少钱一斤 / 今天有什么新鲜货 |
| source | history |
| processed | 否（红色标签） |

### 验收点 1.4：去重验证

1. 再次导入同一个 `test_import.jsonl` 文件
2. 预期：提示 "导入 0 条，跳过 3 条"
3. 表格中消息总数仍为 3 条

### 验收点 1.5：后端 API 直接验证（可选）

```powershell
# 获取 token
$body = '{"username":"admin","password":"admin123"}'
$res = Invoke-RestMethod -Uri http://localhost:8080/api/auth/login -Method POST -Body $body -ContentType "application/json"
$token = $res.data.token
$headers = @{Authorization="Bearer $token"}

# 查看消息列表
Invoke-RestMethod -Uri "http://localhost:8080/api/messages/?page=1&size=20" -Headers $headers
# 预期：data.items 长度 >= 3，sender_name 非空

# 查看未处理消息
Invoke-RestMethod -Uri "http://localhost:8080/api/messages/?processed=0" -Headers $headers
# 预期：仅返回未处理的消息
```

---

## 第二部分：Sprint 2 — 提取引擎 + 规则配置验收

### 验收点 2.1：规则配置页面可访问

1. 以 **admin** 登录
2. 确认左侧菜单出现 **「规则配置」** 菜单项（带设置齿轮图标）
3. 点击进入 → 页面有两个 Tab：「提取规则」「分配规则」

### 验收点 2.2：种子规则已创建

首次访问规则配置页面时，提取规则 Tab 应自动出现 2 条预置规则：

| 规则名称 | 类型 | 优先级 |
|----------|------|--------|
| 订单触发词 | keyword | 10 |
| 金额提取 | regex | 5 |

### 验收点 2.3：新增/编辑/启禁用规则

**新增一条 keyword 规则**：
1. 提取规则 Tab → 点击「新增规则」
2. 名称输入：`测试触发词`
3. 类型选 keyword
4. 规则配置输入：`{"keywords": ["苹果", "橘子"]}`
5. 优先级：8
6. 点击保存 → 列表出现新规则

**编辑规则**：
1. 点击「测试触发词」的编辑按钮
2. 修改优先级为 9
3. 保存 → 验证优先级已更新

**启用/禁用**：
1. 点击开关关闭某条规则
2. 刷新页面 → 确认状态变更持久化

### 验收点 2.4：单条消息提取（keyword 匹配）

1. 切换到「消息管理」页面
2. 确保已导入 test_import.jsonl（第 1 条消息包含"苹果"，第 2 条包含"橘子"）
3. 之前创建的"测试触发词"（keywords: ["苹果", "橘子"]）应匹配这些消息
4. 通过批量提取方式触发（见 2.5）

### 验收点 2.5：批量提取

1. 消息管理页 → 点击「批量提取」按钮
2. 确认对话框 → 点击确定
3. 预期结果：
   - 如果有匹配规则的消息 → 提示"处理 X 条，生成 Y 个订单"
   - 无匹配的消息 → 提示"处理 X 条，生成 0 个订单"
4. 切换到订单管理页面 → 确认新生成的订单状态为 `pending_review`

### 验收点 2.6：端到端（导入→提取→审核→分配→处理）

```
1. [admin] 导入 test_import.jsonl → 3 条消息入库
2. [admin] 消息管理 → 批量提取 → 生成订单
3. [admin] 切换到订单管理 → 看到新订单（状态 pending_review）
4. [reviewer] 登录（review / review123）→ 待审核列表看到订单 → 审核通过
5. [admin] 登录 → 订单管理 → 分配订单给 agent1
6. [agent1] 登录（agent1 / agent123）→ 订单列表看到该订单 → 更新状态为"处理中"→"已完成"
```

### 验收点 2.7：规则 API 直接验证（可选）

```powershell
$token = (Invoke-RestMethod -Uri http://localhost:8080/api/auth/login -Method POST -Body '{"username":"admin","password":"admin123"}' -ContentType "application/json").data.token
$headers = @{Authorization="Bearer $token"}

# 查看提取规则
Invoke-RestMethod -Uri http://localhost:8080/api/rules/extract -Headers $headers

# 查看分配规则
Invoke-RestMethod -Uri http://localhost:8080/api/rules/assign -Headers $headers

# 单条提取
Invoke-RestMethod -Uri http://localhost:8080/api/messages/1/extract -Method POST -Headers $headers

# 批量提取
Invoke-RestMethod -Uri http://localhost:8080/api/messages/batch-extract -Method POST -Headers $headers
```

---

## 第三部分：异常场景验收

### 验收点 3.1：空文件导入
1. 创建一个空 JSONL 文件（0 字节）
2. 导入 → 预期：提示导入 0 条，不报错

### 验收点 3.2：格式错误的 JSONL
1. 创建文件内容为 `这不是JSON`
2. 导入 → 预期：错误数 > 0，不崩溃

### 验收点 3.3：权限验证
1. 以 **agent** 登录（agent1 / agent123）
2. 确认左侧菜单**无**「规则配置」（admin only）
3. 尝试直接访问 `http://localhost:8080/rules` → 应被路由守卫拦截

### 验收点 3.4：前端构建产物存在
```powershell
Get-ChildItem "D:\develop\job\telegram-bot\crm-system\frontend\dist\assets" | Where-Object { $_.Name -like "*RulesConfig*" }
# 预期：存在 RulesConfig-*.js 文件
```

---

## 验收结论

| 验收点 | 状态 | 备注 |
|--------|------|------|
| 1.1 前端导入按钮 | ⬜ | |
| 1.2 导入 JSONL | ⬜ | |
| 1.3 消息列表显示 | ⬜ | |
| 1.4 去重验证 | ⬜ | |
| 1.5 API 验证 | ⬜ | |
| 2.1 规则页面可访问 | ⬜ | |
| 2.2 种子规则 | ⬜ | |
| 2.3 CRUD 规则 | ⬜ | |
| 2.4 单条提取 | ⬜ | |
| 2.5 批量提取 | ⬜ | |
| 2.6 端到端 | ⬜ | |
| 2.7 API 验证 | ⬜ | |
| 3.1 空文件 | ⬜ | |
| 3.2 格式错误 | ⬜ | |
| 3.3 权限 | ⬜ | |
| 3.4 构建产物 | ⬜ | |

**通过条件**：全部验收点标记 ✅，方可进入 Sprint 3。

---

## 常见问题排查

### 导入后消息列表为空
- 检查后端日志是否有错误
- 确认前端 build 是否最新（`npm run build`）
- 浏览器 F12 → Network → 查看 `/api/messages/` 响应

### 提取无反应（无订单生成）
- 确认提取规则已启用（status=1）
- 确认消息文本包含规则匹配的关键词
- 查看后端日志中 run_extraction 输出

### 规则页面 403
- 确认当前登录角色为 admin
- 检查 token 是否过期（重新登录）
