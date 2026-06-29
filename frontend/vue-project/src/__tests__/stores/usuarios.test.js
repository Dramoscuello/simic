import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

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

import { useUsuariosStore } from '../../stores/usuarios'

describe('Usuarios Store', () => {
    let store

    beforeEach(() => {
        setActivePinia(createPinia())
        store = useUsuariosStore()
        mockGet.mockReset()
        mockPost.mockReset()
        mockPut.mockReset()
        mockDelete.mockReset()
    })

    describe('fetchUsuariosInstitucion', () => {
        it('carga admins cuando rol es admin', async () => {
            const admins = [{ id: 1, nombre: 'Admin 1' }]
            mockGet.mockResolvedValue({ data: admins })

            await store.fetchUsuariosInstitucion(10, 'admin')

            expect(store.adminsInstitucion).toEqual(admins)
            expect(mockGet).toHaveBeenCalledWith('/instituciones/10/usuarios', {
                params: { rol: 'admin' },
            })
        })

        it('carga estudiantes cuando rol es estudiante', async () => {
            const students = [{ id: 2, nombre: 'Estudiante 1' }]
            mockGet.mockResolvedValue({ data: students })

            await store.fetchUsuariosInstitucion(10, 'estudiante')

            expect(store.estudiantesInstitucion).toEqual(students)
        })
    })

    describe('createUser', () => {
        it('envía POST con el payload correcto', async () => {
            const newUser = { id: 5, nombre: 'Nuevo' }
            mockPost.mockResolvedValue({ data: newUser })

            const payload = { nombre: 'Nuevo', email: 'nuevo@test.com', password: 'Test1234' }
            const result = await store.createUser(payload)

            expect(result).toEqual(newUser)
            expect(mockPost).toHaveBeenCalledWith('/usuarios/', payload)
        })
    })

    describe('updateUser', () => {
        it('envía PUT y actualiza en listas locales', async () => {
            const updated = { id: 1, nombre: 'Editado' }
            store.adminsInstitucion = [{ id: 1, nombre: 'Original' }]
            mockPut.mockResolvedValue({ data: updated })

            await store.updateUser(1, { nombre: 'Editado' })

            expect(store.adminsInstitucion[0].nombre).toBe('Editado')
        })
    })

    describe('deleteUser', () => {
        it('elimina de todas las listas locales', async () => {
            store.usuarios = [{ id: 1 }, { id: 2 }]
            store.adminsInstitucion = [{ id: 1 }]
            store.estudiantesInstitucion = [{ id: 1 }, { id: 3 }]
            mockDelete.mockResolvedValue({})

            await store.deleteUser(1)

            expect(store.usuarios).toEqual([{ id: 2 }])
            expect(store.adminsInstitucion).toEqual([])
            expect(store.estudiantesInstitucion).toEqual([{ id: 3 }])
        })
    })

    describe('getUserById getter', () => {
        it('busca en todas las listas', () => {
            store.usuarios = []
            store.adminsInstitucion = [{ id: 5, nombre: 'Admin Found' }]
            store.estudiantesInstitucion = []

            const result = store.getUserById(5)
            expect(result).toEqual({ id: 5, nombre: 'Admin Found' })
        })

        it('retorna undefined si no existe', () => {
            store.usuarios = []
            store.adminsInstitucion = []
            store.estudiantesInstitucion = []

            expect(store.getUserById(999)).toBeUndefined()
        })
    })
})
