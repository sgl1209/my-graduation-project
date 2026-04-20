// 声明 .vue 文件模块，解决 TS 无法识别 .vue 组件的问题
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/ban-types
  const component: DefineComponent<{}, {}, any>
  export default component
}

// 声明 API 模块
declare module '@/api/index.js' {
  interface RequestData {
    [key: string]: any
  }
  const request: (method: string, url: string, data?: RequestData, config?: any) => Promise<any>
  export default request
}