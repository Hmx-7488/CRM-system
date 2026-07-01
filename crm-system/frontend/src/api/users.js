import api from './index'

export function getUsers(params) {
  return api.get('/api/users/', { params })
}

export function getUser(userId) {
  return api.get(`/api/users/${userId}`)
}

export function createUser(data) {
  return api.post('/api/users/', data)
}

export function updateUser(userId, data) {
  return api.put(`/api/users/${userId}`, data)
}

export function deleteUser(userId) {
  return api.delete(`/api/users/${userId}`)
}

export function getAgentUsers() {
  return api.get('/api/users/', { params: { role: 'agent' } })
}
