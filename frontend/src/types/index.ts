export interface Portfolio {
  id: number
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface Security {
  id: number
  portfolio_id: number
  sec_id: string
  sec_name: string
  curr_price: number | null
  asset_type: string
  shares: number
  fee_rate: number
  tax_rate: number
  price_unavailable: boolean
  mv_1: number
  tx_fee: number
  tx_tax: number
  mv_2: number
  created_at: string
  updated_at: string
}

export interface AssetTypeSummary {
  asset_type: string
  count: number
  mv_1: number
  tx_fee: number
  tx_tax: number
  mv_2: number
}

export interface PortfolioTotals {
  mv_1: number
  tx_fee: number
  tx_tax: number
  mv_2: number
}

export interface PortfolioDetail extends Portfolio {
  securities: Security[]
  totals: PortfolioTotals
  by_asset_type: AssetTypeSummary[]
}

export interface AssetTypeDefault {
  asset_type: string
  default_tax_rate: string
}

export interface SecurityCreatePayload {
  sec_id: string
  sec_name: string
  curr_price: number | null
  asset_type: string
  shares: number
  fee_rate?: number
  tax_rate?: number
  price_unavailable: boolean
}
