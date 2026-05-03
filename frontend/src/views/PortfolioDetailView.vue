<script setup lang="ts">
import { ref, computed, reactive, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { usePortfolioStore } from '@/stores/portfolio'
import { api } from '@/api'
import PieChart from '@/components/PieChart.vue'
import ImportModal from '@/components/ImportModal.vue'
import type { Security, SecurityCreatePayload } from '@/types'

const route = useRoute()
const store = usePortfolioStore()
const portfolioId = computed(() => Number(route.params.id))
const showImport = ref(false)
const saving = ref(false)

// ── 稅率對照 ──────────────────────────────────────────
const TAX_RATES: Record<string, number> = {
  '股票-個股': 0.003, '股票ETF': 0.001, '債券-ETF': 0, 'CB': 0.001, 'CBAS': 0.001,
}

// ── 計算工具 ──────────────────────────────────────────
function calcRow(price: number | null, shares: number, feeRate: number, taxRate: number, unavail: boolean) {
  if (unavail || !price || !shares) return { mv1: 0, fee: 0, tax: 0, mv2: 0 }
  const mv1 = price * shares
  const fee = Math.round(mv1 * feeRate)
  const tax = Math.round(mv1 * taxRate)
  return { mv1, fee, tax, mv2: mv1 - fee - tax }
}

// ── 新增列（表格底部常駐） ─────────────────────────────
const newRow = reactive({
  sec_id: '', sec_name: '', curr_price: null as number | null,
  asset_type: '股票-個股', shares: 0,
  fee_rate: 0.001425, tax_rate: 0.003,
  price_unavailable: false,
})
const lookingUp = ref(false)
const lookupMsg = ref('')

const newCalc = computed(() =>
  calcRow(newRow.curr_price, newRow.shares, newRow.fee_rate, newRow.tax_rate ?? 0, newRow.price_unavailable)
)

function resetNew() {
  Object.assign(newRow, {
    sec_id: '', sec_name: '', curr_price: null,
    asset_type: '股票-個股', shares: 0,
    fee_rate: 0.001425, tax_rate: 0.003, price_unavailable: false,
  })
  lookupMsg.value = ''
}

async function onSecIdBlur() {
  if (!newRow.sec_id.trim()) return
  lookingUp.value = true
  lookupMsg.value = '查詢中…'
  try {
    const r = await api.lookupStock(newRow.sec_id.trim())
    if (r.found) {
      newRow.sec_name = r.sec_name
      newRow.curr_price = r.curr_price
      lookupMsg.value = r.curr_price ? '' : '查到名稱，但股價暫無（非交易時段）'
    } else {
      lookupMsg.value = '查無此代號，請手動確認'
    }
  } catch {
    lookupMsg.value = '查詢失敗'
  } finally {
    lookingUp.value = false
  }
}

function onNewAssetTypeChange() {
  newRow.tax_rate = TAX_RATES[newRow.asset_type] ?? 0.003
}

async function saveNewRow() {
  if (!newRow.sec_id.trim() || !newRow.sec_name.trim() || newRow.shares <= 0) return
  saving.value = true
  try {
    await api.createSecurity(portfolioId.value, { ...newRow })
    resetNew()
    await store.fetchPortfolio(portfolioId.value)
    await nextTick()
    document.getElementById('new-sec-id')?.focus()
  } finally {
    saving.value = false
  }
}

function onNewKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') saveNewRow()
  if (e.key === 'Escape') resetNew()
}

// ── 行內編輯（雙擊現有列） ────────────────────────────
const editingId = ref<number | null>(null)
const editRow = reactive<SecurityCreatePayload>({
  sec_id: '', sec_name: '', curr_price: null,
  asset_type: '股票-個股', shares: 0,
  fee_rate: 0.001425, tax_rate: 0.003, price_unavailable: false,
})

const editCalc = computed(() =>
  calcRow(editRow.curr_price, editRow.shares, editRow.fee_rate ?? 0.001425, editRow.tax_rate ?? 0.003, editRow.price_unavailable)
)

function startEdit(s: Security) {
  editingId.value = s.id
  Object.assign(editRow, {
    sec_id: s.sec_id, sec_name: s.sec_name,
    curr_price: s.curr_price != null ? Number(s.curr_price) : null,
    asset_type: s.asset_type, shares: s.shares,
    fee_rate: Number(s.fee_rate), tax_rate: Number(s.tax_rate),
    price_unavailable: s.price_unavailable,
  })
}

async function saveEdit() {
  if (!editingId.value) return
  await api.updateSecurity(editingId.value, { ...editRow })
  editingId.value = null
  store.fetchPortfolio(portfolioId.value)
}

function cancelEdit() { editingId.value = null }

function onEditKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') saveEdit()
  if (e.key === 'Escape') cancelEdit()
}

const editLookingUp = ref(false)
const editLookupMsg = ref('')

async function onEditSecIdBlur() {
  if (!editRow.sec_id.trim()) return
  editLookingUp.value = true
  editLookupMsg.value = ''
  try {
    const r = await api.lookupStock(editRow.sec_id.trim())
    if (r.found) {
      editRow.sec_name = r.sec_name
      if (r.curr_price != null) editRow.curr_price = r.curr_price
      editLookupMsg.value = r.curr_price ? '' : '查到名稱，但股價暫無'
    } else {
      editLookupMsg.value = '查無此代號'
    }
  } catch {
    editLookupMsg.value = '查詢失敗'
  } finally {
    editLookingUp.value = false
  }
}

function onEditAssetTypeChange() {
  const found = store.assetTypes.find(a => a.asset_type === editRow.asset_type)
  if (found) editRow.tax_rate = Number(found.default_tax_rate)
}

// ── 批次更新報價 ──────────────────────────────────────
const refreshing = ref(false)
const refreshMsg = ref('')

async function refreshPrices() {
  if (!store.current?.securities.length) return
  refreshing.value = true
  refreshMsg.value = ''
  let updated = 0
  try {
    for (const s of store.current.securities) {
      if (s.price_unavailable) continue
      try {
        const r = await api.lookupStock(s.sec_id)
        if (r.found) {
          const upd: Record<string, unknown> = { sec_name: r.sec_name }
          if (r.curr_price != null) { upd.curr_price = r.curr_price; upd.price_unavailable = false }
          await api.updateSecurity(s.id, upd)
          updated++
        }
      } catch { /* 單筆失敗不中斷 */ }
    }
    await store.fetchPortfolio(portfolioId.value)
    refreshMsg.value = `已更新 ${updated} 筆`
    setTimeout(() => { refreshMsg.value = '' }, 3000)
  } finally {
    refreshing.value = false
  }
}

// ── 刪除 ─────────────────────────────────────────────
async function deleteSecurity(s: Security, e: MouseEvent) {
  e.stopPropagation()
  if (!confirm(`確定刪除「${s.sec_name}」？`)) return
  await api.deleteSecurity(s.id)
  store.fetchPortfolio(portfolioId.value)
}

// ── 匯入 ─────────────────────────────────────────────
async function onImport(rows: SecurityCreatePayload[]) {
  await api.importSecurities(portfolioId.value, rows)
  showImport.value = false
  store.fetchPortfolio(portfolioId.value)
}

// ── 格式化 ───────────────────────────────────────────
function fmt(n: number | string) {
  return Number(n).toLocaleString('zh-TW', { maximumFractionDigits: 0 })
}
function fmtPrice(n: number | string | null) {
  if (n == null) return '—'
  const v = Number(n)
  return v % 1 === 0 ? v.toLocaleString('zh-TW') : v.toLocaleString('zh-TW', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function fmtPct(n: number | string) {
  return (Number(n) * 100).toFixed(4) + '%'
}
function fmtInput(v: number | null | undefined): string {
  if (v == null) return ''
  const n = Number(v)
  return isNaN(n) ? '' : n.toLocaleString('zh-TW', { maximumFractionDigits: 4 })
}
function parseInput(e: Event): number | null {
  const s = (e.target as HTMLInputElement).value.replace(/,/g, '').trim()
  if (!s) return null
  const n = parseFloat(s)
  return isNaN(n) ? null : n
}
function badgeClass(type: string) {
  if (type === '股票-個股') return 'badge badge-stock'
  if (type.includes('債')) return 'badge badge-bond'
  if (type.includes('ETF')) return 'badge badge-etf'
  return 'badge badge-cb'
}

onMounted(async () => {
  await store.fetchPortfolio(portfolioId.value)
  await store.fetchAssetTypes()
})
</script>

<template>
  <div v-if="store.loading" class="text-muted">載入中…</div>
  <div v-else-if="store.error" class="text-danger">{{ store.error }}</div>
  <template v-else-if="store.current">

    <!-- Header -->
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
      <div>
        <router-link to="/portfolios?tab=assets" class="text-muted" style="font-size:13px">← 返回列表</router-link>
        <h1 style="font-size:20px;font-weight:700;margin-top:4px">{{ store.current.name }}</h1>
      </div>
      <button class="btn btn-ghost" @click="showImport=true">⬆ 批次匯入</button>
    </div>

    <!-- Summary cards -->
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr 280px;gap:12px;margin-bottom:16px;align-items:start">
      <div class="card" style="padding:12px">
        <div class="text-muted" style="font-size:11px">市值計算(1)</div>
        <div style="font-size:16px;font-weight:700">{{ fmt(store.current.totals.mv_1) }}</div>
      </div>
      <div class="card" style="padding:12px">
        <div class="text-muted" style="font-size:11px">交易費用</div>
        <div style="font-size:16px;font-weight:700;color:#b45309">{{ fmt(store.current.totals.tx_fee) }}</div>
      </div>
      <div class="card" style="padding:12px">
        <div class="text-muted" style="font-size:11px">證交稅</div>
        <div style="font-size:16px;font-weight:700;color:#b45309">{{ fmt(store.current.totals.tx_tax) }}</div>
      </div>
      <div class="card" style="padding:12px">
        <div class="text-muted" style="font-size:11px">市值計算(2) 淨值</div>
        <div style="font-size:16px;font-weight:700">{{ fmt(store.current.totals.mv_2) }}</div>
      </div>
      <div class="card" style="padding:12px">
        <div class="text-muted" style="font-size:11px;margin-bottom:6px">資產配置</div>
        <PieChart :data="store.current.by_asset_type" />
      </div>
    </div>

    <!-- Category totals -->
    <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px">
      <div v-for="g in store.current.by_asset_type" :key="g.asset_type"
        class="card" style="padding:8px 14px;display:flex;align-items:center;gap:10px">
        <span :class="badgeClass(g.asset_type)">{{ g.asset_type }}</span>
        <strong style="font-size:13px">{{ fmt(g.mv_2) }}</strong>
      </div>
    </div>

    <!-- Main table -->
    <div class="card" style="padding:0;overflow:hidden">
      <div style="background:#1a5276;padding:9px 14px;display:flex;align-items:center;justify-content:space-between">
        <span style="color:#fff;font-weight:700;font-size:13px">證券明細概覽</span>
        <span style="color:#aed6f1;font-size:12px">共 {{ store.current.securities.length }} 筆・雙擊列可編輯</span>
      </div>

      <div style="overflow-x:auto">
        <table class="table excel-table">
          <thead>
            <tr>
              <th style="width:88px">證券代號</th>
              <th style="min-width:110px">證券名稱</th>
              <th class="num" style="width:90px">最新股價</th>
              <th style="width:100px">資產類別</th>
              <th class="num" style="width:90px">購買股數</th>
              <th class="num" style="width:110px">市值計算(1)</th>
              <th class="num" style="width:80px">交易費用</th>
              <th class="num" style="width:70px">證交稅</th>
              <th class="num" style="width:110px">市值計算(2)</th>
              <th class="num" style="width:72px">費率</th>
              <th class="num" style="width:72px">稅率</th>
              <th style="width:52px"></th>
            </tr>
          </thead>
          <tbody>
            <!-- Existing rows -->
            <template v-for="s in store.current.securities" :key="s.id">
              <tr v-if="editingId !== s.id" class="data-row" @dblclick="startEdit(s)">
                <td class="sec-id">{{ s.sec_id }}</td>
                <td style="font-weight:600">{{ s.sec_name }}</td>
                <td class="num">
                  <span v-if="s.price_unavailable" class="unavailable">無法讀取</span>
                  <span v-else>{{ fmtPrice(s.curr_price) }}</span>
                </td>
                <td><span :class="badgeClass(s.asset_type)">{{ s.asset_type }}</span></td>
                <td class="num">{{ s.shares.toLocaleString() }}</td>
                <td class="num fw-bold">{{ fmt(s.mv_1) }}</td>
                <td class="num text-muted">{{ fmt(s.tx_fee) }}</td>
                <td class="num text-muted">{{ fmt(s.tx_tax) }}</td>
                <td class="num fw-bold">{{ fmt(s.mv_2) }}</td>
                <td class="num text-muted" style="font-size:11px">{{ fmtPct(s.fee_rate) }}</td>
                <td class="num text-muted" style="font-size:11px">{{ fmtPct(s.tax_rate) }}</td>
                <td>
                  <button class="btn btn-danger btn-sm" style="padding:2px 7px;font-size:11px"
                    @click="deleteSecurity(s, $event)">刪</button>
                </td>
              </tr>

              <!-- Inline edit mode (雙擊後) -->
              <tr v-else class="edit-row" @keydown="onEditKeydown">
                <td><input class="cell-input" v-model="editRow.sec_id" /></td>
                <td><input class="cell-input" v-model="editRow.sec_name" /></td>
                <td><input class="cell-input num" type="text" :value="fmtInput(editRow.curr_price)" @change="editRow.curr_price = parseInput($event) ?? 0" /></td>
                <td>
                  <select class="cell-input" v-model="editRow.asset_type">
                    <option v-for="t in store.assetTypes" :key="t.asset_type" :value="t.asset_type">{{ t.asset_type }}</option>
                  </select>
                </td>
                <td><input class="cell-input num" type="text" :value="fmtInput(editRow.shares)" @change="editRow.shares = parseInput($event) ?? 0" /></td>
                <td class="num fw-bold">{{ fmt(editCalc.mv1) }}</td>
                <td class="num text-muted">{{ fmt(editCalc.fee) }}</td>
                <td class="num text-muted">{{ fmt(editCalc.tax) }}</td>
                <td class="num fw-bold">{{ fmt(editCalc.mv2) }}</td>
                <td colspan="2" class="text-muted" style="font-size:11px;text-align:center">Enter 儲存<br/>Esc 取消</td>
                <td>
                  <button class="btn btn-primary btn-sm" style="padding:2px 6px;font-size:11px" @click="saveEdit">✓</button>
                </td>
              </tr>
            </template>

            <!-- 新增列（底部常駐，僅輸入3欄） -->
            <tr class="new-row" @keydown="onNewKeydown">
              <td>
                <input id="new-sec-id" class="cell-input" v-model="newRow.sec_id"
                  placeholder="代號" @blur="onSecIdBlur" title="輸入代號後按 Tab 自動查詢" />
              </td>
              <td>
                <div style="display:flex;align-items:center;gap:4px">
                  <input class="cell-input" v-model="newRow.sec_name" placeholder="自動帶出"
                    :readonly="lookingUp" style="flex:1" />
                  <span v-if="lookingUp" style="font-size:11px;color:#64748b">⏳</span>
                </div>
                <div v-if="lookupMsg" style="font-size:10px;color:#d97706;margin-top:2px">{{ lookupMsg }}</div>
              </td>
              <td class="num">
                <input class="cell-input num" type="text" :value="fmtInput(newRow.curr_price)"
                  @change="newRow.curr_price = parseInput($event)" placeholder="自動帶出" :readonly="lookingUp" />
              </td>
              <td>
                <select class="cell-input" v-model="newRow.asset_type" @change="onNewAssetTypeChange">
                  <option v-for="t in store.assetTypes" :key="t.asset_type" :value="t.asset_type">{{ t.asset_type }}</option>
                </select>
              </td>
              <td>
                <input class="cell-input num" type="text" :value="fmtInput(newRow.shares || null)"
                  @change="newRow.shares = parseInput($event) ?? 0" placeholder="股數" />
              </td>
              <td class="num fw-bold">{{ newRow.shares > 0 && newRow.curr_price ? fmt(newCalc.mv1) : '—' }}</td>
              <td class="num text-muted">{{ newRow.shares > 0 && newRow.curr_price ? fmt(newCalc.fee) : '—' }}</td>
              <td class="num text-muted">{{ newRow.shares > 0 && newRow.curr_price ? fmt(newCalc.tax) : '—' }}</td>
              <td class="num fw-bold">{{ newRow.shares > 0 && newRow.curr_price ? fmt(newCalc.mv2) : '—' }}</td>
              <td colspan="2" class="text-muted" style="font-size:10px;text-align:center;vertical-align:middle">
                Tab 查詢<br/>Enter 儲存
              </td>
              <td>
                <button class="btn btn-primary btn-sm" style="padding:3px 8px;font-size:12px"
                  :disabled="!newRow.sec_id.trim() || !newRow.sec_name.trim() || newRow.shares <= 0 || saving"
                  @click="saveNewRow">
                  {{ saving ? '…' : '＋' }}
                </button>
              </td>
            </tr>
          </tbody>

          <tfoot>
            <tr>
              <td colspan="5" style="font-style:italic;color:#888;font-size:12px;padding-left:12px">合計</td>
              <td class="num fw-bold">{{ fmt(store.current.totals.mv_1) }}</td>
              <td class="num fw-bold">{{ fmt(store.current.totals.tx_fee) }}</td>
              <td class="num fw-bold">{{ fmt(store.current.totals.tx_tax) }}</td>
              <td class="num fw-bold">{{ fmt(store.current.totals.mv_2) }}</td>
              <td colspan="3"></td>
            </tr>
          </tfoot>
        </table>
      </div>

      <div style="background:#1a5276;padding:7px 14px;display:flex;gap:20px;flex-wrap:wrap">
        <div v-for="g in store.current.by_asset_type" :key="g.asset_type"
          style="color:#fff;font-size:13px;font-weight:600">
          {{ g.asset_type }}：{{ fmt(g.mv_2) }}
        </div>
      </div>
    </div>

    <ImportModal v-if="showImport" @close="showImport=false" @import="onImport" />
  </template>
</template>

<style scoped>
.excel-table th {
  background: #1a5276;
  color: #d6eaf8;
  font-weight: 600;
  white-space: nowrap;
  font-size: 12px;
  padding: 8px 10px;
}
.excel-table tfoot td {
  background: #f8fafc;
  border-top: 2px solid #cbd5e1;
  padding: 7px 10px;
}
.data-row { cursor: pointer; }
.data-row:hover td { background: #f0f8ff; }
.edit-row td { background: #fffde7 !important; padding: 3px 4px; }
.new-row td { background: #f0fff4; padding: 3px 4px; border-top: 2px dashed #27ae60; }

.cell-input {
  width: 100%;
  border: 1px solid #cbd5e1;
  border-radius: 3px;
  padding: 3px 5px;
  font-size: 12px;
  background: #fff;
  outline: none;
  box-sizing: border-box;
}
.cell-input:focus { border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,0.15); }
.cell-input.num { text-align: right; }
.cell-input[readonly] { background: #f1f5f9; color: #64748b; }
.sec-id { font-style: italic; color: #555; }
</style>
