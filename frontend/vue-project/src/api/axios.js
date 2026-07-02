import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Interceptor para agregar token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// ─── Refresh Token Logic ───
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
    failedQueue.forEach(prom => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
};

// Interceptor para manejar errores 401 (token expirado) con refresh automático
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // Solo intentar refresh si es 401 y NO es el propio request de refresh/login
        if (
            error.response &&
            error.response.status === 401 &&
            !originalRequest._retry &&
            !originalRequest.url.includes('/auth/refresh') &&
            !originalRequest.url.includes('/auth/login')
        ) {
            const refreshToken = localStorage.getItem('refresh_token');

            if (!refreshToken) {
                // No hay refresh token → logout directo
                localStorage.removeItem('token');
                localStorage.removeItem('refresh_token');
                window.location.href = '/login';
                return Promise.reject(error);
            }

            if (isRefreshing) {
                // Ya hay un refresh en curso → encolar este request
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject });
                }).then(token => {
                    originalRequest.headers.Authorization = `Bearer ${token}`;
                    return api(originalRequest);
                }).catch(err => {
                    return Promise.reject(err);
                });
            }

            originalRequest._retry = true;
            isRefreshing = true;

            try {
                const res = await axios.post(
                    `${api.defaults.baseURL}/auth/refresh`,
                    { refresh_token: refreshToken },
                    { headers: { 'Content-Type': 'application/json' } }
                );

                const newAccessToken = res.data.access_token;
                localStorage.setItem('token', newAccessToken);

                // Actualizar header y procesar cola
                api.defaults.headers.common['Authorization'] = `Bearer ${newAccessToken}`;
                processQueue(null, newAccessToken);

                // Reintentar el request original
                originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
                return api(originalRequest);
            } catch (refreshError) {
                // Refresh falló → sesión expirada completamente
                processQueue(refreshError, null);
                localStorage.removeItem('token');
                localStorage.removeItem('refresh_token');
                window.location.href = '/login';
                return Promise.reject(refreshError);
            } finally {
                isRefreshing = false;
            }
        }

        return Promise.reject(error);
    }
);

export default api;
