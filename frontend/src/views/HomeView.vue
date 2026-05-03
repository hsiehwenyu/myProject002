<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePortfolioStore } from '@/stores/portfolio'
import { api } from '@/api'

const store = usePortfolioStore()
const router = useRouter()

// ── Portfolio CRUD ─────────────────────────────────────
const showCreate = ref(false)
const form = ref({ name: '', description: '' })
const saving = ref(false)
const createError = ref<string | null>(null)

onMounted(() => {
  store.fetchPortfolios()
  loadStorage()
})

async function createPortfolio() {
  if (!form.value.name.trim()) return
  saving.value = true
  createError.value = null
  try {
    const p = await api.createPortfolio({ name: form.value.name, description: form.value.description || undefined })
    store.portfolios.unshift(p)
    showCreate.value = false
    form.value = { name: '', description: '' }
  } catch (e: any) {
    createError.value = e.message ?? '新增失敗，請確認 Backend 是否正常運行'
  } finally {
    saving.value = false
  }
}

async function deletePortfolio(id: number, name: string) {
  if (!confirm(`確定刪除「${name}」及其所有資產？`)) return
  try {
    await api.deletePortfolio(id)
    store.portfolios = store.portfolios.filter(p => p.id !== id)
    totalRows.value = totalRows.value.filter(r => r.linkedPortfolioId !== id)
  } catch (e: any) {
    alert('刪除失敗：' + (e.message ?? '未知錯誤'))
  }
}

// ── 資產總計 ──────────────────────────────────────────
const ASSET_COLS = ['股票-個股', '股票ETF', '債券-ETF', 'CB', 'CBAS'] as const
type AssetCol = typeof ASSET_COLS[number]

interface TotalRow {
  id: number
  accountType: string
  marketValue: number | null
  mark: string
  linkedPortfolioId: number | null
  breakdown: Partial<Record<AssetCol, number>>
}

const LS_ROWS = 'ta_rows_v1'
const LS_TYPES = 'ta_types_v1'

const acctTypes = ref<string[]>(['證券帳戶', '銀行帳戶'])
const totalRows = ref<TotalRow[]>([])
let _nid = 1

function loadStorage() {
  try {
    const r = localStorage.getItem(LS_ROWS)
    if (r) {
      totalRows.value = JSON.parse(r)
      _nid = totalRows.value.reduce((m, x) => Math.max(m, x.id), 0) + 1
    }
    const t = localStorage.getItem(LS_TYPES)
    if (t) acctTypes.value = JSON.parse(t)
  } catch {}
}

watch(totalRows, v => localStorage.setItem(LS_ROWS, JSON.stringify(v)), { deep: true })
watch(acctTypes, v => localStorage.setItem(LS_TYPES, JSON.stringify(v)), { deep: true })

function addEmptyRow() {
  totalRows.value.push({
    id: _nid++, accountType: '銀行帳戶',
    marketValue: null, mark: '',
    linkedPortfolioId: null, breakdown: {},
  })
}

function delRow(id: number) {
  if (!confirm('確定刪除此列？')) return
  totalRows.value = totalRows.value.filter(r => r.id !== id)
}

const showPicker = ref(false)
const pickerLoading = ref(false)

async function linkPortfolio(pid: number) {
  if (totalRows.value.some(r => r.linkedPortfolioId === pid)) {
    alert('此證券明細已帶入')
    return
  }
  pickerLoading.value = true
  try {
    const d = await api.getPortfolio(pid)
    const bd: Partial<Record<AssetCol, number>> = {}
    for (const g of d.by_asset_type) {
      if ((ASSET_COLS as readonly string[]).includes(g.asset_type)) {
        bd[g.asset_type as AssetCol] = Number(g.mv_2)
      }
    }
    totalRows.value.push({
      id: _nid++,
      accountType: '證券帳戶',
      marketValue: Number(d.totals.mv_2),
      mark: d.name + '-證券明細',
      linkedPortfolioId: pid,
      breakdown: bd,
    })
    showPicker.value = false
  } catch (e: any) {
    alert('載入失敗：' + (e.message ?? ''))
  } finally {
    pickerLoading.value = false
  }
}

function onAcctTypeBlur(row: TotalRow) {
  const v = row.accountType.trim()
  if (v && !acctTypes.value.includes(v)) {
    acctTypes.value.push(v)
  }
}

function rowSubtotal(row: TotalRow) {
  return ASSET_COLS.reduce((s, c) => s + (row.breakdown[c] ?? 0), 0)
}

const mv = (r: TotalRow) => Number(r.marketValue) || 0

const secTotal = computed(() =>
  totalRows.value.filter(r => r.accountType === '證券帳戶').reduce((s, r) => s + mv(r), 0)
)
const cashTotal = computed(() =>
  totalRows.value.filter(r => r.accountType !== '證券帳戶').reduce((s, r) => s + mv(r), 0)
)
const grandTotal = computed(() => secTotal.value + cashTotal.value)
const secPct = computed(() =>
  grandTotal.value > 0 ? (secTotal.value / grandTotal.value * 100).toFixed(2) + '%' : '0.00%'
)
const cashPct = computed(() =>
  grandTotal.value > 0 ? (cashTotal.value / grandTotal.value * 100).toFixed(2) + '%' : '0.00%'
)
const colTotals = computed(() => {
  const t: Record<string, number> = {}
  for (const c of ASSET_COLS) t[c] = totalRows.value.reduce((s, r) => s + (r.breakdown[c] ?? 0), 0)
  return t
})
const grandSubtotal = computed(() => ASSET_COLS.reduce((s, c) => s + colTotals.value[c], 0))
const linkedIds = computed(() => new Set(totalRows.value.map(r => r.linkedPortfolioId).filter(Boolean)))

function fmtCell(n: number | null | undefined) {
  const v = Number(n)
  if (!n || v === 0) return ''
  return v.toLocaleString('zh-TW', { maximumFractionDigits: 0 })
}
function fmtFoot(n: number) {
  return Number(n).toLocaleString('zh-TW', { maximumFractionDigits: 0 })
}
</script>

<template>
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
    <h1 style="font-size:20px;font-weight:700">投資組合列表</h1>
    <button class="btn btn-primary" @click="showCreate=true">＋ 新增投資組合</button>
  </div>

  <div v-if="store.loading" class="text-muted">載入中…</div>
  <div v-else-if="store.error" class="text-danger">{{ store.error }}</div>
  <div v-else-if="!store.portfolios.length" class="card text-muted" style="text-align:center;padding:48px">
    尚無投資組合，請點擊「新增投資組合」開始建立。
  </div>
  <div v-else style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px">
    <div v-for="p in store.portfolios" :key="p.id" class="card" style="cursor:pointer" @click="router.push(`/portfolios/${p.id}`)">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:8px">
        <span style="font-size:16px;font-weight:700">{{ p.name }}</span>
        <div style="display:flex;gap:6px;align-items:center">
          <span v-if="linkedIds.has(p.id)"
            style="font-size:10px;background:#1a5276;color:#fff;padding:2px 7px;border-radius:10px;white-space:nowrap">
            已帶入
          </span>
          <button class="btn btn-ghost btn-sm" @click.stop="deletePortfolio(p.id, p.name)">刪除</button>
        </div>
      </div>
      <div class="text-muted" style="font-size:12px">{{ p.description || '無描述' }}</div>
      <div class="text-muted" style="font-size:11px;margin-top:8px">
        建立於 {{ new Date(p.created_at).toLocaleDateString('zh-TW') }}
      </div>
    </div>
  </div>

  <!-- ── 資產總計 ── -->
  <div style="margin-top:32px">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
      <h2 style="font-size:18px;font-weight:700">資產總計</h2>
      <div style="display:flex;gap:8px">
        <button class="btn btn-ghost btn-sm" @click="showPicker=true">＋ 從證券明細帶入</button>
        <button class="btn btn-ghost btn-sm" @click="addEmptyRow">＋ 新增列</button>
      </div>
    </div>

    <div class="card" style="padding:0;overflow:hidden">

      <!-- Ratio header (shown only when there's data) -->
      <div v-if="grandTotal > 0"
        style="background:#1e3a5f;padding:12px 20px;display:flex;gap:48px;align-items:center">
        <div style="text-align:center">
          <div style="color:#aed6f1;font-size:11px;margin-bottom:2px">證券占比</div>
          <div style="color:#f1c40f;font-size:22px;font-weight:700;line-height:1.1">{{ secPct }}</div>
          <div style="color:#d6eaf8;font-size:13px;margin-top:2px">{{ fmtFoot(secTotal) }}</div>
        </div>
        <div style="text-align:center">
          <div style="color:#aed6f1;font-size:11px;margin-bottom:2px">現金占比</div>
          <div style="color:#2ecc71;font-size:22px;font-weight:700;line-height:1.1">{{ cashPct }}</div>
          <div style="color:#d6eaf8;font-size:13px;margin-top:2px">{{ fmtFoot(cashTotal) }}</div>
        </div>
        <div style="margin-left:auto;text-align:right">
          <div style="color:#aed6f1;font-size:11px;margin-bottom:2px">資產總計</div>
          <div style="color:#fff;font-size:18px;font-weight:700">{{ fmtFoot(grandTotal) }}</div>
        </div>
      </div>

      <!-- datalist shared for account type combobox -->
      <datalist id="acct-type-list">
        <option v-for="t in acctTypes" :key="t" :value="t" />
      </datalist>

      <div style="overflow-x:auto">
        <table class="table ta-table">
          <thead>
            <tr>
              <th style="width:40px;text-align:center">序</th>
              <th style="min-width:130px">帳戶類型</th>
              <th class="num" style="min-width:130px">市值</th>
              <th style="min-width:160px">mark</th>
              <th v-for="col in ASSET_COLS" :key="col" class="num" style="min-width:100px">{{ col }}</th>
              <th class="num" style="min-width:100px">小計</th>
              <th style="width:44px"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in totalRows" :key="row.id" class="ta-row">
              <td style="text-align:center;color:#888;font-size:12px">{{ idx + 1 }}</td>
              <td>
                <input
                  list="acct-type-list"
                  v-model="row.accountType"
                  class="ta-input"
                  @blur="onAcctTypeBlur(row)"
                />
              </td>
              <td>
                <input
                  class="ta-input num"
                  type="number"
                  v-model.number="row.marketValue"
                  placeholder="0"
                />
              </td>
              <td>
                <input class="ta-input" v-model="row.mark" />
              </td>
              <td v-for="col in ASSET_COLS" :key="col"
                class="num" style="font-size:12px;color:#555;padding:4px 8px">
                {{ fmtCell(row.breakdown[col]) }}
              </td>
              <td class="num fw-bold" style="padding:4px 8px">
                {{ fmtCell(rowSubtotal(row)) || '—' }}
              </td>
              <td style="padding:2px 4px">
                <button class="btn btn-danger btn-sm"
                  style="padding:2px 7px;font-size:11px"
                  @click="delRow(row.id)">刪</button>
              </td>
            </tr>

            <tr v-if="!totalRows.length">
              <td :colspan="5 + ASSET_COLS.length" class="text-muted"
                style="text-align:center;padding:28px;font-size:13px">
                尚無資料。點擊「從證券明細帶入」或「新增列」開始建立。
              </td>
            </tr>
          </tbody>

          <tfoot v-if="totalRows.length">
            <tr>
              <td colspan="2" style="font-weight:700;padding-left:12px">合計</td>
              <td class="num fw-bold">{{ fmtFoot(grandTotal) }}</td>
              <td></td>
              <td v-for="col in ASSET_COLS" :key="col" class="num fw-bold">
                {{ colTotals[col] > 0 ? fmtFoot(colTotals[col]) : '' }}
              </td>
              <td class="num fw-bold">{{ grandSubtotal > 0 ? fmtFoot(grandSubtotal) : '' }}</td>
              <td></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  </div>

  <!-- Portfolio Picker Modal -->
  <div v-if="showPicker" class="modal-overlay" @click.self="showPicker=false">
    <div class="modal" style="min-width:360px">
      <div class="modal-title">從證券明細帶入</div>
      <div v-if="pickerLoading" class="text-muted" style="text-align:center;padding:24px">載入中…</div>
      <div v-else>
        <div v-if="!store.portfolios.length" class="text-muted" style="padding:16px">尚無投資組合</div>
        <div v-for="p in store.portfolios" :key="p.id"
          style="display:flex;align-items:center;justify-content:space-between;
                 padding:10px 4px;border-bottom:1px solid #e2e8f0">
          <div>
            <div style="font-weight:600;font-size:14px">{{ p.name }}</div>
            <div class="text-muted" style="font-size:12px">{{ p.description || '無描述' }}</div>
          </div>
          <button
            class="btn btn-sm"
            :class="linkedIds.has(p.id) ? 'btn-ghost' : 'btn-primary'"
            :disabled="linkedIds.has(p.id)"
            @click="linkPortfolio(p.id)"
          >
            {{ linkedIds.has(p.id) ? '已帶入' : '帶入' }}
          </button>
        </div>
      </div>
      <div class="modal-actions">
        <button class="btn btn-ghost" @click="showPicker=false">關閉</button>
      </div>
    </div>
  </div>

  <!-- Create Portfolio Modal -->
  <div v-if="showCreate" class="modal-overlay" @click.self="showCreate=false">
    <div class="modal">
      <div class="modal-title">新增投資組合</div>
      <div class="form-group">
        <label>名稱 *</label>
        <input v-model="form.name" class="form-control" placeholder="例：富守投資組合" />
      </div>
      <div class="form-group">
        <label>描述</label>
        <input v-model="form.description" class="form-control" placeholder="選填" />
      </div>
      <div v-if="createError" class="text-danger" style="font-size:13px;margin-bottom:8px">{{ createError }}</div>
      <div class="modal-actions">
        <button class="btn btn-ghost" @click="showCreate=false; createError=null">取消</button>
        <button class="btn btn-primary" :disabled="saving || !form.name.trim()" @click="createPortfolio">
          {{ saving ? '建立中…' : '建立' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ta-table th {
  background: #1a5276;
  color: #d6eaf8;
  font-weight: 600;
  white-space: nowrap;
  font-size: 12px;
  padding: 8px 10px;
}
.ta-table tfoot td {
  background: #f8fafc;
  border-top: 2px solid #cbd5e1;
  padding: 7px 10px;
}
.ta-row td { vertical-align: middle; padding: 3px 4px; }
.ta-row:hover td { background: #f0f8ff; }
.ta-input {
  width: 100%;
  border: 1px solid #e2e8f0;
  border-radius: 3px;
  padding: 3px 6px;
  font-size: 12px;
  background: transparent;
  outline: none;
  box-sizing: border-box;
}
.ta-input:focus {
  border-color: #2563eb;
  background: #fff;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15);
}
.ta-input.num { text-align: right; }
</style>
