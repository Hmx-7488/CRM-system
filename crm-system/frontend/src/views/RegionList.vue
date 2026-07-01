<template>
  <div class="region-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>区域管理</span>
          <el-button type="primary" @click="handleAdd">新增区域</el-button>
        </div>
      </template>
      
      <el-table
        :data="regionList"
        stripe
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="name" label="区域名称" min-width="200" />
        <el-table-column prop="code" label="区域编码" width="150" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="showDialog"
      :title="isEdit ? '编辑区域' : '新增区域'"
      width="400px"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="区域名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入区域名称" />
        </el-form-item>
        
        <el-form-item label="区域编码" prop="code">
          <el-input v-model="formData.code" placeholder="请输入区域编码" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getRegions, createRegion, updateRegion, deleteRegion } from '../api/regions'
import { ElMessage, ElMessageBox } from 'element-plus'

const regionList = ref([])
const loading = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const formRef = ref(null)

const formData = reactive({
  name: '',
  code: ''
})

const rules = {
  name: [
    { required: true, message: '请输入区域名称', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入区域编码', trigger: 'blur' }
  ]
}

const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN')
}

const fetchRegions = async () => {
  loading.value = true
  try {
    const res = await getRegions()
    regionList.value = res.data.items || res.data
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  formData.name = ''
  formData.code = ''
}

const handleAdd = () => {
  isEdit.value = false
  editId.value = null
  resetForm()
  showDialog.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  editId.value = row.id
  formData.name = row.name
  formData.code = row.code
  showDialog.value = true
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  
  try {
    if (isEdit.value) {
      await updateRegion(editId.value, formData)
      ElMessage.success('更新成功')
    } else {
      await createRegion(formData)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    fetchRegions()
  } catch (error) {
    // 错误已在拦截器中处理
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(
    `确定要删除区域 "${row.name}" 吗？`,
    '确认删除',
    { type: 'warning' }
  )
    .then(async () => {
      await deleteRegion(row.id)
      ElMessage.success('删除成功')
      fetchRegions()
    })
    .catch(() => {})
}

onMounted(() => {
  fetchRegions()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
