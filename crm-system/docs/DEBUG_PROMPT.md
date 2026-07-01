# 任务：修复 401 未授权错误 (当前架构下)

> 状态: 🔴 待修复  
> 最后更新: 2026-07-01 15:30  
> 当前进度见 [PROGRESS.md](PROGRESS.md)

## 问题现象

登录成功后，点击侧边栏任意菜单项（订单管理、消息管理等），部分 API 请求返回 401，触发前端拦截器跳回 `/login`。

浏览器 Console 报错：

```
messages.js:4  GET http://localhost:8080/api/messages/?page=1&size=20 401 (Unauthorized)
```

## 当前部署架构 (已变更)

```
浏览器 ──→  localhost:8080 (FastAPI)
               │
               ├── /api/*          → FastAPI 路由
               ├── /assets/*       → StaticFiles (前端静态资源)
               └── 其他路径         → SPAMiddleware → index.html (Vue SPA)
```

**关键变更**：不再使用 Vite dev server (`:5173`) + proxy 代理。前端 build 产物 (`frontend/dist/`) 直接挂载在 FastAPI 上，统一从 `:8080` 端口提供。

因此 `localhost:8080` 的请求 URL 是正确的，不是 bug — 请求就应该发到 8080。

## 项目路径

D:\develop\job\telegram-bot\crm-system

## 环境

- 服务: localhost:8080 (FastAPI + SPA 静态文件)
- 数据库: MySQL (root/123456, 库名 crm)
- 登录凭据: admin / admin123
- 前端代码修改后需重建: `cd frontend && npm run build`

## 已完成的改动 (勿回退)

1. `backend/app/main.py`: 新增 SPAMiddleware + StaticFiles 挂载 `/assets`
2. `frontend/src/api/index.js`: baseURL 设为 `''`，用 setApiRouter() 延迟注入
3. `frontend/src/store/auth.js`: 移除 router 直接导入，改用 setStoreRouter()
4. `frontend/src/api/*.js`: 所有列表端点加尾部斜杠
5. `backend/app/utils/deps.py`: HTTPBearer(auto_error=False)

## 排查步骤 (基于当前架构)

### 第一步：确认 dist 是最新构建

```powershell
# 检查 dist 文件时间是否晚于源码修改时间
Get-ChildItem D:\develop\job\telegram-bot\crm-system\frontend\dist -Recurse | Sort-Object LastWriteTime -Desc | Select -First 5
Get-ChildItem D:\develop\job\telegram-bot\crm-system\frontend\src\api\index.js | Select LastWriteTime

# 如果 dist 比源码旧，重建
cd D:\develop\job\telegram-bot\crm-system\frontend
npm run build
```

### 第二步：验证后端 /api/auth/login 正常

```powershell
$body = '{"username":"admin","password":"admin123"}'
$res = Invoke-RestMethod -Uri http://localhost:8080/api/auth/login -Method POST -Body $body -ContentType "application/json"
$res.data.token  # 应有 JWT 字符串
```

### 第三步：验证带 Token 的请求

```powershell
$token = $res.data.token
$headers = @{Authorization="Bearer $token"}

# 测试仪表盘 (如果这个也 401，说明 token 本身有问题)
Invoke-RestMethod -Uri http://localhost:8080/api/dashboard/summary -Headers $headers

# 测试消息列表
Invoke-RestMethod -Uri "http://localhost:8080/api/messages/?page=1&size=20" -Headers $headers
```

如果后端 curl 测试全部正常但浏览器端 401，问题在前端。

### 第四步：浏览器端排查

1. 打开 `http://localhost:8080`（注意是 8080）
2. F12 → Application → Local Storage → `http://localhost:8080`
   - 清空所有条目（如果有残留的旧 token）
3. F12 → Network → 勾选 "Preserve log"
4. 登录 admin / admin123
5. 观察 Network：
   - POST `/api/auth/login` → 200 → Response 含 token
   - GET `/api/auth/me` → 200 → Request Headers 有 `Authorization: Bearer ...`
   - GET `/api/dashboard/summary` → 200
6. 点击"订单管理"或"消息管理"
7. 观察对应的 GET 请求：
   - Request Headers 中 `Authorization` 是否存在？
   - 如果不存在，在 Console 执行：
     ```javascript
     JSON.parse(localStorage.getItem('token'))
     ```
     检查 token 值是否为空/null

### 第五步：检查前端请求拦截器

在浏览器 Console 执行以下代码拦截所有 XHR 请求：

```javascript
const origOpen = XMLHttpRequest.prototype.open
XMLHttpRequest.prototype.open = function(method, url) {
  console.log('[XHR]', method, url, 'auth:', this._authHeader)
  return origOpen.apply(this, arguments)
}
```

然后点击菜单项，观察 [XHR] 输出 — 确认 URL 和 Authorization 状态。

### 第六步：检查 Pinia Store 状态

```javascript
// 在浏览器 Console 中
// 查看 token 是否存在
const pinia = document.querySelector('#app').__vue_app__.config.globalProperties.$pinia
const authStore = pinia._s.get('auth')
console.log('token:', authStore.token?.substring(0, 30))
console.log('user:', authStore.user)
console.log('isLoggedIn:', authStore.isLoggedIn)
```

## 可能原因与修复方向

### 可能性 1：dist 未包含最新代码
前端源码改了拦截器逻辑但没 `npm run build` → 浏览器加载的是旧版本 JS。
**修复**：`cd frontend && npm run build`，重启后端。

### 可能性 2：Token 过期
JWT 默认 24 小时过期。如果登录后长时间未操作，token 会失效。
**验证**：重新登录后再试。
**修复**：在 `frontend/src/api/index.js` 响应拦截器中，401 时不要立即清 token 跳转，先尝试 `/api/auth/me` 刷新验证。

### 可能性 3：SPAMiddleware 影响了 API 路由
SPAMiddleware 是 `BaseHTTPMiddleware`，它在所有路由之后执行。如果中间件捕获了 API 的 401 响应并做了不正确的处理……
**验证**：查看 `backend/app/main.py` 中 SPAMiddleware 只拦截 404 + GET + 非 `/api/`，不会影响 API 的 401。
**排除此项**。

### 可能性 4：CORS 预检请求干扰
虽然同源请求不需要 CORS，但如果 axios 某些配置触发了 OPTIONS 预检……
**验证**：Network 中查看是否有 OPTIONS 请求。
**排除可能性低**。

### 可能性 5：路由守卫与拦截器竞态
`router/index.js` 守卫中调用 `fetchMe()` 失败 → 拦截器清 token → 守卫看到 `!isLoggedIn` → return 不调用 next() → 页面卡住或跳转异常。
**修复方向**：在守卫的 fetchMe catch 块中，确保调用 `next('/login')` 作为兜底，不要仅靠拦截器跳转。

当前代码：
```javascript
if (!authStore.user) {
    try {
      await authStore.fetchMe()
    } catch (error) {
      if (!authStore.isLoggedIn) {
        return  // ← 这里 return 了但没调 next()
      }
      next('/login')
      return
    }
  }
```

当拦截器已清 token 并 push('/login') 后，守卫中的 `return` 可能会有竞态。建议改为：
```javascript
} catch (error) {
  next('/login')
  return
}
```

## 验证标准

修复后：
1. 打开 `http://localhost:8080`，清空 localStorage
2. 登录 admin/admin123
3. 依次点击：订单管理、消息管理、用户管理、产品管理、区域管理
4. 每个页面正常加载数据，不再跳回登录页
5. Console 中无 401/403 错误
6. Network 中所有 API 请求的 Request Headers 都包含 `Authorization: Bearer ...`
