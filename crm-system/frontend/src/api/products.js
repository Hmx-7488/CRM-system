import api from './index'

export function getProducts(params) {
  return api.get('/api/products/', { params })
}

export function getProduct(productId) {
  return api.get(`/api/products/${productId}`)
}

export function createProduct(data) {
  return api.post('/api/products/', data)
}

export function updateProduct(productId, data) {
  return api.put(`/api/products/${productId}`, data)
}

export function deleteProduct(productId) {
  return api.delete(`/api/products/${productId}`)
}
