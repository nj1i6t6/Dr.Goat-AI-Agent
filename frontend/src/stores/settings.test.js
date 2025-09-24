import { vi, describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// Mock localStorage first
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
global.localStorage = localStorageMock

// Mock errorHandler 避免循環依賴
vi.mock('../utils/errorHandler', () => ({
  handleApiError: vi.fn()
}))

// Mock API
vi.mock('../api', () => ({
  default: {
    getAgentTip: vi.fn()
  }
}))

// Import after mocking
import { useSettingsStore } from './settings'
import api from '../api'

describe('settings Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorageMock.getItem.mockReturnValue('')
  })

  describe('初始狀態', () => {
    it('應該有正確的初始狀態', () => {
      localStorageMock.getItem.mockReturnValue('')
      const store = useSettingsStore()
      
      expect(store.apiKey).toBe('')
      expect(store.agentTip).toEqual({
        html: '',
        loading: false,
        loaded: false
      })
      expect(store.hasApiKey).toBe(false)
    })

    it('應該從 localStorage 載入已儲存的 API Key', () => {
      const savedApiKey = 'saved-api-key-123'
      localStorageMock.getItem.mockReturnValue(savedApiKey)
      
      const store = useSettingsStore()
      
      expect(localStorageMock.getItem).toHaveBeenCalledWith('geminiApiKey')
      expect(store.apiKey).toBe(savedApiKey)
      expect(store.hasApiKey).toBe(true)
    })
  })

  describe('Actions', () => {
    describe('setApiKey', () => {
      it('應該設定並儲存 API Key', () => {
        const store = useSettingsStore()
        const testApiKey = 'test-api-key-123'

        store.setApiKey(testApiKey)

        expect(store.apiKey).toBe(testApiKey)
        expect(localStorageMock.setItem).toHaveBeenCalledWith('geminiApiKey', testApiKey)
      })

      it('應該處理空的 API Key', () => {
        const store = useSettingsStore()

        store.setApiKey('')

        expect(store.apiKey).toBe('')
        expect(localStorageMock.setItem).toHaveBeenCalledWith('geminiApiKey', '')
      })
    })

    describe('clearApiKey', () => {
      it('應該清除 API Key', () => {
        localStorageMock.getItem.mockReturnValue('existing-key')
        const store = useSettingsStore()
        
        expect(store.apiKey).toBe('existing-key')

        store.clearApiKey()

        expect(store.apiKey).toBe('')
        expect(localStorageMock.removeItem).toHaveBeenCalledWith('geminiApiKey')
      })
    })

    describe('fetchAndSetAgentTip', () => {
      it('應該成功獲取 Agent 提示', async () => {
        const mockTip = '<p>今日提示：注意山羊的營養平衡</p>'
        localStorageMock.getItem.mockReturnValue('valid-api-key')
        
        const store = useSettingsStore()
        api.getAgentTip.mockResolvedValue({ tip_html: mockTip })

        await store.fetchAndSetAgentTip()

        expect(store.agentTip.loading).toBe(false)
        expect(store.agentTip.html).toBe(mockTip)
        expect(store.agentTip.loaded).toBe(true)
        expect(api.getAgentTip).toHaveBeenCalledWith('valid-api-key')
      })

      it('應該處理獲取提示失敗', async () => {
        localStorageMock.getItem.mockReturnValue('invalid-key')
        
        const store = useSettingsStore()
        api.getAgentTip.mockRejectedValue({ error: 'API 錯誤' })

        await store.fetchAndSetAgentTip()

        expect(store.agentTip.loading).toBe(false)
        expect(store.agentTip.html).toContain('無法獲取提示: API 錯誤')
        expect(store.agentTip.loaded).toBe(true)
      })

      it('loading 狀態應該正確切換', async () => {
        localStorageMock.getItem.mockReturnValue('test-key')
        const store = useSettingsStore()

        let resolvePromise
        const mockPromise = new Promise(resolve => {
          resolvePromise = resolve
        })
        api.getAgentTip.mockReturnValue(mockPromise)

        const fetchPromise = store.fetchAndSetAgentTip()
        expect(store.agentTip.loading).toBe(true)

        resolvePromise({ tip_html: '測試提示' })
        await fetchPromise
        expect(store.agentTip.loading).toBe(false)
      })

      it('應該處理沒有 API Key 的情況', async () => {
        localStorageMock.getItem.mockReturnValue('')
        const store = useSettingsStore()

        await store.fetchAndSetAgentTip()

        expect(store.agentTip.html).toBe('請先在「系統設定」中設定有效的API金鑰以獲取提示。')
        expect(api.getAgentTip).not.toHaveBeenCalled()
      })

      it('應該避免重複獲取（已載入）', async () => {
        localStorageMock.getItem.mockReturnValue('test-key')
        
        const store = useSettingsStore()
        api.getAgentTip.mockResolvedValue({ tip_html: '初次提示' })

        // 第一次調用
        await store.fetchAndSetAgentTip()
        expect(api.getAgentTip).toHaveBeenCalledTimes(1)

        // 第二次調用應該跳過
        await store.fetchAndSetAgentTip()
        expect(api.getAgentTip).toHaveBeenCalledTimes(1) // 仍然是 1 次
      })

      it('應該避免重複獲取（載入中）', async () => {
        localStorageMock.getItem.mockReturnValue('test-key')
        
        const store = useSettingsStore()
        
        let resolveFirst
        api.getAgentTip.mockImplementation(() => new Promise(resolve => {
          resolveFirst = resolve
        }))

        // 同時發起兩個請求
        const promise1 = store.fetchAndSetAgentTip()
        const promise2 = store.fetchAndSetAgentTip()

        resolveFirst({ tip_html: '提示內容' })
        await Promise.all([promise1, promise2])

        expect(api.getAgentTip).toHaveBeenCalledTimes(1)
      })
    })
  })

  describe('Computed Properties', () => {
    it('hasApiKey 應該根據 apiKey 正確計算', () => {
      const store = useSettingsStore()
      
      // 初始狀態：無 API Key
      expect(store.hasApiKey).toBe(false)
      
      // 設置 API Key
      store.setApiKey('test-key')
      expect(store.hasApiKey).toBe(true)
      
      // 清除 API Key
      store.clearApiKey()
      expect(store.hasApiKey).toBe(false)
    })
  })

  describe('localStorage 整合', () => {
    it('應該在初始化時從 localStorage 載入 API Key', () => {
      localStorageMock.getItem.mockReturnValue('stored-key')
      
      const store = useSettingsStore()
      
      expect(localStorageMock.getItem).toHaveBeenCalledWith('geminiApiKey')
      expect(store.apiKey).toBe('stored-key')
    })

    it('應該處理 localStorage 不可用的情況', () => {
      const originalLocalStorage = global.localStorage
      global.localStorage = null
      
      expect(() => {
        const store = useSettingsStore()
      }).toThrow()

      global.localStorage = originalLocalStorage
    })

    it('應該處理 localStorage 拋出異常的情況', () => {
      localStorageMock.getItem.mockImplementation(() => {
        throw new Error('localStorage error')
      })
      
      expect(() => {
        const store = useSettingsStore()
      }).toThrow()
    })
  })

  describe('邊界條件處理', () => {
    it('應該處理網路錯誤', async () => {
      localStorageMock.getItem.mockReturnValue('test-key')
      const store = useSettingsStore()
      
      api.getAgentTip.mockRejectedValue({ message: 'Network Error' })

      await store.fetchAndSetAgentTip()

      expect(store.agentTip.html).toContain('無法獲取提示: Network Error')
      expect(store.agentTip.loaded).toBe(true)
    })

    it('應該處理未知錯誤', async () => {
      localStorageMock.getItem.mockReturnValue('test-key')
      const store = useSettingsStore()
      
      api.getAgentTip.mockRejectedValue({})

      await store.fetchAndSetAgentTip()

      expect(store.agentTip.html).toContain('無法獲取提示:')
      expect(store.agentTip.loaded).toBe(true)
    })

    it('應該處理非常長的 API Key', () => {
      const longApiKey = 'a'.repeat(1000)
      const store = useSettingsStore()

      store.setApiKey(longApiKey)

      expect(store.apiKey).toBe(longApiKey)
      expect(localStorageMock.setItem).toHaveBeenCalledWith('geminiApiKey', longApiKey)
    })

    it('應該處理特殊字符的 API Key', () => {
      const specialApiKey = 'test-key-123!@#$%^&*()_+{}|:"<>?[]\\;\',./'
      const store = useSettingsStore()

      store.setApiKey(specialApiKey)

      expect(store.apiKey).toBe(specialApiKey)
      expect(localStorageMock.setItem).toHaveBeenCalledWith('geminiApiKey', specialApiKey)
    })

    it('應該處理並發的 fetchAndSetAgentTip 請求', async () => {
      localStorageMock.getItem.mockReturnValue('test-key')
      const store = useSettingsStore()
      
      api.getAgentTip.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ tip_html: '並發測試提示' }), 50))
      )

      // 同時發送多個請求
      const promises = Array(3).fill().map(() => store.fetchAndSetAgentTip())
      await Promise.all(promises)

      expect(api.getAgentTip).toHaveBeenCalledTimes(1) // 只調用一次
      expect(store.agentTip.html).toBe('並發測試提示')
    })

    it('應該正確處理 null 和 undefined 的 API Key', () => {
      const store = useSettingsStore()

      store.setApiKey(null)
      expect(store.apiKey).toBe(null)
      expect(store.hasApiKey).toBe(false)

      store.setApiKey(undefined)
      expect(store.apiKey).toBe(undefined)
      expect(store.hasApiKey).toBe(false)
    })
  })

  describe('狀態重置', () => {
    it('應該能夠重置 agentTip 狀態', async () => {
      localStorageMock.getItem.mockReturnValue('test-key')
      const store = useSettingsStore()
      
      // 先獲取提示
      api.getAgentTip.mockResolvedValue({ tip_html: '初始提示' })
      await store.fetchAndSetAgentTip()
      
      expect(store.agentTip.loaded).toBe(true)
      expect(store.agentTip.html).toBe('初始提示')

      // 重置狀態
      store.agentTip.loaded = false
      store.agentTip.html = ''

      expect(store.agentTip.loaded).toBe(false)
      expect(store.agentTip.html).toBe('')
    })

    it('應該在 API Key 改變時能夠重新獲取提示', async () => {
      localStorageMock.getItem.mockReturnValue('old-key')
      const store = useSettingsStore()
      
      // 使用舊 key 獲取提示
      api.getAgentTip.mockResolvedValue({ tip_html: '舊提示' })
      await store.fetchAndSetAgentTip()
      expect(store.agentTip.html).toBe('舊提示')

      // 更改 API Key 並重置狀態
      store.setApiKey('new-key')
      store.agentTip.loaded = false

      // 使用新 key 獲取提示
      api.getAgentTip.mockResolvedValue({ tip_html: '新提示' })
      await store.fetchAndSetAgentTip()
      
      expect(store.agentTip.html).toBe('新提示')
      expect(api.getAgentTip).toHaveBeenLastCalledWith('new-key')
    })
  })
})
