import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api'
import type { Portfolio, PortfolioDetail, AssetTypeDefault } from '@/types'

export const usePortfolioStore = defineStore('portfolio', () => {
  const portfolios = ref<Portfolio[]>([])
  const current = ref<PortfolioDetail | null>(null)
  const assetTypes = ref<AssetTypeDefault[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchPortfolios() {
    loading.value = true
    error.value = null
    try {
      portfolios.value = await api.getPortfolios()
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchPortfolio(id: number) {
    loading.value = true
    error.value = null
    try {
      current.value = await api.getPortfolio(id)
    } catch (e: any) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchAssetTypes() {
    if (assetTypes.value.length) return
    assetTypes.value = await api.getAssetTypes()
  }

  return { portfolios, current, assetTypes, loading, error, fetchPortfolios, fetchPortfolio, fetchAssetTypes }
})
