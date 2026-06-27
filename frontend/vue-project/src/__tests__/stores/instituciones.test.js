import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// Mock axios
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

import { useInstitucionesStore } from '../../stores/instituciones'

describe('Instituciones Store', () => {
    let store

    beforeEach(() => {
        setActivePinia(createPinia())
        store = useInstitucionesStore()
        mockGet.mockReset()
        mockPost.mockReset()
        mockPut.mockReset()
        mockDelete.mockReset()
    })

    describe('fetchInstituciones', () => {
        it('llena institucionesList con datos del API', async () => {
            const mockData = [
                { id: 1, nombre: 'IE Test 1' },
                { id: 2, nombre: 'IE Test 2' },
            ]
            mockGet.mockResolvedValue({ data: mockData })

            await store.fetchInstituciones(true)

            expect(store.institucionesList).toEqual(mockData)
            expect(store.loading).toBe(false)
            expect(mockGet).toHaveBeenCalledWith('/instituciones/')
        })

        it('usa cache si no ha pasado 2 min y no es force', async () => {
            // Pre-populate
            store.institucionesList = [{ id: 1 }]
            store.lastFetchList = Date.now()

            await store.fetchInstituciones(false)

            expect(mockGet).not.toHaveBeenCalled()
        })

        it('ignora cache con force=true', async () => {
            store.institucionesList = [{ id: 1 }]
            store.lastFetchList = Date.now()
            mockGet.mockResolvedValue({ data: [{ id: 2 }] })

            await store.fetchInstituciones(true)

            expect(mockGet).toHaveBeenCalled()
            expect(store.institucionesList).toEqual([{ id: 2 }])
        })
    })

    describe('fetchInstitucion', () => {
        it('carga una institución por ID', async () => {
            const mockInst = { id: 5, nombre: 'IE Detalle' }
            mockGet.mockResolvedValue({ data: mockInst })

            await store.fetchInstitucion(5)

            expect(store.currentInstitucion).toEqual(mockInst)
            expect(mockGet).toHaveBeenCalledWith('/instituciones/5')
        })
    })

    describe('createInstitucion', () => {
        it('envía POST y agrega a la lista', async () => {
            const newInst = { id: 10, nombre: 'IE Nueva' }
            mockPost.mockResolvedValue({ data: newInst })

            const result = await store.createInstitucion({ nombre: 'IE Nueva' })

            expect(result).toEqual(newInst)
            expect(store.institucionesList[0]).toEqual(newInst)
            expect(mockPost).toHaveBeenCalledWith('/instituciones/', { nombre: 'IE Nueva' })
        })
    })

    describe('updateInstitucion', () => {
        it('envía PUT y actualiza en la lista', async () => {
            store.institucionesList = [{ id: 1, nombre: 'Vieja' }]
            const updated = { id: 1, nombre: 'Actualizada' }
            mockPut.mockResolvedValue({ data: updated })

            await store.updateInstitucion(1, { nombre: 'Actualizada' })

            expect(store.institucionesList[0].nombre).toBe('Actualizada')
        })
    })

    describe('deleteInstitucion', () => {
        it('envía DELETE y elimina de la lista', async () => {
            store.institucionesList = [{ id: 1 }, { id: 2 }]
            mockDelete.mockResolvedValue({})

            await store.deleteInstitucion(1)

            expect(store.institucionesList).toEqual([{ id: 2 }])
        })
    })
})
