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

export function importMessages(content, source = 'history') {
  return api.post('/api/messages/import', { content, source })
}

export function batchExtract() {
  return api.post('/api/messages/batch-extract')
}
