import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// Mock vue-router
vi.mock('vue-router', () => ({
    useRouter: () => ({ push: vi.fn() }),
    useRoute: () => ({ params: {}, query: {} }),
}))

// Mock the axios module
const mockGet = vi.fn()
const mockPost = vi.fn()
vi.mock('../api/axios', () => ({
    default: {
        get: (...args) => mockGet(...args),
        post: (...args) => mockPost(...args),
    },
}))

import { useAuthStore } from '../stores/auth'

describe('Auth Store', () => {
    let store

    beforeEach(() => {
        setActivePinia(createPinia())
        store = useAuthStore()
        localStorage.clear()
        mockGet.mockReset()
        mockPost.mockReset()
    })

    describe('login', () => {
        it('guarda access_token y refresh_token en localStorage', async () => {
            mockPost.mockResolvedValue({
                data: { access_token: 'acc123', refresh_token: 'ref456' },
            })
            mockGet.mockResolvedValue({
                data: { id: 1, nombre: 'Test User', rol: { nombre: 'admin' } },
            })

            await store.login('test@test.com', 'password123')

            expect(localStorage.getItem('token')).toBe('acc123')
            expect(localStorage.getItem('refresh_token')).toBe('ref456')
        })

        it('hace fetchUser después de login exitoso', async () => {
            const userData = { id: 1, nombre: 'Test User', rol: { nombre: 'admin' } }
            mockPost.mockResolvedValue({
                data: { access_token: 'acc123', refresh_token: 'ref456' },
            })
            mockGet.mockResolvedValue({ data: userData })

            await store.login('test@test.com', 'password123')

            expect(store.user).toEqual(userData)
            expect(mockGet).toHaveBeenCalledWith('/usuarios/me')
        })

        it('lanza error si las credenciales son inválidas', async () => {
            mockPost.mockRejectedValue({
                response: { status: 401, data: { detail: 'Invalid credentials' } },
            })

            await expect(store.login('bad@test.com', 'wrong')).rejects.toBeDefined()
            // Token should not be set on failure (no localStorage item set)
            expect(localStorage.getItem('token')).toBeNull()
        })
    })

    describe('logout', () => {
        it('limpia token, refresh_token, user y localStorage', () => {
            // Simular sesión activa
            store.token = 'abc'
            store.user = { id: 1 }
            localStorage.setItem('token', 'abc')
            localStorage.setItem('refresh_token', 'ref')

            store.logout()

            expect(store.token).toBeNull()
            expect(store.user).toBeNull()
            expect(localStorage.getItem('token')).toBeNull()
            expect(localStorage.getItem('refresh_token')).toBeNull()
        })
    })

    describe('isAuthenticated', () => {
        it('retorna true cuando hay token', () => {
            store.token = 'some_token'
            expect(store.isAuthenticated).toBe(true)
        })

        it('retorna false cuando no hay token', () => {
            store.token = null
            expect(store.isAuthenticated).toBe(false)
        })
    })

    describe('fetchUser', () => {
        it('no hace nada si no hay token', async () => {
            store.token = null
            await store.fetchUser()
            expect(mockGet).not.toHaveBeenCalled()
        })

        it('carga el usuario si hay token', async () => {
            store.token = 'valid_token'
            const userData = { id: 1, nombre: 'User' }
            mockGet.mockResolvedValue({ data: userData })

            await store.fetchUser()

            expect(store.user).toEqual(userData)
        })
    })
})
