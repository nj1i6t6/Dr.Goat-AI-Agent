import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import PredictionView from '../views/PredictionView.vue'
import { createPinia, setActivePinia } from 'pinia'
import { useSettingsStore } from '../stores/settings'

// Mock API
vi.mock('../api', () => ({
  default: {
    getAllSheep: vi.fn(),
    getSheepPrediction: vi.fn(),
    getPredictionChartData: vi.fn()
  }
}))

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn(),
    success: vi.fn()
  }
}))

// Mock ECharts
vi.mock('echarts', () => ({
  init: vi.fn(() => ({
    setOption: vi.fn(),
    resize: vi.fn()
  }))
}))

// Mock markdown-it
vi.mock('markdown-it', () => ({
  default: vi.fn(() => ({
    render: vi.fn((text) => `<p>${text}</p>`)
  }))
}))

describe('PredictionView', () => {
  let wrapper
  let settingsStore
  let mockApi

  const createWrapper = () => {
    return mount(PredictionView, {
      global: {
        stubs: {
          'el-card': { template: '<div><slot name="header"></slot><slot></slot></div>' },
          'el-form-item': { template: '<div><slot></slot></div>' },
          'el-autocomplete': { template: '<input />' },
          'el-select': { template: '<select><slot></slot></select>' },
          'el-option': { template: '<option></option>' },
          'el-button': { template: '<button><slot></slot></button>' },
          'el-alert': { template: '<div><slot></slot></div>' },
          'el-row': { template: '<div><slot></slot></div>' },
          'el-col': { template: '<div><slot></slot></div>' },
          'el-icon': { template: '<i><slot></slot></i>' }
        }
      }
    })
  }

  beforeEach(async () => {
    setActivePinia(createPinia())
    settingsStore = useSettingsStore()
    
    // 動態導入 API 模組來獲取 mock
    const apiModule = await import('../api')
    mockApi = apiModule.default
    
    // 重置 mocks
    vi.clearAllMocks()
    
    // 設置預設的 mock 回應
    mockApi.getAllSheep.mockResolvedValue([
      { EarNum: 'SH001', Breed: '努比亞', Sex: '母', BirthDate: '2023-01-01' },
      { EarNum: 'SH002', Breed: '波爾', Sex: '公', BirthDate: '2023-02-01' }
    ])
    
    mockApi.getSheepPrediction.mockResolvedValue({
      success: true,
      ear_tag: 'SH001',
      target_days: 30,
      predicted_weight: 25.5,
      average_daily_gain: 0.12,
      historical_data_count: 5,
      data_quality_report: {
        status: 'Good',
        message: '數據品質良好'
      },
      ai_analysis: '# 生長潛力解讀\n這隻羊的生長表現良好。'
    })
    
    mockApi.getPredictionChartData.mockResolvedValue({
      historical_points: [
        { x: 100, y: 20.0, date: '2024-01-01', label: '2024-01-01 (20.0kg)' }
      ],
      trend_line: [
        { x: 100, y: 20.0 },
        { x: 130, y: 22.5 }
      ],
      prediction_point: {
        x: 160, y: 25.5, date: '2024-02-15', label: '預測 (25.5kg)'
      }
    })
  })

  describe('組件初始化', () => {
    it('應該正確渲染頁面標題', () => {
      wrapper = createWrapper()
      
      expect(wrapper.find('.page-title').text()).toContain('羊隻生長預測')
    })

    it('應該載入羊隻清單', async () => {
      wrapper = createWrapper()
      
      // 等待組件掛載完成
      await wrapper.vm.$nextTick()
      
      expect(mockApi.getAllSheep).toHaveBeenCalled()
      expect(wrapper.vm.sheepOptions).toHaveLength(2)
    })

    it('應該顯示 API Key 警告當沒有設定時', () => {
      settingsStore.apiKey = ''
      wrapper = createWrapper()
      
      expect(wrapper.find('el-alert').exists()).toBe(true)
    })
  })

  describe('羊隻選擇', () => {
    beforeEach(() => {
      settingsStore.setApiKey('test-api-key')
      wrapper = createWrapper()
    })

    it('應該支持耳號搜尋', () => {
      const query = 'SH001'
      const callback = vi.fn()
      
      wrapper.vm.querySearch(query, callback)
      
      expect(callback).toHaveBeenCalledWith([
        { value: 'SH001', breed: '努比亞', sex: '母', birth_date: '2023-01-01' }
      ])
    })

    it('應該處理羊隻選擇', () => {
      const item = { value: 'SH001' }
      
      wrapper.vm.handleSelect(item)
      
      expect(wrapper.vm.selectedEarTag).toBe('SH001')
    })

    it('應該清除選擇', () => {
      wrapper.vm.selectedEarTag = 'SH001'
      wrapper.vm.predictionResult = { some: 'data' }
      
      wrapper.vm.clearSelection()
      
      expect(wrapper.vm.selectedEarTag).toBe('')
      expect(wrapper.vm.predictionResult).toBeNull()
    })
  })

  describe('預測功能', () => {
    beforeEach(() => {
      settingsStore.setApiKey('test-api-key')
      wrapper = createWrapper()
      wrapper.vm.selectedEarTag = 'SH001'
    })

    it('應該成功執行預測', async () => {
      await wrapper.vm.startPrediction()
      
      expect(mockApi.getSheepPrediction).toHaveBeenCalledWith(
        'SH001',
        30,
        'test-api-key'
      )
      expect(wrapper.vm.predictionResult).toBeTruthy()
      expect(wrapper.vm.loading).toBe(false)
    })

    it('應該處理預測錯誤', async () => {
      mockApi.getSheepPrediction.mockRejectedValue(new Error('預測失敗'))
      
      await wrapper.vm.startPrediction()
      
      expect(wrapper.vm.loading).toBe(false)
      expect(wrapper.vm.predictionResult).toBeNull()
    })

    it('應該驗證必要欄位', async () => {
      wrapper.vm.selectedEarTag = ''
      
      await wrapper.vm.startPrediction()
      
      expect(mockApi.getSheepPrediction).not.toHaveBeenCalled()
    })

    it('應該檢查 API Key', async () => {
      settingsStore.clearApiKey()
      
      await wrapper.vm.startPrediction()
      
      expect(mockApi.getSheepPrediction).not.toHaveBeenCalled()
    })
  })

  describe('數據品質狀態', () => {
    beforeEach(() => {
      wrapper = createWrapper()
    })

    it('應該正確設定良好狀態樣式', () => {
      const result = wrapper.vm.getQualityStatusClass('Good')
      expect(result).toBe('status-good')
    })

    it('應該正確設定警告狀態樣式', () => {
      const result = wrapper.vm.getQualityStatusClass('Warning')
      expect(result).toBe('status-warning')
    })

    it('應該正確設定錯誤狀態樣式', () => {
      const result = wrapper.vm.getQualityStatusClass('Error')
      expect(result).toBe('status-error')
    })

    it('應該處理未知狀態', () => {
      const result = wrapper.vm.getQualityStatusClass('Unknown')
      expect(result).toBe('')
    })
  })

  describe('AI 分析顯示', () => {
    beforeEach(() => {
      wrapper = createWrapper()
    })

    it('應該將 Markdown 轉換為 HTML', () => {
      wrapper.vm.predictionResult = {
        ai_analysis: '# 測試標題\n這是內容'
      }
      
      expect(wrapper.vm.aiAnalysisHtml).toContain('<p>')
    })

    it('應該處理空的 AI 分析', () => {
      wrapper.vm.predictionResult = null
      
      expect(wrapper.vm.aiAnalysisHtml).toBe('')
    })
  })

  describe('圖表渲染', () => {
    beforeEach(() => {
      settingsStore.setApiKey('test-api-key')
      wrapper = createWrapper()
      wrapper.vm.selectedEarTag = 'SH001'
      wrapper.vm.predictionResult = { some: 'data' }
    })

    it('應該在有數據時渲染圖表', async () => {
      await wrapper.vm.renderChart()
      
      expect(mockApi.getPredictionChartData).toHaveBeenCalledWith('SH001', 30)
    })

    it('應該處理圖表渲染錯誤', async () => {
      mockApi.getPredictionChartData.mockRejectedValue(new Error('圖表錯誤'))
      
      await wrapper.vm.renderChart()
      
      // 不應該拋出錯誤
      expect(true).toBe(true)
    })
  })
})
