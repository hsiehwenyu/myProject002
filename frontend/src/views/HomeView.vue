<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { usePortfolioStore } from '@/stores/portfolio'
import { api } from '@/api'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS, LineElement, PointElement,
  LinearScale, CategoryScale, Tooltip, Legend,
} from 'chart.js'

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend)

const store = usePortfolioStore()
const router = useRouter()
const route  = useRoute()

// ── Tabs ──────────────────────────────────────────────
const activeTab = ref<'master' | 'assets' | 'equity' | 'overview'>('master')

// ── Portfolio CRUD ─────────────────────────────────────
const showCreate = ref(false)
const form = ref({ name: '', description: '' })
const saving = ref(false)
const createError = ref<string | null>(null)

onMounted(() => {
  store.fetchPortfolios()
  loadStorage()
  const tab = route.query.tab
  if (tab === 'assets' || tab === 'equity' || tab === 'master' || tab === 'overview') activeTab.value = tab as typeof activeTab.value
})

async function createPortfolio() {
  if (!form.value.name.trim()) return
  saving.value = true; createError.value = null
  try {
    const p = await api.createPortfolio({ name: form.value.name, description: form.value.description || undefined })
    store.portfolios.unshift(p)
    showCreate.value = false
    form.value = { name: '', description: '' }
  } catch (e: any) {
    createError.value = e.message ?? '新增失敗，請確認 Backend 是否正常運行'
  } finally { saving.value = false }
}

async function deletePortfolio(id: number, name: string) {
  if (!confirm(`確定刪除「${name}」及其所有資產？`)) return
  try {
    await api.deletePortfolio(id)
    store.portfolios = store.portfolios.filter(p => p.id !== id)
    totalRows.value = totalRows.value.filter(r => r.linkedPortfolioId !== id)
  } catch (e: any) { alert('刪除失敗：' + (e.message ?? '未知錯誤')) }
}

// ── 主檔 ──────────────────────────────────────────────
interface MasterRecord {
  id: number
  groupName: string
  createdDate: string
  createdBy: string
}

interface FrEntry {
  id: number
  masterId: number
  date: string
  remark: string
  navAtTime: number
  investors: { name: string; amount: number; shares: number }[]
}

interface ShOverviewRecord {
  id: number
  date: string
  remark: string
  masters: { id: number; name: string; total: number }[]
  rows: { name: string; values: Record<number, number>; total: number }[]
  grandTotal: number
}

// ── 資產總計 ──────────────────────────────────────────
const ASSET_COLS = ['股票-個股', '股票ETF', '債券-ETF', 'CB', 'CBAS', '現金'] as const
type AssetCol = typeof ASSET_COLS[number]

interface TotalRow {
  id: number
  masterId: number
  accountType: string
  marketValue: number | null
  mark: string
  linkedPortfolioId: number | null
  breakdown: Partial<Record<AssetCol, number>>
}

// ── 股東持股管理 ──────────────────────────────────────
interface ShareholderEntry {
  id: number
  masterId: number
  name: string
  shares: number
}

interface EquityRecord {
  id: number
  masterId: number
  date: string
  remark: string
  totalAssets: number
  totalShares: number
  navPerShare: number
  shareholders: { name: string; shares: number }[]
}

// ── 資產歷史記錄 ──────────────────────────────────────
interface AssetRecord {
  id: number
  masterId: number
  date: string
  remark: string
  savedTotal?: number
  bankTotal: number
  stockInd: number
  stockETF: number
  bondETF: number
  cb: number
  cbas: number
}

// ── localStorage keys ─────────────────────────────────
const LS_MASTER      = 'master_info_v1'       // legacy, migration only
const LS_MASTER_RECS = 'master_records_v1'
const LS_ACTIVE      = 'master_active_id_v1'
const LS_EQUITY_SH   = 'equity_sh_v1'
const LS_EQUITY_HIST = 'equity_hist_v1'
const LS_ROWS        = 'ta_rows_v1'
const LS_TYPES       = 'ta_types_v1'
const LS_HISTORY     = 'ta_history_v1'
const LS_FR_HIST     = 'fr_hist_v1'
const LS_SH_OVERVIEW = 'sh_overview_v1'

// ── State ─────────────────────────────────────────────
const masterRecords  = ref<MasterRecord[]>([])
const activeMasterId = ref<number | null>(null)
let _mid = 1

const filterGroupName = ref('')
const newMasterRec = reactive({ groupName: '', createdDate: new Date().toISOString().split('T')[0], createdBy: '' })

const shareholders   = ref<ShareholderEntry[]>([])
const equityHistory  = ref<EquityRecord[]>([])
const frHistory      = ref<FrEntry[]>([])
const shOverviewHistory = ref<ShOverviewRecord[]>([])
let _sid = 1; let _eid = 1; let _frid = 1; let _shoid = 1
const snapshotRemark = ref('')

const newSH        = reactive({ name: '', shares: null as number | null })
const recordRemark = ref('')

const acctTypes = ref<string[]>(['證券帳戶', '銀行帳戶'])
const totalRows = ref<TotalRow[]>([])
let _nid = 1

const historyRows = ref<AssetRecord[]>([])
let _hid = 1

const newRec = reactive({
  date: new Date().toISOString().split('T')[0],
  remark: '',
  bankTotal: null as number | null,
  stockInd:  null as number | null,
  stockETF:  null as number | null,
  bondETF:   null as number | null,
  cb:        null as number | null,
  cbas:      null as number | null,
})

// ── Active master helper ───────────────────────────────
const activeMaster = computed(() =>
  masterRecords.value.find(r => r.id === activeMasterId.value) ?? null
)

function byMaster<T extends { masterId: number }>(arr: T[]): T[] {
  return activeMasterId.value !== null ? arr.filter(r => r.masterId === activeMasterId.value) : []
}

function selectMaster(id: number) {
  activeMasterId.value = id
}

// ── Load / persist ────────────────────────────────────
function loadStorage() {
  try {
    // Master records
    const mr = localStorage.getItem(LS_MASTER_RECS)
    if (mr) {
      masterRecords.value = JSON.parse(mr)
      _mid = masterRecords.value.reduce((m, x) => Math.max(m, x.id), 0) + 1
    } else {
      // Migrate from old single-record format
      const old = localStorage.getItem(LS_MASTER)
      if (old) {
        const o = JSON.parse(old)
        if (o.groupName) masterRecords.value = [{ id: _mid++, groupName: o.groupName, createdDate: o.createdDate || '', createdBy: o.createdBy || '' }]
      }
    }

    // Active master
    const aid = localStorage.getItem(LS_ACTIVE)
    if (aid) {
      const parsed = JSON.parse(aid)
      if (masterRecords.value.some(r => r.id === parsed)) activeMasterId.value = parsed
    }

    // Data arrays
    const r = localStorage.getItem(LS_ROWS)
    if (r) { totalRows.value = JSON.parse(r); _nid = totalRows.value.reduce((m, x) => Math.max(m, x.id), 0) + 1 }
    const t = localStorage.getItem(LS_TYPES)
    if (t) acctTypes.value = JSON.parse(t)
    const h = localStorage.getItem(LS_HISTORY)
    if (h) { historyRows.value = JSON.parse(h); _hid = historyRows.value.reduce((m, x) => Math.max(m, x.id), 0) + 1 }
    const sh = localStorage.getItem(LS_EQUITY_SH)
    if (sh) { shareholders.value = JSON.parse(sh); _sid = shareholders.value.reduce((m, x) => Math.max(m, x.id), 0) + 1 }
    const eh = localStorage.getItem(LS_EQUITY_HIST)
    if (eh) { equityHistory.value = JSON.parse(eh); _eid = equityHistory.value.reduce((m, x) => Math.max(m, x.id), 0) + 1 }
    const fh = localStorage.getItem(LS_FR_HIST)
    if (fh) { frHistory.value = JSON.parse(fh); _frid = frHistory.value.reduce((m, x) => Math.max(m, x.id), 0) + 1 }
    const sho = localStorage.getItem(LS_SH_OVERVIEW)
    if (sho) { shOverviewHistory.value = JSON.parse(sho); _shoid = shOverviewHistory.value.reduce((m, x) => Math.max(m, x.id), 0) + 1 }

    // Migration: assign orphaned records (no masterId) to first master
    if (masterRecords.value.length > 0) {
      const firstId = masterRecords.value[0].id
      totalRows.value.forEach(r => { if (!r.masterId) r.masterId = firstId })
      historyRows.value.forEach(r => { if (!r.masterId) r.masterId = firstId })
      shareholders.value.forEach(r => { if (!r.masterId) r.masterId = firstId })
      equityHistory.value.forEach(r => { if (!r.masterId) r.masterId = firstId })
      frHistory.value.forEach(r => { if (!r.masterId) r.masterId = firstId })
    }
  } catch {}
}

watch(masterRecords,  v => localStorage.setItem(LS_MASTER_RECS, JSON.stringify(v)), { deep: true })
watch(activeMasterId, v => localStorage.setItem(LS_ACTIVE,      JSON.stringify(v)))
watch(totalRows,      v => localStorage.setItem(LS_ROWS,        JSON.stringify(v)), { deep: true })
watch(acctTypes,      v => localStorage.setItem(LS_TYPES,       JSON.stringify(v)), { deep: true })
watch(historyRows,    v => localStorage.setItem(LS_HISTORY,     JSON.stringify(v)), { deep: true })
watch(shareholders,   v => localStorage.setItem(LS_EQUITY_SH,   JSON.stringify(v)), { deep: true })
watch(equityHistory,  v => localStorage.setItem(LS_EQUITY_HIST, JSON.stringify(v)), { deep: true })
watch(frHistory,      v => localStorage.setItem(LS_FR_HIST,     JSON.stringify(v)), { deep: true })
watch(shOverviewHistory, v => localStorage.setItem(LS_SH_OVERVIEW, JSON.stringify(v)), { deep: true })

// ── 主檔 CRUD ─────────────────────────────────────────
const masterGroupNames = computed(() =>
  [...new Set(masterRecords.value.map(r => r.groupName).filter(Boolean))]
)
const filteredMasterRecords = computed(() =>
  filterGroupName.value
    ? masterRecords.value.filter(r => r.groupName === filterGroupName.value)
    : masterRecords.value
)

function addMasterRecord() {
  const name = newMasterRec.groupName.trim()
  if (!name) return
  const newId = _mid++
  masterRecords.value.push({ id: newId, groupName: name, createdDate: newMasterRec.createdDate, createdBy: newMasterRec.createdBy.trim() })
  Object.assign(newMasterRec, { groupName: '', createdDate: new Date().toISOString().split('T')[0], createdBy: '' })
  // Auto-select if first record
  if (masterRecords.value.length === 1) activeMasterId.value = newId
}
function deleteMasterRecord(id: number) {
  if (!confirm('確定刪除此主檔記錄？此操作不會刪除相關的資產及股東資料，但相關資料將不再顯示。')) return
  masterRecords.value = masterRecords.value.filter(r => r.id !== id)
  if (activeMasterId.value === id) activeMasterId.value = masterRecords.value[0]?.id ?? null
}

// ── 資產計算（只計算目前主檔）──────────────────────────
const mv = (r: TotalRow) => Number(r.marketValue) || 0

const secTotal  = computed(() => byMaster(totalRows.value).filter(r => r.accountType === '證券帳戶').reduce((s, r) => s + mv(r), 0))
const cashTotal = computed(() => byMaster(totalRows.value).filter(r => r.accountType !== '證券帳戶').reduce((s, r) => s + mv(r), 0))
const grandTotal    = computed(() => secTotal.value + cashTotal.value)
const secPct        = computed(() => grandTotal.value > 0 ? (secTotal.value  / grandTotal.value * 100).toFixed(2) + '%' : '0.00%')
const cashPct       = computed(() => grandTotal.value > 0 ? (cashTotal.value / grandTotal.value * 100).toFixed(2) + '%' : '0.00%')
function effectiveBreakdown(row: TotalRow): Partial<Record<AssetCol, number>> {
  if (Object.keys(row.breakdown).length > 0) return row.breakdown
  const mv = Number(row.marketValue) || 0
  if (row.accountType === '證券帳戶') {
    const m = row.mark
    if (m.includes('CBAS'))                              return { 'CBAS': mv }
    if (m.includes('CB'))                                return { 'CB': mv }
    if (m.includes('債券-ETF') || m.includes('債券ETF')) return { '債券-ETF': mv }
    if (m.includes('股票ETF') || m.includes('股票-ETF')) return { '股票ETF': mv }
    if (m.includes('股票-個股') || m.includes('個股'))   return { '股票-個股': mv }
  } else {
    return { '現金': mv }
  }
  return row.breakdown
}

const colTotals     = computed(() => {
  const t: Record<string, number> = {}
  for (const c of ASSET_COLS) t[c] = byMaster(totalRows.value).reduce((s, r) => s + (effectiveBreakdown(r)[c] ?? 0), 0)
  return t
})
const grandSubtotal = computed(() => ASSET_COLS.reduce((s, c) => s + colTotals.value[c], 0))
const linkedIds       = computed(() => new Set(byMaster(totalRows.value).map(r => r.linkedPortfolioId).filter(Boolean)))
const linkedByOthers  = computed(() => new Set(
  totalRows.value
    .filter(r => r.linkedPortfolioId !== null && r.masterId !== activeMasterId.value)
    .map(r => r.linkedPortfolioId!)
))

function rowSubtotal(row: TotalRow) { return ASSET_COLS.reduce((s, c) => s + (effectiveBreakdown(row)[c] ?? 0), 0) }
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
function fmtCell(n: number | null | undefined) {
  const v = Number(n); if (!n || v === 0) return ''; return v.toLocaleString('zh-TW', { maximumFractionDigits: 0 })
}
function fmtFoot(n: number) { return Number(n).toLocaleString('zh-TW', { maximumFractionDigits: 0 }) }

// ── 股東持股（只計算目前主檔）──────────────────────────
const totalShares = computed(() => byMaster(shareholders.value).reduce((s, x) => s + (Number(x.shares) || 0), 0))
const navPerShare = computed(() => totalShares.value > 0 ? grandTotal.value / totalShares.value : 0)

function shPct(shares: number) { return totalShares.value > 0 ? (shares / totalShares.value * 100).toFixed(2) + '%' : '0.00%' }
function shMv(shares: number)  { return totalShares.value > 0 ? shares / totalShares.value * grandTotal.value : 0 }
function fmtShares(n: number)  { return Number(n).toLocaleString('zh-TW', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }
function fmtNav(n: number)     { return Number(n).toLocaleString('zh-TW', { minimumFractionDigits: 2, maximumFractionDigits: 4 }) }

function saveShareholder() {
  const name = newSH.name.trim()
  if (!name || !activeMasterId.value) return
  shareholders.value.push({ id: _sid++, masterId: activeMasterId.value, name, shares: Number(newSH.shares) || 0 })
  Object.assign(newSH, { name: '', shares: null })
}
function deleteShareholder(id: number) {
  if (!confirm('確定刪除此股東？')) return
  shareholders.value = shareholders.value.filter(s => s.id !== id)
}
function createEquityRecord() {
  const shList = byMaster(shareholders.value)
  if (!activeMasterId.value) return
  if (!shList.length) { alert('尚未設定任何股東'); return }
  equityHistory.value.push({
    id: _eid++, masterId: activeMasterId.value,
    date: new Date().toISOString().split('T')[0],
    remark: recordRemark.value.trim(),
    totalAssets: grandTotal.value,
    totalShares: totalShares.value,
    navPerShare: navPerShare.value,
    shareholders: shList.map(s => ({ name: s.name, shares: Number(s.shares) })),
  })
  recordRemark.value = ''
}
function delEquityRecord(id: number) {
  if (!confirm('確定刪除此歷史記錄？')) return
  equityHistory.value = equityHistory.value.filter(r => r.id !== id)
}

// ── 募資重算股權 ──────────────────────────────────────
const showFundraise = ref(false)
const frInvestors   = ref<{ investorName: string; amount: number | null }[]>([{ investorName: '', amount: null }])
const frRemark      = ref('')
const frDate        = ref(new Date().toISOString().split('T')[0])

const frTotalAmount  = computed(() => frInvestors.value.reduce((s, r) => s + (Number(r.amount) || 0), 0))
const frNewShares    = computed(() => navPerShare.value > 0 ? frTotalAmount.value / navPerShare.value : 0)
const frNewTotal     = computed(() => grandTotal.value + frTotalAmount.value)
const frNewTotalSH   = computed(() => totalShares.value + frNewShares.value)
const frNewNav       = computed(() => frNewTotalSH.value > 0 ? frNewTotal.value / frNewTotalSH.value : 0)
const frSimRows      = computed(() => {
  const base = byMaster(shareholders.value).map(s => ({ name: s.name, shares: Number(s.shares), isNew: false }))
  for (const inv of frInvestors.value) {
    const name = inv.investorName.trim()
    const amt  = Number(inv.amount) || 0
    if (!name || amt <= 0 || navPerShare.value <= 0) continue
    const ns = amt / navPerShare.value
    const ex = base.find(s => s.name === name)
    if (ex) ex.shares += ns
    else base.push({ name, shares: ns, isNew: true })
  }
  return base
})

function openFundraise() {
  frInvestors.value = [{ investorName: '', amount: null }]
  frRemark.value = ''
  frDate.value = new Date().toISOString().split('T')[0]
  showFundraise.value = true
}
function addFrInvestor()        { frInvestors.value.push({ investorName: '', amount: null }) }
function removeFrInvestor(i: number) { if (frInvestors.value.length > 1) frInvestors.value.splice(i, 1) }
function delFrRecord(id: number) {
  if (!confirm('確定刪除此募資記錄？（不會還原股東持股與資產總計的資料）')) return
  frHistory.value = frHistory.value.filter(r => r.id !== id)
}
function applyFundraise() {
  if (!activeMasterId.value) return
  const valid = frInvestors.value.filter(r => r.investorName.trim() && (Number(r.amount) || 0) > 0)
  if (!valid.length || navPerShare.value <= 0) { alert('請至少填寫一筆有效的投資人名稱與投入金額'); return }
  const histInvestors: { name: string; amount: number; shares: number }[] = []
  for (const inv of valid) {
    const name     = inv.investorName.trim()
    const amt      = Number(inv.amount)
    const newShares = amt / navPerShare.value
    const ex = shareholders.value.find(s => s.name === name && s.masterId === activeMasterId.value)
    if (ex) ex.shares = Number(ex.shares) + newShares
    else shareholders.value.push({ id: _sid++, masterId: activeMasterId.value, name, shares: newShares })
    const mark = name + '-募資' + (frRemark.value.trim() ? '(' + frRemark.value.trim() + ')' : '')
    totalRows.value.push({ id: _nid++, masterId: activeMasterId.value, accountType: '銀行帳戶', marketValue: amt, mark, linkedPortfolioId: null, breakdown: {} })
    histInvestors.push({ name, amount: amt, shares: newShares })
  }
  frHistory.value.push({
    id: _frid++, masterId: activeMasterId.value,
    date: frDate.value, remark: frRemark.value.trim(),
    navAtTime: navPerShare.value, investors: histInvestors,
  })
  showFundraise.value = false
}

// ── 資產總計新增列 ────────────────────────────────────
const newRow = reactive({ accountType: '銀行帳戶', marketValue: null as number | null, mark: '' })
function resetNewRow() { Object.assign(newRow, { accountType: '銀行帳戶', marketValue: null, mark: '' }) }
function saveNewRow() {
  if (!activeMasterId.value || !newRow.accountType.trim()) return
  const v = newRow.accountType.trim()
  if (v && !acctTypes.value.includes(v)) acctTypes.value.push(v)
  totalRows.value.push({ id: _nid++, masterId: activeMasterId.value, accountType: v, marketValue: newRow.marketValue, mark: newRow.mark, linkedPortfolioId: null, breakdown: {} })
  resetNewRow()
}
function delRow(id: number) {
  if (!confirm('確定刪除此列？')) return
  totalRows.value = totalRows.value.filter(r => r.id !== id)
}

// ── 歷史記錄操作 ──────────────────────────────────────
function recSecTotal(r: AssetRecord)   { return r.stockInd + r.stockETF + r.bondETF + (r.cb || 0) + (r.cbas || 0) }
function recGrandTotal(r: AssetRecord) { return r.savedTotal ?? (r.bankTotal + recSecTotal(r)) }
function recPct(n: number, r: AssetRecord) { const t = recGrandTotal(r); return t > 0 ? (n / t * 100).toFixed(2) + '%' : '—' }
function chgIcon(curr: number, prev: number | undefined) { if (prev === undefined) return ''; return curr > prev ? '▲' : curr < prev ? '▼' : '' }
function chgCls(curr: number, prev: number | undefined)  { if (prev === undefined) return ''; return curr > prev ? 'chg-up' : curr < prev ? 'chg-dn' : '' }

function fillNewRecFromCurrent() {
  newRec.bankTotal = cashTotal.value
  newRec.stockInd  = colTotals.value['股票-個股'] ?? 0
  newRec.stockETF  = colTotals.value['股票ETF']   ?? 0
  newRec.bondETF   = colTotals.value['債券-ETF']  ?? 0
  newRec.cb        = colTotals.value['CB']        ?? 0
  newRec.cbas      = colTotals.value['CBAS']      ?? 0
}
function saveNewRec() {
  if (!activeMasterId.value) return
  historyRows.value.push({ id: _hid++, masterId: activeMasterId.value, date: newRec.date, remark: newRec.remark.trim(), savedTotal: grandTotal.value, bankTotal: Number(newRec.bankTotal)||0, stockInd: Number(newRec.stockInd)||0, stockETF: Number(newRec.stockETF)||0, bondETF: Number(newRec.bondETF)||0, cb: Number(newRec.cb)||0, cbas: Number(newRec.cbas)||0 })
  Object.assign(newRec, { date: new Date().toISOString().split('T')[0], remark: '', bankTotal: null, stockInd: null, stockETF: null, bondETF: null, cb: null, cbas: null })
}
function recordCurrentAssets() { fillNewRecFromCurrent(); saveNewRec() }
function delRecord(id: number) {
  if (!confirm('確定刪除此歷史記錄？')) return
  historyRows.value = historyRows.value.filter(r => r.id !== id)
}

// ── Portfolio Picker ──────────────────────────────────
const showPicker     = ref(false)
const pickerLoading  = ref(false)
const pickerSelected = ref<Set<number>>(new Set())
function togglePickerItem(pid: number) {
  const s = new Set(pickerSelected.value); s.has(pid) ? s.delete(pid) : s.add(pid); pickerSelected.value = s
}
function openPicker() { pickerSelected.value = new Set(); showPicker.value = true }
async function fetchAndPushPortfolio(pid: number) {
  if (!activeMasterId.value) return
  const d = await api.getPortfolio(pid)
  const bd: Partial<Record<AssetCol, number>> = {}
  for (const g of d.by_asset_type)
    if ((ASSET_COLS as readonly string[]).includes(g.asset_type)) bd[g.asset_type as AssetCol] = Number(g.mv_2)
  totalRows.value.push({ id: _nid++, masterId: activeMasterId.value, accountType: '證券帳戶', marketValue: Number(d.totals.mv_2), mark: d.name + '-證券明細', linkedPortfolioId: pid, breakdown: bd })
}
async function confirmPicker() {
  const toImport = [...pickerSelected.value].filter(pid => !byMaster(totalRows.value).some(r => r.linkedPortfolioId === pid))
  if (!toImport.length) return
  pickerLoading.value = true
  try { for (const pid of toImport) await fetchAndPushPortfolio(pid); showPicker.value = false }
  catch (e: any) { alert('載入失敗：' + (e.message ?? '')) }
  finally { pickerLoading.value = false }
}

// ── 帳戶類型管理 ──────────────────────────────────────
const DEFAULT_TYPES = ['證券帳戶', '銀行帳戶']
const showTypesMgr  = ref(false)
const newTypeName   = ref('')
function addManagedType() {
  const v = newTypeName.value.trim(); if (!v || acctTypes.value.includes(v)) return
  acctTypes.value.push(v); newTypeName.value = ''
}
function removeManagedType(t: string) {
  if (byMaster(totalRows.value).some(r => r.accountType === t)) { alert(`「${t}」目前有列正在使用，無法刪除`); return }
  acctTypes.value = acctTypes.value.filter(x => x !== t)
}

// ── 主檔圖表（只顯示目前主檔的歷史資料）────────────────
const CHART_COLORS = ['#2563eb','#16a34a','#d97706','#7c3aed','#db2777','#0891b2','#9333ea']

const activeEquityHistory = computed(() => byMaster(equityHistory.value))

const allShNames = computed(() => {
  const names = new Set<string>()
  activeEquityHistory.value.forEach(r => r.shareholders.forEach(s => names.add(s.name)))
  return [...names]
})
const shRatioChartData = computed(() => ({
  labels: activeEquityHistory.value.map(r => r.date),
  datasets: allShNames.value.map((name, i) => ({
    label: name,
    data: activeEquityHistory.value.map(r => {
      const s = r.shareholders.find(x => x.name === name)
      return r.totalShares > 0 && s ? +(s.shares / r.totalShares * 100).toFixed(2) : null
    }),
    borderColor: CHART_COLORS[i % CHART_COLORS.length],
    backgroundColor: CHART_COLORS[i % CHART_COLORS.length] + '33',
    tension: 0.3, fill: false, pointRadius: 4,
  })),
}))
const assetChartData = computed(() => ({
  labels: activeEquityHistory.value.map(r => r.date),
  datasets: [{ label: '資產總計', data: activeEquityHistory.value.map(r => r.totalAssets), borderColor: '#1e3a5f', backgroundColor: '#1e3a5f30', tension: 0.3, fill: true, pointRadius: 4 }],
}))
const navChartData = computed(() => ({
  labels: activeEquityHistory.value.map(r => r.date),
  datasets: [{ label: '每股淨值', data: activeEquityHistory.value.map(r => r.navPerShare), borderColor: '#16a34a', backgroundColor: '#16a34a30', tension: 0.3, fill: true, pointRadius: 4 }],
}))
const lineOpts = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { position: 'bottom' as const, labels: { font: { size: 11 } } }, tooltip: { mode: 'index' as const, intersect: false } },
  scales: { x: { ticks: { font: { size: 10 } } }, y: { ticks: { font: { size: 10 } } } },
}

// ── 股東資產總覽 ──────────────────────────────────────
const masterTotals = computed(() =>
  masterRecords.value.map(m => {
    const rows    = totalRows.value.filter(r => r.masterId === m.id)
    const total   = rows.reduce((s, r) => s + (Number(r.marketValue) || 0), 0)
    const shs     = shareholders.value.filter(r => r.masterId === m.id)
    const shTotal = shs.reduce((s, x) => s + (Number(x.shares) || 0), 0)
    return { masterId: m.id, masterName: m.groupName, total, shs, shTotal }
  })
)

const overviewAllNames = computed(() => {
  const names = new Set<string>()
  shareholders.value.forEach(s => names.add(s.name))
  return [...names].sort()
})

const overviewMatrix = computed(() =>
  overviewAllNames.value.map(name => {
    const values: Record<number, number> = {}
    let rowTotal = 0
    for (const mt of masterTotals.value) {
      const sh  = mt.shs.find(s => s.name === name)
      const val = sh && mt.shTotal > 0 ? (Number(sh.shares) / mt.shTotal) * mt.total : 0
      values[mt.masterId] = val
      rowTotal += val
    }
    return { name, values, total: rowTotal }
  })
)

const overviewGrandTotal = computed(() => masterTotals.value.reduce((s, mt) => s + mt.total, 0))

function saveOverviewSnapshot() {
  shOverviewHistory.value.push({
    id: _shoid++,
    date: new Date().toISOString().split('T')[0],
    remark: snapshotRemark.value.trim(),
    masters: masterTotals.value.map(mt => ({ id: mt.masterId, name: mt.masterName, total: mt.total })),
    rows: overviewMatrix.value.map(r => ({ name: r.name, values: { ...r.values }, total: r.total })),
    grandTotal: overviewGrandTotal.value,
  })
  snapshotRemark.value = ''
}
function delOverviewSnapshot(id: number) {
  if (!confirm('確定刪除此快照？')) return
  shOverviewHistory.value = shOverviewHistory.value.filter(r => r.id !== id)
}
</script>

<template>

  <!-- ══ 頁籤導覽 ══ -->
  <div class="tab-nav">
    <button :class="['tab-btn', { 'tab-btn--active': activeTab==='master' }]" @click="activeTab='master'">主檔</button>
    <button :class="['tab-btn', { 'tab-btn--active': activeTab==='assets' }]" @click="activeTab='assets'">資產紀錄作業</button>
    <button :class="['tab-btn', { 'tab-btn--active': activeTab==='equity' }]" @click="activeTab='equity'">股東股本記錄作業</button>
    <button :class="['tab-btn', { 'tab-btn--active': activeTab==='overview' }]" @click="activeTab='overview'">股東資產總覽</button>
  </div>

  <!-- ══ Tab 0：主檔 ══ -->
  <div v-if="activeTab==='master'" class="tab-panel">

    <!-- 主檔資訊 -->
    <div style="margin-bottom:28px">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:12px">
        <h2 style="font-size:18px;font-weight:700;margin:0">主檔資訊</h2>
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
          <span style="font-size:13px;color:#64748b;white-space:nowrap">查詢：</span>
          <select v-model="filterGroupName" class="form-control" style="min-width:200px;max-width:280px;font-size:13px">
            <option value="">所有資料（{{ masterRecords.length }} 筆）</option>
            <option v-for="name in masterGroupNames" :key="name" :value="name">{{ name }}</option>
          </select>
          <button v-if="filterGroupName" class="btn btn-ghost btn-sm" @click="filterGroupName=''" style="font-size:12px">✕ 清除</button>
        </div>
      </div>

      <div class="card" style="padding:0;overflow:hidden">
        <div style="overflow-x:auto">
          <table class="table master-table">
            <thead>
              <tr>
                <th style="width:36px"></th>
                <th style="width:40px;text-align:center">序</th>
                <th style="min-width:200px">公司群組名稱</th>
                <th style="min-width:140px">建立日期</th>
                <th style="min-width:150px">建立人員</th>
                <th style="width:44px"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(rec, i) in filteredMasterRecords" :key="rec.id"
                class="ta-row master-row"
                :class="{ 'master-row--active': activeMasterId === rec.id }">
                <td style="padding:2px 6px;text-align:center">
                  <button
                    v-if="activeMasterId !== rec.id"
                    class="btn-select-master"
                    @click="selectMaster(rec.id)"
                    title="選取此主檔">▶</button>
                  <span v-else class="master-active-badge">啟用中</span>
                </td>
                <td style="text-align:center;color:#888;font-size:12px">{{ i + 1 }}</td>
                <td><input class="ta-input" v-model="rec.groupName" placeholder="公司群組名稱" /></td>
                <td><input class="ta-input" type="date" v-model="rec.createdDate" /></td>
                <td><input class="ta-input" v-model="rec.createdBy" placeholder="建立人員" /></td>
                <td style="padding:2px 4px">
                  <button class="btn btn-danger btn-sm" style="padding:2px 7px;font-size:11px"
                    @click="deleteMasterRecord(rec.id)">刪</button>
                </td>
              </tr>

              <tr v-if="!filteredMasterRecords.length">
                <td colspan="6" class="text-muted" style="text-align:center;padding:20px;font-size:13px">
                  {{ filterGroupName ? `查無「${filterGroupName}」的記錄` : '尚無主檔資料，請在下方新增。' }}
                </td>
              </tr>

              <!-- Inline new row -->
              <tr class="ta-new-row" @keydown.enter="addMasterRecord">
                <td></td>
                <td style="text-align:center;color:#aaa;font-size:12px">—</td>
                <td><input class="ta-input" v-model="newMasterRec.groupName" placeholder="公司群組名稱" /></td>
                <td><input class="ta-input" type="date" v-model="newMasterRec.createdDate" /></td>
                <td><input class="ta-input" v-model="newMasterRec.createdBy" placeholder="建立人員" /></td>
                <td style="padding:2px 4px">
                  <button class="btn btn-primary btn-sm"
                    style="padding:2px 10px;font-size:13px;font-weight:700"
                    :disabled="!newMasterRec.groupName.trim()"
                    @click="addMasterRecord">＋</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 目前資產摘要 -->
    <div v-if="activeMaster && (grandTotal > 0 || totalShares > 0)" style="margin-bottom:28px">
      <h2 style="font-size:18px;font-weight:700;margin:0 0 12px">
        目前資產摘要
        <span style="font-size:13px;font-weight:400;color:#1b4d2e;margin-left:8px">{{ activeMaster.groupName }}</span>
      </h2>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px">
        <div class="summary-card"><div class="summary-label">資產總計</div><div class="summary-value">{{ fmtFoot(grandTotal) }}</div></div>
        <div class="summary-card"><div class="summary-label">證券占比</div><div class="summary-value" style="color:#d97706">{{ secPct }}</div></div>
        <div class="summary-card"><div class="summary-label">現金占比</div><div class="summary-value" style="color:#2ecc71">{{ cashPct }}</div></div>
        <div class="summary-card" v-if="navPerShare > 0"><div class="summary-label">每股淨值</div><div class="summary-value" style="color:#1a5276">{{ fmtNav(navPerShare) }}</div></div>
        <div class="summary-card" v-if="totalShares > 0"><div class="summary-label">總股數</div><div class="summary-value">{{ fmtShares(totalShares) }}</div></div>
        <div class="summary-card" v-if="byMaster(shareholders).length"><div class="summary-label">股東人數</div><div class="summary-value">{{ byMaster(shareholders).length }}</div></div>
      </div>
    </div>

    <!-- 歷史趨勢圖 -->
    <div v-if="activeMaster" style="margin-bottom:28px">
      <h2 style="font-size:18px;font-weight:700;margin:0 0 12px">歷史趨勢圖</h2>
      <div v-if="activeEquityHistory.length >= 2"
        style="display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:20px">
        <div class="card">
          <div style="font-size:14px;font-weight:700;margin-bottom:12px;color:#1b4d2e">股東持股比例趨勢（%）</div>
          <div style="height:260px;position:relative"><Line :data="shRatioChartData" :options="lineOpts" /></div>
        </div>
        <div class="card">
          <div style="font-size:14px;font-weight:700;margin-bottom:12px;color:#1e3a5f">資產總計趨勢</div>
          <div style="height:260px;position:relative"><Line :data="assetChartData" :options="lineOpts" /></div>
        </div>
        <div class="card">
          <div style="font-size:14px;font-weight:700;margin-bottom:12px;color:#16a34a">每股淨值趨勢</div>
          <div style="height:260px;position:relative"><Line :data="navChartData" :options="lineOpts" /></div>
        </div>
      </div>
      <div v-else class="card text-muted" style="text-align:center;padding:40px;font-size:13px">
        {{ activeEquityHistory.length === 0
          ? '尚無股東持股歷史記錄，請至「股東股本記錄作業」新增記錄後即可顯示圖表。'
          : '目前僅有 1 筆歷史記錄，需至少 2 筆才能顯示趨勢圖。' }}
      </div>
    </div>

  </div>
  <!-- ══ Tab 0 end ══ -->

  <!-- ══ Tab 1：資產紀錄作業 ══ -->
  <div v-if="activeTab==='assets'" class="tab-panel">

    <!-- No master guard -->
    <div v-if="!activeMaster" class="no-master-guard">
      <div class="no-master-icon">🗂️</div>
      <div class="no-master-title">尚未選取主檔</div>
      <div class="no-master-desc">請先至「主檔」頁籤選取一筆主檔資訊，才能新增或查看資產紀錄作業的資料。</div>
      <button class="btn btn-primary" @click="activeTab='master'">前往選取主檔</button>
    </div>

    <template v-else>

      <!-- Active master banner -->
      <div class="master-banner">
        <span style="font-size:12px;color:#aed6f1">目前主檔</span>
        <strong style="font-size:14px;color:#fff;margin-left:8px">{{ activeMaster.groupName }}</strong>
        <span v-if="activeMaster.createdBy" style="font-size:12px;color:#93c5fd;margin-left:12px">{{ activeMaster.createdBy }}</span>
        <button class="btn btn-ghost btn-sm" style="margin-left:auto;font-size:12px;color:#93c5fd"
          @click="activeTab='master'">切換主檔</button>
      </div>

      <!-- 證券紀錄明細表 -->
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
        <h1 style="font-size:20px;font-weight:700">證券紀錄明細表</h1>
        <button class="btn btn-primary" @click="showCreate=true">＋ 新增投資組合</button>
      </div>

      <div v-if="store.loading" class="text-muted">載入中…</div>
      <div v-else-if="store.error" class="text-danger">{{ store.error }}</div>
      <div v-else-if="!store.portfolios.length" class="card text-muted" style="text-align:center;padding:48px">
        尚無投資組合，請點擊「新增投資組合」開始建立。
      </div>
      <div v-else style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px">
        <div v-for="p in store.portfolios.filter(p => !linkedByOthers.has(p.id))" :key="p.id" class="card" style="cursor:pointer" @click="router.push(`/portfolios/${p.id}`)">
          <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:8px">
            <span style="font-size:16px;font-weight:700">{{ p.name }}</span>
            <div style="display:flex;gap:6px;align-items:center">
              <span v-if="linkedIds.has(p.id)" style="font-size:10px;background:#1a5276;color:#fff;padding:2px 7px;border-radius:10px;white-space:nowrap">已帶入</span>
              <button class="btn btn-ghost btn-sm" @click.stop="deletePortfolio(p.id, p.name)">刪除</button>
            </div>
          </div>
          <div class="text-muted" style="font-size:12px">{{ p.description || '無描述' }}</div>
          <div class="text-muted" style="font-size:11px;margin-top:8px">建立於 {{ new Date(p.created_at).toLocaleDateString('zh-TW') }}</div>
        </div>
      </div>

      <!-- ── 資產總計 ── -->
      <div style="margin-top:32px">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
          <h2 style="font-size:18px;font-weight:700">資產總計</h2>
          <button class="btn btn-ghost btn-sm" @click="openPicker">＋ 從證券明細帶入</button>
        </div>

        <div class="card" style="padding:0;overflow:hidden">
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

          <div style="overflow-x:auto">
            <table class="table ta-table">
              <thead>
                <tr>
                  <th style="width:40px;text-align:center">序</th>
                  <th style="min-width:130px">
                    帳戶類型
                    <button class="btn-type-mgr" @click="showTypesMgr=true" title="管理帳戶類型選單">＋</button>
                  </th>
                  <th class="num" style="min-width:130px">市值</th>
                  <th style="min-width:160px">mark</th>
                  <th v-for="col in ASSET_COLS" :key="col" class="num" style="min-width:100px">{{ col }}</th>
                  <th class="num" style="min-width:100px">小計</th>
                  <th style="width:44px"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, idx) in byMaster(totalRows)" :key="row.id" class="ta-row">
                  <td style="text-align:center;color:#888;font-size:12px">{{ idx + 1 }}</td>
                  <td>
                    <select class="ta-input ta-select" v-model="row.accountType">
                      <option v-for="t in acctTypes" :key="t" :value="t">{{ t }}</option>
                    </select>
                  </td>
                  <td><input class="ta-input num" type="text" :value="fmtInput(row.marketValue)" @change="row.marketValue = parseInput($event)" placeholder="0" /></td>
                  <td><input class="ta-input" v-model="row.mark" /></td>
                  <td v-for="col in ASSET_COLS" :key="col" class="num" style="font-size:12px;color:#555;padding:4px 8px">{{ fmtCell(effectiveBreakdown(row)[col]) }}</td>
                  <td class="num fw-bold" style="padding:4px 8px">{{ fmtCell(rowSubtotal(row)) || '—' }}</td>
                  <td style="padding:2px 4px">
                    <button class="btn btn-danger btn-sm" style="padding:2px 7px;font-size:11px" @click="delRow(row.id)">刪</button>
                  </td>
                </tr>

                <tr v-if="!byMaster(totalRows).length">
                  <td :colspan="5 + ASSET_COLS.length" class="text-muted" style="text-align:center;padding:28px;font-size:13px">
                    尚無資料。點擊「從證券明細帶入」或在下方直接輸入新增。
                  </td>
                </tr>

                <tr class="ta-new-row" @keydown.enter="saveNewRow">
                  <td style="text-align:center;color:#aaa;font-size:12px">—</td>
                  <td>
                    <select class="ta-input ta-select" v-model="newRow.accountType">
                      <option v-for="t in acctTypes" :key="t" :value="t">{{ t }}</option>
                    </select>
                  </td>
                  <td><input class="ta-input num" type="text" :value="fmtInput(newRow.marketValue)" @change="newRow.marketValue = parseInput($event)" placeholder="0" /></td>
                  <td><input class="ta-input" v-model="newRow.mark" placeholder="備註" /></td>
                  <td v-for="col in ASSET_COLS" :key="col" class="num" style="color:#ccc;font-size:12px;padding:4px 8px">—</td>
                  <td class="num" style="color:#ccc;padding:4px 8px">—</td>
                  <td style="padding:2px 4px">
                    <button class="btn btn-primary btn-sm" style="padding:2px 10px;font-size:13px;font-weight:700"
                      :disabled="!newRow.accountType.trim()" @click="saveNewRow">＋</button>
                  </td>
                </tr>
              </tbody>

              <tfoot v-if="byMaster(totalRows).length">
                <tr>
                  <td colspan="2" style="font-weight:700;padding-left:12px">合計</td>
                  <td class="num fw-bold">{{ fmtFoot(grandTotal) }}</td>
                  <td></td>
                  <td v-for="col in ASSET_COLS" :key="col" class="num fw-bold">{{ colTotals[col] > 0 ? fmtFoot(colTotals[col]) : '' }}</td>
                  <td class="num fw-bold">{{ grandSubtotal > 0 ? fmtFoot(grandSubtotal) : '' }}</td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </div>

      <!-- ── 資產歷史記錄 ── -->
      <div style="margin-top:28px">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
          <h2 style="font-size:18px;font-weight:700">資產歷史記錄</h2>
          <button class="btn btn-primary btn-sm" @click="recordCurrentAssets" style="font-size:13px;padding:5px 14px">⊕ 記錄當前資產</button>
        </div>

        <div class="card" style="padding:0;overflow:hidden">
          <div style="overflow-x:auto">
            <table class="table hist-table">
              <thead>
                <tr>
                  <th style="width:44px;text-align:center">序號</th>
                  <th style="min-width:110px">日期</th>
                  <th style="min-width:140px">備註</th>
                  <th class="chg-th"></th>
                  <th class="num" style="min-width:120px">資產總計</th>
                  <th class="chg-th"></th>
                  <th class="num" style="min-width:110px">銀行帳戶</th>
                  <th class="chg-th"></th>
                  <th class="num" style="min-width:120px">證券帳戶</th>
                  <th class="chg-th"></th>
                  <th class="num" style="min-width:110px">股票-個股</th>
                  <th class="chg-th"></th>
                  <th class="num" style="min-width:100px">股票-ETF</th>
                  <th class="chg-th"></th>
                  <th class="num" style="min-width:100px">債券-ETF</th>
                  <th class="num" style="min-width:90px">CB</th>
                  <th class="num" style="min-width:90px">CBAS</th>
                  <th class="num pct-th">股票-個股</th>
                  <th class="num pct-th">股票-ETF</th>
                  <th class="num pct-th">債券-ETF</th>
                  <th class="num pct-th">現金</th>
                  <th style="width:36px"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(rec, i) in byMaster(historyRows)" :key="rec.id" class="hist-row">
                  <td style="text-align:center;color:#888;font-size:12px">{{ i + 1 }}</td>
                  <td><input class="ta-input" type="date" v-model="rec.date" style="min-width:108px" /></td>
                  <td><input class="ta-input" v-model="rec.remark" placeholder="備註" style="min-width:130px" /></td>
                  <td class="chg-col" :class="chgCls(recGrandTotal(rec), i>0 ? recGrandTotal(byMaster(historyRows)[i-1]) : undefined)">{{ chgIcon(recGrandTotal(rec), i>0 ? recGrandTotal(byMaster(historyRows)[i-1]) : undefined) }}</td>
                  <td class="num fw-bold">{{ fmtFoot(recGrandTotal(rec)) }}</td>
                  <td class="chg-col" :class="chgCls(rec.bankTotal, i>0 ? byMaster(historyRows)[i-1].bankTotal : undefined)">{{ chgIcon(rec.bankTotal, i>0 ? byMaster(historyRows)[i-1].bankTotal : undefined) }}</td>
                  <td class="num"><input class="ta-input num" type="text" :value="fmtInput(rec.bankTotal)" @change="rec.bankTotal = parseInput($event) ?? 0" /></td>
                  <td class="chg-col" :class="chgCls(recSecTotal(rec), i>0 ? recSecTotal(byMaster(historyRows)[i-1]) : undefined)">{{ chgIcon(recSecTotal(rec), i>0 ? recSecTotal(byMaster(historyRows)[i-1]) : undefined) }}</td>
                  <td class="num fw-bold">{{ fmtFoot(recSecTotal(rec)) }}</td>
                  <td class="chg-col" :class="chgCls(rec.stockInd, i>0 ? byMaster(historyRows)[i-1].stockInd : undefined)">{{ chgIcon(rec.stockInd, i>0 ? byMaster(historyRows)[i-1].stockInd : undefined) }}</td>
                  <td class="num"><input class="ta-input num" type="text" :value="fmtInput(rec.stockInd)" @change="rec.stockInd = parseInput($event) ?? 0" /></td>
                  <td class="chg-col" :class="chgCls(rec.stockETF, i>0 ? byMaster(historyRows)[i-1].stockETF : undefined)">{{ chgIcon(rec.stockETF, i>0 ? byMaster(historyRows)[i-1].stockETF : undefined) }}</td>
                  <td class="num"><input class="ta-input num" type="text" :value="fmtInput(rec.stockETF)" @change="rec.stockETF = parseInput($event) ?? 0" /></td>
                  <td class="chg-col" :class="chgCls(rec.bondETF, i>0 ? byMaster(historyRows)[i-1].bondETF : undefined)">{{ chgIcon(rec.bondETF, i>0 ? byMaster(historyRows)[i-1].bondETF : undefined) }}</td>
                  <td class="num"><input class="ta-input num" type="text" :value="fmtInput(rec.bondETF)" @change="rec.bondETF = parseInput($event) ?? 0" /></td>
                  <td class="num"><input class="ta-input num" type="text" :value="fmtInput(rec.cb)" @change="rec.cb = parseInput($event) ?? 0" /></td>
                  <td class="num"><input class="ta-input num" type="text" :value="fmtInput(rec.cbas)" @change="rec.cbas = parseInput($event) ?? 0" /></td>
                  <td class="num pct-cell">{{ recPct(rec.stockInd, rec) }}</td>
                  <td class="num pct-cell">{{ recPct(rec.stockETF, rec) }}</td>
                  <td class="num pct-cell">{{ recPct(rec.bondETF, rec) }}</td>
                  <td class="num pct-cell">{{ recPct(rec.bankTotal, rec) }}</td>
                  <td style="padding:2px 4px">
                    <button class="btn btn-danger btn-sm" style="padding:2px 7px;font-size:11px" @click="delRecord(rec.id)">刪</button>
                  </td>
                </tr>

                <tr v-if="!byMaster(historyRows).length">
                  <td :colspan="22" class="text-muted" style="text-align:center;padding:24px;font-size:13px">
                    尚無記錄。點擊「記錄當前資產」或在下方手動輸入。
                  </td>
                </tr>

                <tr class="ta-new-row" @keydown.enter="saveNewRec">
                  <td style="text-align:center;color:#aaa;font-size:12px">—</td>
                  <td><input class="ta-input" type="date" v-model="newRec.date" style="min-width:108px" /></td>
                  <td><input class="ta-input" v-model="newRec.remark" placeholder="備註" style="min-width:130px" /></td>
                  <td class="chg-col"></td>
                  <td class="num" style="color:#aaa;font-size:12px;padding:4px 8px">—</td>
                  <td class="chg-col"></td>
                  <td><input class="ta-input num" type="text" :value="fmtInput(newRec.bankTotal)" @change="newRec.bankTotal = parseInput($event)" placeholder="銀行帳戶" /></td>
                  <td class="chg-col"></td>
                  <td class="num" style="color:#aaa;font-size:12px;padding:4px 8px">—</td>
                  <td class="chg-col"></td>
                  <td><input class="ta-input num" type="text" :value="fmtInput(newRec.stockInd)"  @change="newRec.stockInd = parseInput($event)"  placeholder="股票-個股" /></td>
                  <td class="chg-col"></td>
                  <td><input class="ta-input num" type="text" :value="fmtInput(newRec.stockETF)"  @change="newRec.stockETF = parseInput($event)"  placeholder="股票-ETF" /></td>
                  <td class="chg-col"></td>
                  <td><input class="ta-input num" type="text" :value="fmtInput(newRec.bondETF)"   @change="newRec.bondETF = parseInput($event)"   placeholder="債券-ETF" /></td>
                  <td><input class="ta-input num" type="text" :value="fmtInput(newRec.cb)"        @change="newRec.cb = parseInput($event)"        placeholder="CB" /></td>
                  <td><input class="ta-input num" type="text" :value="fmtInput(newRec.cbas)"      @change="newRec.cbas = parseInput($event)"      placeholder="CBAS" /></td>
                  <td colspan="4" style="padding:4px 8px">
                    <button class="btn btn-ghost btn-sm" style="font-size:11px;margin-right:6px"
                      @click="fillNewRecFromCurrent" title="從資產總計帶入當前數值">帶入當前</button>
                  </td>
                  <td style="padding:2px 4px">
                    <button class="btn btn-primary btn-sm" style="padding:2px 10px;font-size:13px;font-weight:700" @click="saveNewRec">＋</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

    </template>
  </div>
  <!-- ══ Tab 1 end ══ -->

  <!-- ══ Tab 2：股東股本記錄作業 ══ -->
  <div v-if="activeTab==='equity'" class="tab-panel">

    <!-- No master guard -->
    <div v-if="!activeMaster" class="no-master-guard">
      <div class="no-master-icon">🗂️</div>
      <div class="no-master-title">尚未選取主檔</div>
      <div class="no-master-desc">請先至「主檔」頁籤選取一筆主檔資訊，才能新增或查看股東股本記錄作業的資料。</div>
      <button class="btn btn-primary" @click="activeTab='master'">前往選取主檔</button>
    </div>

    <template v-else>

      <!-- Active master banner -->
      <div class="master-banner">
        <span style="font-size:12px;color:#aed6f1">目前主檔</span>
        <strong style="font-size:14px;color:#fff;margin-left:8px">{{ activeMaster.groupName }}</strong>
        <span v-if="activeMaster.createdBy" style="font-size:12px;color:#93c5fd;margin-left:12px">{{ activeMaster.createdBy }}</span>
        <button class="btn btn-ghost btn-sm" style="margin-left:auto;font-size:12px;color:#93c5fd"
          @click="activeTab='master'">切換主檔</button>
      </div>

      <!-- Section header -->
      <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:12px;flex-wrap:wrap;gap:10px">
        <div>
          <h2 style="font-size:18px;font-weight:700;margin:0">股票管理</h2>
          <div v-if="totalShares > 0" style="font-size:12px;color:#64748b;margin-top:4px;display:flex;gap:16px;flex-wrap:wrap">
            <span>總股數：<strong>{{ fmtShares(totalShares) }}</strong></span>
            <span>資產總計：<strong>{{ fmtFoot(grandTotal) }}</strong></span>
            <span v-if="navPerShare > 0" style="color:#1a5276;font-weight:700">每股淨值：{{ fmtNav(navPerShare) }}</span>
          </div>
        </div>
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
          <button class="btn btn-ghost btn-sm" @click="openFundraise" style="white-space:nowrap;font-size:13px;padding:5px 14px">⚖ 募資重算股權</button>
          <input v-model="recordRemark" class="form-control" placeholder="本次記錄備註…" style="width:200px;font-size:12px" @keydown.enter="createEquityRecord" />
          <button class="btn btn-primary btn-sm" :disabled="!byMaster(shareholders).length"
            style="white-space:nowrap;font-size:13px;padding:5px 14px" @click="createEquityRecord">⊕ 新增記錄</button>
        </div>
      </div>

      <!-- Current shareholders table -->
      <div class="card" style="padding:0;overflow:hidden">
        <div style="background:#1b4d2e;padding:8px 14px">
          <span style="color:#d4edda;font-weight:700;font-size:13px">持股明細</span>
        </div>
        <div style="overflow-x:auto">
          <table class="table eq-table">
            <thead>
              <tr>
                <th style="min-width:120px">股東</th>
                <th class="num" style="min-width:130px">股權數量</th>
                <th class="num" style="min-width:90px">股權占比</th>
                <th class="num" style="min-width:120px">股權市值</th>
                <th style="width:44px"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in byMaster(shareholders)" :key="s.id" class="ta-row">
                <td><input class="ta-input" v-model="s.name" placeholder="股東名稱" /></td>
                <td><input class="ta-input num" type="text" :value="fmtInput(s.shares)" @change="s.shares = parseInput($event) ?? 0" placeholder="0.00" /></td>
                <td class="num" style="font-size:13px">{{ shPct(Number(s.shares)) }}</td>
                <td class="num fw-bold">{{ fmtFoot(shMv(Number(s.shares))) }}</td>
                <td style="padding:2px 4px">
                  <button class="btn btn-danger btn-sm" style="padding:2px 7px;font-size:11px" @click="deleteShareholder(s.id)">刪</button>
                </td>
              </tr>

              <tr v-if="!byMaster(shareholders).length">
                <td colspan="5" class="text-muted" style="text-align:center;padding:20px;font-size:13px">
                  尚無股東，請在下方輸入新增。
                </td>
              </tr>

              <tr class="ta-new-row" @keydown.enter="saveShareholder">
                <td><input class="ta-input" v-model="newSH.name" placeholder="股東名稱" /></td>
                <td><input class="ta-input num" type="text" :value="fmtInput(newSH.shares)" @change="newSH.shares = parseInput($event)" placeholder="持股數" /></td>
                <td class="num" style="color:#aaa;padding:4px 8px">—</td>
                <td class="num" style="color:#aaa;padding:4px 8px">—</td>
                <td style="padding:2px 4px">
                  <button class="btn btn-primary btn-sm" style="padding:2px 10px;font-size:13px;font-weight:700"
                    :disabled="!newSH.name.trim()" @click="saveShareholder">＋</button>
                </td>
              </tr>
            </tbody>

            <tfoot v-if="byMaster(shareholders).length">
              <tr>
                <td style="font-weight:700;padding-left:12px">總計</td>
                <td class="num fw-bold">{{ fmtShares(totalShares) }}</td>
                <td class="num fw-bold">100%</td>
                <td class="num fw-bold">{{ fmtFoot(grandTotal) }}</td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      <!-- Equity history -->
      <div v-if="byMaster(equityHistory).length" style="margin-top:20px">
        <div style="font-size:15px;font-weight:700;margin-bottom:8px;color:#1b4d2e">股票管理歷史記錄</div>
        <div class="card" style="padding:0;overflow:hidden">
          <div style="overflow-x:auto">
            <table class="table eq-hist-table">
              <thead>
                <tr>
                  <th style="width:40px;text-align:center">序</th>
                  <th style="min-width:100px">日期</th>
                  <th style="min-width:180px">備註</th>
                  <th class="num" style="min-width:120px">資產總計</th>
                  <th class="num" style="min-width:120px">總股數</th>
                  <th class="num" style="min-width:100px;background:#2e6b42 !important">每股淨值</th>
                  <th style="min-width:220px">各股東持股</th>
                  <th style="width:40px"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(r, i) in byMaster(equityHistory)" :key="r.id" class="hist-row">
                  <td style="text-align:center;color:#888;font-size:12px">{{ i + 1 }}</td>
                  <td style="font-size:13px">{{ r.date }}</td>
                  <td style="font-size:13px;color:#374151">{{ r.remark || '—' }}</td>
                  <td class="num fw-bold">{{ fmtFoot(r.totalAssets) }}</td>
                  <td class="num">{{ fmtShares(r.totalShares) }}</td>
                  <td class="num" style="color:#1b4d2e;font-weight:700;font-size:14px">{{ fmtNav(r.navPerShare) }}</td>
                  <td style="padding:4px 8px;font-size:11px">
                    <span v-for="s in r.shareholders" :key="s.name"
                      style="display:inline-block;margin:1px 6px 1px 0;background:#f0fdf4;border:1px solid #bbf7d0;padding:1px 6px;border-radius:10px;white-space:nowrap">
                      {{ s.name }}: {{ fmtShares(s.shares) }}
                      ({{ r.totalShares > 0 ? (s.shares / r.totalShares * 100).toFixed(2) : '0' }}%)
                    </span>
                  </td>
                  <td style="padding:2px 4px">
                    <button class="btn btn-danger btn-sm" style="padding:2px 7px;font-size:11px" @click="delEquityRecord(r.id)">刪</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 募資歷史記錄 -->
      <div v-if="byMaster(frHistory).length" style="margin-top:20px">
        <div style="font-size:15px;font-weight:700;margin-bottom:8px;color:#7c3aed">募資歷史記錄</div>
        <div class="card" style="padding:0;overflow:hidden">
          <div style="overflow-x:auto">
            <table class="table fr-hist-table">
              <thead>
                <tr>
                  <th style="width:40px;text-align:center">序</th>
                  <th style="min-width:100px">日期</th>
                  <th style="min-width:180px">備註</th>
                  <th class="num" style="min-width:110px">募資當時每股淨值</th>
                  <th class="num" style="min-width:110px">本次募資總金額</th>
                  <th style="min-width:280px">投資人明細</th>
                  <th style="width:40px"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(r, i) in byMaster(frHistory)" :key="r.id" class="hist-row">
                  <td style="text-align:center;color:#888;font-size:12px">{{ i + 1 }}</td>
                  <td style="font-size:13px">{{ r.date }}</td>
                  <td style="font-size:13px;color:#374151">{{ r.remark || '—' }}</td>
                  <td class="num" style="color:#1b4d2e;font-weight:700">{{ fmtNav(r.navAtTime) }}</td>
                  <td class="num fw-bold">{{ fmtFoot(r.investors.reduce((s, x) => s + x.amount, 0)) }}</td>
                  <td style="padding:4px 8px;font-size:11px">
                    <span v-for="inv in r.investors" :key="inv.name"
                      style="display:inline-block;margin:1px 6px 1px 0;background:#f5f3ff;border:1px solid #ddd6fe;padding:2px 8px;border-radius:10px;white-space:nowrap">
                      {{ inv.name }}：{{ fmtFoot(inv.amount) }}
                      <span style="color:#7c3aed">（{{ fmtShares(inv.shares) }} 股）</span>
                    </span>
                  </td>
                  <td style="padding:2px 4px">
                    <button class="btn btn-danger btn-sm" style="padding:2px 7px;font-size:11px" @click="delFrRecord(r.id)">刪</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

    </template>
  </div>
  <!-- ══ Tab 2 end ══ -->

  <!-- ══ Tab 3：股東資產總覽 ══ -->
  <div v-if="activeTab==='overview'" class="tab-panel">

    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:10px">
      <h2 style="font-size:18px;font-weight:700;margin:0">股東資產總覽</h2>
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
        <input v-model="snapshotRemark" class="form-control" placeholder="快照備註（選填）" style="width:200px;font-size:12px" @keydown.enter="saveOverviewSnapshot" />
        <button class="btn btn-primary btn-sm" style="font-size:13px;padding:5px 14px;white-space:nowrap"
          :disabled="masterRecords.length === 0"
          @click="saveOverviewSnapshot">⊕ 儲存快照</button>
      </div>
    </div>

    <!-- 當下總覽矩陣 -->
    <div v-if="masterRecords.length === 0" class="card text-muted" style="text-align:center;padding:48px;font-size:13px">
      尚未建立任何主檔，請至「主檔」頁籤新增。
    </div>
    <div v-else-if="overviewAllNames.length === 0" class="card text-muted" style="text-align:center;padding:48px;font-size:13px">
      尚未設定任何股東，請至「股東股本記錄作業」頁籤新增股東。
    </div>
    <div v-else class="card" style="padding:0;overflow:hidden">
      <div style="background:#1e3a5f;padding:8px 16px">
        <span style="color:#d6eaf8;font-weight:700;font-size:13px">當下各股東各公司群組資產市值</span>
        <span style="color:#93c5fd;font-size:12px;margin-left:12px">（依各公司股權占比換算）</span>
      </div>
      <div style="overflow-x:auto">
        <table class="table ov-table">
          <thead>
            <tr>
              <th style="min-width:130px;position:sticky;left:0;z-index:2">股東姓名</th>
              <th v-for="mt in masterTotals" :key="mt.masterId" class="num" style="min-width:130px">{{ mt.masterName }}</th>
              <th class="num" style="min-width:130px;background:#2e5985 !important">合計</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in overviewMatrix" :key="row.name" class="ov-row">
              <td style="font-weight:600;position:sticky;left:0;background:#fff;z-index:1">{{ row.name }}</td>
              <td v-for="mt in masterTotals" :key="mt.masterId" class="num">
                {{ row.values[mt.masterId] > 0 ? fmtFoot(row.values[mt.masterId]) : '—' }}
              </td>
              <td class="num fw-bold" style="background:#f0f6ff">{{ row.total > 0 ? fmtFoot(row.total) : '—' }}</td>
            </tr>
            <tr v-if="!overviewMatrix.length">
              <td :colspan="masterTotals.length + 2" class="text-muted" style="text-align:center;padding:20px">無資料</td>
            </tr>
          </tbody>
          <tfoot>
            <tr>
              <td style="font-weight:700;padding-left:12px;position:sticky;left:0;background:#f8fafc">公司資產總計</td>
              <td v-for="mt in masterTotals" :key="mt.masterId" class="num fw-bold">{{ mt.total > 0 ? fmtFoot(mt.total) : '—' }}</td>
              <td class="num fw-bold" style="color:#1e3a5f">{{ overviewGrandTotal > 0 ? fmtFoot(overviewGrandTotal) : '—' }}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>

    <!-- 歷史快照 -->
    <div v-if="shOverviewHistory.length" style="margin-top:28px">
      <h3 style="font-size:16px;font-weight:700;margin:0 0 12px;color:#1e3a5f">歷史快照</h3>
      <div v-for="snap in [...shOverviewHistory].reverse()" :key="snap.id" class="card" style="margin-bottom:16px;padding:0;overflow:hidden">
        <div style="display:flex;align-items:center;justify-content:space-between;background:#1e3a5f;padding:8px 14px">
          <div style="display:flex;align-items:center;gap:12px">
            <span style="color:#d6eaf8;font-size:12px">{{ snap.date }}</span>
            <span v-if="snap.remark" style="color:#93c5fd;font-size:12px">{{ snap.remark }}</span>
            <span style="color:#60a5fa;font-size:12px">總計：{{ fmtFoot(snap.grandTotal) }}</span>
          </div>
          <button class="btn btn-danger btn-sm" style="padding:2px 8px;font-size:11px" @click="delOverviewSnapshot(snap.id)">刪除</button>
        </div>
        <div style="overflow-x:auto">
          <table class="table ov-table">
            <thead>
              <tr>
                <th style="min-width:130px;position:sticky;left:0;z-index:2">股東姓名</th>
                <th v-for="m in snap.masters" :key="m.id" class="num" style="min-width:130px">{{ m.name }}</th>
                <th class="num" style="min-width:130px;background:#2e5985 !important">合計</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in snap.rows" :key="row.name" class="ov-row">
                <td style="font-weight:600;position:sticky;left:0;background:#fff;z-index:1">{{ row.name }}</td>
                <td v-for="m in snap.masters" :key="m.id" class="num">
                  {{ (row.values[m.id] ?? 0) > 0 ? fmtFoot(row.values[m.id]) : '—' }}
                </td>
                <td class="num fw-bold" style="background:#f0f6ff">{{ row.total > 0 ? fmtFoot(row.total) : '—' }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr>
                <td style="font-weight:700;padding-left:12px;position:sticky;left:0;background:#f8fafc">公司資產總計</td>
                <td v-for="m in snap.masters" :key="m.id" class="num fw-bold">{{ m.total > 0 ? fmtFoot(m.total) : '—' }}</td>
                <td class="num fw-bold" style="color:#1e3a5f">{{ snap.grandTotal > 0 ? fmtFoot(snap.grandTotal) : '—' }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>

  </div>
  <!-- ══ Tab 3 end ══ -->

  <!-- ══ Portfolio Picker Modal ══ -->
  <div v-if="showPicker" class="modal-overlay" @click.self="showPicker=false">
    <div class="modal" style="min-width:380px">
      <div class="modal-title">從證券明細帶入</div>
      <div v-if="pickerLoading" class="text-muted" style="text-align:center;padding:24px">載入中…</div>
      <div v-else>
        <div v-if="!store.portfolios.length" class="text-muted" style="padding:16px">尚無投資組合</div>
        <label v-for="p in store.portfolios.filter(p => !linkedByOthers.has(p.id))" :key="p.id"
          class="picker-row" :class="{ 'picker-row--done': linkedIds.has(p.id) }">
          <input v-if="!linkedIds.has(p.id)" type="checkbox"
            :checked="pickerSelected.has(p.id)" @change="togglePickerItem(p.id)"
            style="width:16px;height:16px;cursor:pointer;flex-shrink:0" />
          <span v-else style="width:16px;height:16px;flex-shrink:0;display:flex;align-items:center;justify-content:center;color:#27ae60;font-size:14px">✓</span>
          <div style="flex:1;min-width:0">
            <div style="font-weight:600;font-size:14px">{{ p.name }}</div>
            <div class="text-muted" style="font-size:12px">{{ p.description || '無描述' }}</div>
          </div>
          <span v-if="linkedIds.has(p.id)" style="font-size:12px;color:#27ae60;font-weight:600;white-space:nowrap">已帶入</span>
        </label>
      </div>
      <div class="modal-actions">
        <button class="btn btn-ghost" @click="showPicker=false">關閉</button>
        <button class="btn btn-primary" :disabled="pickerSelected.size===0 || pickerLoading" @click="confirmPicker">
          帶入已選取（{{ pickerSelected.size }}）
        </button>
      </div>
    </div>
  </div>

  <!-- ══ Account Type Manager Modal ══ -->
  <div v-if="showTypesMgr" class="modal-overlay" @click.self="showTypesMgr=false">
    <div class="modal" style="min-width:320px">
      <div class="modal-title">管理帳戶類型選單</div>
      <div style="max-height:280px;overflow-y:auto;margin-bottom:4px">
        <div v-for="t in acctTypes" :key="t" class="type-mgr-row">
          <span style="flex:1;font-size:14px">{{ t }}</span>
          <span v-if="DEFAULT_TYPES.includes(t)" style="font-size:11px;color:#94a3b8;margin-right:6px">預設</span>
          <button class="btn btn-danger btn-sm" style="padding:1px 8px;font-size:11px"
            :disabled="DEFAULT_TYPES.includes(t) || byMaster(totalRows).some(r => r.accountType === t)"
            :title="DEFAULT_TYPES.includes(t) ? '預設類型不可刪除' : byMaster(totalRows).some(r => r.accountType === t) ? '使用中，無法刪除' : ''"
            @click="removeManagedType(t)">刪</button>
        </div>
        <div v-if="!acctTypes.length" class="text-muted" style="padding:12px;font-size:13px">尚無類型</div>
      </div>
      <div style="display:flex;gap:8px;padding:12px 0 4px;border-top:1px solid #e2e8f0">
        <input v-model="newTypeName" class="form-control" placeholder="輸入新帳戶類型名稱" style="flex:1" @keydown.enter="addManagedType" />
        <button class="btn btn-primary" :disabled="!newTypeName.trim() || acctTypes.includes(newTypeName.trim())" @click="addManagedType">新增</button>
      </div>
      <div class="modal-actions">
        <button class="btn btn-ghost" @click="showTypesMgr=false">關閉</button>
      </div>
    </div>
  </div>

  <!-- ══ Create Portfolio Modal ══ -->
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

  <!-- ══ 募資重算股權 Modal ══ -->
  <div v-if="showFundraise" class="modal-overlay" @click.self="showFundraise=false">
    <div class="modal" style="min-width:480px;max-width:560px">
      <div class="modal-title">⚖ 募資重算股權</div>

      <!-- 目前狀態 -->
      <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;padding:10px 16px;margin-bottom:14px;font-size:13px">
        <div style="display:flex;gap:24px;flex-wrap:wrap">
          <span>目前每股淨值：<strong style="color:#1b4d2e;font-size:15px">{{ fmtNav(navPerShare) }}</strong></span>
          <span>目前總資產：<strong>{{ fmtFoot(grandTotal) }}</strong></span>
          <span>目前總股數：<strong>{{ fmtShares(totalShares) }}</strong></span>
        </div>
      </div>

      <!-- 日期 + 備註 -->
      <div style="display:flex;gap:12px;margin-bottom:12px;flex-wrap:wrap">
        <div class="form-group" style="flex:0 0 140px;margin-bottom:0">
          <label style="font-size:13px;font-weight:600">募資日期</label>
          <input type="date" v-model="frDate" class="form-control" />
        </div>
        <div class="form-group" style="flex:1;min-width:160px;margin-bottom:0">
          <label style="font-size:13px;font-weight:600">備註說明</label>
          <input v-model="frRemark" class="form-control" placeholder="例：A輪增資、股權轉讓…" />
        </div>
      </div>

      <!-- 多投資人列表 -->
      <div style="font-size:13px;font-weight:600;margin-bottom:6px;color:#1e3a5f">投資人清單</div>
      <table style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:8px">
        <thead>
          <tr style="background:#f1f5f9">
            <th style="padding:5px 8px;text-align:left;border:1px solid #e2e8f0;min-width:150px">投資人名稱</th>
            <th style="padding:5px 8px;text-align:right;border:1px solid #e2e8f0;min-width:130px">投入金額</th>
            <th style="padding:5px 8px;text-align:right;border:1px solid #e2e8f0;min-width:110px">可換股數</th>
            <th style="padding:5px 8px;width:36px;border:1px solid #e2e8f0"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(inv, i) in frInvestors" :key="i">
            <td style="padding:3px 4px;border:1px solid #e2e8f0">
              <input class="ta-input" v-model="inv.investorName" placeholder="投資人名稱" />
            </td>
            <td style="padding:3px 4px;border:1px solid #e2e8f0">
              <input class="ta-input num" type="text" :value="fmtInput(inv.amount)" @change="inv.amount = parseInput($event)" placeholder="0" />
            </td>
            <td style="padding:4px 8px;text-align:right;border:1px solid #e2e8f0;font-size:12px;color:#374151">
              {{ navPerShare > 0 && (Number(inv.amount)||0) > 0 ? fmtShares((Number(inv.amount)||0) / navPerShare) : '—' }}
            </td>
            <td style="padding:2px 4px;text-align:center;border:1px solid #e2e8f0">
              <button class="btn btn-danger btn-sm" style="padding:1px 6px;font-size:11px"
                :disabled="frInvestors.length <= 1" @click="removeFrInvestor(i)">✕</button>
            </td>
          </tr>
        </tbody>
        <tfoot>
          <tr style="background:#f8fafc">
            <td style="padding:5px 8px;border:1px solid #e2e8f0;font-weight:700">合計</td>
            <td style="padding:5px 8px;text-align:right;border:1px solid #e2e8f0;font-weight:700">{{ fmtFoot(frTotalAmount) }}</td>
            <td style="padding:5px 8px;text-align:right;border:1px solid #e2e8f0;font-weight:700">{{ fmtShares(frNewShares) }}</td>
            <td style="border:1px solid #e2e8f0"></td>
          </tr>
        </tfoot>
      </table>
      <button class="btn btn-ghost btn-sm" style="font-size:12px;margin-bottom:14px" @click="addFrInvestor">＋ 新增投資人</button>

      <!-- 模擬結果 -->
      <div v-if="frTotalAmount > 0 && navPerShare > 0" style="margin-bottom:14px">
        <div style="font-size:12px;font-weight:700;color:#1e3a5f;margin-bottom:6px">模擬計算結果</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px">
          <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:6px;padding:7px 12px;font-size:12px">
            <div style="color:#3b82f6;font-size:11px">新增後總資產</div>
            <div style="font-weight:700;font-size:14px">{{ fmtFoot(frNewTotal) }}</div>
          </div>
          <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:6px;padding:7px 12px;font-size:12px">
            <div style="color:#3b82f6;font-size:11px">新增後總股數</div>
            <div style="font-weight:700;font-size:14px">{{ fmtShares(frNewTotalSH) }}</div>
          </div>
          <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;padding:7px 12px;font-size:12px;grid-column:span 2">
            <div style="color:#16a34a;font-size:11px">新增後每股淨值（應不變）</div>
            <div style="font-weight:700;font-size:15px;color:#1b4d2e">{{ fmtNav(frNewNav) }}</div>
          </div>
        </div>
        <div style="font-size:12px;font-weight:700;color:#374151;margin-bottom:5px">股東持股模擬</div>
        <table style="width:100%;border-collapse:collapse;font-size:12px">
          <thead><tr style="background:#f1f5f9">
            <th style="padding:4px 8px;text-align:left;border:1px solid #e2e8f0">股東</th>
            <th style="padding:4px 8px;text-align:right;border:1px solid #e2e8f0">股數</th>
            <th style="padding:4px 8px;text-align:right;border:1px solid #e2e8f0">占比</th>
          </tr></thead>
          <tbody>
            <tr v-for="s in frSimRows" :key="s.name" :style="s.isNew ? 'background:#fffbeb' : ''">
              <td style="padding:3px 8px;border:1px solid #e2e8f0">
                {{ s.name }}
                <span v-if="s.isNew" style="font-size:10px;background:#fef3c7;color:#92400e;padding:1px 5px;border-radius:8px;margin-left:4px">新投資人</span>
              </td>
              <td style="padding:3px 8px;text-align:right;border:1px solid #e2e8f0">{{ fmtShares(s.shares) }}</td>
              <td style="padding:3px 8px;text-align:right;border:1px solid #e2e8f0">
                {{ frNewTotalSH > 0 ? (s.shares / frNewTotalSH * 100).toFixed(2) + '%' : '—' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="modal-actions">
        <button class="btn btn-ghost" @click="showFundraise=false">取消</button>
        <button class="btn btn-primary"
          :disabled="frTotalAmount <= 0 || navPerShare === 0"
          @click="applyFundraise">確認套用</button>
      </div>
    </div>
  </div>

</template>

<style scoped>
/* ── Tab 導覽 ── */
.tab-nav { display:flex; gap:0; border-bottom:2px solid #e2e8f0; margin-bottom:24px; }
.tab-btn { padding:10px 24px; font-size:14px; font-weight:600; border:none; border-bottom:3px solid transparent; background:transparent; color:#64748b; cursor:pointer; margin-bottom:-2px; transition:color .15s,border-color .15s; white-space:nowrap; }
.tab-btn:hover { color:#1e3a5f; }
.tab-btn--active { color:#1e3a5f; border-bottom-color:#1e3a5f; background:#f8fafc; }
.tab-panel { animation:fadeIn .15s ease; }
@keyframes fadeIn { from { opacity:0; transform:translateY(4px); } to { opacity:1; transform:none; } }

/* ── No master guard ── */
.no-master-guard { text-align:center; padding:60px 20px; border:2px dashed #e2e8f0; border-radius:12px; background:#fafafa; }
.no-master-icon  { font-size:48px; margin-bottom:12px; }
.no-master-title { font-size:18px; font-weight:700; color:#1e293b; margin-bottom:8px; }
.no-master-desc  { font-size:13px; color:#64748b; margin-bottom:20px; max-width:420px; margin-left:auto; margin-right:auto; line-height:1.6; }

/* ── Active master banner ── */
.master-banner { display:flex; align-items:center; background:#1e3a5f; border-radius:8px; padding:10px 16px; margin-bottom:20px; gap:4px; }

/* ── 主檔資訊表 ── */
.master-table th { background:#1e3a5f; color:#d6eaf8; font-weight:600; white-space:nowrap; font-size:12px; padding:8px 10px; }
.master-row--active td { background:#f0fdf4 !important; }
.master-row--active { border-left:3px solid #16a34a; }
.btn-select-master { padding:2px 8px; font-size:11px; font-weight:700; background:#e0f2fe; color:#0369a1; border:1px solid #bae6fd; border-radius:3px; cursor:pointer; white-space:nowrap; }
.btn-select-master:hover { background:#bae6fd; }
.master-active-badge { font-size:10px; font-weight:700; background:#dcfce7; color:#16a34a; padding:2px 7px; border-radius:8px; white-space:nowrap; }

/* ── 主檔摘要卡片 ── */
.summary-card { background:#fff; border:1px solid #e2e8f0; border-radius:8px; padding:14px 18px; box-shadow:0 1px 3px rgba(0,0,0,.06); }
.summary-label { font-size:11px; color:#64748b; margin-bottom:4px; }
.summary-value { font-size:20px; font-weight:700; color:#1e293b; }

/* ── 資產總計表 ── */
.ta-table th { background:#1a5276; color:#d6eaf8; font-weight:600; white-space:nowrap; font-size:12px; padding:8px 10px; }
.ta-table tfoot td { background:#f8fafc; border-top:2px solid #cbd5e1; padding:7px 10px; }
.ta-row td { vertical-align:middle; padding:3px 4px; }
.ta-row:hover td { background:#f0f8ff; }
.ta-input { width:100%; border:1px solid #e2e8f0; border-radius:3px; padding:3px 6px; font-size:12px; background:transparent; outline:none; box-sizing:border-box; }
.ta-input:focus { border-color:#2563eb; background:#fff; box-shadow:0 0 0 2px rgba(37,99,235,.15); }
.ta-input.num { text-align:right; }
.ta-select { cursor:pointer; }
.ta-new-row td { background:#f0fff4; padding:3px 4px; border-top:2px dashed #27ae60; vertical-align:middle; }
.btn-type-mgr { margin-left:6px; padding:1px 6px; font-size:11px; font-weight:700; background:rgba(255,255,255,.2); color:#fff; border:1px solid rgba(255,255,255,.4); border-radius:3px; cursor:pointer; line-height:1.4; vertical-align:middle; }
.btn-type-mgr:hover { background:rgba(255,255,255,.35); }
.type-mgr-row { display:flex; align-items:center; padding:8px 4px; border-bottom:1px solid #f1f5f9; }
.type-mgr-row:last-child { border-bottom:none; }
.picker-row { display:flex; align-items:center; gap:12px; padding:10px 4px; border-bottom:1px solid #e2e8f0; cursor:pointer; user-select:none; transition:background .1s; }
.picker-row:hover { background:#f0f8ff; }
.picker-row--done { opacity:.6; cursor:default; }
.picker-row--done:hover { background:transparent; }

/* ── 歷史記錄表 ── */
.hist-table th { background:#1e3a5f; color:#d6eaf8; font-weight:600; font-size:11px; padding:7px 8px; white-space:nowrap; text-align:center; line-height:1.4; }
.hist-row td { vertical-align:middle; padding:3px 3px; }
.hist-row:hover td { background:#f0f4ff; }
.chg-th { width:22px; padding:0 !important; }
.chg-col { width:22px; text-align:center; font-size:11px; font-weight:700; padding:0 2px; white-space:nowrap; }
.chg-up { color:#16a34a; }
.chg-dn { color:#dc2626; }
.pct-th { background:#2e5985 !important; min-width:72px; }
.pct-cell { font-size:12px; color:#374151; background:#f8fafc; padding:4px 8px; }

/* ── 股東持股表 ── */
.eq-table th, .eq-hist-table th { background:#1b4d2e; color:#d4edda; font-weight:600; white-space:nowrap; font-size:12px; padding:8px 10px; }
.eq-table tfoot td { background:#f0fdf4; border-top:2px solid #86efac; padding:8px 10px; font-size:13px; }
.eq-hist-table td { vertical-align:middle; padding:5px 6px; }
.eq-hist-table tr:hover td { background:#f0fdf4; }

/* ── 募資歷史記錄表 ── */
.fr-hist-table th { background:#6d28d9; color:#ede9fe; font-weight:600; white-space:nowrap; font-size:12px; padding:8px 10px; }
.fr-hist-table td { vertical-align:middle; padding:5px 6px; }
.fr-hist-table tr:hover td { background:#faf5ff; }

/* ── 股東資產總覽表 ── */
.ov-table th { background:#1e3a5f; color:#d6eaf8; font-weight:600; white-space:nowrap; font-size:12px; padding:8px 10px; }
.ov-table tfoot td { background:#f8fafc; border-top:2px solid #cbd5e1; padding:8px 10px; }
.ov-row td { vertical-align:middle; padding:6px 10px; }
.ov-row:hover td { background:#f0f6ff; }
</style>
