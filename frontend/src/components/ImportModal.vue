<script setup lang="ts">
import { ref } from 'vue'
import type { SecurityCreatePayload } from '@/types'

const emit = defineEmits<{
  close: []
  import: [rows: SecurityCreatePayload[]]
}>()

const text = ref('')
const preview = ref<SecurityCreatePayload[]>([])
const parseError = ref('')
const importing = ref(false)

const ASSET_TYPE_MAP: Record<string, string> = {
  '股票ETF': '股票ETF', '股票 ETF': '股票ETF',
  '債券-ETF': '債券-ETF', '債劵-ETF': '債券-ETF', '債券ETF': '債券-ETF',
  '股票-個股': '股票-個股', '個股': '股票-個股',
  'CB': 'CB', 'CBAS': 'CBAS',
}

function normalizeAssetType(raw: string): string {
  const trimmed = raw.trim()
  for (const [k, v] of Object.entries(ASSET_TYPE_MAP)) {
    if (trimmed.includes(k) || k.includes(trimmed)) return v
  }
  if (trimmed.includes('債') && trimmed.includes('ETF')) return '債券-ETF'
  if (trimmed.includes('ETF')) return '股票ETF'
  if (trimmed.includes('股票') || trimmed.includes('個股')) return '股票-個股'
  return trimmed || '股票-個股'
}

function parseText() {
  parseError.value = ''
  preview.value = []
  if (!text.value.trim()) return

  const lines = text.value.trim().split('\n').map(l => l.trim()).filter(Boolean)
  const rows: SecurityCreatePayload[] = []

  for (const line of lines) {
    // Support both tab and comma separated
    const cols = line.includes('\t') ? line.split('\t') : line.split(',')
    const c = cols.map(x => x.trim().replace(/^"|"$/g, ''))

    const sec_id = c[0]
    const sec_name = c[1]
    if (!sec_id || !sec_name || sec_id === '證券代號' || sec_id === '代號') continue

    const priceStr = c[2]?.replace(/,/g, '') ?? ''
    const assetTypeRaw = c[3] ?? ''
    const sharesStr = c[4]?.replace(/,/g, '') ?? '0'

    const price_unavailable = sec_name === '無法讀取網頁' || priceStr === '' || priceStr === '-'
    const curr_price = price_unavailable ? null : (isNaN(Number(priceStr)) ? null : Number(priceStr))
    const shares = parseInt(sharesStr) || 0
    const asset_type = normalizeAssetType(assetTypeRaw)

    // Determine default tax_rate from asset_type
    const taxRateMap: Record<string, number> = {
      '股票-個股': 0.003, '股票ETF': 0.001, '債券-ETF': 0, 'CB': 0.001, 'CBAS': 0.001,
    }

    rows.push({
      sec_id, sec_name, curr_price, asset_type, shares,
      fee_rate: 0.001425,
      tax_rate: taxRateMap[asset_type] ?? 0.003,
      price_unavailable,
    })
  }

  if (!rows.length) {
    parseError.value = '未能解析出任何資料，請確認格式（欄位順序：代號、名稱、股價、類別、股數）'
    return
  }
  preview.value = rows
}

async function doImport() {
  importing.value = true
  try {
    emit('import', preview.value)
  } finally {
    importing.value = false
  }
}
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal" style="width:680px;max-height:90vh;overflow-y:auto">
      <div class="modal-title">批次匯入資產</div>

      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:12px;margin-bottom:14px;font-size:12px;color:#64748b">
        <strong style="color:#1e293b">匯入格式（Tab 或逗號分隔，可直接從 Excel 複製貼上）：</strong><br/>
        欄位順序：<code>證券代號 &nbsp;證券名稱 &nbsp;最新股價 &nbsp;資產類別 &nbsp;購買股數</code><br/>
        資產類別可填：股票-個股 / 股票ETF / 債券-ETF / CB / CBAS<br/>
        股價無法取得時，名稱填「無法讀取網頁」或股價留空即可
      </div>

      <div class="form-group">
        <label>貼上資料</label>
        <textarea v-model="text" class="form-control" rows="8"
          placeholder="00662&#9;富邦NASDAQ&#9;110.45&#9;股票ETF&#9;6100&#10;2330&#9;台積電&#9;2135&#9;股票-個股&#9;3000"
          style="font-family:monospace;font-size:12px" />
      </div>

      <button class="btn btn-ghost" style="margin-bottom:14px" @click="parseText">解析預覽</button>

      <div v-if="parseError" class="text-danger" style="font-size:13px;margin-bottom:10px">{{ parseError }}</div>

      <div v-if="preview.length">
        <div style="font-size:13px;font-weight:600;margin-bottom:8px">預覽（共 {{ preview.length }} 筆）</div>
        <div style="overflow-x:auto;max-height:260px;overflow-y:auto;border:1px solid #e2e8f0;border-radius:6px">
          <table class="table" style="font-size:12px">
            <thead>
              <tr>
                <th>代號</th><th>名稱</th><th class="num">股價</th>
                <th>類別</th><th class="num">股數</th><th class="num">市值(1)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(r, i) in preview" :key="i">
                <td>{{ r.sec_id }}</td>
                <td :class="r.price_unavailable ? 'unavailable' : ''">{{ r.sec_name }}</td>
                <td class="num">{{ r.price_unavailable ? '—' : (r.curr_price ?? '—') }}</td>
                <td>{{ r.asset_type }}</td>
                <td class="num">{{ r.shares.toLocaleString() }}</td>
                <td class="num">
                  {{ r.curr_price != null ? (r.curr_price * r.shares).toLocaleString(undefined, {maximumFractionDigits:0}) : 0 }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="modal-actions">
        <button class="btn btn-ghost" @click="emit('close')">取消</button>
        <button class="btn btn-primary" :disabled="!preview.length || importing" @click="doImport">
          {{ importing ? '匯入中…' : `確認匯入 ${preview.length} 筆` }}
        </button>
      </div>
    </div>
  </div>
</template>
