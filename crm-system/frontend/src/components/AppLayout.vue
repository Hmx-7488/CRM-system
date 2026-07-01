<template>
  <el-container class="app-container">
    <!-- 左侧导航 -->
    <el-aside :width="isCollapse ? '64px' : '200px'" class="app-aside">
      <div class="logo">
        <h1 v-if="!isCollapse">CRM</h1>
        <h1 v-else>C</h1>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        router
        class="app-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        
        <el-menu-item index="/orders">
          <el-icon><List /></el-icon>
          <template #title>订单管理</template>
        </el-menu-item>
        
        <el-menu-item v-if="isReviewer" index="/orders/review">
          <el-icon><Checked /></el-icon>
          <template #title>待审核</template>
        </el-menu-item>
        
        <el-menu-item v-if="isAdmin || isReviewer" index="/products">
          <el-icon><Goods /></el-icon>
          <template #title>产品管理</template>
        </el-menu-item>
        
        <el-menu-item index="/messages">
          <el-icon><ChatDotSquare /></el-icon>
          <template #title>消息管理</template>
        </el-menu-item>
        
        <el-menu-item v-if="isAdmin" index="/users">
          <el-icon><User /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>
        
        <el-menu-item v-if="isAdmin" index="/regions">
          <el-icon><Location /></el-icon>
          <template #title>区域管理</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <!-- 右侧内容区 -->
    <el-container>
      <!-- 顶部栏 -->
      <el-header class="app-header">
        <div class="header-left">
          <el-icon
            class="collapse-btn"
            @click="isCollapse = !isCollapse"
          >
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
        </div>
        
        <div class="header-right">
          <span class="user-info">
            {{ authStore.username }}
            <el-tag size="small" :type="roleTagType">{{ roleLabel }}</el-tag>
          </span>
          <el-button type="danger" text @click="handleLogout">
            退出登录
          </el-button>
        </div>
      </el-header>
      
      <!-- 内容区 -->
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../store/auth'
import { ElMessageBox } from 'element-plus'
import {
  DataBoard, List, Checked, Goods, ChatDotSquare,
  User, Location, Fold, Expand
} from '@element-plus/icons-vue'

const route = useRoute()
const authStore = useAuthStore()
const isCollapse = ref(false)

const activeMenu = computed(() => {
  return route.path
})

const isAdmin = computed(() => authStore.userRole === 'admin')
const isReviewer = computed(() => authStore.userRole === 'reviewer')

const roleLabel = computed(() => {
  const roleMap = {
    admin: '管理员',
    reviewer: '审核员',
    agent: '业务员'
  }
  return roleMap[authStore.userRole] || authStore.userRole
})

const roleTagType = computed(() => {
  const typeMap = {
    admin: 'danger',
    reviewer: 'warning',
    agent: 'info'
  }
  return typeMap[authStore.userRole] || ''
})

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    authStore.logout()
  } catch {
    // 取消操作
  }
}
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.app-aside {
  background-color: #304156;
  transition: width 0.3s;
  overflow: hidden;
}

.logo {
  height: 60px;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #263445;
}

.logo h1 {
  color: #fff;
  font-size: 20px;
  margin: 0;
}

.app-menu {
  border-right: none;
  background-color: #304156;
}

.app-menu .el-menu-item {
  color: #bfcbd9;
}

.app-menu .el-menu-item:hover,
.app-menu .el-menu-item.is-active {
  background-color: #263445;
  color: #409eff;
}

.app-header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  color: #606266;
}

.collapse-btn:hover {
  color: #409eff;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #606266;
}

.app-main {
  background-color: #f5f7fa;
  padding: 20px;
}
</style>
