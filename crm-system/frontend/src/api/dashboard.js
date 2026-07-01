import api from './index'

export function getDashboardStats() {
  return api.get('/api/dashboard/summary')
}

export function getDashboardTrend() {
  return api.get('/api/dashboard/orders')
}
