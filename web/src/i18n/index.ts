import { createI18n } from 'vue-i18n'
import enUS from './messages/en-US'
import zhCN from './messages/zh-CN'

export type Locale = 'zh-CN' | 'en-US'

export const DEFAULT_LOCALE: Locale = 'en-US'
export const LOCALE_STORAGE_KEY = 'bem-nexus-locale'

export const localeOptions: Array<{ value: Locale; label: string }> = [
  { value: 'zh-CN', label: '中文' },
  { value: 'en-US', label: 'EN' },
]

const messages = {
  'zh-CN': zhCN,
  'en-US': enUS,
}

function isLocale(value: string | null): value is Locale {
  return value === 'zh-CN' || value === 'en-US'
}

function getInitialLocale(): Locale {
  if (typeof localStorage === 'undefined') return DEFAULT_LOCALE
  const saved = localStorage.getItem(LOCALE_STORAGE_KEY)
  return isLocale(saved) ? saved : DEFAULT_LOCALE
}

function applyDocumentLanguage(locale: Locale) {
  if (typeof document === 'undefined') return
  document.documentElement.lang = locale
}

export const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: getInitialLocale(),
  fallbackLocale: 'en-US',
  messages,
})

export function setAppLocale(locale: Locale) {
  i18n.global.locale.value = locale
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(LOCALE_STORAGE_KEY, locale)
  }
  applyDocumentLanguage(locale)
}

export function initializeLocale() {
  setAppLocale(i18n.global.locale.value as Locale)
}
