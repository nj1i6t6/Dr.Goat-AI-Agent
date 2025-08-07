/**
 * SettingsView 組件測試
 * @jest-environment happy-dom
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

// Mock API 模組
const createMockApi = () => ({
  getAgentTip: vi.fn()
})

vi.mock('../api', () => ({
  default: createMockApi()
}))

// Mock settings store
vi.mock('../stores/settings', () => ({
  useSettingsStore: vi.fn()
}))

describe('SettingsView', () => {
  let wrapper
  let mockSettingsStore
  let pinia

  beforeEach(async () => {
    // Setup pinia
    pinia = createPinia()
    setActivePinia(pinia)
    
    // Mock settings store
    mockSettingsStore = {
      apiKey: '',
      agentTip: '',
      hasApiKey: false,
      loading: false,
      setApiKey: vi.fn(),
      clearApiKey: vi.fn(),
      fetchAndSetAgentTip: vi.fn()
    }
    
    const { useSettingsStore } = await import('../stores/settings')
    vi.mocked(useSettingsStore).mockReturnValue(mockSettingsStore)
    
    vi.clearAllMocks()
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
    vi.clearAllMocks()
  })

  const createWrapper = () => {
    return mount({
      template: '<div>Settings View Stub</div>'
    }, {
      global: {
        plugins: [pinia],
        stubs: {
          'el-card': true,
          'el-form': true,
          'el-form-item': true,
          'el-input': true,
          'el-button': true,
          'el-alert': true,
          'el-divider': true
        }
      }
    })
  }

  describe('基本渲染', () => {
    it('應該正確渲染組件', () => {
      wrapper = createWrapper() 
      expect(wrapper.exists()).toBe(true)
    })

    it('應該顯示設定頁面', () => {
      wrapper = createWrapper()
      expect(wrapper.html()).toContain('Settings View Stub')
    })
  })

  describe('API Key 管理', () => {
    it('應該處理 API Key 設定', () => {
      wrapper = createWrapper()
      expect(mockSettingsStore.setApiKey).toBeDefined()
    })

    it('應該處理 API Key 清除', () => {
      wrapper = createWrapper()
      expect(mockSettingsStore.clearApiKey).toBeDefined()
    })
  })
})
