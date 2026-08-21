import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import { i18n, initializeLocale } from './i18n'

// Create Vue application instance
const app = createApp(App)

app.use(i18n)
initializeLocale()

// Mount application
app.mount('#app')
