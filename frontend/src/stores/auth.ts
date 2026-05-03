import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('invest_token'))
  const username = ref<string>(localStorage.getItem('invest_user') ?? '')
  const role = ref<string>(localStorage.getItem('invest_role') ?? '')

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => role.value === 'admin')

  function setLogin(newToken: string, user: string, userRole: string) {
    token.value = newToken
    username.value = user
    role.value = userRole
    localStorage.setItem('invest_token', newToken)
    localStorage.setItem('invest_user', user)
    localStorage.setItem('invest_role', userRole)
  }

  function logout() {
    token.value = null
    username.value = ''
    role.value = ''
    localStorage.removeItem('invest_token')
    localStorage.removeItem('invest_user')
    localStorage.removeItem('invest_role')
  }

  return { token, username, role, isAuthenticated, isAdmin, setLogin, logout }
})
