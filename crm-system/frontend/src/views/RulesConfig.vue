<template>
  <div class="rules-config">
    <el-card>
      <template #header>
        <span>规则配置</span>
      </template>

      <el-tabs v-model="activeTab">
        <!-- 提取规则 Tab -->
        <el-tab-pane label="提取规则" name="extract">
          <div style="margin-bottom: 16px;">
            <el-button type="primary" @click="openExtractDialog(null)">新增规则</el-button>
          </div>

          <el-table :data="extractRules" v-loading="loadingExtract" stripe>
            <el-table-column prop="name" label="名称" width="180" />
            <el-table-column prop="rule_type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag>{{ row.rule_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="priority" label="优先级" width="100" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-switch
                  :model-value="row.status === 1"
                  @change="(val) => toggleExtractRuleStatus(row, val)"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button type="primary" link @click="openExtractDialog(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 分配规则 Tab -->
        <el-tab-pane label="分配规则" name="assign">
          <div style="margin-bottom: 16px;">
            <el-button type="primary" @click="openAssignDialog(null)">新增规则</el-button>
          </div>

          <el-table :data="assignRules" v-loading="loadingAssign" stripe>
            <el-table-column prop="name" label="名称" width="180" />
            <el-table-column prop="rule_type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag>{{ row.rule_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="priority" label="优先级" width="100" />
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-switch
                  :model-value="row.status === 1"
                  @change="(val) => toggleAssignRuleStatus(row, val)"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button type="primary" link @click="openAssignDialog(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 提取规则对话框 -->
    <el-dialog
      v-model="showExtractDialog"
      :title="extractForm.id ? '编辑提取规则' : '新增提取规则'"
      width="600px"
    >
      <el-form :model="extractForm" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="extractForm.name" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="extractForm.rule_type" @change="onExtractTypeChange">
            <el-option label="关键词" value="keyword" />
            <el-option label="正则" value="regex" />
            <el-option label="发送者" value="sender" />
            <el-option label="群组" value="group" />
          </el-select>
        </el-form-item>
        <el-form-item label="规则配置" required>
          <el-input
            v-model="extractForm.rule_config_str"
            type="textarea"
            :rows="8"
            :placeholder="extractPlaceholder"
          />
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="extractForm.priority" :min="0" :max="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showExtractDialog = false">取消</el-button>
        <el-button type="primary" @click="saveExtractRule" :loading="savingExtract">保存</el-button>
      </template>
    </el-dialog>

    <!-- 分配规则对话框 -->
    <el-dialog
      v-model="showAssignDialog"
      :title="assignForm.id ? '编辑分配规则' : '新增分配规则'"
      width="600px"
    >
      <el-form :model="assignForm" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="assignForm.name" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="assignForm.rule_type" @change="onAssignTypeChange">
            <el-option label="区域" value="region" />
            <el-option label="负载均衡" value="load_balance" />
            <el-option label="产品" value="product" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="规则配置" required>
          <el-input
            v-model="assignForm.rule_config_str"
            type="textarea"
            :rows="8"
            :placeholder="assignPlaceholder"
          />
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="assignForm.priority" :min="0" :max="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAssignDialog = false">取消</el-button>
        <el-button type="primary" @click="saveAssignRule" :loading="savingAssign">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getExtractRules, createExtractRule, updateExtractRule,
  getAssignRules, createAssignRule, updateAssignRule
} from '../api/rules'

// ============ 提取规则 ============
const extractRules = ref([])
const loadingExtract = ref(false)
const showExtractDialog = ref(false)
const savingExtract = ref(false)
const extractForm = ref({ id: null, name: '', rule_type: 'keyword', rule_config_str: '', priority: 0 })

const extractPlaceholders = {
  keyword: '{"keywords": ["下单", "订购", "来货"]}',
  regex: '{"pattern": "[¥￥](\\\\d+(?:\\\\.\\\\d{1,2})?)", "field_mapping": {"total_amount": 1}}',
  sender: '{"sender_ids": [123456, 789012]}',
  group: '{"group_ids": [-100111, -100222]}'
}
const extractPlaceholder = computed(() => extractPlaceholders[extractForm.value.rule_type] || '')

const onExtractTypeChange = () => {
  extractForm.value.rule_config_str = ''
}

const fetchExtractRules = async () => {
  loadingExtract.value = true
  try {
    const res = await getExtractRules()
    extractRules.value = res.data || []
  } catch { /* 拦截器已处理 */ }
  finally { loadingExtract.value = false }
}

const openExtractDialog = (row) => {
  if (row) {
    extractForm.value = {
      id: row.id,
      name: row.name,
      rule_type: row.rule_type,
      rule_config_str: JSON.stringify(row.rule_config, null, 2),
      priority: row.priority
    }
  } else {
    extractForm.value = { id: null, name: '', rule_type: 'keyword', rule_config_str: '', priority: 0 }
  }
  showExtractDialog.value = true
}

const saveExtractRule = async () => {
  if (!extractForm.value.name) {
    ElMessage.warning('请输入规则名称')
    return
  }
  let config
  try {
    config = JSON.parse(extractForm.value.rule_config_str)
  } catch {
    ElMessage.error('规则配置 JSON 格式错误')
    return
  }
  savingExtract.value = true
  try {
    const data = {
      name: extractForm.value.name,
      rule_type: extractForm.value.rule_type,
      rule_config: config,
      priority: extractForm.value.priority
    }
    if (extractForm.value.id) {
      await updateExtractRule(extractForm.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await createExtractRule(data)
      ElMessage.success('创建成功')
    }
    showExtractDialog.value = false
    fetchExtractRules()
  } catch { /* 拦截器已处理 */ }
  finally { savingExtract.value = false }
}

const toggleExtractRuleStatus = async (row, val) => {
  try {
    await updateExtractRule(row.id, { status: val ? 1 : 0 })
    ElMessage.success(val ? '已启用' : '已禁用')
    fetchExtractRules()
  } catch { /* 拦截器已处理 */ }
}

// ============ 分配规则 ============
const assignRules = ref([])
const loadingAssign = ref(false)
const showAssignDialog = ref(false)
const savingAssign = ref(false)
const assignForm = ref({ id: null, name: '', rule_type: 'region', rule_config_str: '', priority: 0 })

const assignPlaceholders = {
  region: '{"region_id": 1}',
  load_balance: '{"agent_ids": [1, 2, 3]}',
  product: '{"product_id": 1}',
  custom: '{}'
}
const assignPlaceholder = computed(() => assignPlaceholders[assignForm.value.rule_type] || '')

const onAssignTypeChange = () => {
  assignForm.value.rule_config_str = ''
}

const fetchAssignRules = async () => {
  loadingAssign.value = true
  try {
    const res = await getAssignRules()
    assignRules.value = res.data || []
  } catch { /* 拦截器已处理 */ }
  finally { loadingAssign.value = false }
}

const openAssignDialog = (row) => {
  if (row) {
    assignForm.value = {
      id: row.id,
      name: row.name,
      rule_type: row.rule_type,
      rule_config_str: JSON.stringify(row.rule_config, null, 2),
      priority: row.priority
    }
  } else {
    assignForm.value = { id: null, name: '', rule_type: 'region', rule_config_str: '', priority: 0 }
  }
  showAssignDialog.value = true
}

const saveAssignRule = async () => {
  if (!assignForm.value.name) {
    ElMessage.warning('请输入规则名称')
    return
  }
  let config
  try {
    config = JSON.parse(assignForm.value.rule_config_str)
  } catch {
    ElMessage.error('规则配置 JSON 格式错误')
    return
  }
  savingAssign.value = true
  try {
    const data = {
      name: assignForm.value.name,
      rule_type: assignForm.value.rule_type,
      rule_config: config,
      priority: assignForm.value.priority
    }
    if (assignForm.value.id) {
      await updateAssignRule(assignForm.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await createAssignRule(data)
      ElMessage.success('创建成功')
    }
    showAssignDialog.value = false
    fetchAssignRules()
  } catch { /* 拦截器已处理 */ }
  finally { savingAssign.value = false }
}

const toggleAssignRuleStatus = async (row, val) => {
  try {
    await updateAssignRule(row.id, { status: val ? 1 : 0 })
    ElMessage.success(val ? '已启用' : '已禁用')
    fetchAssignRules()
  } catch { /* 拦截器已处理 */ }
}

// ============ 初始化 ============
onMounted(() => {
  fetchExtractRules()
  fetchAssignRules()
})
</script>

<style scoped>
.rules-config {
  padding: 0;
}
</style>