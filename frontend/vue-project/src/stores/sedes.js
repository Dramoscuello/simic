import { defineStore } from 'pinia';
import api from '../api/axios';

export const useSedesStore = defineStore('sedes', {
    state: () => ({
        sedes: [],
        loading: false,
        error: null
    }),

    actions: {
        async fetchSedes(institucionId = null) {
            this.loading = true;
            try {
                const params = {};
                if (institucionId) params.institucion_id = institucionId;
                const response = await api.get('/sedes/', { params });
                this.sedes = response.data;
                return response.data;
            } catch (err) {
                this.error = err.response?.data?.detail || err.message;
                throw err;
            } finally {
                this.loading = false;
            }
        }
    }
});
