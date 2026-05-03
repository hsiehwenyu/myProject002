<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <template v-if="auth.isAuthenticated">
    <nav class="app-nav">
      <router-link to="/" class="brand">📊 金融資產紀錄系統</router-link>
      <router-link to="/all-functions">功能總覽</router-link>
      <router-link to="/portfolios">投資紀錄</router-link>
      <template v-if="auth.isAdmin">
        <router-link to="/admin/users">帳號管理</router-link>
        <router-link to="/admin/menu">選單管理</router-link>
      </template>
      <div style="margin-left:auto;display:flex;align-items:center;gap:12px">
        <span style="font-size:13px;color:#64748b">
          {{ auth.username }}
          <span v-if="auth.isAdmin" class="nav-role-badge">admin</span>
        </span>
        <button class="btn btn-ghost btn-sm" @click="logout">登出</button>
      </div>
    </nav>
    <main style="padding:24px 0">
      <div class="container">
        <router-view />
      </div>
    </main>
  </template>
  <template v-else>
    <router-view />
  </template>
</template>

<style scoped>
.nav-role-badge {
  display: inline-block;
  font-size: 10px;
  font-weight: 700;
  background: #7c3aed;
  color: #fff;
  padding: 1px 5px;
  border-radius: 4px;
  margin-left: 4px;
  vertical-align: middle;
  letter-spacing: 0.03em;
}
</style>
