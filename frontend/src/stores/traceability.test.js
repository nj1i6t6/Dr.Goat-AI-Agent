import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTraceabilityStore } from '@/stores/traceability'

vi.mock('@/api', () => ({
  default: {
    getTraceabilityBatches: vi.fn(),
    createTraceabilityBatch: vi.fn(),
    updateTraceabilityBatch: vi.fn(),
    replaceBatchSheepLinks: vi.fn(),
  }
}))

import api from '@/api'

describe('traceability store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('should have correct initial state', () => {
    const store = useTraceabilityStore()
    expect(store.batches).toEqual([])
    expect(store.isLoading).toBe(false)
    expect(store.selectedBatch).toBeNull()
  })

  it('fetchBatches should populate list', async () => {
    const store = useTraceabilityStore()
    const mockData = [{ id: 1, batch_number: 'B001', product_name: '羊乳' }]
    api.getTraceabilityBatches.mockResolvedValue(mockData)

    await store.fetchBatches(true)

    expect(store.isLoading).toBe(false)
    expect(api.getTraceabilityBatches).toHaveBeenCalledWith(true)
    expect(store.batches).toEqual(mockData)
  })

  it('createBatch should prepend newly created batch', async () => {
    const store = useTraceabilityStore()
    const created = { id: 5, batch_number: 'B005', product_name: '乳酪' }
    api.createTraceabilityBatch.mockResolvedValue(created)

    await store.createBatch({ batch_number: 'B005', product_name: '乳酪' })

    expect(api.createTraceabilityBatch).toHaveBeenCalledTimes(1)
    expect(store.batches[0]).toEqual(created)
  })

  it('replaceSheepLinks should update selected batch', async () => {
    const store = useTraceabilityStore()
    const existing = { id: 2, batch_number: 'B002', sheep_links: [] }
    store.batches = [existing]
    store.selectedBatch = existing

    const updated = { id: 2, batch_number: 'B002', sheep_links: [{ sheep_id: 1 }] }
    api.replaceBatchSheepLinks.mockResolvedValue(updated)

    await store.replaceSheepLinks(2, [{ sheep_id: 1 }])

    expect(api.replaceBatchSheepLinks).toHaveBeenCalledWith(2, [{ sheep_id: 1 }])
    expect(store.selectedBatch.sheep_links).toHaveLength(1)
    expect(store.batches[0].sheep_links).toHaveLength(1)
  })
})
