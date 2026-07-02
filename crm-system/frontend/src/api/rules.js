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