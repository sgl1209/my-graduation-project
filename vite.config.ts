import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  // ========== base 移到顶层（核心修正） ==========
  base: './', // 相对路径配置（App 打包必需）
  
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
      imports: ['vue', 'vue-router'],
      dts: 'src/auto-imports.d.ts'
    }),
    Components({
      resolvers: [
        ElementPlusResolver({
          //@ts-ignore 忽略 less 样式的 TS 提示
          importStyle: 'less'
        })
      ],
      dts: 'src/components.d.ts'
    })
  ],
  
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  
  build: {
    // 仅保留 chunk 大小警告配置（可选）
    chunkSizeWarningLimit: 1000
  }
})