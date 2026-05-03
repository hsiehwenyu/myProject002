<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'
import type { MenuItemRead } from '@/api'
import { APP_FUNCTIONS } from '@/constants/appFunctions'

const items = ref<MenuItemRead[]>([])
const loading = ref(true)
const error = ref('')

const showCreate = ref(false)
const form = ref({ label: '', url: '', icon: '🔗', sort_order: 0, is_active: true, min_role: 'user' })
const saving = ref(false)
const formError = ref('')
const selectedFuncKey = ref('')   // tracks which function card is highlighted

function selectFunc(icon: string, label: string, path: string, adminOnly?: boolean) {
  form.value.icon  = icon
  form.value.label = label
  form.value.url   = path
  if (adminOnly) form.value.min_role = 'admin'
  selectedFuncKey.value = path + label
}

function openCreate() {
  form.value = { label: '', url: '', icon: '🔗', sort_order: 0, is_active: true, min_role: 'user' }
  selectedFuncKey.value = ''
  formError.value = ''
  showCreate.value = true
}

const editTarget = ref<MenuItemRead | null>(null)
const editForm = ref({ label: '', url: '', icon: '', sort_order: 0, is_active: true, min_role: 'user' })

onMounted(load)

async function load() {
  loading.value = true
  try {
    items.value = await api.getAllMenuItems()
  } catch (e: any) {
    error.value = e.message ?? '載入失敗'
  } finally {
    loading.value = false
  }
}

async function createItem() {
  if (!form.value.label.trim() || !form.value.url.trim()) return
  saving.value = true
  formError.value = ''
  try {
    const item = await api.createMenuItem(form.value)
    items.value.push(item)
    showCreate.value = false
    form.value = { label: '', url: '', icon: '🔗', sort_order: 0, is_active: true, min_role: 'user' }
  } catch (e: any) {
    formError.value = e.message ?? '新增失敗'
  } finally {
    saving.value = false
  }
}

function openEdit(item: MenuItemRead) {
  editTarget.value = item
  editForm.value = { ...item }
}

async function saveEdit() {
  if (!editTarget.value) return
  saving.value = true
  formError.value = ''
  try {
    const updated = await api.updateMenuItem(editTarget.value.id, editForm.value)
    const idx = items.value.findIndex(i => i.id === updated.id)
    if (idx !== -1) items.value[idx] = updated
    editTarget.value = null
  } catch (e: any) {
    formError.value = e.message ?? '更新失敗'
  } finally {
    saving.value = false
  }
}

async function deleteItem(item: MenuItemRead) {
  if (!confirm(`確定刪除「${item.label}」？`)) return
  try {
    await api.deleteMenuItem(item.id)
    items.value = items.value.filter(i => i.id !== item.id)
  } catch (e: any) {
    alert('刪除失敗：' + (e.message ?? '未知錯誤'))
  }
}
</script>

<template>
  <div>
    <div class="page-toolbar">
      <h2 class="page-title">選單管理</h2>
      <button class="btn btn-primary" @click="openCreate">＋ 新增連結</button>
    </div>

    <div v-if="loading" class="text-muted">載入中…</div>
    <div v-else-if="error" class="text-danger">{{ error }}</div>
    <div v-else-if="!items.length" class="text-muted" style="text-align:center;padding:48px">尚無選單項目</div>
    <div v-else>
      <table class="data-table">
        <thead>
          <tr>
            <th>圖示</th>
            <th>名稱</th>
            <th>連結</th>
            <th>排序</th>
            <th>可見角色</th>
            <th>狀態</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td style="font-size:22px;text-align:center">{{ item.icon }}</td>
            <td style="font-weight:600">{{ item.label }}</td>
            <td class="text-muted url-cell">{{ item.url }}</td>
            <td class="text-muted" style="text-align:center">{{ item.sort_order }}</td>
            <td><span :class="['role-badge', item.min_role]">{{ item.min_role }}</span></td>
            <td><span :class="['status-dot', item.is_active ? 'active' : 'inactive']">{{ item.is_active ? '顯示' : '隱藏' }}</span></td>
            <td class="row-actions">
              <button class="btn btn-ghost btn-sm" @click="openEdit(item)">編輯</button>
              <button class="btn btn-ghost btn-sm text-danger" @click="deleteItem(item)">刪除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create modal -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false; formError = ''">
      <div class="modal modal-wide">
        <div class="modal-title">新增作業連結</div>

        <!-- Function picker -->
        <div class="picker-section">
          <div class="picker-section-label">從作業功能挑選</div>
          <div v-for="group in APP_FUNCTIONS" :key="group.group" style="margin-bottom:10px">
            <div class="picker-group-label">{{ group.group }}</div>
            <div class="picker-grid">
              <button
                v-for="item in group.items"
                :key="item.path + item.label"
                type="button"
                class="picker-func-card"
                :class="{ 'picker-func-card--selected': selectedFuncKey === item.path + item.label }"
                @click="selectFunc(item.icon, item.label, item.path, item.adminOnly)"
              >
                <span class="picker-func-icon">{{ item.icon }}</span>
                <span class="picker-func-body">
                  <span class="picker-func-label">
                    {{ item.label }}
                    <span v-if="item.adminOnly" class="badge-admin">Admin</span>
                    <span v-if="item.external"  class="badge-ext">外部</span>
                  </span>
                  <span class="picker-func-desc">{{ item.desc }}</span>
                </span>
                <span v-if="selectedFuncKey === item.path + item.label" class="picker-check">✓</span>
              </button>
            </div>
          </div>
        </div>

        <div class="picker-divider">
          <span>或手動填寫</span>
        </div>

        <!-- Form fields -->
        <div class="form-row">
          <div class="form-group" style="flex:0 0 70px">
            <label>圖示</label>
            <input v-model="form.icon" class="form-control" maxlength="2" style="text-align:center;font-size:20px" />
          </div>
          <div class="form-group" style="flex:1">
            <label>名稱</label>
            <input v-model="form.label" class="form-control" placeholder="作業名稱" />
          </div>
        </div>
        <div class="form-group">
          <label>連結 URL</label>
          <input v-model="form.url" class="form-control" placeholder="https://... 或 /portfolios" />
        </div>
        <div class="form-row">
          <div class="form-group" style="flex:1">
            <label>可見角色</label>
            <select v-model="form.min_role" class="form-control">
              <option value="user">user（所有人）</option>
              <option value="admin">admin（管理員）</option>
            </select>
          </div>
          <div class="form-group" style="flex:0 0 100px">
            <label>排序</label>
            <input v-model.number="form.sort_order" type="number" class="form-control" />
          </div>
          <div class="form-group" style="flex:0 0 90px">
            <label>狀態</label>
            <select v-model="form.is_active" class="form-control">
              <option :value="true">顯示</option>
              <option :value="false">隱藏</option>
            </select>
          </div>
        </div>
        <div v-if="formError" class="text-danger" style="font-size:13px;margin-bottom:8px">{{ formError }}</div>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="showCreate = false; formError = ''">取消</button>
          <button class="btn btn-primary" :disabled="saving || !form.label.trim() || !form.url.trim()" @click="createItem">
            {{ saving ? '新增中…' : '新增' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Edit modal -->
    <div v-if="editTarget" class="modal-overlay" @click.self="editTarget = null; formError = ''">
      <div class="modal">
        <div class="modal-title">編輯：{{ editTarget.label }}</div>
        <div class="form-row">
          <div class="form-group" style="flex:0 0 70px">
            <label>圖示</label>
            <input v-model="editForm.icon" class="form-control" maxlength="2" style="text-align:center;font-size:20px" />
          </div>
          <div class="form-group" style="flex:1">
            <label>名稱</label>
            <input v-model="editForm.label" class="form-control" />
          </div>
        </div>
        <div class="form-group">
          <label>連結 URL</label>
          <input v-model="editForm.url" class="form-control" />
        </div>
        <div class="form-row">
          <div class="form-group" style="flex:1">
            <label>可見角色</label>
            <select v-model="editForm.min_role" class="form-control">
              <option value="user">user（所有人）</option>
              <option value="admin">admin（管理員）</option>
            </select>
          </div>
          <div class="form-group" style="flex:0 0 100px">
            <label>排序</label>
            <input v-model.number="editForm.sort_order" type="number" class="form-control" />
          </div>
          <div class="form-group" style="flex:0 0 90px">
            <label>狀態</label>
            <select v-model="editForm.is_active" class="form-control">
              <option :value="true">顯示</option>
              <option :value="false">隱藏</option>
            </select>
          </div>
        </div>
        <div v-if="formError" class="text-danger" style="font-size:13px;margin-bottom:8px">{{ formError }}</div>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="editTarget = null; formError = ''">取消</button>
          <button class="btn btn-primary" :disabled="saving" @click="saveEdit">
            {{ saving ? '儲存中…' : '儲存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-title {
  font-size: 18px;
  font-weight: 700;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 6px rgba(0,0,0,0.06);
}

.data-table th {
  background: #f8fafc;
  padding: 10px 14px;
  text-align: left;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.data-table td {
  padding: 10px 14px;
  border-top: 1px solid #f1f5f9;
}

.url-cell {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
}

.row-actions {
  display: flex;
  gap: 6px;
}

.form-row {
  display: flex;
  gap: 12px;
}

.role-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
}

.role-badge.admin {
  background: #ede9fe;
  color: #6d28d9;
}

.role-badge.user {
  background: #e0f2fe;
  color: #0369a1;
}

.status-dot {
  font-size: 12px;
  font-weight: 600;
}

.status-dot.active { color: #16a34a; }
.status-dot.inactive { color: #9ca3af; }

/* ── Function picker ── */
.modal-wide { min-width: 560px; max-width: 660px; max-height: 90vh; overflow-y: auto; }

.picker-section { margin-bottom: 4px; }
.picker-section-label {
  font-size: 12px;
  font-weight: 700;
  color: #1e3a5f;
  text-transform: uppercase;
  letter-spacing: .05em;
  margin-bottom: 8px;
}
.picker-group-label {
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: .04em;
  margin-bottom: 5px;
  padding-bottom: 4px;
  border-bottom: 1px solid #f1f5f9;
}
.picker-grid {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 6px;
}
.picker-func-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  text-align: left;
  transition: border-color .12s, background .12s;
  width: 100%;
}
.picker-func-card:hover { border-color: #1a5276; background: #f0f7ff; }
.picker-func-card--selected { border-color: #1a5276; background: #eff6ff; }
.picker-func-icon { font-size: 20px; width: 28px; text-align: center; flex-shrink: 0; }
.picker-func-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.picker-func-label { font-size: 13px; font-weight: 600; color: #1e293b; display: flex; align-items: center; gap: 5px; }
.picker-func-desc  { font-size: 11px; color: #64748b; }
.picker-check { font-size: 14px; color: #1a5276; font-weight: 700; flex-shrink: 0; }

.picker-divider {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 14px 0 12px;
  color: #94a3b8;
  font-size: 12px;
}
.picker-divider::before,
.picker-divider::after { content: ''; flex: 1; border-top: 1px solid #e2e8f0; }

.badge-admin { font-size: 10px; font-weight: 700; background: #ede9fe; color: #6d28d9; padding: 1px 5px; border-radius: 3px; }
.badge-ext   { font-size: 10px; font-weight: 700; background: #dcfce7; color: #16a34a; padding: 1px 5px; border-radius: 3px; }
</style>
