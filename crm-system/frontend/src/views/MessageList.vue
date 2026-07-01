<template>
  <div class="message-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>消息管理</span>
          <div>
            <el-select
              v-model="filterProcessed"
              placeholder="处理状态"
              clearable
              style="width: 150px; margin-right: 12px;"
              @change="handleFilter"
            >
              <el-option label="已处理" value="1" />
              <el-option label="未处理" value="0" />
            </el-select>
            <el-button type="primary" @click="fetchMessages">刷新</el-button>
          </div>
        </div>
      </template>
      
      <el-table
        :data="messageList"
        stripe
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="group_name" label="群名称" width="150" />
        <el-table-column prop="sender_name" label="发送者" width="120" />
        <el-table-column prop="text" label="消息内容" min-width="250">
          <template #default="{ row }">
            <el-tooltip :content="row.text" placement="top" :show-after="500">
              <span class="message-preview">{{ truncateText(row.text, 50) }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="received_at" label="时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.received_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="processed" label="处理状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.processed ? 'success' : 'info'" size="small">
              {{ row.processed ? '已处理' : '未处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              :disabled="row.processed"
              @click="handleExtract(row)"
            >
              处理
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
import { ref, reactive, onMounted } from 'vue'
import { getMessages, markExtracted } from '../api/messages'
import { ElMessage } from 'element-plus'

const messageList = ref([])
const loading = ref(false)
const filterProcessed = ref('')

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const truncateText = (text, length) => {
  if (!text) return '-'
  return text.length > length ? text.substring(0, length) + '...' : text
}

const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN')
}

const fetchMessages = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size
    }

    if (filterProcessed.value !== '') {
      params.processed = filterProcessed.value
    }

    const res = await getMessages(params)
    messageList.value = res.data.items || res.data
    pagination.total = res.data.total || messageList.value.length
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

const handleFilter = () => {
  pagination.page = 1
  fetchMessages()
}

const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  fetchMessages()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchMessages()
}

const handleExtract = async (row) => {
  try {
    await markExtracted(row.id)
    ElMessage.success('处理成功')
    row.processed = 1
  } catch (error) {
    // 错误已在拦截器中处理
  }
}

onMounted(() => {
  fetchMessages()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.message-preview {
  cursor: pointer;
  color: #606266;
}

.message-preview:hover {
  color: #409eff;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
