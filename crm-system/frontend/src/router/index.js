import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../store/auth'
import { ElMessage } from 'element-plus'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    component: () => import('../components/AppLayout.vue'),
    children: [
      {
        path: '',
        redirect: '/dashboard'
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue')
      },
      {
        path: 'orders',
        name: 'OrderList',
        component: () => import('../views/OrderList.vue')
      },
      {
        path: 'orders/review',
        name: 'OrderReview',
        component: () => import('../views/OrderReview.vue'),
        meta: { roles: ['reviewer'] }
      },
      {
        path: 'orders/:id',
        name: 'OrderDetail',
        component: () => import('../views/OrderDetail.vue')
      },
      {
        path: 'products',
        name: 'ProductList',
        component: () => import('../views/ProductList.vue'),
        meta: { roles: ['admin', 'reviewer'] }
      },
      {
        path: 'messages',
        name: 'MessageList',
        component: () => import('../views/MessageList.vue')
      },
      {
        path: 'users',
        name: 'UserList',
        component: () => import('../views/UserList.vue'),
        meta: { roles: ['admin'] }
      },
      {
        path: 'rules',
        name: 'RulesConfig',
        component: () => import('../views/RulesConfig.vue'),
        meta: { roles: ['admin'] }
      },
      {
        path: 'regions',
        name: 'RegionList',
        component: () => import('../views/RegionList.vue'),
        meta: { roles: ['admin'] }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  // 公开页面直接放行
  if (to.meta.public) {
    // 已登录用户访问登录页，跳转到首页
    if (to.path === '/login' && authStore.isLoggedIn) {
      next('/dashboard')
      return
    }
    next()
    return
  }
  
  // 需要登录的页面
  if (!authStore.isLoggedIn) {
    next('/login')
    return
  }
  
  // 如果没有用户信息，先获取
  if (!authStore.user) {
    try {
      await authStore.fetchMe()
    } catch (error) {
      // 如果拦截器已经清除了 token（401），authStore.isLoggedIn 会变为 false
      // 此时不需要重复跳转，拦截器已经处理了
      if (!authStore.isLoggedIn) {
        // token 已被清除，直接返回，拦截器会处理跳转
        return
      }
      // 其他错误（网络等），尝试跳转登录页
      next('/login')
      return
    }
  }
  
  // 检查角色权限
  if (to.meta.roles && !to.meta.roles.includes(authStore.userRole)) {
    ElMessage.warning('您没有权限访问此页面')
    next('/dashboard')
    return
  }
  
  next()
})

export default router
