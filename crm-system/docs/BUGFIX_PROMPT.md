# 任务：修复前端页面字段显示问题 [✅ 已完成]

> 本文件记录的问题已在 2026-07-01 15:10 全部修复，保留作为历史参考。
> 当前进度见 [PROGRESS.md](PROGRESS.md)。

## 已修复的问题

### 1. 后端 API 返回关联实体名称 ✅
### 2. 前端 UserList.vue status 字段类型不匹配 ✅
### 3. 用户管理页面 region_name 列空白 ✅
### 4. 全局字段排查 ✅

## 修复摘要

### 订单 API (`backend/app/api/orders.py`)
在 `list_orders`、`get_order`、`create_order`、`update_order` 四个函数的返回字典中新增（保留原有 ID 字段）：

```python
"product_name": order.product.name if order.product else None,
"region_name": order.region.name if order.region else None,
"assigned_user": order.assigned_user.display_name if order.assigned_user else None,
"reviewer_user": order.reviewer.display_name if order.reviewer else None,
```

### 用户 API (`backend/app/api/users.py`)
在 `list_users` 返回字典中新增：
```python
"region_name": user.region.name if user.region else None,
```

### 前端 `UserList.vue`
所有 status 比较从字符串 `'active'`/`'inactive'` 改为整数 `1`/`0`。

### 全局排查结果

| 页面 | 列/字段 | 状态 |
|------|---------|------|
| OrderList.vue | product_name, region_name, assigned_user | ✅ |
| OrderDetail.vue | 同上 + reviewer_user | ✅ |
| OrderReview.vue | product_name | ✅ |
| UserList.vue | region_name, status | ✅ |
| MessageList.vue | group_name, sender_name | ✅ |
| ProductList.vue | status | ✅ |
| Dashboard.vue | region_stats.region_name | ✅ |
| RegionList.vue | name, code | ✅ |
