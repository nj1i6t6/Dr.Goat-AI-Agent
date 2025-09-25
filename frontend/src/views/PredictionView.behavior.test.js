import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import PredictionView from './PredictionView.vue'

vi.mock('../stores/settings', () => ({
  useSettingsStore: () => ({ apiKey: 'k', hasApiKey: true, setApiKey: vi.fn() })
}))

const mockStartPrediction = vi.fn(async () => {})
vi.mock('../stores/prediction', () => ({
  usePredictionStore: () => ({
    isLoading: false,
    result: null,
    chartData: null,
    selectedEarTag: '',
    targetDays: 30,
    setSelectedEarTag: vi.fn(),
    setTargetDays: vi.fn(),
    startPrediction: mockStartPrediction,
    clear: vi.fn()
  })
}))

vi.mock('../api', () => ({
  default: {
    getAllSheep: async () => [{ EarNum: 'E001', Breed: 'AL', Sex: '公' }],
    getPredictionChartData: async () => ({ historical_points: [], trend_line: [], prediction_point: null })
  }
}))

describe('PredictionView interactions', () => {
  it('selects 7/14/30 days and triggers prediction', async () => {
    const wrapper = mount(PredictionView, {
      global: {
        stubs: {
          'el-button': {
            template: '<button class="el-button" @click="$emit(\'click\')"><slot /></button>',
            emits: ['click']
          }
        }
      }
    })

  // script setup uses refs; set via vm directly
  wrapper.vm.selectedEarTag = 'E001'
  await wrapper.vm.$nextTick()

  // change targetDays via vm property
  wrapper.vm.targetDays = 7
  await wrapper.vm.$nextTick()
  wrapper.vm.targetDays = 14
  await wrapper.vm.$nextTick()
  wrapper.vm.targetDays = 30
  await wrapper.vm.$nextTick()

    // click start prediction
    await wrapper.vm.startPrediction()
    expect(mockStartPrediction).toHaveBeenCalled()
  })
})
