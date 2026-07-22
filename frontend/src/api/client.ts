import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') {
      error.message = detail
    } else if (Array.isArray(detail)) {
      error.message = detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join('; ')
    }
    return Promise.reject(error)
  },
)

export default api
