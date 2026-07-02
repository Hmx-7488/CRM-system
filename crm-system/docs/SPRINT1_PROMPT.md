# Sprint 1：消息入库 — 将 JSONL 消息导入 CRM 数据库

> 项目进度见 `docs/PROGRESS.md`，开发计划见 `docs/DEVELOPMENT_PLAN.md`

## 当前状态

- CRM 系统前后端数据库全链路已打通（FastAPI :8080 统一端口）
- `raw_messages` 表已建好，但目前是空的 — 没有任何数据导入途径
- 消息拉取模块 (`telegram-bot-demo/`) 产出的 JSONL 文件无法进入 CRM

## 本次任务

实现 JSONL 文件上传 → 解析 → 去重 → 入库的完整链路。

---

## 一、JSONL 格式说明

消息拉取模块有两个脚本，产出的 JSONL 格式**不同**，导入服务必须同时兼容：

### 格式 A：dump_messages.py（Telethon 历史消息）

```json
{
  "id": 123,
  "date": "2026-06-30T12:00:00+00:00",
  "text": "老板，来两箱苹果",
  "sender": {"id": 456, "first_name": "张三", "last_name": null, "username": "zhangsan"},
  "chat_id": -1001234567890,
  "is_reply": false
}
```

### 格式 B：live_capture.py（Bot API 实时消息）

```json
{
  "message_id": 456,
  "date": "2026-06-30T12:01:00+00:00",
  "text": "老板，来两箱苹果",
  "from_user": {"id": 789, "first_name": "张三", "last_name": null, "username": "zhangsan", "is_bot": false},
  "chat_id": -1001234567890,
  "chat_title": "海绵蟹的测试群组",
  "chat_type": "supergroup"
}
```

### 字段映射到 raw_messages 表

| raw_messages 列 | 格式 A 来源 | 格式 B 来源 | 备注 |
|----------------|------------|------------|------|
| `group_name` | ❌ 无此字段 | `chat_title` | 格式 A 缺 group_name 时填入 `"chat_" + chat_id` |
| `group_id` | `chat_id` | `chat_id` | |
| `message_id` | `id` | `message_id` | |
| `sender_id` | `sender.id` | `from_user.id` | |
| `sender_name` | `sender.first_name`（拼接 last_name） | `from_user.first_name`（拼接 last_name） | 格式：`"first_name last_name"`（strip） |
| `text` | `text` | `text` | None 时存空字符串 |
| `raw_json` | 整条 JSON 记录 | 整条 JSON 记录 | 原始数据完整保留 |
| `source` | `"history"` | `"live"` | 由导入时参数指定 |
| `received_at` | `date` | `date` | ISO 8601 字符串转 datetime |
| `processed` | 0 | 0 | 默认未处理 |

格式自动检测逻辑：
- 如果 JSON 对象有 `from_user` 字段 → 格式 B
- 如果 JSON 对象有 `sender` 字段 → 格式 A
- 其他 → 跳过并记录 warning

---

## 二、后端：新建 `backend/app/services/import_service.py`

### 函数签名

```python
def import_messages(db: Session, jsonl_content: str, source: str = "history") -> dict:
    """
    解析 JSONL 内容并导入 raw_messages 表。
    
    参数:
        db: SQLAlchemy 数据库 session
        jsonl_content: JSONL 文件的完整文本内容
        source: 'history' 或 'live'
    
    返回:
        {"imported": N, "skipped": M, "errors": K, "total": N+M+K}
    """
```

### 核心逻辑

1. 按行分割 `jsonl_content`
2. 逐行 `json.loads()` 解析
3. 自动检测格式 A / B，按上表映射字段
4. 去重：以 `(group_id, message_id)` 为联合唯一键
   - 查询数据库中是否已存在相同 `group_id + message_id` 的记录
   - 已存在 → skipped += 1，跳过
5. 不存在 → 创建 `RawMessage` 对象 → `db.add()`
6. 每 100 条 `db.flush()`（避免内存膨胀）
7. 最后 `db.commit()`
8. 返回统计结果

### 错误处理

- JSON 解析失败 → errors += 1，记录日志，继续处理下一行
- 字段映射异常（如 sender 为 null）→ 对应列填 None 或默认值，不中断
- 数据库写入失败 → rollback 当前批次，返回错误信息

---

## 三、后端：修改 `backend/app/api/messages.py`

### 新增端点

```python
from pydantic import BaseModel
from ..services.import_service import import_messages

class ImportRequest(BaseModel):
    content: str        # JSONL 文件内容
    source: str = "history"  # 'history' 或 'live'

@router.post("/import")
async def import_messages_api(
    req: ImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导入 JSONL 消息"""
    result = import_messages(db, req.content, req.source)
    return {
        "code": 0,
        "data": result,
        "message": f"导入 {result['imported']} 条，跳过 {result['skipped']} 条"
    }
```

注意：`content` 字段接收 JSONL 文件的**完整文本**，由前端读取文件后传入。

---

## 四、前端：修改 `frontend/src/api/messages.js`

新增函数：

```javascript
export function importMessages(content, source = 'history') {
  return api.post('/api/messages/import', { content, source })
}
```

---

## 五、前端：修改 `frontend/src/views/MessageList.vue`

### 在 card-header 区域新增"导入消息"按钮

在 `<el-button type="primary" @click="fetchMessages">刷新</el-button>` 后面增加：

```html
<el-button type="success" @click="showImportDialog = true">导入消息</el-button>
```

### 新增导入对话框

```html
<!-- 放在 </el-card> 之前 -->
<el-dialog v-model="showImportDialog" title="导入消息" width="500px">
  <el-form>
    <el-form-item label="消息来源">
      <el-radio-group v-model="importSource">
        <el-radio value="history">历史消息 (dump)</el-radio>
        <el-radio value="live">实时捕获 (live)</el-radio>
      </el-radio-group>
    </el-form-item>
    <el-form-item label="选择文件">
      <input
        type="file"
        accept=".jsonl,.json"
        @change="handleFileSelect"
        ref="fileInput"
      />
    </el-form-item>
  </el-form>
  <div v-if="importResult" style="margin-top: 12px;">
    <el-alert
      :title="`导入 ${importResult.imported} 条，跳过 ${importResult.skipped} 条${importResult.errors ? '，失败 ' + importResult.errors + ' 条' : ''}`"
      :type="importResult.errors > 0 ? 'warning' : 'success'"
      :closable="false"
    />
  </div>
  <template #footer>
    <el-button @click="showImportDialog = false">取消</el-button>
    <el-button
      type="primary"
      @click="handleImport"
      :disabled="!selectedFile"
      :loading="importing"
    >
      开始导入
    </el-button>
  </template>
</el-dialog>
```

### 新增 script 逻辑

```javascript
import { importMessages } from '../api/messages'

const showImportDialog = ref(false)
const importSource = ref('history')
const selectedFile = ref(null)
const importing = ref(false)
const importResult = ref(null)
const fileInput = ref(null)

const handleFileSelect = (event) => {
  selectedFile.value = event.target.files[0]
  importResult.value = null
}

const handleImport = async () => {
  if (!selectedFile.value) return
  
  importing.value = true
  try {
    const content = await selectedFile.value.text()
    const res = await importMessages(content, importSource.value)
    importResult.value = res.data
    ElMessage.success(`导入完成：${res.data.imported} 条`)
    // 刷新消息列表
    fetchMessages()
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    importing.value = false
  }
}
```

**注意**：不要改动现有表格、分页、筛选逻辑，只在已有基础上增加导入功能。

---

## 六、涉及文件清单

| 操作 | 文件 | 说明 |
|------|------|------|
| **新建** | `backend/app/services/import_service.py` | JSONL 解析 + 映射 + 去重 + 入库 |
| **新建** | `backend/app/services/__init__.py` | 如果不存在则创建空文件 |
| **修改** | `backend/app/api/messages.py` | 新增 `POST /api/messages/import` 端点 |
| **修改** | `frontend/src/api/messages.js` | 新增 `importMessages()` 函数 |
| **修改** | `frontend/src/views/MessageList.vue` | 新增导入按钮 + 对话框 + 逻辑 |
| **不改** | 其他所有文件 | — |

---

## 七、验证步骤（完成后执行）

### 1. 准备测试数据

创建测试文件 `test_import.jsonl`（两条格式 A + 一条格式 B）：

```jsonl
{"id":1,"date":"2026-07-01T10:00:00+00:00","text":"老板，来两箱苹果","sender":{"id":100,"first_name":"张三","last_name":null,"username":"zhangsan"},"chat_id":-100111}
{"id":2,"date":"2026-07-01T10:01:00+00:00","text":"橘子多少钱一斤","sender":{"id":200,"first_name":"李四","last_name":null},"chat_id":-100111}
{"message_id":3,"date":"2026-07-01T10:02:00+00:00","text":"今天有什么新鲜货","from_user":{"id":300,"first_name":"王五","last_name":null,"is_bot":false},"chat_id":-100111,"chat_title":"测试群"}
```

### 2. 后端 curl 验证

```powershell
# 登录
$body = '{"username":"admin","password":"admin123"}'
$res = Invoke-RestMethod -Uri http://localhost:8080/api/auth/login -Method POST -Body $body -ContentType "application/json"
$token = $res.data.token
$headers = @{Authorization="Bearer $token"}

# 导入
$jsonl = Get-Content test_import.jsonl -Raw
$importBody = @{content=$jsonl; source="history"} | ConvertTo-Json
$importRes = Invoke-RestMethod -Uri http://localhost:8080/api/messages/import -Method POST -Body $importBody -Headers $headers -ContentType "application/json"
$importRes
# 预期：{"code":0,"data":{"imported":3,"skipped":0,"errors":0,"total":3},"message":"..."}

# 验证消息列表
$msgRes = Invoke-RestMethod -Uri "http://localhost:8080/api/messages/?page=1&size=20" -Headers $headers
$msgRes.data.items.Count
# 预期：3
$msgRes.data.items[0].sender_name
# 预期有值（非空）

# 重复导入（验证去重）
$importRes2 = Invoke-RestMethod -Uri http://localhost:8080/api/messages/import -Method POST -Body $importBody -Headers $headers -ContentType "application/json"
$importRes2.data.skipped
# 预期：3（全部跳过）
```

### 3. 前端验证

```bash
cd frontend && npm run build
```
访问 `http://localhost:8080` → 登录 → 消息管理 → 点击"导入消息" → 选择 test_import.jsonl → 开始导入 → 表格出现 3 条消息。

---

## 八、注意事项

- **不要修改** `D:\develop\job\telegram-bot\telegram-bot-demo` 下任何文件
- **不要修改** 数据库表结构
- **不要回退** 已有代码改动（特别是 api/index.js 的 baseURL、SPAMiddleware、尾部斜杠等）
- **不要修改** `frontend/src/api/index.js` 拦截器逻辑
- 导入 API 接收的是 JSONL 文件的**文本内容**，不是文件上传（multipart），前端用 `FileReader` 或 `file.text()` 读取后通过 JSON body 传递
- 去重键是 `(group_id, message_id)`，不是数据库自增 id
- 如果 `__init__.py` 不存在，创建空文件即可
- 写完后 `cd frontend && npm run build`
