import { computed, onMounted, shallowRef, watchEffect } from 'vue'

export type Theme = 'light' | 'dark'

const THEME_KEY = 'theme'
const THEMES: Theme[] = ['light', 'dark']

const THEME_OPTIONS: Array<{ value: Theme; labelKey: string }> = [
  { value: 'light', labelKey: 'common.theme.light' },
  { value: 'dark', labelKey: 'common.theme.dark' },
]

const LEGACY_THEME_MAP: Record<string, Theme> = {
  'light': 'light',
  'bright': 'light',
  'dark': 'dark',
  'ocean': 'dark',
}

const pickSystemTheme = (): Theme => 'light'

const normalizeTheme = (value: string | null): Theme =>
  value && value in LEGACY_THEME_MAP ? LEGACY_THEME_MAP[value] : pickSystemTheme()

const theme = shallowRef<Theme>('light')
let initialized = false

export function useTheme() {
  const applyTheme = (nextTheme: Theme) => {
    const root = document.documentElement
    root.classList.remove('light', 'dark')
    root.classList.add(nextTheme)
    root.setAttribute('data-theme', nextTheme)
    localStorage.setItem(THEME_KEY, nextTheme)
  }

  const setTheme = (nextTheme: Theme) => {
    theme.value = nextTheme
  }

  const toggleTheme = () => {
    const idx = THEMES.indexOf(theme.value)
    const next = THEMES[(idx + 1) % THEMES.length]
    theme.value = next
  }

  onMounted(() => {
    if (!initialized) {
      initialized = true
      theme.value = normalizeTheme(localStorage.getItem(THEME_KEY))
      applyTheme(theme.value)
    }
  })

  watchEffect(() => {
    applyTheme(theme.value)
  })

  return {
    theme,
    themeOptions: THEME_OPTIONS,
    setTheme,
    toggleTheme,
    isDark: computed(() => theme.value === 'dark'),
  }
}
