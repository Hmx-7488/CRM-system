<template>
  <div class="order-review">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>待审核订单</span>
          <el-button type="primary" @click="fetchOrders">刷新</el-button>
        </div>
      </template>
      
      <el-table
        :data="orderList"
        stripe
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="order_no" label="订单号" width="150" />
        <el-table-column prop="customer_name" label="客户名" width="120" />
        <el-table-column prop="product_name" label="产品" width="150" />
        <el-table-column prop="total_amount" label="金额" width="100" align="right">
          <template #default="{ row }">
            ¥{{ row.total_amount?.toFixed(2) || '0.00' }}
          </template>
        </el-table-column>
        <el-table-column prop="source_msg_id" label="消息来源" width="120">
          <template #default="{ row }">
            {{ row.source_msg_id ? '消息提取' : '手动创建' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="success" size="small" @click="handleReview(row.id, 'approve')">
              通过
            </el-button>
            <el-button type="danger" size="small" @click="handleReview(row.id, 'reject')">
              驳回
            </el-button>
            <el-button type="primary" size="small" link @click="goToDetail(row.id)">
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
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getOrders, reviewOrder } from '../api/orders'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

const orderList = ref([])
const loading = ref(false)
const showRejectDialog = ref(false)
const currentOrderId = ref(null)

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const rejectForm = reactive({
  reason: ''
})

const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN')
}

const fetchOrders = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      status: 'pending_review'
    }
    
    const res = await getOrders(params)
    orderList.value = res.data.items
    pagination.total = res.data.total
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
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

const handleReview = (orderId, action) => {
  if (action === 'approve') {
    ElMessageBox.confirm('确定要审核通过吗？', '确认操作', { type: 'warning' })
      .then(async () => {
        await reviewOrder(orderId, 'approve')
        ElMessage.success('审核通过')
        fetchOrders()
      })
      .catch(() => {})
  } else {
    currentOrderId.value = orderId
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
    await reviewOrder(currentOrderId.value, 'reject', rejectForm.reason)
    ElMessage.success('已驳回')
    showRejectDialog.value = false
    fetchOrders()
  } catch (error) {
    // 错误已在拦截器中处理
  }
}

const goToDetail = (id) => {
  router.push(`/orders/${id}`)
}

onMounted(() => {
  fetchOrders()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
