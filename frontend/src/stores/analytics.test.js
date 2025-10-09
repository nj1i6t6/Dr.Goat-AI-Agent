/**
 * Analytics Store 測試
 * @jest-environment happy-dom
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAnalyticsStore } from './analytics'
import api from '../api'

vi.mock('../api', () => ({
  default: {
    getCostEntries: vi.fn(),
    createCostEntry: vi.fn(),
    updateCostEntry: vi.fn(),
    deleteCostEntry: vi.fn(),
    getRevenueEntries: vi.fn(),
    createRevenueEntry: vi.fn(),
    updateRevenueEntry: vi.fn(),
    deleteRevenueEntry: vi.fn(),
    requestCohortAnalysis: vi.fn(),
    requestCostBenefit: vi.fn(),
    requestBiAiReport: vi.fn(),
  }
}))

describe('Analytics Store', () => {
  let store

  beforeEach(() => {
    const pinia = createPinia()
    setActivePinia(pinia)
    store = useAnalyticsStore()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  it('應能載入成本資料', async () => {
    api.getCostEntries.mockResolvedValue([{ id: 1, category: '飼料', amount: 1000 }])
    const result = await store.fetchCostEntries()
    expect(api.getCostEntries).toHaveBeenCalledTimes(1)
    expect(result).toHaveLength(1)
    expect(store.costEntries[0].category).toBe('飼料')
  })

  it('應支援新增與刪除收益資料', async () => {
    api.createRevenueEntry.mockResolvedValue({ id: 9, category: '乳品', amount: 3200 })
    api.deleteRevenueEntry.mockResolvedValue({ success: true })
    await store.createRevenueEntry({ category: '乳品', amount: 3200, recorded_at: new Date() })
    expect(store.revenueEntries).toHaveLength(1)
    await store.deleteRevenueEntry(9)
    expect(store.revenueEntries).toHaveLength(0)
  })

  it('應對 Cohort 查詢結果進行快取', async () => {
    const response = {
      dimensions: ['breed'],
      metrics: ['total_cost'],
      rows: [{ dimensions: { breed: '撒能' }, metrics: { total_cost: 1000 } }],
    }
    api.requestCohortAnalysis.mockResolvedValue(response)
    await store.runCohortAnalysis({ force: true })
    expect(api.requestCohortAnalysis).toHaveBeenCalledTimes(1)

    await store.runCohortAnalysis()
    expect(api.requestCohortAnalysis).toHaveBeenCalledTimes(1)
    expect(store.cohortResult.rows[0].metrics.total_cost).toBe(1000)
  })

  it('應產生 AI 報告並保存', async () => {
    api.requestBiAiReport.mockResolvedValue({ report_markdown: '# 報告', report_html: '<h1>報告</h1>' })
    store.costBenefitResult = { kpis: { total_cost: 1000 } }
    await store.generateAiReport('fake-key', ['亮點'])
    expect(api.requestBiAiReport).toHaveBeenCalledWith(
      'fake-key',
      expect.objectContaining({
        highlights: ['亮點'],
        aggregates: expect.objectContaining({ total_cost: 1000 }),
        metrics: expect.arrayContaining(['total_cost', 'total_revenue']),
      })
    )
    expect(store.aiReport.report_markdown).toContain('# 報告')
  })
})
