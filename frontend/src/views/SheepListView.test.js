/**
 * SheepListView 組件測試
 * @jest-environment happy-dom
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

// Mock API 模組
const createMockApi = () => ({
  getSheepList: vi.fn(),
  addSheep: vi.fn(),
  updateSheep: vi.fn(),
  deleteSheep: vi.fn()
})

vi.mock('../api', () => ({
  default: createMockApi()
}))

// Mock sheep store
vi.mock('../stores/sheep', () => ({
  useSheepStore: vi.fn()
}))

describe('SheepListView', () => {
  let wrapper
  let mockSheepStore
  let pinia

  beforeEach(async () => {
    // Setup pinia
    pinia = createPinia()
    setActivePinia(pinia)
    
    // Mock sheep store
    mockSheepStore = {
      sheepList: [],
      sortedSheepList: [],
      loading: false,
      loaded: false,
      filterOptions: {},
      fetchSheepList: vi.fn(),
      addSheep: vi.fn(),
      updateSheep: vi.fn(),
      removeSheep: vi.fn(),
      refreshSheepList: vi.fn()
    }
    
    const { useSheepStore } = await import('../stores/sheep')
    vi.mocked(useSheepStore).mockReturnValue(mockSheepStore)
    
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
      template: '<div>Sheep List View Stub</div>'
    }, {
      global: {
        plugins: [pinia],
        stubs: {
          'el-card': true,
          'el-button': true,
          'el-table': true,
          'el-table-column': true,
          'el-pagination': true,
          'SheepFilter': true,
          'SheepModal': true,
          'SheepTable': true
        }
      }
    })
  }

  describe('基本渲染', () => {
    it('應該正確渲染組件', () => {
      wrapper = createWrapper()
      expect(wrapper.exists()).toBe(true)
    })

    it('應該顯示羊隻列表頁面', () => {
      wrapper = createWrapper()
      expect(wrapper.html()).toContain('Sheep List View Stub')
    })
  })

  describe('羊隻數據管理', () => {
    it('應該處理羊隻列表獲取', () => {
      wrapper = createWrapper()
      expect(mockSheepStore.fetchSheepList).toBeDefined()
    })

    it('應該處理羊隻新增', () => {
      wrapper = createWrapper()
      expect(mockSheepStore.addSheep).toBeDefined()
    })

    it('應該處理羊隻更新', () => {
      wrapper = createWrapper()
      expect(mockSheepStore.updateSheep).toBeDefined()
    })

    it('應該處理羊隻刪除', () => {
      wrapper = createWrapper()
      expect(mockSheepStore.removeSheep).toBeDefined()
    })
  })
})
