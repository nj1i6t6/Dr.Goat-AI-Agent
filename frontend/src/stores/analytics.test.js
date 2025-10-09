import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

const apiMock = vi.hoisted(() => ({
  listCostEntries: vi.fn(),
  listRevenueEntries: vi.fn(),
  createCostEntry: vi.fn(),
  updateCostEntry: vi.fn(),
  deleteCostEntry: vi.fn(),
  createRevenueEntry: vi.fn(),
  updateRevenueEntry: vi.fn(),
  deleteRevenueEntry: vi.fn(),
  runCohortAnalysis: vi.fn(),
  runCostBenefit: vi.fn(),
  generateAnalyticsReport: vi.fn(),
}))

vi.mock('../api', () => ({
  default: apiMock,
}))

import { useAnalyticsStore } from './analytics'

describe('analytics store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    apiMock.listCostEntries.mockResolvedValue({ items: [] })
    apiMock.listRevenueEntries.mockResolvedValue({ items: [] })
    apiMock.runCohortAnalysis.mockResolvedValue({ metrics: [], items: [] })
    apiMock.runCostBenefit.mockResolvedValue({ summary: {}, items: [], metrics: [] })
    apiMock.generateAnalyticsReport.mockResolvedValue({ report_html: '<p>ok</p>', report_markdown: 'ok' })
  })

  it('loads cost entries and updates state', async () => {
    apiMock.listCostEntries.mockResolvedValueOnce({ total: 1, items: [{ id: 1, category: 'feed' }] })
    const store = useAnalyticsStore()
    await store.loadCostEntries()
    expect(store.costEntries).toHaveLength(1)
    expect(apiMock.listCostEntries).toHaveBeenCalledTimes(1)
  })

  it('throttles repeated cohort calls', async () => {
    const store = useAnalyticsStore()
    apiMock.runCohortAnalysis.mockResolvedValue({ metrics: ['sheep_count'], items: [] })
    const payload = { cohort_by: ['breed'] }
    await store.fetchCohortAnalysis(payload)
    await store.fetchCohortAnalysis(payload)
    expect(apiMock.runCohortAnalysis).toHaveBeenCalledTimes(1)
  })

  it('stores report output', async () => {
    const store = useAnalyticsStore()
    await store.generateReport({ api_key: 'key' })
    expect(store.reportState.html).toContain('<p>ok</p>')
    expect(apiMock.generateAnalyticsReport).toHaveBeenCalledWith({ api_key: 'key' }, expect.any(Function))
  })
})
