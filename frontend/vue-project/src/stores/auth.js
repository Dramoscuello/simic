import { defineStore } from 'pinia';
import api from '../api/axios';
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';

export const useAuthStore = defineStore('auth', () => {
    const user = ref(null);
    const token = ref(localStorage.getItem('token') || null);
    const isAuthenticated = computed(() => !!token.value);
    const router = useRouter();

    async function fetchUser() {
        if (!token.value) return;
        try {
            // Configurar header si no está configurado globalmente (axios interceptor usualmente lo hace, 
            // pero aseguremos que el token está actualizado)
            // Asumo que hay interceptor o api.defaults.headers.common['Authorization']
            // api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`;

            const res = await api.get('/usuarios/me');
            user.value = res.data;
        } catch (e) {
            console.error("Error fetching user", e);
            logout();
        }
    }

    async function login(username, password) {
        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            const response = await api.post('/auth/login', formData, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            });

            token.value = response.data.access_token;
            localStorage.setItem('token', token.value);
            localStorage.setItem('refresh_token', response.data.refresh_token);

            await fetchUser();

            return true;
        } catch (error) {
            console.error('Login failed:', error);
            throw error;
        }
    }

    // Attempt to restore session
    if (token.value) {
        fetchUser();
    }

    function logout() {
        token.value = null;
        user.value = null;
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        router.push('/login');
    }

    return { user, token, isAuthenticated, login, logout, fetchUser };
});
