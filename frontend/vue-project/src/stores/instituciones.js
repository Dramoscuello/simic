import { defineStore } from 'pinia';
import api from '../api/axios';

export const useInstitucionesStore = defineStore('instituciones', {
    state: () => ({
        currentInstitucion: null, // Para vista detalle
        institucionesList: [], // Para vista lista
        loading: false,
        error: null,
        lastFetchList: 0, // Cache simple
    }),

    actions: {
        // Cargar una institucion (detalle)
        async fetchInstitucion(id) {
            this.loading = true;
            try {
                const response = await api.get(`/instituciones/${id}`);
                this.currentInstitucion = response.data;
                return response.data;
            } catch (err) {
                console.error('Error fetching institucion:', err);
                this.error = err;
                throw err;
            } finally {
                this.loading = false;
            }
        },

        // Cargar todas las instituciones (lista)
        async fetchInstituciones(force = false) {
            // Cache de 2 minutos
            if (!force && this.institucionesList.length > 0 && (Date.now() - this.lastFetchList < 120000)) {
                return this.institucionesList;
            }

            this.loading = true;
            try {
                const response = await api.get('/instituciones/');
                this.institucionesList = response.data;
                this.lastFetchList = Date.now();
                return response.data;
            } catch (err) {
                console.error('Error fetching instituciones:', err);
                this.error = err;
                throw err;
            } finally {
                this.loading = false;
            }
        },

        async createInstitucion(payload) {
            this.loading = true;
            try {
                const response = await api.post('/instituciones/', payload);
                const newInst = response.data;
                // Agregar a la lista local
                this.institucionesList.unshift(newInst);
                return newInst;
            } catch (err) {
                this.error = err;
                throw err;
            } finally {
                this.loading = false;
            }
        },

        async updateInstitucion(id, payload) {
            this.loading = true;
            try {
                const response = await api.put(`/instituciones/${id}`, payload);
                const updatedInst = response.data;

                // Actualizar en lista
                const idx = this.institucionesList.findIndex(i => i.id === id);
                if (idx !== -1) {
                    this.institucionesList[idx] = updatedInst;
                }

                // Actualizar en detalle si es la actual
                // Usar parseInt para evitar problemas de string vs number
                if (this.currentInstitucion && this.currentInstitucion.id === parseInt(id)) {
                    this.currentInstitucion = updatedInst;
                }

                return updatedInst;
            } catch (err) {
                this.error = err;
                throw err;
            } finally {
                this.loading = false;
            }
        },

        async deleteInstitucion(id) {
            this.loading = true;
            try {
                await api.delete(`/instituciones/${id}`);
                this.institucionesList = this.institucionesList.filter(i => i.id !== id);
            } catch (err) {
                this.error = err;
                throw err;
            } finally {
                this.loading = false;
            }
        }
    }
});
