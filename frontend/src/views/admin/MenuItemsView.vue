<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'
import type { MenuItemRead } from '@/api'

const items = ref<MenuItemRead[]>([])
const loading = ref(true)
const error = ref('')

const showCreate = ref(false)
const form = ref({ label: '', url: '', icon: '🔗', sort_order: 0, is_active: true, min_role: 'user' })
const saving = ref(false)
const formError = ref('')

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
      <button class="btn btn-primary" @click="showCreate = true">＋ 新增連結</button>
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
      <div class="modal">
        <div class="modal-title">新增作業連結</div>
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
</style>
