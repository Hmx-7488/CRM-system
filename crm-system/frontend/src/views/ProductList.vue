<template>
  <div class="product-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>产品管理</span>
          <div>
            <el-input
              v-model="searchKeyword"
              placeholder="搜索产品名称"
              style="width: 200px; margin-right: 12px;"
              clearable
              @clear="handleSearch"
              @keyup.enter="handleSearch"
            >
              <template #append>
                <el-button @click="handleSearch">
                  <el-icon><Search /></el-icon>
                </el-button>
              </template>
            </el-input>
            <el-button type="primary" @click="handleAdd">新增产品</el-button>
          </div>
        </div>
      </template>
      
      <el-table
        :data="productList"
        stripe
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="name" label="产品名称" min-width="150" />
        <el-table-column prop="spec" label="规格" width="120" />
        <el-table-column prop="category" label="品类" width="100" />
        <el-table-column prop="unit_price" label="单价" width="100" align="right">
          <template #default="{ row }">
            ¥{{ row.unit_price?.toFixed(2) || '0.00' }}
          </template>
        </el-table-column>
        <el-table-column prop="unit" label="单位" width="80" align="center" />
        <el-table-column prop="source" label="来源" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.source === 'auto' ? 'success' : 'info'" size="small">
              {{ row.source === 'auto' ? '自动' : '手动' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'danger'" size="small">
              {{ row.status === 'active' ? '启用' : '禁用' }}
            </el-tag>
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
      :title="isEdit ? '编辑产品' : '新增产品'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="产品名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入产品名称" />
        </el-form-item>
        
        <el-form-item label="规格" prop="spec">
          <el-input v-model="formData.spec" placeholder="请输入规格" />
        </el-form-item>
        
        <el-form-item label="品类" prop="category">
          <el-input v-model="formData.category" placeholder="请输入品类" />
        </el-form-item>
        
        <el-form-item label="单价" prop="unit_price">
          <el-input-number
            v-model="formData.unit_price"
            :min="0"
            :precision="2"
            style="width: 100%;"
          />
        </el-form-item>
        
        <el-form-item label="单位" prop="unit">
          <el-input v-model="formData.unit" placeholder="请输入单位" />
        </el-form-item>
        
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="formData.status">
            <el-radio value="active">启用</el-radio>
            <el-radio value="inactive">禁用</el-radio>
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
import { getProducts, createProduct, updateProduct, deleteProduct } from '../api/products'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'

const productList = ref([])
const loading = ref(false)
const showDialog = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const searchKeyword = ref('')
const formRef = ref(null)

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const formData = reactive({
  name: '',
  spec: '',
  category: '',
  unit_price: 0,
  unit: '',
  status: 'active'
})

const rules = {
  name: [
    { required: true, message: '请输入产品名称', trigger: 'blur' }
  ],
  unit_price: [
    { required: true, message: '请输入单价', trigger: 'blur' }
  ],
  unit: [
    { required: true, message: '请输入单位', trigger: 'blur' }
  ]
}

const fetchProducts = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size
    }
    
    if (searchKeyword.value) {
      params.keyword = searchKeyword.value
    }
    
    const res = await getProducts(params)
    productList.value = res.data.items || res.data
    pagination.total = res.data.total || productList.value.length
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchProducts()
}

const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  fetchProducts()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchProducts()
}

const resetForm = () => {
  formData.name = ''
  formData.spec = ''
  formData.category = ''
  formData.unit_price = 0
  formData.unit = ''
  formData.status = 'active'
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
  formData.spec = row.spec
  formData.category = row.category
  formData.unit_price = row.unit_price
  formData.unit = row.unit
  formData.status = row.status
  showDialog.value = true
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  
  try {
    if (isEdit.value) {
      await updateProduct(editId.value, formData)
      ElMessage.success('更新成功')
    } else {
      await createProduct(formData)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    fetchProducts()
  } catch (error) {
    // 错误已在拦截器中处理
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(
    `确定要删除产品 "${row.name}" 吗？`,
    '确认删除',
    { type: 'warning' }
  )
    .then(async () => {
      await deleteProduct(row.id)
      ElMessage.success('删除成功')
      fetchProducts()
    })
    .catch(() => {})
}

onMounted(() => {
  fetchProducts()
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
