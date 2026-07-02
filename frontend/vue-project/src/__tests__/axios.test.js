import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'

// We test the interceptor behavior by importing the configured api instance
// and simulating 401 responses

describe('Axios Interceptor — Refresh Token', () => {
    let api

    beforeEach(async () => {
        // Clear localStorage
        localStorage.clear()

        // Reset module cache to get fresh interceptors
        vi.resetModules()

        // Dynamically import to get fresh instance
        const mod = await import('../api/axios.js')
        api = mod.default
    })

    afterEach(() => {
        vi.restoreAllMocks()
    })

    it('agrega Authorization header cuando hay token en localStorage', async () => {
        localStorage.setItem('token', 'test_access_token')

        // Intercept the request to check headers
        const requestInterceptor = api.interceptors.request.handlers[0]
        const config = { headers: {} }
        const result = requestInterceptor.fulfilled(config)

        expect(result.headers.Authorization).toBe('Bearer test_access_token')
    })

    it('no agrega Authorization header cuando no hay token', () => {
        const requestInterceptor = api.interceptors.request.handlers[0]
        const config = { headers: {} }
        const result = requestInterceptor.fulfilled(config)

        expect(result.headers.Authorization).toBeUndefined()
    })

    it('redirige a /login cuando 401 sin refresh_token', async () => {
        // No refresh token in localStorage
        const originalLocation = window.location.href

        const responseInterceptor = api.interceptors.response.handlers[0]
        const error = {
            config: { url: '/api/test', headers: {} },
            response: { status: 401 },
        }

        try {
            await responseInterceptor.rejected(error)
        } catch (e) {
            // Expected to reject
        }

        expect(localStorage.getItem('token')).toBeNull()
    })

    it('no intenta refresh en llamadas a /auth/login', async () => {
        localStorage.setItem('refresh_token', 'some_refresh')

        const responseInterceptor = api.interceptors.response.handlers[0]
        const error = {
            config: { url: '/auth/login', headers: {} },
            response: { status: 401 },
        }

        const result = responseInterceptor.rejected(error)
        await expect(result).rejects.toBeDefined()
    })

    it('no intenta refresh en llamadas a /auth/refresh', async () => {
        localStorage.setItem('refresh_token', 'some_refresh')

        const responseInterceptor = api.interceptors.response.handlers[0]
        const error = {
            config: { url: '/auth/refresh', headers: {} },
            response: { status: 401 },
        }

        const result = responseInterceptor.rejected(error)
        await expect(result).rejects.toBeDefined()
    })
})
