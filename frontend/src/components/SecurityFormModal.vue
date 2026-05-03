<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { usePortfolioStore } from '@/stores/portfolio'
import type { Security, SecurityCreatePayload } from '@/types'

const props = defineProps<{
  portfolioId: number
  editTarget?: Security | null
}>()

const emit = defineEmits<{
  close: []
  saved: [payload: SecurityCreatePayload, id?: number]
}>()

const store = usePortfolioStore()

const form = ref<SecurityCreatePayload>({
  sec_id: '', sec_name: '', curr_price: null, asset_type: '股票-個股',
  shares: 0, price_unavailable: false,
})

onMounted(() => store.fetchAssetTypes())

watch(() => props.editTarget, (t) => {
  if (t) {
    form.value = {
      sec_id: t.sec_id, sec_name: t.sec_name, curr_price: t.curr_price,
      asset_type: t.asset_type, shares: t.shares,
      fee_rate: Number(t.fee_rate), tax_rate: Number(t.tax_rate),
      price_unavailable: t.price_unavailable,
    }
  }
}, { immediate: true })

function onAssetTypeChange() {
  const found = store.assetTypes.find(a => a.asset_type === form.value.asset_type)
  if (found) form.value.tax_rate = Number(found.default_tax_rate)
}

function submit() {
  emit('saved', { ...form.value }, props.editTarget?.id)
}
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal" style="width:520px">
      <div class="modal-title">{{ editTarget ? '編輯資產' : '新增資產' }}</div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:0 16px">
        <div class="form-group">
          <label>證券代號 *</label>
          <input v-model="form.sec_id" class="form-control" placeholder="例：2330" />
        </div>
        <div class="form-group">
          <label>證券名稱 *</label>
          <input v-model="form.sec_name" class="form-control" placeholder="例：台積電" />
        </div>
        <div class="form-group">
          <label>資產類別 *</label>
          <select v-model="form.asset_type" class="form-control" @change="onAssetTypeChange">
            <option v-for="t in store.assetTypes" :key="t.asset_type" :value="t.asset_type">
              {{ t.asset_type }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>購買股數 *</label>
          <input v-model.number="form.shares" type="number" class="form-control" min="0" />
        </div>
        <div class="form-group">
          <label>最新股價</label>
          <input v-model.number="form.curr_price" type="number" class="form-control"
            :disabled="form.price_unavailable" placeholder="留空=未設定" step="0.01" />
        </div>
        <div class="form-group" style="display:flex;align-items:flex-end;padding-bottom:14px">
          <label style="display:flex;gap:8px;align-items:center;margin:0;cursor:pointer">
            <input type="checkbox" v-model="form.price_unavailable" @change="form.price_unavailable && (form.curr_price = null)" />
            無法讀取股價
          </label>
        </div>
        <div class="form-group">
          <label>手續費率</label>
          <input v-model.number="form.fee_rate" type="number" class="form-control" step="0.000001" />
        </div>
        <div class="form-group">
          <label>證交稅率</label>
          <input v-model.number="form.tax_rate" type="number" class="form-control" step="0.0001" />
        </div>
      </div>

      <div class="modal-actions">
        <button class="btn btn-ghost" @click="emit('close')">取消</button>
        <button class="btn btn-primary"
          :disabled="!form.sec_id.trim() || !form.sec_name.trim() || form.shares < 0"
          @click="submit">
          {{ editTarget ? '更新' : '新增' }}
        </button>
      </div>
    </div>
  </div>
</template>
