import api from './index'

export function login(username, password) {
  return api.post('/api/auth/login', { username, password })
}

export function getMe() {
  return api.get('/api/auth/me')
}
