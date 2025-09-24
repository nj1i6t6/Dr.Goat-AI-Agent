import { vi, describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
global.localStorage = localStorageMock

vi.mock('../router', () => ({
  default: {
    push: vi.fn()
  }
}))

// Mock errorHandler 避免循環依賴
vi.mock('../utils/errorHandler', () => ({
  handleApiError: vi.fn()
}))

vi.mock('../api', () => ({
  default: {
    register: vi.fn(),
    login: vi.fn(),
    logout: vi.fn()
  }
}))

import { useAuthStore } from './auth'
import router from '../router'
import api from '../api'

describe('auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorageMock.getItem.mockReturnValue(null)
  })

  describe('初始狀態', () => {
    it('應該有正確的初始狀態', () => {
      const store = useAuthStore()
      
      expect(store.user).toBe(null)
      expect(store.isAuthenticated).toBe(false)
      expect(store.username).toBe('訪客')
    })
  })

  describe('Actions', () => {
    it('應該成功登入用戶', async () => {
      const loginData = { email: 'test@example.com', password: 'password123' }
      const mockUser = { id: 1, username: 'testuser', email: 'test@example.com' }
      
      api.login.mockResolvedValue({ success: true, user: mockUser })
      
      const store = useAuthStore()
      await store.login(loginData)
      
      expect(store.user).toEqual(mockUser)
      expect(store.isAuthenticated).toBe(true)
    })
  })
})
