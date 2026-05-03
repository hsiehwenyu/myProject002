<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function login() {
  if (!username.value.trim() || !password.value) return
  loading.value = true
  error.value = ''
  try {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value, password: password.value }),
    })
    const data = await res.json()
    if (!res.ok) {
      error.value = data.detail ?? '登入失敗'
      return
    }
    auth.setLogin(data.access_token, data.username, data.role)
    router.push('/')
  } catch {
    error.value = '無法連線至伺服器，請確認 Backend 已啟動'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-bg">
    <div class="login-card">
      <div class="login-header">
        <div class="login-icon">📊</div>
        <h1 class="login-title">投資資產管理系統</h1>
        <p class="login-subtitle">Investment Portfolio Manager</p>
      </div>

      <form class="login-form" @submit.prevent="login">
        <div class="form-group">
          <label>帳號</label>
          <input
            v-model="username"
            class="form-control"
            placeholder="請輸入帳號"
            autocomplete="username"
            :disabled="loading"
          />
        </div>
        <div class="form-group">
          <label>密碼</label>
          <input
            v-model="password"
            type="password"
            class="form-control"
            placeholder="請輸入密碼"
            autocomplete="current-password"
            :disabled="loading"
          />
        </div>

        <div v-if="error" class="login-error">{{ error }}</div>

        <button
          type="submit"
          class="btn-login"
          :disabled="loading || !username.trim() || !password"
        >
          {{ loading ? '登入中…' : '登入' }}
        </button>
      </form>

      <div class="login-hint">預設帳號：admin　／　密碼：admin1234</div>
    </div>
  </div>
</template>

<style scoped>
.login-bg {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a5276 0%, #6c3483 100%);
}

.login-card {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  padding: 40px 44px;
  width: 380px;
  max-width: 95vw;
}

.login-header {
  text-align: center;
  margin-bottom: 28px;
}

.login-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

.login-title {
  font-size: 20px;
  font-weight: 800;
  color: #1a5276;
  margin-bottom: 4px;
}

.login-subtitle {
  font-size: 12px;
  color: #94a3b8;
  letter-spacing: 0.5px;
}

.login-form .form-group {
  margin-bottom: 16px;
}

.login-form label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 6px;
  display: block;
}

.login-form .form-control {
  font-size: 14px;
  padding: 10px 12px;
  border-radius: 8px;
}

.login-error {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  color: #dc2626;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 13px;
  margin-bottom: 14px;
}

.btn-login {
  width: 100%;
  padding: 11px;
  background: linear-gradient(135deg, #1a5276, #6c3483);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.15s;
  margin-top: 4px;
}
.btn-login:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-login:not(:disabled):hover { opacity: 0.9; }

.login-hint {
  text-align: center;
  font-size: 11px;
  color: #94a3b8;
  margin-top: 20px;
}
</style>
