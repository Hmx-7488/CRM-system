import api from './index'

export function getRegions(params) {
  return api.get('/api/regions/', { params })
}

export function getRegion(regionId) {
  return api.get(`/api/regions/${regionId}`)
}

export function createRegion(data) {
  return api.post('/api/regions/', data)
}

export function updateRegion(regionId, data) {
  return api.put(`/api/regions/${regionId}`, data)
}

export function deleteRegion(regionId) {
  return api.delete(`/api/regions/${regionId}`)
}
