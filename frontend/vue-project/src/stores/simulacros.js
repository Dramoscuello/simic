import { defineStore } from 'pinia';
import api from '../api/axios';

export const useSimulacrosStore = defineStore('simulacros', {
    state: () => ({
        simulacros: [],
        loading: false,
        error: null,
        lastFetch: null,
        // Cache de opciones para filtros (para evitar recargas)
        institucionesCache: []
    }),

    getters: {
        getSimulacroById: (state) => (id) => {
            return state.simulacros.find(s => s.id === parseInt(id));
        },

        // Getter base que retorna simulacros según rol sin filtros de UI
        // (Útil si necesitamos datos "crudos" permitidos para el usuario)
        permittedSimulacros: (state) => {
            // Nota: El backend ya filtra por seguridad, así que esto es redundante
            // pero aquí podríamos poner lógica extra si fuera necesaria.
            return state.simulacros;
        }
    },

    actions: {
        async fetchSimulacros(paramsOrForce = {}, maybeForce = false) {
            // Manejo flexible de argumentos: (params={}, force=false) o (force=boolean)
            let params = {};
            let force = false;

            if (typeof paramsOrForce === 'boolean') {
                force = paramsOrForce;
            } else {
                params = paramsOrForce;
                force = maybeForce;
            }

            // Política de caché: Si hay params específicos, ignoramos caché global.
            // Si es carga general (sin params) y tenemos caché reciente, usamos caché.
            const hasParams = Object.keys(params).length > 0;
            const CACHE_TIME = 5 * 60 * 1000;
            const now = Date.now();

            if (!force && !hasParams && this.simulacros.length > 0 && this.lastFetch && (now - this.lastFetch < CACHE_TIME)) {
                return;
            }

            this.loading = true;
            this.error = null;

            try {
                const response = await api.get('/simulacros/', { params });
                this.simulacros = response.data;

                // Solo actualizamos timestamp de caché global si fue un fetch sin filtros
                if (!hasParams) {
                    this.lastFetch = now;
                }
            } catch (err) {
                console.error('Error fetching simulacros:', err);
                this.error = 'Error cargando simulacros. Intente nuevamente.';
            } finally {
                this.loading = false;
            }
        },

        // Acción específica para cargar filtrando desde backend (para SuperAdmin seleccionando Institución)
        async fetchByInstitucion(institucionId) {
            this.loading = true;
            try {
                const params = {};
                if (institucionId) params.institucion_id = institucionId;

                const response = await api.get('/simulacros/', { params });
                this.simulacros = response.data;
                // Invalidamos caché global porque ahora tenemos un subset parcial
                this.lastFetch = null;
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },

        // Cargar un simulacro individual (útil para edición directa por URL)
        async fetchSimulacro(id) {
            // Primero buscar en local
            const existing = this.simulacros.find(s => s.id === parseInt(id));
            if (existing) return existing;

            this.loading = true;
            try {
                const response = await api.get(`/simulacros/${id}`);
                const simulacro = response.data;

                // Opcional: Agregarlo a la lista local si no existe, para caché futura
                // Pero cuidado con duplicados si recargamos la lista luego.
                // Mejor solo retornarlo, o agregarlo si no rompe la consistencia de filtros.
                // Como fetchSimulacros sobrescribe 'this.simulacros', agregar uno aquí es seguro temporalmente.
                this.simulacros.push(simulacro);

                return simulacro;
            } catch (err) {
                throw err;
            } finally {
                this.loading = false;
            }
        },

        async createSimulacro(data) {
            this.loading = true;
            try {
                const response = await api.post('/simulacros/', data);
                // Agregar al inicio de la lista
                this.simulacros.unshift(response.data);
                return response.data;
            } catch (err) {
                throw err;
            } finally {
                this.loading = false;
            }
        },

        async updateSimulacro(id, data) {
            this.loading = true;
            try {
                const response = await api.put(`/simulacros/${id}`, data);
                // Actualizar en la lista local (Parsear ID para asegurar coincidencia)
                const index = this.simulacros.findIndex(s => s.id === parseInt(id));
                if (index !== -1) {
                    // Usar splice para asegurar reactividad y reemplazo completo
                    this.simulacros.splice(index, 1, response.data);
                }
                return response.data;
            } catch (err) {
                throw err;
            } finally {
                this.loading = false;
            }
        },

        // Auxiliar: Cargar Instituciones (cacheada)
        async fetchInstituciones() {
            if (this.institucionesCache.length > 0) return this.institucionesCache;
            try {
                const res = await api.get('/instituciones/');
                this.institucionesCache = res.data;
                return res.data;
            } catch (e) {
                console.error(e);
                return [];
            }
        },

        // Generar simulacros automáticamente con IA
        // Generar simulacros automáticamente con IA (Wrapper para Async)
        async generateSimulacros(data) {
            console.warn("generateSimulacros (sync) is deprecated. Redirecting to async...");
            return this.generateSimulacrosAsync(data);
        },

        // Generar simulacros de forma asíncrona (background)
        async generateSimulacrosAsync(data) {
            try {
                const response = await api.post('/simulacros/generate-async', data);
                return response.data;
            } catch (err) {
                throw err;
            }
        },

        // Consultar estado de un job de generación
        async fetchJobStatus(jobId) {
            try {
                const response = await api.get(`/simulacros/jobs/${jobId}`);
                return response.data;
            } catch (err) {
                throw err;
            }
        },

        // Polling de estado de job (helper)
        async pollJobUntilComplete(jobId, onProgress, pollInterval = 3000) {
            return new Promise((resolve, reject) => {
                const poll = async () => {
                    try {
                        const status = await this.fetchJobStatus(jobId);

                        // Callback de progreso
                        if (onProgress) {
                            onProgress(status);
                        }

                        // Verificar si terminó
                        if (status.status === 'completed' || status.status === 'failed') {
                            // Invalidar caché para recargar lista
                            this.lastFetch = null;
                            resolve(status);
                        } else {
                            // Seguir polling
                            setTimeout(poll, pollInterval);
                        }
                    } catch (err) {
                        reject(err);
                    }
                };

                poll();
            });
        },

        // Regenerar preguntas específicas de un simulacro
        async regenerarPreguntas(simulacroId, data) {
            this.loading = true;
            try {
                const response = await api.post(`/simulacros/${simulacroId}/regenerar`, data);

                // Actualizar el simulacro en la lista local
                const index = this.simulacros.findIndex(s => s.id === parseInt(simulacroId));
                if (index !== -1) {
                    // Recargar el simulacro actualizado
                    const updated = await api.get(`/simulacros/${simulacroId}`);
                    this.simulacros.splice(index, 1, updated.data);
                }

                return response.data;
            } catch (err) {
                throw err;
            } finally {
                this.loading = false;
            }
        },

        // Eliminar simulacro
        async deleteSimulacro(simulacroId) {
            this.loading = true;
            try {
                await api.delete(`/simulacros/${simulacroId}`);

                // Remover del estado local
                const index = this.simulacros.findIndex(s => s.id === parseInt(simulacroId));
                if (index !== -1) {
                    this.simulacros.splice(index, 1);
                }

                return true;
            } catch (err) {
                console.error('Error eliminando simulacro:', err);
                throw err;
            } finally {
                this.loading = false;
            }
        },

        // Optimizar gráfico SVG con IA Vision
        async optimizarGrafico(simulacroId, preguntaId, imagenBase64, instruccionesAdicionales = null) {
            this.loading = true;
            try {
                const response = await api.post(`/simulacros/${simulacroId}/optimizar-grafico`, {
                    pregunta_id: preguntaId,
                    imagen_base64: imagenBase64,
                    instrucciones_adicionales: instruccionesAdicionales
                });

                // Recargar el simulacro actualizado
                const index = this.simulacros.findIndex(s => s.id === parseInt(simulacroId));
                if (index !== -1) {
                    const updated = await api.get(`/simulacros/${simulacroId}`);
                    this.simulacros.splice(index, 1, updated.data);
                }

                return response.data;
            } catch (err) {
                console.error('Error optimizando gráfico:', err);
                throw err;
            } finally {
                this.loading = false;
            }
        }
    }
});
