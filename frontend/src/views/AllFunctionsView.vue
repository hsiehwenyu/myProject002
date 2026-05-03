<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

interface FuncItem {
  icon: string
  label: string
  desc: string
  path: string
  adminOnly?: boolean
  external?: boolean
}

interface FuncGroup {
  group: string
  items: FuncItem[]
}

const functions: FuncGroup[] = [
  {
    group: '主要作業',
    items: [
      {
        icon: '🏠',
        label: 'Portal 首頁',
        desc: '可設定的作業連結入口頁',
        path: '/',
      },
      {
        icon: '📁',
        label: '投資組合管理',
        desc: '建立、查閱、刪除投資組合',
        path: '/portfolios',
      },
      {
        icon: '📈',
        label: '持股明細',
        desc: '進入投資組合後查看持股、損益',
        path: '/portfolios',
      },
    ],
  },
  {
    group: '系統管理',
    items: [
      {
        icon: '👥',
        label: '帳號管理',
        desc: '新增 / 編輯 / 停用系統帳號',
        path: '/admin/users',
        adminOnly: true,
      },
      {
        icon: '🗂️',
        label: '選單管理',
        desc: '設定 Portal 首頁顯示的作業連結',
        path: '/admin/menu',
        adminOnly: true,
      },
    ],
  },
  {
    group: 'API 文件',
    items: [
      {
        icon: '📄',
        label: 'Swagger UI',
        desc: '互動式 API 文件，可直接測試所有端點',
        path: 'http://localhost:8001/docs',
        external: true,
      },
      {
        icon: '📋',
        label: 'ReDoc',
        desc: '閱讀友善的 API 規格文件',
        path: 'http://localhost:8001/redoc',
        external: true,
      },
    ],
  },
]
</script>

<template>
  <div class="all-functions">
    <div class="page-header">
      <h2 class="page-title">功能總覽</h2>
      <p class="page-subtitle">系統所有作業功能的快速入口</p>
    </div>

    <div v-for="group in functions" :key="group.group" class="func-group">
      <h3 class="group-label">{{ group.group }}</h3>
      <div class="func-grid">
        <template v-for="item in group.items" :key="item.path + item.label">
          <a
            v-if="item.external"
            :href="item.path"
            target="_blank"
            rel="noopener"
            class="func-card"
          >
            <div class="func-icon">{{ item.icon }}</div>
            <div class="func-body">
              <div class="func-label">
                {{ item.label }}
                <span class="badge-ext">外部</span>
              </div>
              <div class="func-desc">{{ item.desc }}</div>
            </div>
            <span class="func-arrow">↗</span>
          </a>

          <router-link
            v-else-if="!item.adminOnly || auth.isAdmin"
            :to="item.path"
            class="func-card"
          >
            <div class="func-icon">{{ item.icon }}</div>
            <div class="func-body">
              <div class="func-label">
                {{ item.label }}
                <span v-if="item.adminOnly" class="badge-admin">Admin</span>
              </div>
              <div class="func-desc">{{ item.desc }}</div>
            </div>
            <span class="func-arrow">›</span>
          </router-link>

          <div v-else class="func-card disabled">
            <div class="func-icon">{{ item.icon }}</div>
            <div class="func-body">
              <div class="func-label">
                {{ item.label }}
                <span class="badge-lock">需要 Admin</span>
              </div>
              <div class="func-desc">{{ item.desc }}</div>
            </div>
            <span class="func-arrow muted">🔒</span>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.all-functions {
  max-width: 760px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 28px;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 4px;
}

.page-subtitle {
  font-size: 13px;
  color: #64748b;
}

.func-group {
  margin-bottom: 28px;
}

.group-label {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #94a3b8;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid #f1f5f9;
}

.func-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.func-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  background: #fff;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  text-decoration: none;
  color: #1e293b;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.func-card:not(.disabled):hover {
  border-color: #1a5276;
  box-shadow: 0 2px 10px rgba(26, 82, 118, 0.1);
}

.func-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.func-icon {
  font-size: 26px;
  width: 36px;
  text-align: center;
  flex-shrink: 0;
}

.func-body {
  flex: 1;
  min-width: 0;
}

.func-label {
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 2px;
}

.func-desc {
  font-size: 12px;
  color: #64748b;
}

.func-arrow {
  font-size: 18px;
  color: #94a3b8;
  flex-shrink: 0;
}

.func-arrow.muted {
  font-size: 14px;
}

.badge-admin {
  font-size: 10px;
  font-weight: 700;
  background: #ede9fe;
  color: #6d28d9;
  padding: 1px 6px;
  border-radius: 4px;
}

.badge-lock {
  font-size: 10px;
  font-weight: 700;
  background: #f1f5f9;
  color: #94a3b8;
  padding: 1px 6px;
  border-radius: 4px;
}

.badge-ext {
  font-size: 10px;
  font-weight: 700;
  background: #dcfce7;
  color: #16a34a;
  padding: 1px 6px;
  border-radius: 4px;
}
</style>
