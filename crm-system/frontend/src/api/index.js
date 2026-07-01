import axios from 'axios'
import { useAuthStore } from '../store/auth'
import { ElMessage } from 'element-plus'

// 延迟获取 router，避免循环依赖
// index.js -> router -> store/auth -> api/auth -> index.js
let _router = null
export function setApiRouter(router) {
  _router = router
}

const api = axios.create({
  baseURL: '',
  timeout: 10000
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code !== 0) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail

    if (status === 401) {
      const authStore = useAuthStore()
      const isLoginRequest = error.config?.url?.includes('/api/auth/login')
      if (!isLoginRequest) {
        authStore.clearToken()
        if (_router) {
          _router.push('/login')
        } else {
          // 兜底：router 未初始化时用 location
          window.location.href = '/login'
        }
        ElMessage.error('登录已过期，请重新登录')
      } else {
        ElMessage.error(detail || '用户名或密码错误')
      }
    } else if (status === 403) {
      ElMessage.error(detail || '权限不足')
    } else {
      ElMessage.error(error.message || '网络错误')
    }
    return Promise.reject(error)
  }
)

export default api
