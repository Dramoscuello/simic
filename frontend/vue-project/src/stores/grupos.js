import { defineStore } from 'pinia';
import api from '../api/axios';

export const useGruposStore = defineStore('grupos', {
    state: () => ({
        grupos: [],
        loading: false,
        error: null
    }),

    actions: {
        async fetchGrupos(institucionId = null, sedeId = null) {
            this.loading = true;
            try {
                const params = {};
                if (institucionId) params.institucion_id = institucionId;
                if (sedeId) params.sede_id = sedeId;
                const response = await api.get('/grupos/', { params });
                this.grupos = response.data;
                return response.data;
            } catch (err) {
                this.error = err.response?.data?.detail || err.message;
                throw err;
            } finally {
                this.loading = false;
            }
        },

        async createGrupo(data) {
            this.loading = true;
            try {
                const response = await api.post('/grupos/', data);
                this.grupos.push(response.data);
                return response.data;
            } catch (err) {
                this.error = err.response?.data?.detail || err.message;
                throw err;
            } finally {
                this.loading = false;
            }
        },

        async updateGrupo(id, data) {
            this.loading = true;
            try {
                const response = await api.put(`/grupos/${id}`, data);
                const index = this.grupos.findIndex(g => g.id === id);
                if (index !== -1) {
                    this.grupos.splice(index, 1, response.data);
                }
                return response.data;
            } catch (err) {
                this.error = err.response?.data?.detail || err.message;
                throw err;
            } finally {
                this.loading = false;
            }
        },

        async deleteGrupo(id) {
            this.loading = true;
            try {
                await api.delete(`/grupos/${id}`);
                this.grupos = this.grupos.filter(g => g.id !== id);
            } catch (err) {
                this.error = err.response?.data?.detail || err.message;
                throw err;
            } finally {
                this.loading = false;
            }
        }
    }
});
