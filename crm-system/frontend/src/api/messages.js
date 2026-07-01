import api from './index'

export function getMessages(params) {
  return api.get('/api/messages/', { params })
}

export function getMessage(messageId) {
  return api.get(`/api/messages/${messageId}`)
}

export function markExtracted(messageId) {
  return api.post(`/api/messages/${messageId}/extract`)
}
