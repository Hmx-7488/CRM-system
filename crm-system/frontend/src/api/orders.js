import api from './index'

export function getOrders(params) {
  return api.get('/api/orders/', { params })
}

export function getOrder(orderId) {
  return api.get(`/api/orders/${orderId}`)
}

export function createOrder(data) {
  return api.post('/api/orders/', data)
}

export function updateOrder(orderId, data) {
  return api.put(`/api/orders/${orderId}`, data)
}

export function updateOrderStatus(orderId, status) {
  return api.post(`/api/orders/${orderId}/status`, { status })
}

export function reviewOrder(orderId, action, reason) {
  return api.post(`/api/orders/${orderId}/review`, { action, reason })
}

export function assignOrder(orderId, assignedTo) {
  return api.post(`/api/orders/${orderId}/assign`, { assigned_to: assignedTo })
}

export function getOrderLogs(orderId) {
  return api.get(`/api/orders/${orderId}/logs`)
}
