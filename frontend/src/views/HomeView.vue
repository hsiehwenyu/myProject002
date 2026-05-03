<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePortfolioStore } from '@/stores/portfolio'
import { api } from '@/api'

const store = usePortfolioStore()
const router = useRouter()

const showCreate = ref(false)
const form = ref({ name: '', description: '' })
const saving = ref(false)
const createError = ref<string | null>(null)

onMounted(() => store.fetchPortfolios())

async function createPortfolio() {
  if (!form.value.name.trim()) return
  saving.value = true
  createError.value = null
  try {
    const p = await api.createPortfolio({ name: form.value.name, description: form.value.description || undefined })
    store.portfolios.unshift(p)
    showCreate.value = false
    form.value = { name: '', description: '' }
  } catch (e: any) {
    createError.value = e.message ?? '新增失敗，請確認 Backend 是否正常運行'
  } finally {
    saving.value = false
  }
}

async function deletePortfolio(id: number, name: string) {
  if (!confirm(`確定刪除「${name}」及其所有資產？`)) return
  try {
    await api.deletePortfolio(id)
    store.portfolios = store.portfolios.filter(p => p.id !== id)
  } catch (e: any) {
    alert('刪除失敗：' + (e.message ?? '未知錯誤'))
  }
}
</script>

<template>
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
    <h1 style="font-size:20px;font-weight:700">投資組合列表</h1>
    <button class="btn btn-primary" @click="showCreate=true">＋ 新增投資組合</button>
  </div>

  <div v-if="store.loading" class="text-muted">載入中…</div>
  <div v-else-if="store.error" class="text-danger">{{ store.error }}</div>
  <div v-else-if="!store.portfolios.length" class="card text-muted" style="text-align:center;padding:48px">
    尚無投資組合，請點擊「新增投資組合」開始建立。
  </div>
  <div v-else style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px">
    <div v-for="p in store.portfolios" :key="p.id" class="card" style="cursor:pointer" @click="router.push(`/portfolios/${p.id}`)">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:8px">
        <span style="font-size:16px;font-weight:700">{{ p.name }}</span>
        <button class="btn btn-ghost btn-sm" @click.stop="deletePortfolio(p.id, p.name)">刪除</button>
      </div>
      <div class="text-muted" style="font-size:12px">{{ p.description || '無描述' }}</div>
      <div class="text-muted" style="font-size:11px;margin-top:8px">建立於 {{ new Date(p.created_at).toLocaleDateString('zh-TW') }}</div>
    </div>
  </div>

  <!-- Create modal -->
  <div v-if="showCreate" class="modal-overlay" @click.self="showCreate=false">
    <div class="modal">
      <div class="modal-title">新增投資組合</div>
      <div class="form-group">
        <label>名稱 *</label>
        <input v-model="form.name" class="form-control" placeholder="例：富守投資組合" />
      </div>
      <div class="form-group">
        <label>描述</label>
        <input v-model="form.description" class="form-control" placeholder="選填" />
      </div>
      <div v-if="createError" class="text-danger" style="font-size:13px;margin-bottom:8px">{{ createError }}</div>
      <div class="modal-actions">
        <button class="btn btn-ghost" @click="showCreate=false; createError=null">取消</button>
        <button class="btn btn-primary" :disabled="saving || !form.name.trim()" @click="createPortfolio">
          {{ saving ? '建立中…' : '建立' }}
        </button>
      </div>
    </div>
  </div>
</template>
