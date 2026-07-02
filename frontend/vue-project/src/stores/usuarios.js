import { defineStore } from 'pinia';
import api from '../api/axios';

export const useUsuariosStore = defineStore('usuarios', {
    state: () => ({
        // Podríamos separar por listas si necesario, pero a menudo se cargan bajo demanda
        usuarios: [], // Lista genérica (ej. resultados de búsqueda)
        adminsInstitucion: [], // Lista específica para una vista
        estudiantesInstitucion: [], // Lista específica para una vista
        loading: false,
        error: null,
    }),

    getters: {
        getUserById: (state) => (id) => {
            // Buscar en todas las listas posibles
            return state.usuarios.find(u => u.id === id) ||
                state.adminsInstitucion.find(u => u.id === id) ||
                state.estudiantesInstitucion.find(u => u.id === id);
        }
    },

    actions: {
        // Cargar usuarios por institución y rol
        async fetchUsuariosInstitucion(institucionId, rol) {
            this.loading = true;
            try {
                const response = await api.get(`/instituciones/${institucionId}/usuarios`, { params: { rol } });
                if (rol === 'admin') {
                    this.adminsInstitucion = response.data;
                } else if (rol === 'estudiante') {
                    this.estudiantesInstitucion = response.data;
                }
                return response.data;
            } catch (err) {
                console.error(`Error fetching usuarios (${rol}):`, err);
                throw err;
            } finally {
                this.loading = false;
            }
        },

        // Cargar usuarios globales (ej. búsqueda de Estudiantes.vue o Grupos)
        async fetchUsuariosGlobal(filters = {}) {
            this.loading = true;
            try {
                let params = {};
                if (typeof filters === 'string') {
                    params = { rol: filters };
                } else {
                    params = filters;
                }
                const response = await api.get('/usuarios/', { params });
                this.usuarios = response.data;
                return response.data;
            } catch (err) {
                console.error('Error fetching usuarios:', err);
                throw err;
            } finally {
                this.loading = false;
            }
        },

        async createUser(payload) {
            this.loading = true;
            try {
                const response = await api.post('/usuarios/', payload);
                const newUser = response.data;

                // Actualizar listas locales si corresponde
                // (La lógica exacta depende de qué listas tenemos en memoria, pero podemos intentar añadirlos)
                if (payload.rol_id) { // Necesitamos saber role name, no ID. Esto es tricky sin el role map.
                    // Lo más seguro es que la vista que llama haga el push a su lista local observada
                    // O recargar. Por ahora devolvemos el usuario.
                }
                return newUser;
            } catch (err) {
                throw err;
            } finally {
                this.loading = false;
            }
        },

        async updateUser(id, payload) {
            this.loading = true;
            try {
                const response = await api.put(`/usuarios/${id}`, payload);
                const user = response.data;

                // Actualizar en listas locales
                this._updateInList(this.usuarios, user);
                this._updateInList(this.adminsInstitucion, user);
                this._updateInList(this.estudiantesInstitucion, user);

                return user;
            } catch (err) {
                throw err;
            } finally {
                this.loading = false;
            }
        },

        async deleteUser(id) {
            this.loading = true;
            try {
                await api.delete(`/usuarios/${id}`);
                // Eliminar de listas locales
                this.usuarios = this.usuarios.filter(u => u.id !== id);
                this.adminsInstitucion = this.adminsInstitucion.filter(u => u.id !== id);
                this.estudiantesInstitucion = this.estudiantesInstitucion.filter(u => u.id !== id);
            } catch (err) {
                throw err;
            } finally {
                this.loading = false;
            }
        },

        async importUsers(institucionId, formData) {
            this.loading = true;
            try {
                const res = await api.post(`/instituciones/${institucionId}/usuarios/import`, formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
                return res.data;
            } catch (err) {
                throw err;
            } finally {
                this.loading = false;
            }
        },

        // Helper interno
        _updateInList(list, updatedUser) {
            const idx = list.findIndex(u => u.id === updatedUser.id);
            if (idx !== -1) list[idx] = updatedUser;
        }
    }
});
