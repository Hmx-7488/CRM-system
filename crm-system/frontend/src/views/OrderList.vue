<template>
  <div class="order-list">
    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部状态" clearable style="width: 150px;">
            <el-option
              v-for="item in statusOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="关键词">
          <el-input
            v-model="filterForm.keyword"
            placeholder="订单号/客户名"
            clearable
            style="width: 200px;"
          />
        </el-form-item>
        
        <el-form-item v-if="showRegionFilter" label="区域">
          <el-select v-model="filterForm.region_id" placeholder="全部区域" clearable style="width: 150px;">
            <el-option
              v-for="region in regions"
              :key="region.id"
              :label="region.name"
              :value="region.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 订单表格 -->
    <el-card style="margin-top: 20px;">
      <el-table
        :data="orderList"
        stripe
        style="width: 100%"
        @row-click="handleRowClick"
      >
        <el-table-column prop="order_no" label="订单号" width="150" />
        <el-table-column prop="customer_name" label="客户名" width="120" />
        <el-table-column prop="product_name" label="产品" width="150" />
        <el-table-column prop="quantity" label="数量" width="80" align="center" />
        <el-table-column prop="total_amount" label="金额" width="100" align="right">
          <template #default="{ row }">
            ¥{{ row.total_amount?.toFixed(2) || '0.00' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="region_name" label="区域" width="100" />
        <el-table-column prop="assigned_user" label="处理人" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click.stop="goToDetail(row.id)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import { getOrders } from '../api/orders'
import { getRegions } from '../api/regions'

const router = useRouter()
const authStore = useAuthStore()

const orderList = ref([])
const regions = ref([])

const filterForm = reactive({
  status: '',
  keyword: '',
  region_id: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const statusOptions = [
  { label: '待提取', value: 'pending_extract' },
  { label: '待审核', value: 'pending_review' },
  { label: '已驳回', value: 'rejected' },
  { label: '已分配', value: 'assigned' },
  { label: '处理中', value: 'processing' },
  { label: '已完成', value: 'completed' },
  { label: '已取消', value: 'cancelled' }
]

const showRegionFilter = computed(() => {
  return ['admin', 'reviewer'].includes(authStore.userRole)
})

const getStatusType = (status) => {
  const typeMap = {
    pending_extract: 'info',
    pending_review: 'warning',
    rejected: 'danger',
    assigned: '',
    processing: '',
    completed: 'success',
    cancelled: 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusLabel = (status) => {
  const labelMap = {
    pending_extract: '待提取',
    pending_review: '待审核',
    rejected: '已驳回',
    assigned: '已分配',
    processing: '处理中',
    completed: '已完成',
    cancelled: '已取消'
  }
  return labelMap[status] || status
}

const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN')
}

const fetchOrders = async () => {
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      ...filterForm
    }
    
    // 清理空值
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })
    
    const res = await getOrders(params)
    orderList.value = res.data.items
    pagination.total = res.data.total
  } catch (error) {
    // 错误已在拦截器中处理
  }
}

const fetchRegions = async () => {
  try {
    const res = await getRegions()
    regions.value = res.data.items || res.data
  } catch (error) {
    // 错误已在拦截器中处理
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchOrders()
}

const handleReset = () => {
  filterForm.status = ''
  filterForm.keyword = ''
  filterForm.region_id = ''
  pagination.page = 1
  fetchOrders()
}

const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  fetchOrders()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchOrders()
}

const handleRowClick = (row) => {
  goToDetail(row.id)
}

const goToDetail = (id) => {
  router.push(`/orders/${id}`)
}

onMounted(() => {
  fetchOrders()
  if (showRegionFilter.value) {
    fetchRegions()
  }
})
</script>

<style scoped>
.filter-card {
  margin-bottom: 20px;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.el-table {
  cursor: pointer;
}
</style>
