import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// Mock vue-router (needed by simulacros store which imports auth store)
vi.mock('vue-router', () => ({
    useRouter: () => ({ push: vi.fn() }),
    useRoute: () => ({ params: {}, query: {} }),
}))

const mockGet = vi.fn()
const mockPost = vi.fn()
const mockPut = vi.fn()
const mockDelete = vi.fn()
vi.mock('../../api/axios', () => ({
    default: {
        get: (...args) => mockGet(...args),
        post: (...args) => mockPost(...args),
        put: (...args) => mockPut(...args),
        delete: (...args) => mockDelete(...args),
    },
}))

import { useSimulacrosStore } from '../../stores/simulacros'

describe('Simulacros Store', () => {
    let store

    beforeEach(() => {
        setActivePinia(createPinia())
        store = useSimulacrosStore()
        mockGet.mockReset()
        mockPost.mockReset()
        mockPut.mockReset()
        mockDelete.mockReset()
    })

    describe('fetchSimulacros', () => {
        it('llena la lista de simulacros', async () => {
            const mockData = [
                { id: 1, nombre: 'Simulacro 1' },
                { id: 2, nombre: 'Simulacro 2' },
            ]
            mockGet.mockResolvedValue({ data: mockData })

            await store.fetchSimulacros({}, true)

            expect(store.simulacros.length).toBe(2)
            expect(store.loading).toBe(false)
        })
    })

    describe('fetchSimulacro', () => {
        it('carga un simulacro individual por ID', async () => {
            const mockSim = { id: 5, nombre: 'Detalle Sim' }
            mockGet.mockResolvedValue({ data: mockSim })

            const result = await store.fetchSimulacro(5)

            expect(result).toEqual(mockSim)
            expect(store.simulacros).toContainEqual(mockSim)
            expect(mockGet).toHaveBeenCalledWith('/simulacros/5')
        })
    })

    describe('createSimulacro', () => {
        it('envía POST y agrega a la lista', async () => {
            const newSim = { id: 10, nombre: 'Nuevo Sim' }
            mockPost.mockResolvedValue({ data: newSim })

            const result = await store.createSimulacro({ nombre: 'Nuevo Sim' })

            expect(result).toEqual(newSim)
            expect(mockPost).toHaveBeenCalledWith('/simulacros/', { nombre: 'Nuevo Sim' })
        })
    })

    describe('deleteSimulacro', () => {
        it('envía DELETE y elimina de la lista', async () => {
            store.simulacros = [{ id: 1 }, { id: 2 }]
            mockDelete.mockResolvedValue({})

            await store.deleteSimulacro(1)

            expect(store.simulacros).toEqual([{ id: 2 }])
        })
    })
})
