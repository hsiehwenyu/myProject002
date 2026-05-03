<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '@/api'
import { useAuthStore } from '@/stores/auth'
import type { MenuItemRead } from '@/api'

const auth = useAuthStore()
const items = ref<MenuItemRead[]>([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    items.value = await api.getMenuItems()
  } catch (e: any) {
    error.value = e.message ?? '載入失敗'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="portal">
    <div class="portal-header">
      <h1>歡迎，{{ auth.username }}</h1>
      <p class="portal-subtitle">請選擇要進行的作業</p>
    </div>

    <div v-if="loading" class="text-muted" style="text-align:center;padding:48px">載入中…</div>
    <div v-else-if="error" class="text-danger" style="text-align:center;padding:48px">{{ error }}</div>
    <div v-else-if="!items.length" class="empty-hint">
      尚未設定任何作業連結。<br />
      <span v-if="auth.isAdmin">請至「選單管理」新增連結。</span>
    </div>
    <div v-else class="menu-grid">
      <a
        v-for="item in items"
        :key="item.id"
        :href="item.url"
        class="menu-card"
        target="_blank"
        rel="noopener"
      >
        <span class="menu-icon">{{ item.icon }}</span>
        <span class="menu-label">{{ item.label }}</span>
        <span v-if="item.min_role === 'admin'" class="badge-admin">Admin</span>
      </a>
    </div>
  </div>
</template>

<style scoped>
.portal {
  max-width: 860px;
  margin: 0 auto;
}

.portal-header {
  margin-bottom: 32px;
}

.portal-header h1 {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 4px;
}

.portal-subtitle {
  font-size: 14px;
  color: #64748b;
}

.empty-hint {
  text-align: center;
  padding: 60px 24px;
  color: #94a3b8;
  font-size: 15px;
  line-height: 1.8;
}

.menu-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.menu-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 28px 16px;
  background: #fff;
  border: 1.5px solid #e2e8f0;
  border-radius: 14px;
  text-decoration: none;
  color: #1e293b;
  position: relative;
  transition: border-color 0.15s, box-shadow 0.15s, transform 0.1s;
  cursor: pointer;
}

.menu-card:hover {
  border-color: #1a5276;
  box-shadow: 0 4px 16px rgba(26, 82, 118, 0.12);
  transform: translateY(-2px);
}

.menu-icon {
  font-size: 36px;
}

.menu-label {
  font-size: 14px;
  font-weight: 600;
  text-align: center;
}

.badge-admin {
  position: absolute;
  top: 8px;
  right: 10px;
  font-size: 10px;
  font-weight: 700;
  background: #7c3aed;
  color: #fff;
  padding: 2px 6px;
  border-radius: 4px;
  letter-spacing: 0.03em;
}
</style>
