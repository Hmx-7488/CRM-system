import { defineStore } from 'pinia'
import { login as loginApi, getMe } from '../api/auth'

// 延迟获取 router，避免循环依赖
let _router = null
export function setStoreRouter(router) {
  _router = router
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: null
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    userRole: (state) => state.user?.role || '',
    username: (state) => state.user?.username || ''
  },

  actions: {
    async login(username, password) {
      try {
        const res = await loginApi(username, password)
        this.token = res.data.token
        localStorage.setItem('token', res.data.token)

        // 获取用户信息
        await this.fetchMe()

        return true
      } catch (error) {
        // fetchMe 失败时 token 可能已被清，确保清理
        if (!this.token) {
          // token 已被拦截器清除
        }
        throw error
      }
    },

    async fetchMe() {
      const res = await getMe()
      this.user = res.data
      return res.data
    },

    logout() {
      this.clearToken()
      this.user = null
      if (_router) {
        _router.push('/login')
      } else {
        window.location.href = '/login'
      }
    },

    clearToken() {
      this.token = ''
      localStorage.removeItem('token')
    }
  }
})
