<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue'
import type { EChartsOption } from 'echarts'
import type { ChartGroup, SimulationResult } from '../api'
import InteractiveEChart from './charts/InteractiveEChart.vue'

const props = defineProps<{
  result: SimulationResult
}>()

const weatherKeys = shallowRef<string[]>([])
const indoorKeys = shallowRef<string[]>([])
const energyKeys = shallowRef<string[]>([])

const palette = ['#4477aa', '#ee6677', '#228833', '#ccbb44', '#66ccee', '#aa3377']

watch(
  () => props.result,
  (result) => {
    weatherKeys.value = result.weather.series.slice(0, 1).map((item) => item.key)
    indoorKeys.value = result.indoor.series.map((item) => item.key)
    energyKeys.value = result.energy.series.map((item) => item.key)
  },
  { immediate: true },
)

const weatherSelectors = computed(() => selectors(props.result.weather))
const indoorSelectors = computed(() => selectors(props.result.indoor))
const energySelectors = computed(() => selectors(props.result.energy))

const weatherOption = computed(() =>
  buildOption(props.result.weather, weatherKeys.value, false),
)
const indoorOption = computed(() =>
  buildOption(props.result.indoor, indoorKeys.value, false),
)
const energyOption = computed(() =>
  buildOption(props.result.energy, energyKeys.value, true),
)

function selectors(group: ChartGroup) {
  return group.series.map((item) => ({
    key: item.key,
    label: `${item.label} · ${item.unit}`,
  }))
}

function buildOption(
  group: ChartGroup,
  selectedKeys: string[],
  area: boolean,
): EChartsOption {
  const selected = group.series.filter((item) => selectedKeys.includes(item.key))
  const units = Array.from(new Set(selected.map((item) => item.unit)))
  const unitByLabel = new Map(group.series.map((item) => [item.label, item.unit]))
  return {
    color: palette,
    animation: false,
    tooltip: {
      trigger: 'axis',
      formatter: (params: unknown) => formatTooltip(params, unitByLabel),
    },
    legend: {
      type: 'scroll',
      top: 2,
      textStyle: { color: '#475569', fontSize: 11 },
    },
    grid: { left: 58, right: 24, top: 48, bottom: 54, containLabel: true },
    dataZoom: [
      { type: 'inside', filterMode: 'none' },
      {
        type: 'slider',
        left: 58,
        right: 24,
        bottom: 8,
        height: 18,
        showDetail: false,
        brushSelect: false,
      },
    ],
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: group.labels,
      axisLabel: { color: '#64748b', hideOverlap: true },
      axisLine: { lineStyle: { color: 'rgba(15, 23, 42, 0.22)' } },
    },
    yAxis: {
      type: 'value',
      name: units.length === 1 ? units[0] : units.join(' / '),
      nameTextStyle: { color: '#64748b' },
      axisLabel: { color: '#64748b' },
      splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.18)' } },
    },
    series: selected.map((item, index) => ({
      id: item.key,
      name: item.label,
      type: 'line',
      data: item.values,
      showSymbol: false,
      connectNulls: false,
      sampling: 'lttb',
      lineStyle: { width: 1.8 },
      areaStyle: area && index === 0 ? { opacity: 0.16 } : undefined,
      emphasis: { focus: 'series' },
    })),
  }
}

function formatTooltip(
  params: unknown,
  units: Map<string, string>,
): string {
  const entries = Array.isArray(params) ? params : [params]
  const first = entries[0] as { axisValueLabel?: string } | undefined
  const lines = [String(first?.axisValueLabel ?? '')]
  for (const entry of entries as Array<{
    marker?: string
    seriesName?: string
    value?: unknown
  }>) {
    const name = String(entry.seriesName ?? '')
    const numeric = Number(entry.value)
    const value = Number.isFinite(numeric)
      ? numeric.toLocaleString(undefined, { maximumFractionDigits: 2 })
      : '-'
    lines.push(`${entry.marker ?? ''}${name}: ${value} ${units.get(name) ?? ''}`)
  }
  return lines.join('<br/>')
}
</script>

<template>
  <section class="grid grid-cols-1 xl:grid-cols-3 auto-rows-[390px] gap-4">
    <InteractiveEChart
      title="Outdoor Weather Monitoring"
      :option="weatherOption"
      :selectors="weatherSelectors"
      :selected-keys="weatherKeys"
      :show-expand-button="false"
      @update:selected-keys="weatherKeys = $event"
    />
    <InteractiveEChart
      title="Indoor Temperature Curves"
      :option="indoorOption"
      :selectors="indoorSelectors"
      :selected-keys="indoorKeys"
      :show-expand-button="false"
      @update:selected-keys="indoorKeys = $event"
    />
    <InteractiveEChart
      title="Energy Area Trends"
      :option="energyOption"
      :selectors="energySelectors"
      :selected-keys="energyKeys"
      :show-expand-button="false"
      @update:selected-keys="energyKeys = $event"
    />
  </section>
</template>
