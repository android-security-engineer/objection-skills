import DefaultTheme from 'vitepress/theme'
import type { EnhanceAppContext } from 'vitepress'
import './custom.css'

export default {
  extends: DefaultTheme,
  enhanceApp(ctx: EnhanceAppContext) {
    // 预留：可在此注册全局组件
  }
}
