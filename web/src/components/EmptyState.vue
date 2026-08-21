<script setup lang="ts">
withDefaults(
  defineProps<{
    title?: string
    description?: string
  }>(),
  {
    title: 'No data',
    description: 'Nothing to display yet.',
  },
)
</script>

<template>
  <div class="h-full w-full flex items-center justify-center">
    <div class="max-w-sm w-full rounded-xl border border-[color:var(--app-border)] bg-[var(--app-panel-2)] px-4 py-5 text-center">
      <div class="text-sm font-semibold mb-1">{{ title }}</div>
      <div class="text-sm text-[var(--app-text-muted)]">{{ description }}</div>
    </div>
  </div>
</template>
