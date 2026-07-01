<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>总订单数</span>
              <el-icon><List /></el-icon>
            </div>
          </template>
          <div class="stat-value">{{ stats.total_orders || 0 }}</div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>待审核</span>
              <el-icon><Clock /></el-icon>
            </div>
          </template>
          <div class="stat-value warning">{{ stats.pending_review || 0 }}</div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>处理中</span>
              <el-icon><Loading /></el-icon>
            </div>
          </template>
          <div class="stat-value primary">{{ stats.processing || 0 }}</div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>今日完成</span>
              <el-icon><CircleCheck /></el-icon>
            </div>
          </template>
          <div class="stat-value success">{{ stats.completed_today || 0 }}</div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 区域分布 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>区域订单分布</span>
          </template>
          <div v-if="stats.region_stats && stats.region_stats.length" class="region-list">
            <div
              v-for="region in stats.region_stats"
              :key="region.region_name"
              class="region-item"
            >
              <span class="region-name">{{ region.region_name || '未分配' }}</span>
              <el-tag type="info">{{ region.count }} 单</el-tag>
            </div>
          </div>
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
      
      <!-- 近7天趋势 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>近7天订单趋势</span>
          </template>
          <div v-if="trendData.length" class="trend-chart">
            <div
              v-for="item in trendData"
              :key="item.date"
              class="trend-bar-wrapper"
            >
              <div class="trend-bar-container">
                <div
                  class="trend-bar"
                  :style="{ height: getBarHeight(item.count) + '%' }"
                ></div>
              </div>
              <div class="trend-label">{{ formatDate(item.date) }}</div>
              <div class="trend-count">{{ item.count }}</div>
            </div>
          </div>
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getDashboardStats, getDashboardTrend } from '../api/dashboard'
import { List, Clock, Loading, CircleCheck } from '@element-plus/icons-vue'

const stats = ref({})
const trendData = ref([])

const maxCount = computed(() => {
  if (!trendData.value.length) return 1
  return Math.max(...trendData.value.map(item => item.count), 1)
})

const getBarHeight = (count) => {
  return (count / maxCount.value) * 100
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

onMounted(async () => {
  try {
    const [statsRes, trendRes] = await Promise.all([
      getDashboardStats(),
      getDashboardTrend()
    ])
    stats.value = statsRes.data
    // 转换趋势数据格式
    trendData.value = trendRes.data.map(item => ({
      date: item.date,
      count: item.completed || 0
    }))
  } catch (error) {
    // 错误已在拦截器中处理
  }
})
</script>

<style scoped>
.stat-cards {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  text-align: center;
}

.stat-value.warning {
  color: #e6a23c;
}

.stat-value.primary {
  color: #409eff;
}

.stat-value.success {
  color: #67c23a;
}

.region-list {
  max-height: 300px;
  overflow-y: auto;
}

.region-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #ebeef5;
}

.region-item:last-child {
  border-bottom: none;
}

.region-name {
  color: #606266;
}

.trend-chart {
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  height: 200px;
  padding: 20px 0;
}

.trend-bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.trend-bar-container {
  width: 30px;
  height: 150px;
  background-color: #f5f7fa;
  border-radius: 4px;
  display: flex;
  align-items: flex-end;
}

.trend-bar {
  width: 100%;
  background-color: #409eff;
  border-radius: 4px 4px 0 0;
  transition: height 0.3s;
}

.trend-label {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.trend-count {
  font-size: 12px;
  color: #606266;
  font-weight: bold;
}
</style>
