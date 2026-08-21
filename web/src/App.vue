<script setup lang="ts">
import { computed, shallowRef } from 'vue'
import { Box, LoaderCircle, Play, Upload } from 'lucide-vue-next'
import EpshapeViewer from './components/EpshapeViewer.vue'
import EmptyState from './components/EmptyState.vue'
import ResultCharts from './components/ResultCharts.vue'
import {
  renderGeometry,
  runSimulation,
  type GeometryData,
  type SimulationResult,
} from './api'

type ActiveAction = 'render' | 'simulation' | null
type NoticeKind = 'idle' | 'success' | 'failure'

const idfFile = shallowRef<File | null>(null)
const epwFile = shallowRef<File | null>(null)
const geometry = shallowRef<GeometryData | null>(null)
const result = shallowRef<SimulationResult | null>(null)
const activeAction = shallowRef<ActiveAction>(null)
const notice = shallowRef('Select an IDF to render or select both files to simulate.')
const noticeKind = shallowRef<NoticeKind>('idle')

const busy = computed(() => activeAction.value !== null)
const canRender = computed(() => idfFile.value !== null && !busy.value)
const canSimulate = computed(
  () => idfFile.value !== null && epwFile.value !== null && !busy.value,
)
const noticeClasses = computed(() => ({
  'border-[color:var(--app-border)] text-[var(--app-text-muted)] bg-[var(--app-panel-2)]':
    noticeKind.value === 'idle',
  'border-green-500/25 text-green-700 bg-green-500/10':
    noticeKind.value === 'success',
  'border-red-500/25 text-red-700 bg-red-500/10':
    noticeKind.value === 'failure',
}))

function handleIdfFile(event: Event) {
  const input = event.target as HTMLInputElement
  idfFile.value = input.files?.[0] ?? null
  geometry.value = null
  result.value = null
  resetNotice()
}

function handleEpwFile(event: Event) {
  const input = event.target as HTMLInputElement
  epwFile.value = input.files?.[0] ?? null
  result.value = null
  resetNotice()
}

async function handleRender() {
  if (!idfFile.value || busy.value) return
  activeAction.value = 'render'
  notice.value = 'Parsing IDF geometry...'
  noticeKind.value = 'idle'
  try {
    geometry.value = await renderGeometry(idfFile.value)
    notice.value = '3D geometry is ready.'
    noticeKind.value = 'success'
  } catch (caught) {
    showFailure(caught, 'The IDF could not be rendered.')
  } finally {
    activeAction.value = null
  }
}

async function handleSimulation() {
  if (!idfFile.value || !epwFile.value || busy.value) return
  activeAction.value = 'simulation'
  notice.value = 'Running EnergyPlus simulation...'
  noticeKind.value = 'idle'
  try {
    result.value = await runSimulation(idfFile.value, epwFile.value)
    notice.value = `Simulation completed with ${result.value.row_count.toLocaleString()} result rows.`
    noticeKind.value = 'success'
  } catch (caught) {
    showFailure(caught, 'The simulation could not be completed.')
  } finally {
    activeAction.value = null
  }
}

function resetNotice() {
  notice.value = 'Select an IDF to render or select both files to simulate.'
  noticeKind.value = 'idle'
}

function showFailure(caught: unknown, fallback: string) {
  notice.value = caught instanceof Error ? caught.message : fallback
  noticeKind.value = 'failure'
}
</script>

<template>
  <div class="min-h-screen bg-[var(--app-bg)] text-[var(--app-text)]">
    <header
      class="h-16 px-5 border-b border-[color:var(--app-border)] bg-[var(--app-header)] flex items-center justify-center"
    >
      <span class="font-semibold text-lg tracking-wide">EnergyPlus Visualization</span>
    </header>

    <main class="max-w-[1800px] mx-auto p-4 space-y-4">
      <section
        class="rounded-lg border p-4 bg-[var(--app-panel)] border-[color:var(--app-border)]"
      >
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-[1fr_1fr_auto_auto] gap-3 items-end">
          <div class="space-y-1">
            <label class="text-xs text-[var(--app-text-muted)]">Building File (IDF)</label>
            <div
              class="relative flex items-center h-[34px] rounded border border-[color:var(--app-border)] overflow-hidden hover:border-blue-400 transition-colors"
            >
              <input
                type="file"
                accept=".idf,.expidf"
                class="absolute inset-0 opacity-0 cursor-pointer w-full h-full z-10"
                :disabled="busy"
                @change="handleIdfFile"
              />
              <div
                class="px-3 h-full flex items-center gap-2 bg-[var(--app-panel-2)] border-r border-[color:var(--app-border)] text-xs font-medium"
              >
                <Upload :size="14" /> Choose
              </div>
              <div class="px-3 text-xs text-[var(--app-text-muted)] truncate flex-1">
                {{ idfFile?.name || 'No file selected' }}
              </div>
            </div>
          </div>

          <div class="space-y-1">
            <label class="text-xs text-[var(--app-text-muted)]">Weather File (EPW)</label>
            <div
              class="relative flex items-center h-[34px] rounded border border-[color:var(--app-border)] overflow-hidden hover:border-blue-400 transition-colors"
            >
              <input
                type="file"
                accept=".epw"
                class="absolute inset-0 opacity-0 cursor-pointer w-full h-full z-10"
                :disabled="busy"
                @change="handleEpwFile"
              />
              <div
                class="px-3 h-full flex items-center gap-2 bg-[var(--app-panel-2)] border-r border-[color:var(--app-border)] text-xs font-medium"
              >
                <Upload :size="14" /> Choose
              </div>
              <div class="px-3 text-xs text-[var(--app-text-muted)] truncate flex-1">
                {{ epwFile?.name || 'No file selected' }}
              </div>
            </div>
          </div>

          <button
            type="button"
            class="h-[34px] px-4 rounded border border-[color:var(--app-border)] flex items-center justify-center gap-2 text-xs font-semibold hover:bg-[color:color-mix(in_srgb,var(--app-accent)_10%,transparent)] disabled:opacity-45 disabled:cursor-not-allowed transition-colors"
            :disabled="!canRender"
            @click="handleRender"
          >
            <LoaderCircle v-if="activeAction === 'render'" :size="15" class="animate-spin" />
            <Box v-else :size="15" />
            3D Render
          </button>
          <button
            type="button"
            class="h-[34px] px-4 rounded bg-[var(--app-accent)] text-white flex items-center justify-center gap-2 text-xs font-semibold disabled:opacity-45 disabled:cursor-not-allowed hover:brightness-105 transition"
            :disabled="!canSimulate"
            @click="handleSimulation"
          >
            <LoaderCircle
              v-if="activeAction === 'simulation'"
              :size="15"
              class="animate-spin"
            />
            <Play v-else :size="15" />
            Simulation
          </button>
        </div>

        <div class="mt-3 rounded border px-3 py-2 text-xs" :class="noticeClasses">
          {{ notice }}
        </div>
      </section>

      <section
        class="rounded-lg border h-[500px] p-3 flex flex-col bg-[var(--app-panel)] border-[color:var(--app-border)]"
      >
        <div class="text-sm font-semibold mb-2">3D Building Viewer</div>
        <div
          v-if="geometry"
          class="flex-1 min-h-0 rounded border overflow-hidden border-[color:var(--app-border)] bg-[var(--app-panel-2)]"
        >
          <EpshapeViewer
            :geometry-data="geometry"
            :is-maximized="false"
            :show-fullscreen-button="false"
          />
        </div>
        <div v-else class="flex-1 min-h-0">
          <EmptyState
            title="No 3D geometry"
            description="Select an IDF file and click 3D Render."
          />
        </div>
      </section>

      <ResultCharts v-if="result" :result="result" />
      <section v-else class="grid grid-cols-1 xl:grid-cols-3 auto-rows-[390px] gap-4">
        <div
          v-for="title in ['Outdoor Weather Monitoring', 'Indoor Temperature Curves', 'Energy Area Trends']"
          :key="title"
          class="rounded-lg border p-3 flex flex-col bg-[var(--app-panel)] border-[color:var(--app-border)]"
        >
          <div class="text-sm font-semibold mb-2">{{ title }}</div>
          <div class="flex-1 min-h-0">
            <EmptyState
              title="No simulation results"
              description="Select IDF and EPW files, then click Simulation."
            />
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
