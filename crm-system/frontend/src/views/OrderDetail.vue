<template>
  <div class="order-detail" v-loading="loading">
    <!-- 返回按钮 -->
    <el-page-header @back="goBack" style="margin-bottom: 20px;">
      <template #content>
        <span class="page-title">订单详情</span>
      </template>
    </el-page-header>
    
    <!-- 订单基本信息 -->
    <el-card class="info-card">
      <template #header>
        <div class="card-header">
          <span>订单信息</span>
          <el-tag :type="getStatusType(order.status)" size="large">
            {{ getStatusLabel(order.status) }}
          </el-tag>
        </div>
      </template>
      
      <el-descriptions :column="3" border>
        <el-descriptions-item label="订单号">{{ order.order_no }}</el-descriptions-item>
        <el-descriptions-item label="客户名称">{{ order.customer_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ order.customer_phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="产品名称">{{ order.product_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="数量">{{ order.quantity || '-' }}</el-descriptions-item>
        <el-descriptions-item label="金额">¥{{ order.total_amount?.toFixed(2) || '0.00' }}</el-descriptions-item>
        <el-descriptions-item label="区域">{{ order.region_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="处理人">{{ order.assigned_user || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审核人">{{ order.reviewer_user || '-' }}</el-descriptions-item>
        <el-descriptions-item label="客户地址" :span="3">{{ order.customer_address || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="3">{{ order.remark || '-' }}</el-descriptions-item>
        <el-descriptions-item v-if="order.reject_reason" label="驳回原因" :span="3">
          <span style="color: #f56c6c;">{{ order.reject_reason }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(order.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatTime(order.updated_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
    
    <!-- 操作按钮 -->
    <el-card v-if="showActions" class="action-card">
      <template #header>
        <span>状态操作</span>
      </template>
      
      <div class="action-buttons">
        <!-- reviewer 待审核操作 -->
        <template v-if="isReviewer && order.status === 'pending_review'">
          <el-button type="success" @click="handleReview('approve')">
            审核通过
          </el-button>
          <el-button type="danger" @click="handleReview('reject')">
            驳回
          </el-button>
        </template>
        
        <!-- admin/reviewer 分配操作 -->
        <template v-if="(isAdmin || isReviewer) && order.status === 'pending_review'">
          <el-button type="primary" @click="showAssignDialog = true">
            分配订单
          </el-button>
        </template>
        
        <!-- agent 待处理操作 -->
        <template v-if="isAgent && order.status === 'assigned'">
          <el-button type="primary" @click="handleStatusChange('processing')">
            开始处理
          </el-button>
        </template>
        
        <!-- agent 处理中操作 -->
        <template v-if="isAgent && order.status === 'processing'">
          <el-button type="success" @click="handleStatusChange('completed')">
            完成订单
          </el-button>
          <el-button type="warning" @click="handleStatusChange('cancelled')">
            取消订单
          </el-button>
        </template>
      </div>
    </el-card>
    
    <!-- 操作日志 -->
    <el-card class="log-card">
      <template #header>
        <span>操作日志</span>
      </template>
      
      <el-timeline v-if="logs.length">
        <el-timeline-item
          v-for="log in logs"
          :key="log.id"
          :timestamp="formatTime(log.created_at)"
          placement="top"
        >
          <el-card shadow="never">
            <div class="log-content">
              <span class="log-operator">{{ log.operator_name }}</span>
              <span class="log-action">{{ log.remark }}</span>
            </div>
            <div class="log-status">
              <el-tag size="small" :type="getStatusType(log.from_status)">
                {{ getStatusLabel(log.from_status) }}
              </el-tag>
              <el-icon style="margin: 0 8px;"><Right /></el-icon>
              <el-tag size="small" :type="getStatusType(log.to_status)">
                {{ getStatusLabel(log.to_status) }}
              </el-tag>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
      
      <el-empty v-else description="暂无操作日志" />
    </el-card>
    
    <!-- 分配对话框 -->
    <el-dialog v-model="showAssignDialog" title="分配订单" width="400px">
      <el-form :model="assignForm" label-width="80px">
        <el-form-item label="处理人" required>
          <el-select v-model="assignForm.assigned_to" placeholder="请选择处理人" style="width: 100%;">
            <el-option
              v-for="user in agentUsers"
              :key="user.id"
              :label="user.display_name || user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAssignDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAssign">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 驳回原因对话框 -->
    <el-dialog v-model="showRejectDialog" title="驳回订单" width="400px">
      <el-form :model="rejectForm" label-width="80px">
        <el-form-item label="驳回原因" required>
          <el-input
            v-model="rejectForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请输入驳回原因"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showRejectDialog = false">取消</el-button>
        <el-button type="danger" @click="confirmReject">确定驳回</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../store/auth'
import { getOrder, getOrderLogs, reviewOrder, assignOrder, updateOrderStatus } from '../api/orders'
import { getAgentUsers } from '../api/users'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Right } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const order = ref({})
const logs = ref([])
const agentUsers = ref([])
const loading = ref(false)
const showAssignDialog = ref(false)
const showRejectDialog = ref(false)

const assignForm = reactive({
  assigned_to: ''
})

const rejectForm = reactive({
  reason: ''
})

const isAdmin = computed(() => authStore.userRole === 'admin')
const isReviewer = computed(() => authStore.userRole === 'reviewer')
const isAgent = computed(() => authStore.userRole === 'agent')

const showActions = computed(() => {
  const status = order.value.status
  if (isReviewer.value && status === 'pending_review') return true
  if ((isAdmin.value || isReviewer.value) && status === 'pending_review') return true
  if (isAgent.value && (status === 'assigned' || status === 'processing')) return true
  return false
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

const fetchOrder = async () => {
  loading.value = true
  try {
    const res = await getOrder(route.params.id)
    order.value = res.data
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

const fetchLogs = async () => {
  try {
    const res = await getOrderLogs(route.params.id)
    logs.value = res.data
  } catch (error) {
    // 错误已在拦截器中处理
  }
}

const fetchAgentUsers = async () => {
  try {
    const res = await getAgentUsers()
    agentUsers.value = res.data.items || res.data
  } catch (error) {
    // 错误已在拦截器中处理
  }
}

const handleStatusChange = async (newStatus) => {
  const statusLabel = {
    processing: '开始处理',
    completed: '完成订单',
    cancelled: '取消订单'
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要${statusLabel[newStatus]}吗？`,
      '确认操作',
      { type: 'warning' }
    )
    
    await updateOrderStatus(route.params.id, newStatus)
    ElMessage.success('操作成功')
    fetchOrder()
    fetchLogs()
  } catch (error) {
    if (error !== 'cancel') {
      // 错误已在拦截器中处理
    }
  }
}

const handleReview = (action) => {
  if (action === 'approve') {
    ElMessageBox.confirm('确定要审核通过吗？', '确认操作', { type: 'warning' })
      .then(async () => {
        await reviewOrder(route.params.id, 'approve')
        ElMessage.success('审核通过')
        fetchOrder()
        fetchLogs()
      })
      .catch(() => {})
  } else {
    rejectForm.reason = ''
    showRejectDialog.value = true
  }
}

const confirmReject = async () => {
  if (!rejectForm.reason.trim()) {
    ElMessage.warning('请输入驳回原因')
    return
  }
  
  try {
    await reviewOrder(route.params.id, 'reject', rejectForm.reason)
    ElMessage.success('已驳回')
    showRejectDialog.value = false
    fetchOrder()
    fetchLogs()
  } catch (error) {
    // 错误已在拦截器中处理
  }
}

const handleAssign = async () => {
  if (!assignForm.assigned_to) {
    ElMessage.warning('请选择处理人')
    return
  }
  
  try {
    await assignOrder(route.params.id, assignForm.assigned_to)
    ElMessage.success('分配成功')
    showAssignDialog.value = false
    fetchOrder()
    fetchLogs()
  } catch (error) {
    // 错误已在拦截器中处理
  }
}

const goBack = () => {
  router.push('/orders')
}

onMounted(() => {
  fetchOrder()
  fetchLogs()
  if (isAdmin.value || isReviewer.value) {
    fetchAgentUsers()
  }
})
</script>

<style scoped>
.page-title {
  font-size: 18px;
  font-weight: bold;
}

.info-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-card {
  margin-bottom: 20px;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.log-card {
  margin-bottom: 20px;
}

.log-content {
  margin-bottom: 8px;
}

.log-operator {
  font-weight: bold;
  margin-right: 12px;
}

.log-action {
  color: #606266;
}

.log-status {
  display: flex;
  align-items: center;
}
</style>
