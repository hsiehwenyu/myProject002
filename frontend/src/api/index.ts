import { useAuthStore } from '@/stores/auth'
import type {
  Portfolio, PortfolioDetail, Security,
  SecurityCreatePayload, AssetTypeDefault,
} from '@/types'

const BASE = '/api/v1'

async function req<T>(url: string, options?: RequestInit): Promise<T> {
  const auth = useAuthStore()
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (auth.token) headers['Authorization'] = `Bearer ${auth.token}`

  const res = await fetch(BASE + url, { headers, ...options })

  if (res.status === 401) {
    auth.logout()
    window.location.href = '/login'
    throw new Error('登入已逾時')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? res.statusText)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export interface UserRead {
  id: number
  username: string
  role: string
  is_active: boolean
  created_at: string
}

export interface MenuItemRead {
  id: number
  label: string
  url: string
  icon: string
  sort_order: number
  is_active: boolean
  min_role: string
}

export const api = {
  // Portfolios
  getPortfolios: () => req<Portfolio[]>('/portfolios/'),
  createPortfolio: (data: { name: string; description?: string }) =>
    req<Portfolio>('/portfolios/', { method: 'POST', body: JSON.stringify(data) }),
  getPortfolio: (id: number) => req<PortfolioDetail>(`/portfolios/${id}`),
  updatePortfolio: (id: number, data: { name?: string; description?: string }) =>
    req<Portfolio>(`/portfolios/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deletePortfolio: (id: number) => req<void>(`/portfolios/${id}`, { method: 'DELETE' }),

  // Securities
  getSecurities: (portfolioId: number) =>
    req<Security[]>(`/portfolios/${portfolioId}/securities`),
  createSecurity: (portfolioId: number, data: SecurityCreatePayload) =>
    req<Security>(`/portfolios/${portfolioId}/securities`, {
      method: 'POST', body: JSON.stringify(data),
    }),
  updateSecurity: (id: number, data: Partial<SecurityCreatePayload>) =>
    req<Security>(`/securities/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  updateSecurityPrice: (id: number, data: { curr_price: number | null; price_unavailable: boolean }) =>
    req<Security>(`/securities/${id}/price`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteSecurity: (id: number) => req<void>(`/securities/${id}`, { method: 'DELETE' }),
  importSecurities: (portfolioId: number, rows: SecurityCreatePayload[]) =>
    req<Security[]>(`/portfolios/${portfolioId}/import`, {
      method: 'POST', body: JSON.stringify(rows),
    }),

  // Stock lookup
  lookupStock: (stockId: string) =>
    req<{ sec_id: string; found: boolean; sec_name: string; curr_price: number | null }>(
      `/stocks/${stockId}`
    ),

  // Meta
  getAssetTypes: () => req<AssetTypeDefault[]>('/asset-types'),

  // Users (admin only)
  getUsers: () => req<UserRead[]>('/users/'),
  createUser: (data: { username: string; password: string; role: string }) =>
    req<UserRead>('/users/', { method: 'POST', body: JSON.stringify(data) }),
  updateUser: (id: number, data: { password?: string; role?: string; is_active?: boolean }) =>
    req<UserRead>(`/users/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteUser: (id: number) => req<void>(`/users/${id}`, { method: 'DELETE' }),

  // Menu items
  getMenuItems: () => req<MenuItemRead[]>('/menu-items/'),
  getAllMenuItems: () => req<MenuItemRead[]>('/menu-items/all'),
  createMenuItem: (data: Omit<MenuItemRead, 'id'>) =>
    req<MenuItemRead>('/menu-items/', { method: 'POST', body: JSON.stringify(data) }),
  updateMenuItem: (id: number, data: Partial<Omit<MenuItemRead, 'id'>>) =>
    req<MenuItemRead>(`/menu-items/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteMenuItem: (id: number) => req<void>(`/menu-items/${id}`, { method: 'DELETE' }),
}
