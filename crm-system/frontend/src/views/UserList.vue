<template>
  <div class="user-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" @click="handleAdd">新增用户</el-button>
        </div>
      </template>
      
      <el-table
        :data="userList"
        stripe
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="display_name" label="显示名称" width="150" />
        <el-table-column prop="role" label="角色" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)" size="small">
              {{ getRoleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="region_name" label="所属区域" width="120" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
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
    
    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="showDialog"
      :title="isEdit ? '编辑用户' : '新增用户'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="formData.username"
            placeholder="请输入用户名"
            :disabled="isEdit"
          />
        </el-form-item>
        
        <el-form-item :label="isEdit ? '新密码' : '密码'" :prop="isEdit ? '' : 'password'">
          <el-input
            v-model="formData.password"
            type="password"
            :placeholder="isEdit ? '留空则不修改密码' : '请输入密码'"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="显示名称" prop="display_name">
          <el-input v-model="formData.display_name" placeholder="请输入显示名称" />
        </el-form-item>
        
        <el-form-item label="角色" prop="role">
          <el-select v-model="formData.role" placeholder="请选择角色" style="width: 100%;">
            <el-option label="管理员" value="admin" />
            <el-option label="审核员" value="reviewer" />
            <el-option label="业务员" value="agent" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="所属区域" prop="region_id">
          <el-select v-model="formData.region_id" placeholder="请选择区域" clearable style="width: 100%;">
            <el-option
              v-for="region in regions"
              :key="region.id"
              :label="region.name"
              :value="region.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="formData.status">
            <el-radio :value="1">启用</el-radio>
            <el-radio :value="0">禁用</el-radio>
          </el-radio-group>
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
import { getUsers, createUser, updateUser, deleteUser } from '../api/users'
import { getRegions } from '../api/regions'
import { ElMessage, ElMessageBox } from 'element-plus'

const userList = ref([])
const regions = ref([])
const loading = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const formRef = ref(null)

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const formData = reactive({
  username: '',
  password: '',
  display_name: '',
  role: '',
  region_id: '',
  status: 1
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ],
  display_name: [
    { required: true, message: '请输入显示名称', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

const getRoleType = (role) => {
  const typeMap = {
    admin: 'danger',
    reviewer: 'warning',
    agent: 'info'
  }
  return typeMap[role] || ''
}

const getRoleLabel = (role) => {
  const labelMap = {
    admin: '管理员',
    reviewer: '审核员',
    agent: '业务员'
  }
  return labelMap[role] || role
}

const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN')
}

const fetchUsers = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size
    }
    
    const res = await getUsers(params)
    userList.value = res.data.items || res.data
    pagination.total = res.data.total || userList.value.length
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
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

const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  fetchUsers()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchUsers()
}

const resetForm = () => {
  formData.username = ''
  formData.password = ''
  formData.display_name = ''
  formData.role = ''
  formData.region_id = ''
  formData.status = 1
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
  formData.username = row.username
  formData.password = ''
  formData.display_name = row.display_name
  formData.role = row.role
  formData.region_id = row.region_id || ''
  formData.status = row.status
  showDialog.value = true
}

const handleSubmit = async () => {
  // 编辑时密码非必填
  if (!isEdit.value) {
    const valid = await formRef.value.validate().catch(() => false)
    if (!valid) return
  } else {
    // 编辑时只验证其他字段
    const valid = await formRef.value.validateField(['username', 'display_name', 'role']).catch(() => false)
    if (!valid) return
  }
  
  try {
    const submitData = { ...formData }
    
    // 编辑时如果密码为空，则不提交密码字段
    if (isEdit.value && !submitData.password) {
      delete submitData.password
    }
    
    // 清理空值
    if (!submitData.region_id) {
      submitData.region_id = null
    }
    
    if (isEdit.value) {
      await updateUser(editId.value, submitData)
      ElMessage.success('更新成功')
    } else {
      await createUser(submitData)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    fetchUsers()
  } catch (error) {
    // 错误已在拦截器中处理
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(
    `确定要删除用户 "${row.username}" 吗？`,
    '确认删除',
    { type: 'warning' }
  )
    .then(async () => {
      await deleteUser(row.id)
      ElMessage.success('删除成功')
      fetchUsers()
    })
    .catch(() => {})
}

onMounted(() => {
  fetchUsers()
  fetchRegions()
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
