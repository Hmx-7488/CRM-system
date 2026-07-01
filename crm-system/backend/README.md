# CRM System Backend

基于 FastAPI + MySQL 的 CRM 系统后端

## 技术栈

- Python 3.11+
- FastAPI
- SQLAlchemy (同步模式)
- PyMySQL
- passlib[bcrypt] (密码哈希)
- python-jose (JWT 认证)

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件，配置数据库连接和 JWT 密钥：

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DATABASE=crm
JWT_SECRET_KEY=your-secret-key
JWT_EXPIRE_HOURS=24
```

### 3. 初始化数据库

```bash
python init_db.py
```

这将：
- 创建数据库表
- 插入种子数据（区域、用户）

### 4. 启动服务

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问 API 文档：http://localhost:8000/docs

## 默认用户

| 用户名 | 密码 | 角色 | 区域 |
|--------|------|------|------|
| admin | admin123 | 管理员 | 华东 |
| review | review123 | 审核员 | 华东 |
| agent1 | agent123 | 操作员 | 华东 |

## API 端点

### 认证
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

### 用户管理 (admin)
- `GET /api/users` - 用户列表
- `POST /api/users` - 创建用户
- `PUT /api/users/{id}` - 编辑用户
- `DELETE /api/users/{id}` - 禁用用户

### 区域管理 (admin)
- `GET /api/regions` - 区域列表
- `POST /api/regions` - 创建区域
- `PUT /api/regions/{id}` - 编辑区域
- `DELETE /api/regions/{id}` - 删除区域

### 产品管理
- `GET /api/products` - 产品列表（分页 + 搜索）
- `POST /api/products` - 创建产品 (admin/reviewer)
- `PUT /api/products/{id}` - 编辑产品 (admin/reviewer)

### 原始消息
- `GET /api/messages` - 消息列表（分页 + 筛选）
- `POST /api/messages/{id}/extract` - 触发消息提取

### 订单管理
- `GET /api/orders` - 订单列表（分页 + 筛选）
- `GET /api/orders/{id}` - 订单详情
- `POST /api/orders` - 创建订单
- `PUT /api/orders/{id}` - 编辑订单
- `POST /api/orders/{id}/status` - 更新订单状态
- `POST /api/orders/{id}/review` - 审核订单
- `POST /api/orders/{id}/assign` - 分配订单

### 仪表盘
- `GET /api/dashboard/summary` - 概览统计
- `GET /api/dashboard/orders` - 订单统计

### 规则管理 (admin)
- `GET /api/rules/extract` - 提取规则列表
- `POST /api/rules/extract` - 创建提取规则
- `PUT /api/rules/extract/{id}` - 编辑提取规则
- `GET /api/rules/assign` - 分配规则列表
- `POST /api/rules/assign` - 创建分配规则
- `PUT /api/rules/assign/{id}` - 编辑分配规则

## 统一响应格式

```json
{
  "code": 0,
  "data": {...},
  "message": "ok"
}
```

## 订单状态流转

```
待提取(pending_extract) -> 待审核(pending_review) -> 已分配(assigned) -> 处理中(processing) -> 已完成(completed)
                                                    -> 已驳回(rejected)
                                                    -> 已取消(cancelled)
```

## 目录结构

```
backend/
  app/
    __init__.py
    main.py              # FastAPI 入口
    config.py            # 配置
    database.py          # 数据库连接
    models/              # SQLAlchemy 模型
    schemas/             # Pydantic 模型
    api/                 # API 路由
    services/            # 业务逻辑
    utils/               # 工具函数
  requirements.txt
  .env
  init_db.py            # 数据库初始化
  test_db.py            # 数据库测试
  README.md
```