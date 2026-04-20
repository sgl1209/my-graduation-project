// 封装axios
import axios, { type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const service = axios.create({
  baseURL: 'http://8.138.208.57:8000/api', // 后端接口的基础URL
  // baseURL: 'http://localhost:8000/api', // 后端接口的基础URL
  timeout: 500000 // 请求超时时间
})

// 使用拦截器
service.interceptors.request.use(
  config => {
    // 在发送请求之前可以进行一些处理，例如添加认证信息
    // config.headers['Authorization'] = 'Bearer ' + token
    return config
  }
)
service.interceptors.response.use(
  (response: AxiosResponse) => {
    // 对响应数据进行处理，例如统一处理错误
    if (response.data.code !== 200) {
      // 处理错误
      ElMessage.error(response.data.msg || '请求错误')
      return Promise.reject(new Error(response.data.msg || '请求错误'))
    }

    return response.data
  }
)

interface RequestData {
  [key: string]: any
}

const request = <T = any>(method: string, url: string, data?: RequestData, config?: any): Promise<T> => {
  // axios 的类型无法感知拦截器对返回值的“解包”，这里显式把返回类型收敛为业务数据 T
  return service.request<any, T>({
    method,
    url,
    data,
    ...config
  })
}
export default request