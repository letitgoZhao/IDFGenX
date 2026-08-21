<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, shallowRef, watch } from 'vue'
import type { ComponentPublicInstance } from 'vue'
import * as echarts from 'echarts'
import { Expand, Shrink } from 'lucide-vue-next'
import EmptyState from '../EmptyState.vue'
import { useTheme } from '../../composables/useTheme'

type SeriesSelector = {
  key: string
  label: string
}

const props = withDefaults(
  defineProps<{
    title: string
    option: echarts.EChartsOption
    selectors: SeriesSelector[]
    selectedKeys: string[]
    compact?: boolean
    expanded?: boolean
    showExpandButton?: boolean
  }>(),
  {
    compact: false,
    expanded: false,
    showExpandButton: true,
  },
)

const emit = defineEmits<{
  (e: 'update:selectedKeys', keys: string[]): void
  (e: 'toggle-expand'): void
}>()

const { theme } = useTheme()
const chartEl = shallowRef<HTMLDivElement | null>(null)
const chartInstance = shallowRef<echarts.EChartsType | null>(null)
let resizeObserver: ResizeObserver | null = null
let renderFrame = 0

const selectedSet = computed(() => new Set(props.selectedKeys))
const hasSelectors = computed(() => props.selectors.length > 0)
const hasSelection = computed(() => props.selectedKeys.length > 0)

const toggleSeries = (key: string) => {
  const next = selectedSet.value.has(key)
    ? props.selectedKeys.filter((item) => item !== key)
    : [...props.selectedKeys, key]
  emit('update:selectedKeys', next)
}

const canRenderChart = () => {
  const el = chartEl.value
  return !!el && el.clientWidth > 0 && el.clientHeight > 0
}

const initChart = async () => {
  await nextTick()
  if (!chartEl.value || !canRenderChart()) return
  chartInstance.value?.dispose()
  chartInstance.value = echarts.init(chartEl.value, theme.value === 'light' ? undefined : 'dark')
  chartInstance.value.setOption(props.option, { notMerge: false, lazyUpdate: true })
  chartInstance.value.resize()
}

const resizeChart = () => {
  if (!canRenderChart()) return
  chartInstance.value?.resize()
}

const disposeChart = () => {
  chartInstance.value?.dispose()
  chartInstance.value = null
}

const observeChartElement = (el: Element | ComponentPublicInstance | null) => {
  const nextEl = el instanceof HTMLDivElement ? el : null
  if (resizeObserver && chartEl.value) {
    resizeObserver.unobserve(chartEl.value)
  }
  chartEl.value = nextEl
  if (!nextEl) {
    disposeChart()
    return
  }
  if (typeof ResizeObserver !== 'undefined') {
    if (!resizeObserver) {
      resizeObserver = new ResizeObserver(() => scheduleChartRender())
    }
    resizeObserver.observe(nextEl)
  }
  void initChart()
}

const scheduleChartRender = (option = props.option) => {
  if (renderFrame) cancelAnimationFrame(renderFrame)
  renderFrame = requestAnimationFrame(() => {
    renderFrame = 0
    if (!canRenderChart()) return
    if (!chartInstance.value) {
      void initChart()
      return
    }
    chartInstance.value.setOption(option, {
      notMerge: false,
      lazyUpdate: true,
      replaceMerge: ['series'],
    })
    chartInstance.value.resize()
  })
}

watch(
  () => props.option,
  (option) => {
    scheduleChartRender(option)
  },
  { flush: 'post' },
)

watch(
  () => theme.value,
  () => {
    void initChart()
  },
)

watch(
  () => props.expanded,
  () => {
    scheduleChartRender()
  },
  { flush: 'post' },
)

watch(
  () => hasSelection.value,
  (selected) => {
    if (selected) {
      scheduleChartRender()
    } else {
      disposeChart()
    }
  },
  { flush: 'post' },
)

onMounted(() => {
  void initChart()
  window.addEventListener('resize', resizeChart)
})

onBeforeUnmount(() => {
  if (renderFrame) cancelAnimationFrame(renderFrame)
  resizeObserver?.disconnect()
  window.removeEventListener('resize', resizeChart)
  disposeChart()
})
</script>

<template>
  <div class="h-full rounded-lg border p-3 flex flex-col bg-[var(--app-panel)] border-[color:var(--app-border)]">
    <div class="flex items-start justify-between gap-2 mb-2">
      <h3 class="text-sm font-semibold tracking-wide">{{ title }}</h3>
      <button
        v-if="showExpandButton"
        class="h-8 w-8 rounded border flex items-center justify-center hover:bg-[color:color-mix(in_srgb,var(--app-accent)_12%,transparent)] border-[color:var(--app-border)] transition-colors"
        :disabled="!hasSelectors"
        @click="emit('toggle-expand')"
      >
        <Shrink v-if="expanded" :size="16" />
        <Expand v-else :size="16" />
      </button>
    </div>
    <div v-if="hasSelectors" class="flex flex-wrap gap-2 mb-2 overflow-auto max-h-[70px]">
      <button
        v-for="selector in selectors"
        :key="selector.key"
        class="px-2 py-1 text-xs rounded border transition-colors"
        :class="selectedSet.has(selector.key) ? 'text-[var(--app-accent)] border-[var(--app-accent)] bg-[color:color-mix(in_srgb,var(--app-accent)_14%,transparent)]' : 'border-[color:var(--app-border)] text-[var(--app-text-muted)] hover:bg-[color:color-mix(in_srgb,var(--app-accent)_10%,transparent)]'"
        @click="toggleSeries(selector.key)"
      >
        {{ selector.label }}
      </button>
    </div>
    <div v-if="!hasSelectors" class="flex-1 min-h-0">
      <EmptyState title="No series available" description="Parse configuration and select variables/meters to unlock this chart." />
    </div>
    <div v-else-if="!hasSelection" class="flex-1 min-h-0">
      <EmptyState title="No series selected" description="Pick at least one curve to render the chart." />
    </div>
    <div v-else :ref="observeChartElement" class="flex-1 min-h-0" :class="compact ? 'h-[250px]' : 'h-full'" />
  </div>
</template>
