<script setup lang="ts">
import { computed } from 'vue'
import { Pie } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import type { AssetTypeSummary } from '@/types'

ChartJS.register(ArcElement, Tooltip, Legend)

const props = defineProps<{ data: AssetTypeSummary[] }>()

const COLORS = ['#2563eb', '#16a34a', '#d97706', '#7c3aed', '#db2777']

const chartData = computed(() => ({
  labels: props.data.map(d => d.asset_type),
  datasets: [{
    data: props.data.map(d => Number(d.mv_2)),
    backgroundColor: COLORS.slice(0, props.data.length),
    borderWidth: 2,
    borderColor: '#fff',
  }],
}))

const options = {
  responsive: true,
  plugins: {
    legend: { position: 'bottom' as const },
    tooltip: {
      callbacks: {
        label: (ctx: any) => {
          const val = ctx.parsed
          const total = ctx.dataset.data.reduce((a: number, b: number) => a + b, 0)
          const pct = total ? ((val / total) * 100).toFixed(1) : '0'
          return ` ${ctx.label}: ${val.toLocaleString()} (${pct}%)`
        },
      },
    },
  },
}
</script>

<template>
  <Pie :data="chartData" :options="options" style="max-height:260px" />
</template>
