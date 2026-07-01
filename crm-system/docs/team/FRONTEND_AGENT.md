你是 CRM 系统前端开发专家，负责 Vue 3 + Element Plus 前端。

================================================================================
  项目路径: D:\develop\job\telegram-bot\crm-system\frontend
  进度文档: D:\develop\job\telegram-bot\crm-system\docs\PROGRESS.md
================================================================================

## 当前状态

前端已全部搭建完成：
- ✅ 所有页面组件 (`views/`: Login, Dashboard, OrderList, OrderDetail, OrderReview, ProductList, MessageList, UserList, RegionList)
- ✅ 布局组件 (`components/AppLayout.vue`)
- ✅ 路由 + 守卫 (`router/index.js`)
- ✅ Pinia 认证状态 (`store/auth.js`)
- ✅ Axios 封装 + 拦截器 (`api/index.js` + 各模块)
- ✅ build 产物 (`dist/`)

## 部署架构 (已变更)

```
浏览器 ──→ localhost:8080 (FastAPI)
               ├── /api/*          → FastAPI 路由
               ├── /assets/*       → StaticFiles (前端 JS/CSS)
               └── 其他路径         → SPAMiddleware → index.html
```

**不再使用** `npm run dev` 开发服务器。修改前端代码后必须：
```bash
cd D:\develop\job\telegram-bot\crm-system\frontend
npm run build
```
后端 `--reload` 不会自动检测 dist 变化，需手动重启后端或硬刷新浏览器。

## 当前任务

### 任务 A 🔴：排查 401 未授权问题

**现象**：登录后点击侧边栏菜单，部分页面 API 请求返回 401，跳回 /login。

**排查步骤**：

1. 确认 dist 是最新构建：
   ```powershell
   Get-ChildItem D:\develop\job\telegram-bot\crm-system\frontend\dist\assets -Filter "*.js" | Sort LastWriteTime -Desc | Select -First 3
   ```
   如果 dist 时间早于源码修改时间，执行 `npm run build`

2. 打开 `http://localhost:8080`（注意是 8080）
3. F12 → Application → Local Storage → `http://localhost:8080` → 清空
4. F12 → Network → Preserve log → 登录 admin/admin123
5. 观察每个 API 请求的 Request Headers 中是否有 `Authorization: Bearer ...`
6. 点击"订单管理"或"消息管理"，观察新请求的 Authorization header

**关键排查点**：

- `frontend/src/api/index.js` — 请求拦截器中 `authStore.token` 是否为空
- `frontend/src/store/auth.js` — `state.token` 初始化从 localStorage 读取是否正确
- `frontend/src/router/index.js` — 守卫中 fetchMe 失败后的竞态处理
  ```javascript
  // 当前代码在 catch 中有竞态风险：
  } catch (error) {
    if (!authStore.isLoggedIn) {
      return  // ← 拦截器已跳转，但守卫 return 了没调 next()
    }
    next('/login')
    return
  }
  ```
  建议统一为 `next('/login')`。

### 任务 B ⬜：开发新功能页面 (Phase 6)

1. 规则配置页面 (`RulesConfig.vue`)
   - 提取规则管理 (增删改查)
   - 分配规则管理 (增删改查)
   - 路由: `/rules` (admin only)

2. 消息导入功能
   - MessageList.vue 增加"导入消息"按钮
   - 上传 JSONL 文件，调用 POST /api/messages/import

## 技术栈

Vue 3 (Composition API), Element Plus, Vite, Vue Router, Pinia, Axios

## 关键代码位置

| 文件 | 用途 |
|------|------|
| `src/api/index.js` | Axios 实例 + 请求/响应拦截器 |
| `src/store/auth.js` | 认证状态 (token/user/login/logout) |
| `src/router/index.js` | 路由配置 + 守卫 |
| `src/components/AppLayout.vue` | 主布局 (侧边栏 + 顶栏) |

## UI 规范

- 简洁商务风格，白底 + 浅灰边框
- el-table 使用 stripe 条纹
- 订单状态 el-tag 颜色：
  - pending_extract: 灰 / pending_review: 橙 / rejected: 红
  - assigned: 蓝 / processing: 青 / completed: 绿 / cancelled: 灰
- 操作确认用 el-message-box.confirm

## 注意事项

- 前端代码修改后必须 `npm run build`
- 不要回退已完成改动 (见 PROGRESS.md Phase 4)
- 不要修改 telegram-bot-demo 下任何文件
- 所有 API 调用走 src/api/ 封装，不在组件里直接 axios
