<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'
import type { UserRead } from '@/api'

const users = ref<UserRead[]>([])
const loading = ref(true)
const error = ref('')

const showCreate = ref(false)
const form = ref({ username: '', password: '', role: 'user' })
const saving = ref(false)
const formError = ref('')

const editTarget = ref<UserRead | null>(null)
const editForm = ref({ password: '', role: 'user', is_active: true })

onMounted(load)

async function load() {
  loading.value = true
  error.value = ''
  try {
    users.value = await api.getUsers()
  } catch (e: any) {
    error.value = e.message ?? '載入失敗'
  } finally {
    loading.value = false
  }
}

async function createUser() {
  if (!form.value.username.trim() || !form.value.password) return
  saving.value = true
  formError.value = ''
  try {
    const u = await api.createUser(form.value)
    users.value.push(u)
    showCreate.value = false
    form.value = { username: '', password: '', role: 'user' }
  } catch (e: any) {
    formError.value = e.message ?? '建立失敗'
  } finally {
    saving.value = false
  }
}

function openEdit(u: UserRead) {
  editTarget.value = u
  editForm.value = { password: '', role: u.role, is_active: u.is_active }
}

async function saveEdit() {
  if (!editTarget.value) return
  saving.value = true
  formError.value = ''
  try {
    const payload: any = { role: editForm.value.role, is_active: editForm.value.is_active }
    if (editForm.value.password) payload.password = editForm.value.password
    const updated = await api.updateUser(editTarget.value.id, payload)
    const idx = users.value.findIndex(u => u.id === updated.id)
    if (idx !== -1) users.value[idx] = updated
    editTarget.value = null
  } catch (e: any) {
    formError.value = e.message ?? '更新失敗'
  } finally {
    saving.value = false
  }
}

async function deleteUser(u: UserRead) {
  if (!confirm(`確定刪除帳號「${u.username}」？`)) return
  try {
    await api.deleteUser(u.id)
    users.value = users.value.filter(x => x.id !== u.id)
  } catch (e: any) {
    alert('刪除失敗：' + (e.message ?? '未知錯誤'))
  }
}
</script>

<template>
  <div>
    <div class="page-toolbar">
      <h2 class="page-title">帳號管理</h2>
      <button class="btn btn-primary" @click="showCreate = true">＋ 新增帳號</button>
    </div>

    <div v-if="loading" class="text-muted">載入中…</div>
    <div v-else-if="error" class="text-danger">{{ error }}</div>
    <div v-else>
      <table class="data-table">
        <thead>
          <tr>
            <th>帳號</th>
            <th>角色</th>
            <th>狀態</th>
            <th>建立時間</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td>{{ u.username }}</td>
            <td><span :class="['role-badge', u.role]">{{ u.role }}</span></td>
            <td><span :class="['status-dot', u.is_active ? 'active' : 'inactive']">{{ u.is_active ? '啟用' : '停用' }}</span></td>
            <td class="text-muted">{{ new Date(u.created_at).toLocaleDateString('zh-TW') }}</td>
            <td class="row-actions">
              <button class="btn btn-ghost btn-sm" @click="openEdit(u)">編輯</button>
              <button class="btn btn-ghost btn-sm text-danger" @click="deleteUser(u)">刪除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create modal -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false; formError = ''">
      <div class="modal">
        <div class="modal-title">新增帳號</div>
        <div class="form-group">
          <label>帳號</label>
          <input v-model="form.username" class="form-control" placeholder="輸入帳號" />
        </div>
        <div class="form-group">
          <label>密碼</label>
          <input v-model="form.password" type="password" class="form-control" placeholder="輸入密碼" />
        </div>
        <div class="form-group">
          <label>角色</label>
          <select v-model="form.role" class="form-control">
            <option value="user">user（一般使用者）</option>
            <option value="admin">admin（管理員）</option>
          </select>
        </div>
        <div v-if="formError" class="text-danger" style="font-size:13px;margin-bottom:8px">{{ formError }}</div>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="showCreate = false; formError = ''">取消</button>
          <button class="btn btn-primary" :disabled="saving || !form.username.trim() || !form.password" @click="createUser">
            {{ saving ? '建立中…' : '建立' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Edit modal -->
    <div v-if="editTarget" class="modal-overlay" @click.self="editTarget = null; formError = ''">
      <div class="modal">
        <div class="modal-title">編輯帳號：{{ editTarget.username }}</div>
        <div class="form-group">
          <label>新密碼（留空不變）</label>
          <input v-model="editForm.password" type="password" class="form-control" placeholder="留空則不修改密碼" />
        </div>
        <div class="form-group">
          <label>角色</label>
          <select v-model="editForm.role" class="form-control">
            <option value="user">user（一般使用者）</option>
            <option value="admin">admin（管理員）</option>
          </select>
        </div>
        <div class="form-group">
          <label>狀態</label>
          <select v-model="editForm.is_active" class="form-control">
            <option :value="true">啟用</option>
            <option :value="false">停用</option>
          </select>
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

.row-actions {
  display: flex;
  gap: 6px;
}

.role-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  text-transform: uppercase;
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
