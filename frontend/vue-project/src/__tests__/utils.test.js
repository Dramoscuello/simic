import { describe, it, expect } from 'vitest'

/**
 * Utility functions extracted for testing.
 * These exist inline in components but are pure functions.
 */

// From InstitucionDetalle.vue
function getInitials(name) {
    if (!name) return '?'
    const parts = name.split(' ')
    return parts.length >= 2
        ? (parts[0][0] + parts[1][0]).toUpperCase()
        : name.substring(0, 2).toUpperCase()
}

// Password validation (from createPasswordReqs computed)
function validatePassword(pwd) {
    return {
        length: pwd.length >= 8,
        hasLetters: /[A-Za-z]/.test(pwd),
        hasNumbers: /\d/.test(pwd),
    }
}

// Password match validation (from passwordRequirements computed)
function validatePasswordChange(newPwd, confirmPwd) {
    return {
        length: newPwd.length >= 8,
        chars: /^(?=.*[A-Za-z])(?=.*\d)/.test(newPwd),
        match: newPwd === confirmPwd && newPwd.length > 0,
    }
}

describe('getInitials', () => {
    it('retorna las iniciales de nombre y apellido', () => {
        expect(getInitials('Juan Pérez')).toBe('JP')
    })

    it('retorna las primeras 2 letras si es una sola palabra', () => {
        expect(getInitials('Admin')).toBe('AD')
    })

    it('retorna ? si el nombre es vacío', () => {
        expect(getInitials('')).toBe('?')
    })

    it('retorna ? si el nombre es null', () => {
        expect(getInitials(null)).toBe('?')
    })

    it('retorna ? si el nombre es undefined', () => {
        expect(getInitials(undefined)).toBe('?')
    })

    it('maneja nombres con múltiples palabras', () => {
        expect(getInitials('María del Carmen Rodríguez')).toBe('MD')
    })
})

describe('validatePassword (create)', () => {
    it('contraseña válida cumple todas las reglas', () => {
        const result = validatePassword('Test1234')
        expect(result.length).toBe(true)
        expect(result.hasLetters).toBe(true)
        expect(result.hasNumbers).toBe(true)
    })

    it('contraseña corta falla en length', () => {
        const result = validatePassword('Te1')
        expect(result.length).toBe(false)
        expect(result.hasLetters).toBe(true)
        expect(result.hasNumbers).toBe(true)
    })

    it('contraseña sin números falla en hasNumbers', () => {
        const result = validatePassword('TestTestTest')
        expect(result.length).toBe(true)
        expect(result.hasLetters).toBe(true)
        expect(result.hasNumbers).toBe(false)
    })

    it('contraseña sin letras falla en hasLetters', () => {
        const result = validatePassword('12345678')
        expect(result.length).toBe(true)
        expect(result.hasLetters).toBe(false)
        expect(result.hasNumbers).toBe(true)
    })

    it('contraseña vacía falla en todo', () => {
        const result = validatePassword('')
        expect(result.length).toBe(false)
        expect(result.hasLetters).toBe(false)
        expect(result.hasNumbers).toBe(false)
    })
})

describe('validatePasswordChange', () => {
    it('contraseñas que coinciden y cumplen reglas', () => {
        const result = validatePasswordChange('Password1', 'Password1')
        expect(result.length).toBe(true)
        expect(result.chars).toBe(true)
        expect(result.match).toBe(true)
    })

    it('contraseñas que no coinciden', () => {
        const result = validatePasswordChange('Password1', 'Password2')
        expect(result.match).toBe(false)
    })

    it('contraseña vacía no coincide', () => {
        const result = validatePasswordChange('', '')
        expect(result.match).toBe(false)
    })
})
