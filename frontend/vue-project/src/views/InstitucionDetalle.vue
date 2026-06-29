<template>
  <div class="mx-auto flex w-full max-w-7xl flex-col gap-8">
    <!-- Breadcrumb -->
    <div class="flex items-center gap-2 text-sm">
      <router-link v-if="userRole === 'admin'" to="/instituciones" class="text-slate-500 hover:text-primary transition-colors flex items-center gap-1 dark:text-slate-400 dark:hover:text-primary-400">
        <span class="material-icons-round text-[18px]">arrow_back</span>
        Instituciones
      </router-link>
      <router-link v-else to="/dashboard" class="text-slate-500 hover:text-primary transition-colors flex items-center gap-1 dark:text-slate-400 dark:hover:text-primary-400">
        <span class="material-icons-round text-[18px]">arrow_back</span>
        Dashboard
      </router-link>
      <span class="material-icons-round text-slate-300 dark:text-slate-600 text-[16px]">chevron_right</span>
      <span class="text-slate-800 font-medium dark:text-white">{{ institucion.nombre }}</span>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex flex-col items-center justify-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mb-4"></div>
      <p class="text-slate-500 dark:text-slate-400">Cargando información...</p>
    </div>

    <div v-else class="flex flex-col gap-8">
        <!-- Institution Header Card -->
        <div class="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-slate-100 dark:border-slate-700 flex flex-col md:flex-row items-center gap-6">
          <div class="h-20 w-20 rounded-2xl bg-gradient-to-br from-primary to-indigo-600 flex items-center justify-center text-white font-bold text-3xl shadow-lg shrink-0">
            {{ getInitials(institucion.nombre) }}
          </div>
          <div class="flex-1 text-center md:text-left">
            <h1 class="text-2xl font-bold text-slate-800 dark:text-white">{{ institucion.nombre }}</h1>
            <div class="flex flex-wrap items-center justify-center md:justify-start gap-4 mt-2 text-sm text-slate-500 dark:text-slate-400">
              <span class="flex items-center gap-1">
                <span class="material-icons-round text-[18px]">badge</span>
                Cod. DANE: {{ institucion.nit || 'N/A' }}
              </span>
              <span class="flex items-center gap-1">
                <span class="material-icons-round text-[18px]">location_on</span>
                {{ institucion.ciudad }}, {{ institucion.departamento }}
              </span>
              <span 
                :class="institucion.activo ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-slate-100 text-slate-500 dark:bg-slate-700/50 dark:text-slate-400'"
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
              >
                {{ institucion.activo ? 'Activa' : 'Inactiva' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Tabs -->
        <div class="flex flex-col gap-6">
          <div class="border-b border-slate-200 dark:border-slate-700">
            <nav class="-mb-px flex space-x-8 overflow-x-auto" aria-label="Tabs">
              <button
                v-for="tab in tabs"
                :key="tab.id"
                @click="currentTab = tab.id; selectedGrupo = null"
                :class="[
                  currentTab === tab.id
                    ? 'border-primary text-primary dark:text-primary-400 dark:border-primary-400'
                    : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:border-slate-300 dark:hover:border-slate-600',
                  'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2'
                ]"
              >
                <span class="material-icons-round text-[20px]">{{ tab.icon }}</span>
                {{ tab.name }}
                <span v-if="tab.count !== undefined" class="bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 py-0.5 px-2 rounded-full text-xs ml-1">
                  {{ tab.count }}
                </span>
              </button>
            </nav>
          </div>

          <!-- General Info Tab -->
          <div v-if="currentTab === 'info'" class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 p-6">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
                  <span class="material-icons-round text-primary dark:text-primary-400">contact_mail</span>
                    Información básica
                </h3>
                <button
                  v-if="canEditInstitutionInfo && !institutionInfoEditMode"
                  type="button"
                  @click="startInstitutionInfoEdit"
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-600 text-xs font-semibold text-slate-600 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                  title="Editar información básica"
                >
                  <span class="material-icons-round text-[16px]">edit</span>
                  Editar
                </button>
                <span
                  v-else-if="!canEditInstitutionInfo"
                  class="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300"
                >
                  Solo lectura
                </span>
              </div>

              <div v-if="!institutionInfoEditMode" class="space-y-4">
                 <div class="flex items-start gap-3">
                    <span class="material-icons-round text-slate-400 dark:text-slate-500 mt-1">email</span>
                    <div>
                      <p class="text-sm font-medium text-slate-700 dark:text-slate-300">Email</p>
                      <p class="text-sm text-slate-500 dark:text-slate-400">{{ institucion.email_contacto || 'No registrado' }}</p>
                    </div>
                 </div>
                 <div class="flex items-start gap-3">
                    <span class="material-icons-round text-slate-400 dark:text-slate-500 mt-1">phone</span>
                    <div>
                      <p class="text-sm font-medium text-slate-700 dark:text-slate-300">Teléfono</p>
                      <p class="text-sm text-slate-500 dark:text-slate-400">{{ institucion.telefono || 'No registrado' }}</p>
                    </div>
                 </div>
                 <div class="flex items-start gap-3">
                    <span class="material-icons-round text-slate-400 dark:text-slate-500 mt-1">place</span>
                    <div>
                      <p class="text-sm font-medium text-slate-700 dark:text-slate-300">Dirección</p>
                      <p class="text-sm text-slate-500 dark:text-slate-400">{{ institucion.direccion || 'No registrada' }}</p>
                    </div>
                 </div>
              </div>

              <form v-else class="space-y-4" @submit.prevent="saveInstitutionInfo">
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div class="sm:col-span-2">
                    <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Nombre institución</label>
                    <input
                      v-model="institucionForm.nombre"
                      type="text"
                      required
                      :disabled="!canEditInstitutionInfo"
                      class="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 p-2.5 text-sm text-slate-800 dark:text-white outline-none focus:ring-2 focus:ring-primary/40 disabled:opacity-70 disabled:cursor-not-allowed"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Cod. DANE</label>
                    <input
                      v-model="institucionForm.nit"
                      type="text"
                      :disabled="!canEditInstitutionInfo"
                      class="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 p-2.5 text-sm text-slate-800 dark:text-white outline-none focus:ring-2 focus:ring-primary/40 disabled:opacity-70 disabled:cursor-not-allowed"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Teléfono</label>
                    <input
                      v-model="institucionForm.telefono"
                      type="text"
                      :disabled="!canEditInstitutionInfo"
                      class="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 p-2.5 text-sm text-slate-800 dark:text-white outline-none focus:ring-2 focus:ring-primary/40 disabled:opacity-70 disabled:cursor-not-allowed"
                    />
                  </div>
                  <div class="sm:col-span-2">
                    <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Email de contacto</label>
                    <input
                      v-model="institucionForm.email_contacto"
                      type="email"
                      required
                      :disabled="!canEditInstitutionInfo"
                      class="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 p-2.5 text-sm text-slate-800 dark:text-white outline-none focus:ring-2 focus:ring-primary/40 disabled:opacity-70 disabled:cursor-not-allowed"
                    />
                  </div>
                  <div class="sm:col-span-2">
                    <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Dirección</label>
                    <textarea
                      v-model="institucionForm.direccion"
                      rows="2"
                      :disabled="!canEditInstitutionInfo"
                      class="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 p-2.5 text-sm text-slate-800 dark:text-white outline-none focus:ring-2 focus:ring-primary/40 resize-none disabled:opacity-70 disabled:cursor-not-allowed"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Departamento</label>
                    <Select 
                      v-model="institucionForm.departamento"
                      :options="editDepartamentosOptions"
                      optionLabel="label"
                      optionValue="value"
                      placeholder="Seleccionar..."
                      class="w-full"
                      filter
                      :disabled="!canEditInstitutionInfo"
                      :pt="{
                          root: { class: 'w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 text-slate-800 dark:text-white focus:ring-2 focus:ring-primary/40' },
                          trigger: { class: 'text-slate-500 dark:text-slate-400' },
                          panel: { class: 'bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600' },
                          item: { class: 'text-slate-700 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-600' },
                          filterInput: { class: 'w-full p-2 border border-slate-200 dark:border-slate-600 dark:bg-slate-800 dark:text-white rounded-md' }
                      }"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Municipio</label>
                    <Select 
                      v-model="institucionForm.ciudad"
                      :options="editMunicipiosOptions"
                      optionLabel="label"
                      optionValue="value"
                      placeholder="Seleccionar municipio..."
                      class="w-full"
                      filter
                      :loading="editLoadingMunicipios"
                      :disabled="!canEditInstitutionInfo || !institucionForm.departamento"
                      :pt="{
                          root: { class: 'w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 text-slate-800 dark:text-white focus:ring-2 focus:ring-primary/40' },
                          trigger: { class: 'text-slate-500 dark:text-slate-400' },
                          panel: { class: 'bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600' },
                          item: { class: 'text-slate-700 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-600' },
                          filterInput: { class: 'w-full p-2 border border-slate-200 dark:border-slate-600 dark:bg-slate-800 dark:text-white rounded-md' }
                      }"
                    />
                  </div>
                </div>

                <div class="pt-2 flex items-center justify-end gap-2">
                  <button
                    type="button"
                    @click="resetInstitutionInfoForm"
                    :disabled="institutionInfoSaving"
                    class="px-4 py-2 rounded-lg border border-slate-200 dark:border-slate-600 text-sm font-medium text-slate-600 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    :disabled="institutionInfoSaving || !institutionInfoDirty"
                    class="px-4 py-2 rounded-lg bg-primary hover:bg-indigo-600 text-sm font-medium text-white disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    <span v-if="institutionInfoSaving" class="animate-spin h-4 w-4 border-2 border-white rounded-full border-t-transparent"></span>
                    {{ institutionInfoSaving ? 'Guardando...' : 'Guardar cambios' }}
                  </button>
                </div>
              </form>
            </div>
            <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 p-6">
              <h3 class="text-lg font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
                <span class="material-icons-round text-primary dark:text-primary-400">analytics</span>
                Métricas rápidas
              </h3>
               <div class="grid grid-cols-2 gap-4">
                  <div class="p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg text-center">
                    <p class="text-2xl font-bold text-slate-800 dark:text-white">{{ admins.length }}</p>
                    <p class="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide">Administradores</p>
                  </div>
                  <div class="p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg text-center">
                     <p class="text-2xl font-bold text-slate-800 dark:text-white">{{ estudiantes.length }}</p>
                     <p class="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide">Estudiantes</p>
                  </div>
               </div>
            </div>
          </div>

          <!-- Admin Users Tab -->
          <div v-if="currentTab === 'admins'" class="space-y-4">
            <div class="flex justify-between items-center">
              <h3 class="text-lg font-bold text-slate-800 dark:text-white">Administradores de institución</h3>
              <div class="flex gap-2">
                <button 
                  @click="toggleUpload($event, 'admin')"
                  class="flex items-center gap-2 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  <span class="material-icons-round text-[18px]">upload_file</span>
                  Carga masiva
                </button>
                <button 
                  @click="openUserModal('admin')"
                  class="flex items-center gap-2 bg-primary hover:bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  <span class="material-icons-round text-[18px]">add</span>
                  Nuevo admin
                </button>
              </div>
            </div>
            
            <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 overflow-hidden">
              <table class="w-full text-left" v-if="admins.length > 0">
                <thead class="bg-slate-50 dark:bg-slate-700/50 border-b border-slate-100 dark:border-slate-700">
                  <tr>
                    <th class="px-6 py-4 text-xs font-bold uppercase text-slate-500 dark:text-slate-400">Usuario</th>
                    <th class="px-6 py-4 text-xs font-bold uppercase text-slate-500 dark:text-slate-400">Documento</th>
                    <th class="px-6 py-4 text-xs font-bold uppercase text-slate-500 dark:text-slate-400">Email</th>
                    <th class="px-6 py-4 text-xs font-bold uppercase text-slate-500 dark:text-slate-400 text-center">Estado</th>
                    <th class="px-6 py-4 text-xs font-bold uppercase text-slate-500 dark:text-slate-400 text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
                  <tr v-for="user in admins" :key="user.id" class="hover:bg-slate-50 dark:hover:bg-indigo-900/10">
                    <td class="px-6 py-4 text-sm font-medium text-slate-800 dark:text-white">{{ user.nombre }}</td>
                    <td class="px-6 py-4 text-sm text-slate-600 dark:text-slate-300">{{ user.tipo_documento }} {{ user.numero_documento }}</td>
                    <td class="px-6 py-4 text-sm text-slate-600 dark:text-slate-300">{{ user.email }}</td>
                     <td class="px-6 py-4 text-center">
                       <button 
                         v-if="user.id !== currentUserId"
                         @click="toggleStatus(user)"
                         class="px-2 py-0.5 rounded-full text-xs font-medium cursor-pointer"
                         :class="user.activo ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'"
                       >
                          {{ user.activo ? 'Activo' : 'Inactivo' }}
                       </button>
                       <span v-else class="px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400">
                          Activo (Tú)
                       </span>
                    </td>
                    <td class="px-6 py-4 text-right">
                      <div v-if="user.id !== currentUserId">
                        <button @click="openEditUserModal(user)" class="text-slate-400 dark:text-slate-500 hover:text-primary dark:hover:text-primary mr-2"><span class="material-icons-round">edit</span></button>
                        <button @click="confirmDelete(user)" class="text-slate-400 dark:text-slate-500 hover:text-rose-500 dark:hover:text-rose-500"><span class="material-icons-round">delete</span></button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-else class="p-8 text-center text-slate-500 dark:text-slate-400">
                No hay administradores registrados.
              </div>
            </div>
          </div>

          <!-- Grupos Tab (New) -->
          <div v-if="currentTab === 'grupos'" class="space-y-6">
              <!-- Vista Lista Grupos -->
              <div v-if="!selectedGrupo">
                  <div class="flex justify-between items-center">
                    <h3 class="text-lg font-bold text-slate-800 dark:text-white">Grupos académicos</h3>
                    <button 
                      v-if="userRole === 'admin'"
                      @click="openGroupModal"
                      class="flex items-center gap-2 bg-primary hover:bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                    >
                      <span class="material-icons-round text-[18px]">add</span>
                      Nuevo grupo
                    </button>
                  </div>

                  <div v-if="grupos.length === 0" class="text-center py-12 bg-white dark:bg-slate-800 rounded-xl border border-dashed border-slate-200 dark:border-slate-700">
                      <div class="h-12 w-12 bg-slate-50 dark:bg-slate-700/50 rounded-full flex items-center justify-center mx-auto mb-3">
                          <span class="material-icons-round text-slate-400 dark:text-slate-500">class</span>
                      </div>
                      <p class="text-slate-500 dark:text-slate-400">No hay grupos creados.</p>
                      <button v-if="userRole === 'admin'" @click="openGroupModal" class="text-primary dark:text-primary-400 text-sm font-medium mt-2 hover:underline">Crear el primero</button>
                  </div>

                  <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      <div 
                        v-for="grupo in grupos" 
                        :key="grupo.id"
                        @click="selectGrupo(grupo)"
                        class="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-md cursor-pointer transition-all group overflow-hidden"
                      >
                          <div class="p-5 flex items-center justify-between">
                              <div class="flex items-center gap-3">
                                  <div class="h-10 w-10 rounded-lg bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 flex items-center justify-center font-bold text-lg group-hover:bg-primary group-hover:text-white transition-colors">
                                      {{ grupo.nombre.substring(0, 2).toUpperCase() }}
                                  </div>
                                  <div>
                                      <h4 class="font-bold text-slate-800 dark:text-white">{{ grupo.nombre }}</h4>
                                  </div>
                              </div>
                              <span class="material-icons-round text-slate-300 dark:text-slate-600 group-hover:text-primary dark:group-hover:text-primary-400 transition-colors">chevron_right</span>
                          </div>
                      </div>
                  </div>
              </div>

              <!-- Vista Detalle Grupo (Estudiantes) -->
              <div v-else class="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
                  <div class="flex items-center gap-4">
                      <button @click="selectedGrupo = null" class="h-8 w-8 rounded-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center text-slate-500 dark:text-slate-400 hover:text-primary dark:hover:text-primary-400 hover:border-primary dark:hover:border-primary-400 transition-colors">
                          <span class="material-icons-round">arrow_back</span>
                      </button>
                      <div>
                          <h3 class="text-xl font-bold text-slate-800 dark:text-white">{{ selectedGrupo.nombre }}</h3>
                          <p class="text-slate-500 dark:text-slate-400 text-sm">{{ grupoEstudiantes.length }} Estudiantes asignados</p>
                      </div>
                      <div class="ml-auto flex gap-2">
                           <button 
                              @click="toggleUpload($event, 'estudiante')"
                              class="flex items-center gap-2 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 px-3 py-2 rounded-lg text-xs font-medium transition-colors"
                              title="Subir masivo (Nota: Se subirán sin grupo asignado inicialmente en esta versión)"
                            >
                              <span class="material-icons-round text-[18px]">upload_file</span>
                              Masivo
                            </button>
                           <button 
                              v-if="userRole === 'admin'"
                              @click="openUserModal('estudiante', selectedGrupo.id)"
                              class="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-white px-3 py-2 rounded-lg text-xs font-medium transition-colors"
                            >
                              <span class="material-icons-round text-[18px]">person_add</span>
                              Nuevo estudiante
                            </button>
                      </div>
                  </div>

                  <!-- Tabla Estudiantes Grupo -->
                  <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 overflow-hidden">
                      <table class="w-full text-left" v-if="grupoEstudiantes.length > 0">
                          <thead class="bg-slate-50 dark:bg-slate-700/50 border-b border-slate-100 dark:border-slate-700">
                              <tr>
                                <th class="px-6 py-4 text-xs font-bold uppercase text-slate-500 dark:text-slate-400">Estudiante</th>
                                <th class="px-6 py-4 text-xs font-bold uppercase text-slate-500 dark:text-slate-400">Documento</th>
                                <th class="px-6 py-4 text-xs font-bold uppercase text-slate-500 dark:text-slate-400">Email</th>
                                <th class="px-6 py-4 text-xs font-bold uppercase text-slate-500 dark:text-slate-400 text-center">Estado</th>
                                <th class="px-6 py-4 text-xs font-bold uppercase text-slate-500 dark:text-slate-400 text-right">Acciones</th>
                              </tr>
                          </thead>
                          <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
                              <tr v-for="user in grupoEstudiantes" :key="user.id" class="hover:bg-slate-50 dark:hover:bg-indigo-900/10">
                                  <td class="px-6 py-4 text-sm font-medium text-slate-800 dark:text-white">{{ user.nombre }}</td>
                                  <td class="px-6 py-4 text-sm text-slate-600 dark:text-slate-300">{{ user.tipo_documento }} {{ user.numero_documento }}</td>
                                  <td class="px-6 py-4 text-sm text-slate-600 dark:text-slate-300">{{ user.email }}</td>
                                  <td class="px-6 py-4 text-center">
                                     <button 
                                       @click="toggleStatus(user)"
                                       class="px-2 py-0.5 rounded-full text-xs font-medium cursor-pointer"
                                       :class="user.activo ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'"
                                     >
                                        {{ user.activo ? 'Activo' : 'Inactivo' }}
                                     </button>
                                  </td>
                                  <td class="px-6 py-4 text-right">
                                    <button @click="openEditUserModal(user)" class="text-slate-400 dark:text-slate-500 hover:text-primary dark:hover:text-primary mr-2"><span class="material-icons-round">edit</span></button>
                                    <button @click="confirmDelete(user)" class="text-slate-400 dark:text-slate-500 hover:text-rose-500 dark:hover:text-rose-500"><span class="material-icons-round">delete</span></button>
                                  </td>
                              </tr>
                          </tbody>
                      </table>
                      <div v-else class="p-12 text-center">
                          <span class="material-icons-round text-4xl text-slate-200 dark:text-slate-600 mb-2">school</span>
                          <p class="text-slate-500 dark:text-slate-400 mb-4">No hay estudiantes en este grupo.</p>
                          <button v-if="userRole === 'admin'" @click="openUserModal('estudiante', selectedGrupo.id)" class="text-primary dark:text-primary-400 font-medium hover:underline">Crear el primero</button>
                      </div>
                  </div>
              </div>
          </div>
          
        </div>
    </div>
    
    <!-- Modales -->
    
    <!-- Modal Crear Grupo -->
    <teleport to="body">
      <div v-if="showGroupModal" class="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
        <div class="bg-white dark:bg-slate-800 w-full max-w-md rounded-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in duration-200">
          <div class="px-6 py-4 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center bg-slate-50/50 dark:bg-slate-700/30">
              <h3 class="text-lg font-bold text-slate-800 dark:text-white">Nuevo grupo</h3>
              <button @click="closeGroupModal" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
                  <span class="material-icons-round">close</span>
              </button>
          </div>
          
          <form @submit.prevent="saveGroup" class="p-6 space-y-4">
              <div>
                  <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Nombre del grupo</label>
                  <input 
                      v-model="groupForm.nombre" 
                      type="text" 
                      required
                      placeholder="Ej: 11-A" 
                      class="w-full px-4 py-2 border border-slate-200 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all bg-white dark:bg-slate-800 text-slate-800 dark:text-white"
                  />
              </div>
              
              <div class="flex justify-end gap-3 pt-2">
                  <button type="button" @click="closeGroupModal" class="px-4 py-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg font-medium transition-colors">
                      Cancelar
                  </button>
                  <button type="submit" class="px-4 py-2 bg-primary hover:bg-indigo-600 text-white rounded-lg font-medium shadow-sm transition-all">
                      Guardar
                  </button>
              </div>
          </form>
        </div>
      </div>
    </teleport>

    <!-- User Modal -->
    <div v-if="showUserModal" class="fixed inset-0 z-50 overflow-y-auto">
       <div class="fixed inset-0 bg-black/50 dark:bg-black/70 backdrop-blur-sm transition-opacity" @click="closeUserModal"></div>
       <div class="flex min-h-full items-center justify-center p-4">
        <div class="relative bg-white dark:bg-slate-800 rounded-2xl shadow-xl max-w-md w-full animate-in zoom-in duration-200">
           <div class="p-6 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center bg-slate-50/50 dark:bg-slate-700/30">
              <h3 class="text-lg font-bold text-slate-800 dark:text-white">
                  {{ editingUser ? 'Editar usuario' : (newUserRole === 'estudiante' ? 'Nuevo estudiante' : 'Nuevo admin') }}
              </h3>
              <button @click="closeUserModal" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"><span class="material-icons-round">close</span></button>
           </div>
           <form @submit.prevent="saveUser" class="p-6 space-y-4">
            <!-- Tabs Navigation (Solo Edición) -->
            <div v-if="editingUser" class="flex border-b border-slate-200 dark:border-slate-700 mb-2">
                <button 
                   type="button"
                   @click="userModalTab = 'info'"
                   :class="userModalTab === 'info' ? 'border-primary text-primary dark:text-primary-400 dark:border-primary-400' : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'"
                   class="flex-1 pb-3 text-center text-sm font-medium border-b-2 transition-colors focus:outline-none"
                >
                  Información básica
                </button>
                <button 
                   type="button"
                   @click="userModalTab = 'password'"
                   :class="userModalTab === 'password' ? 'border-primary text-primary dark:text-primary-400 dark:border-primary-400' : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'"
                   class="flex-1 pb-3 text-center text-sm font-medium border-b-2 transition-colors focus:outline-none"
                >
                   Contraseña
                </button>
            </div>

            <!-- Tab: Información Básica -->
            <div v-if="!editingUser || userModalTab === 'info'" class="space-y-4 animate-in fade-in">
                  <div>
                     <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Nombre completo</label>
                     <input v-model="userForm.nombre" required type="text" class="w-full rounded-lg border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 p-2.5 text-sm text-slate-800 dark:text-white focus:ring-primary focus:border-primary border outline-none" />
                  </div>
                  <div class="grid grid-cols-2 gap-4">
                      <div>
                        <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Tipo Doc.</label>
                        <Select v-model="userForm.tipo_documento" :options="tipoDocOptions" optionLabel="label" optionValue="value" class="w-full" 
                            :pt="{
                                root: { class: 'w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 text-slate-800 dark:text-white focus:ring-2 focus:ring-primary' },
                                trigger: { class: 'text-slate-500 dark:text-slate-400' },
                                panel: { class: 'bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600' },
                                item: { class: 'text-slate-700 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-600' }
                            }"
                        />
                      </div>
                      <div>
                        <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Número</label>
                        <input v-model="userForm.numero_documento" required type="text" class="w-full rounded-lg border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 p-2.5 text-sm text-slate-800 dark:text-white focus:ring-primary focus:border-primary border outline-none" />
                      </div>
                  </div>
                  <div>
                     <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Email</label>
                     <input v-model="userForm.email" :required="newUserRole !== 'estudiante'" type="email" class="w-full rounded-lg border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 p-2.5 text-sm text-slate-800 dark:text-white focus:ring-primary focus:border-primary border outline-none" />
                  </div>
                  <div v-if="!editingUser">
                     <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                       Contraseña <span class="text-xs text-slate-400 font-normal">(mín. 8 caracteres, letras y números)</span>
                     </label>
                     <input v-model="userForm.password" required type="password" class="w-full rounded-lg border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 p-2.5 text-sm text-slate-800 dark:text-white focus:ring-primary focus:border-primary border outline-none" />
                     <!-- Password requirements -->
                     <div v-if="userForm.password" class="mt-2 space-y-1.5">
                        <div class="flex items-center gap-2 text-xs transition-colors" :class="createPasswordReqs.length ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400'">
                           <span class="material-icons-round text-[14px]">{{ createPasswordReqs.length ? 'check_circle' : 'radio_button_unchecked' }}</span>
                           Mínimo 8 caracteres
                        </div>
                        <div class="flex items-center gap-2 text-xs transition-colors" :class="createPasswordReqs.hasLetters ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400'">
                           <span class="material-icons-round text-[14px]">{{ createPasswordReqs.hasLetters ? 'check_circle' : 'radio_button_unchecked' }}</span>
                           Contiene letras
                        </div>
                        <div class="flex items-center gap-2 text-xs transition-colors" :class="createPasswordReqs.hasNumbers ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400'">
                           <span class="material-icons-round text-[14px]">{{ createPasswordReqs.hasNumbers ? 'check_circle' : 'radio_button_unchecked' }}</span>
                           Contiene números
                        </div>
                     </div>
                  </div>
                  
                  <!-- Mostrar Grupo si es estudiante -->
                  <div v-if="newUserRole === 'estudiante' || (editingUser && editingUser.rol?.nombre === 'estudiante')">
                       <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Grupo asignado</label>
                       <Select 
                          v-model="userForm.grupo_id" 
                          :options="grupos" 
                          optionLabel="nombre" 
                          optionValue="id" 
                          placeholder="Sin Grupo" 
                          class="w-full"
                          showClear
                          :pt="{
                              root: { class: 'w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 text-slate-800 dark:text-white focus:ring-2 focus:ring-primary' },
                              trigger: { class: 'text-slate-500 dark:text-slate-400' },
                              panel: { class: 'bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600' },
                              item: { class: 'text-slate-700 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-600' }
                          }"
                       />
                  </div>

                  <div v-if="editingUser" class="pt-2">
                     <label class="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" v-model="userForm.activo" class="rounded text-primary focus:ring-primary bg-slate-50 dark:bg-slate-700 border-slate-300 dark:border-slate-600" />
                        <span class="text-sm text-slate-700 dark:text-slate-300">Usuario activo</span>
                     </label>
                  </div>
            </div>

            <!-- Tab: Contraseña (Solo Edición) -->
            <div v-if="editingUser && userModalTab === 'password'" class="space-y-6 animate-in fade-in">
                 <div class="bg-indigo-50 dark:bg-indigo-900/20 p-4 rounded-xl border border-indigo-100 dark:border-indigo-800">
                    <p class="text-sm text-indigo-700 dark:text-indigo-300 flex items-start gap-2">
                        <span class="material-icons-round text-lg mt-0.5">lock_reset</span>
                        Establece una nueva contraseña segura para este usuario.
                    </p>
                 </div>
                 
                 <div>
                     <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Nueva contraseña</label>
                     <input v-model="newPassword" type="password" class="w-full rounded-lg border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 p-2.5 text-sm text-slate-800 dark:text-white focus:ring-primary focus:border-primary border outline-none" placeholder="••••••••" />
                 </div>
                 <div>
                     <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Repetir contraseña</label>
                     <input v-model="confirmPassword" type="password" class="w-full rounded-lg border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 p-2.5 text-sm text-slate-800 dark:text-white focus:ring-primary focus:border-primary border outline-none" placeholder="••••••••" />
                 </div>
                 
                 <div class="space-y-2 p-4 bg-slate-50 dark:bg-slate-700/30 rounded-xl border border-slate-100 dark:border-slate-700/50">
                     <p class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2">Requisitos de seguridad</p>
                     
                     <div class="flex items-center gap-2 text-sm transition-colors" :class="passwordRequirements.length ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400'">
                        <span class="material-icons-round text-[16px]">{{ passwordRequirements.length ? 'check_circle' : 'radio_button_unchecked' }}</span>
                        Mínimo 8 caracteres
                     </div>
                     <div class="flex items-center gap-2 text-sm transition-colors" :class="passwordRequirements.chars ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400'">
                        <span class="material-icons-round text-[16px]">{{ passwordRequirements.chars ? 'check_circle' : 'radio_button_unchecked' }}</span>
                        Combinar letras y números
                     </div>
                     <div class="flex items-center gap-2 text-sm transition-colors" :class="passwordRequirements.match ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400'">
                        <span class="material-icons-round text-[16px]">{{ passwordRequirements.match ? 'check_circle' : 'radio_button_unchecked' }}</span>
                        Contraseñas coinciden
                     </div>
                 </div>
            </div>

              <div v-if="userError" class="text-rose-600 dark:text-rose-400 text-sm bg-rose-50 dark:bg-rose-900/20 p-3 rounded-lg flex gap-2">
                  <span class="material-icons-round text-sm mt-0.5">error</span> {{ userError }}
              </div>
              
              <div class="pt-4 flex justify-end gap-3">
                 <button type="button" @click="closeUserModal" class="px-4 py-2 border border-slate-200 dark:border-slate-600 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 text-sm font-medium">Cancelar</button>
                 <button type="submit" :disabled="userSaving" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-indigo-600 disabled:opacity-50 text-sm font-medium">
                    {{ userSaving ? 'Guardando...' : 'Guardar' }}
                 </button>
              </div>
           </form>
        </div>
       </div>
    </div>

    <!-- Group Modal -->

    <Toast position="bottom-right" />
    <ConfirmDialog />
    <OverlayPanel ref="op" class="dark:bg-slate-800 dark:border-slate-700">
        <div class="w-80 p-2">
            <h4 class="font-bold text-slate-800 dark:text-white mb-2">Carga masiva</h4>
            
            <div class="bg-indigo-50 dark:bg-indigo-900/30 p-3 rounded-lg border border-indigo-100 dark:border-indigo-800 mb-3 text-xs">
                <p class="font-bold text-indigo-800 dark:text-indigo-300 mb-1 flex items-center gap-1">
                    <span class="material-icons-round text-[14px]">info</span>
                    Requisitos del Excel (.xlsx)
                </p>
                <p class="text-indigo-700 dark:text-indigo-400 mb-2">Las columnas deben llamarse exactamente:</p>
                <div class="bg-white dark:bg-slate-800 p-2 rounded border border-indigo-100 dark:border-indigo-900/50">
                    <code class="text-indigo-600 dark:text-indigo-400 font-mono block">nombre</code>
                    <code class="text-indigo-600 dark:text-indigo-400 font-mono block">tipo_documento <span class="text-slate-400 dark:text-slate-500 text-[10px]">(CC, TI, CE)</span></code>
                    <code class="text-indigo-600 dark:text-indigo-400 font-mono block">numero_documento</code>
                    <code class="text-indigo-600 dark:text-indigo-400 font-mono block">email</code>
                    <code class="text-indigo-600 dark:text-indigo-400 font-mono block">password <span class="text-slate-400 dark:text-slate-500 text-[10px]">(Min 8 caracteres. letras + números)</span></code>
                </div>
            </div>

            <input type="file" ref="fileInput" @change="fileSelected = $event.target.files.length > 0" accept=".xlsx" class="block w-full text-sm text-slate-500 dark:text-slate-400 mb-3 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20"/>
            
            <button @click="handleUpload" :disabled="uploading || !fileSelected" class="w-full bg-primary text-white py-2 rounded-lg text-sm font-medium hover:bg-indigo-600 disabled:opacity-50 flex items-center justify-center gap-2">
                <span v-if="uploading" class="animate-spin h-4 w-4 border-2 border-white rounded-full border-t-transparent"></span>
                {{ uploading ? 'Subiendo...' : 'Subir Archivo' }}
            </button>
        </div>
    </OverlayPanel>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { useUsuariosStore } from '../stores/usuarios';
import { useInstitucionesStore } from '../stores/instituciones';
import { useGruposStore } from '../stores/grupos';
import api from '../api/axios';

import { useToast } from "primevue/usetoast";
import { useConfirm } from "primevue/useconfirm";
import Toast from 'primevue/toast';
import ConfirmDialog from 'primevue/confirmdialog';
import OverlayPanel from 'primevue/overlaypanel';
import Select from 'primevue/select';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const usuariosStore = useUsuariosStore();
const institucionesStore = useInstitucionesStore();
const gruposStore = useGruposStore();
const toast = useToast();
const confirm = useConfirm();

const institucionId = route.params.id;

// Data del Store
const institucion = computed(() => institucionesStore.currentInstitucion || {});
const admins = computed(() => usuariosStore.adminsInstitucion);
const estudiantes = computed(() => usuariosStore.estudiantesInstitucion);
const grupos = computed(() => gruposStore.grupos);
const loading = computed(() => institucionesStore.loading || usuariosStore.loading || gruposStore.loading);

// ─── API Colombia: Departamentos y Municipios ───
const editDepartamentosApi = ref([]);
const editMunicipiosApi = ref([]);
const editLoadingMunicipios = ref(false);

const fetchEditDepartamentos = async () => {
  try {
    const res = await fetch('https://api-colombia.com/api/v1/Department');
    const data = await res.json();
    editDepartamentosApi.value = data
      .map(d => ({ id: d.id, name: d.name }))
      .sort((a, b) => a.name.localeCompare(b.name));
  } catch (err) {
    console.error('Error cargando departamentos:', err);
  }
};

const fetchEditMunicipios = async (departmentId) => {
  if (!departmentId) { editMunicipiosApi.value = []; return; }
  editLoadingMunicipios.value = true;
  try {
    const res = await fetch(`https://api-colombia.com/api/v1/Department/${departmentId}/cities`);
    const data = await res.json();
    editMunicipiosApi.value = data
      .map(c => ({ id: c.id, name: c.name }))
      .sort((a, b) => a.name.localeCompare(b.name));
  } catch (err) {
    console.error('Error cargando municipios:', err);
    editMunicipiosApi.value = [];
  } finally {
    editLoadingMunicipios.value = false;
  }
};

const editDepartamentosOptions = computed(() => [
  { label: 'Seleccionar...', value: null },
  ...editDepartamentosApi.value.map(d => ({ label: d.name, value: d.name, apiId: d.id }))
]);

const editMunicipiosOptions = computed(() => [
  { label: 'Seleccionar municipio...', value: null },
  ...editMunicipiosApi.value.map(m => ({ label: m.name, value: m.name }))
]);

// UI State
const currentTab = ref(route.query.tab || 'info');
const roles = ref([]);
const uploadRole = ref('');
const op = ref();
const fileInput = ref(null);
const uploading = ref(false);
const fileSelected = ref(false);

// Modal User
const showUserModal = ref(false);
const editingUser = ref(null);
const newUserRole = ref(''); 
const userSaving = ref(false);
const userError = ref('');
const userModalTab = ref('info');
const newPassword = ref('');
const confirmPassword = ref('');

const passwordRequirements = computed(() => {
    const pwd = newPassword.value;
    return {
         length: pwd.length >= 8,
         chars: /^(?=.*[A-Za-z])(?=.*\d)/.test(pwd),
         match: pwd === confirmPassword.value && pwd.length > 0
    };
});

// Password requirements for CREATE user (admin)
const createPasswordReqs = computed(() => {
    const pwd = userForm.value?.password || '';
    return {
        length: pwd.length >= 8,
        hasLetters: /[A-Za-z]/.test(pwd),
        hasNumbers: /\d/.test(pwd)
    };
});
// Modal Group
const showGroupModal = ref(false);
const groupForm = ref({ nombre: '' });
// Nav Grupos
const selectedGrupo = ref(null);


const userRole = computed(() => authStore.user?.rol?.nombre || 'guest');
const currentUserId = computed(() => authStore.user?.id);
const canEditInstitutionInfo = computed(() => ['admin', 'admin'].includes(userRole.value));
const institutionInfoEditMode = ref(false);
const institutionInfoSaving = ref(false);
const institucionForm = ref({
    nombre: '',
    nit: '',
    direccion: '',
    telefono: '',
    email_contacto: '',
    ciudad: '',
    departamento: ''
});

const normalizeText = (value) => (value ?? '').toString().trim();

const getInstitutionBaseInfoPayload = () => ({
    nombre: normalizeText(institucionForm.value.nombre),
    nit: normalizeText(institucionForm.value.nit) || null,
    direccion: normalizeText(institucionForm.value.direccion) || null,
    telefono: normalizeText(institucionForm.value.telefono) || null,
    email_contacto: normalizeText(institucionForm.value.email_contacto),
    ciudad: normalizeText(institucionForm.value.ciudad) || null,
    departamento: normalizeText(institucionForm.value.departamento) || null
});

const institutionInfoDirty = computed(() => {
    const base = institucion.value || {};
    const payload = getInstitutionBaseInfoPayload();
    return (
        payload.nombre !== normalizeText(base.nombre) ||
        payload.nit !== (normalizeText(base.nit) || null) ||
        payload.direccion !== (normalizeText(base.direccion) || null) ||
        payload.telefono !== (normalizeText(base.telefono) || null) ||
        payload.email_contacto !== normalizeText(base.email_contacto) ||
        payload.ciudad !== (normalizeText(base.ciudad) || null) ||
        payload.departamento !== (normalizeText(base.departamento) || null)
    );
});

const syncInstitutionInfoForm = () => {
    const base = institucion.value || {};
    institucionForm.value = {
        nombre: base.nombre || '',
        nit: base.nit || '',
        direccion: base.direccion || '',
        telefono: base.telefono || '',
        email_contacto: base.email_contacto || '',
        ciudad: base.ciudad || '',
        departamento: base.departamento || ''
    };
    // Pre-load municipios if there's a department set
    if (base.departamento) {
        const dep = editDepartamentosApi.value.find(d => d.name === base.departamento);
        if (dep) fetchEditMunicipios(dep.id);
    }
};

// Watcher: when departamento changes in edit form, load municipios
let _skipDepWatch = false;
watch(() => institucionForm.value.departamento, (newDep, oldDep) => {
    if (_skipDepWatch) { _skipDepWatch = false; return; }
    if (newDep !== oldDep) {
        institucionForm.value.ciudad = ''; // Reset municipio
    }
    if (newDep) {
        const dep = editDepartamentosApi.value.find(d => d.name === newDep);
        if (dep) fetchEditMunicipios(dep.id);
        else editMunicipiosApi.value = [];
    } else {
        editMunicipiosApi.value = [];
    }
});

const tipoDocOptions = [
  { label: 'CC', value: 'CC' },
  { label: 'TI', value: 'TI' },
  { label: 'CE', value: 'CE' }
];

const tabs = computed(() => {
  const t = [
    { id: 'info', name: 'Información general', icon: 'info' },
    { id: 'admins', name: 'Administradores', icon: 'admin_panel_settings', count: admins.value.length },
    { id: 'grupos', name: 'Grupos', icon: 'class', count: grupos.value.length }
  ];
  return t;
});

const grupoEstudiantes = computed(() => {
    if (!selectedGrupo.value) return [];
    return estudiantes.value.filter(e => e.grupo_id === selectedGrupo.value.id);
});

const userForm = ref({
    nombre: '',
    tipo_documento: 'CC',
    numero_documento: '',
    email: '',
    password: '',
    activo: true,
    grupo_id: null
});

const getInitials = (name) => {
  if (!name) return '?';
  const parts = name.split(' ');
  return parts.length >= 2 ? (parts[0][0] + parts[1][0]).toUpperCase() : name.substring(0, 2).toUpperCase();
};

const fetchData = async () => {
    try {
        const rolesRes = await api.get('/roles/');
        roles.value = rolesRes.data;

        // Load departamentos from API Colombia in parallel
        fetchEditDepartamentos();

        await institucionesStore.fetchInstitucion(institucionId);
        await gruposStore.fetchGrupos(institucionId);
        
        // Cargar usuarios
        await Promise.all([
            usuariosStore.fetchUsuariosInstitucion(institucionId, 'estudiante'),
            usuariosStore.fetchUsuariosInstitucion(institucionId, 'admin')
        ]);
    } catch (e) {
        console.error("Error fetching data:", e);
    }
};

const resetInstitutionInfoForm = () => {
    syncInstitutionInfoForm();
    institutionInfoEditMode.value = false;
};

const startInstitutionInfoEdit = () => {
    if (!canEditInstitutionInfo.value) return;
    syncInstitutionInfoForm();
    institutionInfoEditMode.value = true;
};

const saveInstitutionInfo = async () => {
    if (!canEditInstitutionInfo.value) return;
    if (!institutionInfoDirty.value) return;

    institutionInfoSaving.value = true;
    try {
        const payload = getInstitutionBaseInfoPayload();
        if (!payload.nombre) {
            throw new Error('El nombre de la institución es obligatorio.');
        }
        if (!payload.email_contacto) {
            throw new Error('El email de contacto es obligatorio.');
        }

        await institucionesStore.updateInstitucion(institucionId, payload);
        syncInstitutionInfoForm();
        institutionInfoEditMode.value = false;
        toast.add({ severity: 'success', summary: 'Información actualizada', life: 2500 });
    } catch (e) {
        const detail = e.response?.data?.detail || e.message || 'No se pudo guardar la información.';
        toast.add({ severity: 'error', summary: 'Error', detail, life: 3500 });
    } finally {
        institutionInfoSaving.value = false;
    }
};

const openUserModal = (roleName, grupoId = null) => {
    editingUser.value = null;
    newUserRole.value = roleName;
    userForm.value = {
        nombre: '',
        tipo_documento: roleName === 'estudiante' ? 'TI' : 'CC',
        numero_documento: '',
        email: '',
        password: '',
        activo: true,
        grupo_id: grupoId // Pre-fill grupo if creating from group detail
    };
    userError.value = '';
    showUserModal.value = true;
    userModalTab.value = 'info';
    newPassword.value = '';
    confirmPassword.value = '';
};

const openEditUserModal = (user) => {
    editingUser.value = user;
    userForm.value = {
        nombre: user.nombre,
        tipo_documento: user.tipo_documento,
        numero_documento: user.numero_documento,
        email: user.email,
        password: '',
        activo: user.activo,
        grupo_id: user.grupo_id
    };
    userError.value = '';
    showUserModal.value = true;
    userModalTab.value = 'info';
    newPassword.value = '';
    confirmPassword.value = '';
};

const closeUserModal = () => {
    showUserModal.value = false;
    userError.value = '';
};

const saveUser = async () => {
    userSaving.value = true;
    userError.value = '';

    try {
        if (editingUser.value) {
            // Logic Tab Contraseña
            const payload = { ...userForm.value };
            
            if (userModalTab.value === 'password') {
                if (!passwordRequirements.value.length || !passwordRequirements.value.chars) {
                     throw new Error('La contraseña no cumple con los requisitos de seguridad.');
                }
                if (!passwordRequirements.value.match) {
                     throw new Error('Las contraseñas no coinciden.');
                }
                payload.password = newPassword.value;
            } else {
                // Info Tab: Remove password just in case
                delete payload.password;
            }

            await usuariosStore.updateUser(editingUser.value.id, payload);
            
            // Refetch simple para actualizar listas
            await usuariosStore.fetchUsuariosInstitucion(institucionId, 'estudiante');
            // Nota: admins se actualiza también.
            
        } else {
            const targetRole = roles.value.find(r => r.nombre === newUserRole.value);
            if (!targetRole) throw new Error(`Rol '${newUserRole.value}' no encontrado.`);

            // Validate password for all new users
            const pwd = userForm.value.password || '';
            if (pwd.length < 8) {
                throw new Error('La contraseña debe tener mínimo 8 caracteres.');
            }
            if (!/[A-Za-z]/.test(pwd) || !/\d/.test(pwd)) {
                throw new Error('La contraseña debe contener letras y números.');
            }

            const payload = {
                ...userForm.value,
                institucion_id: parseInt(institucionId),
                rol_id: targetRole.id
            };
            if (userForm.value.grupo_id) payload.grupo_id = userForm.value.grupo_id;
            
            await usuariosStore.createUser(payload);
            await usuariosStore.fetchUsuariosInstitucion(institucionId, newUserRole.value);
        }
        
        toast.add({ severity: 'success', summary: 'Éxito', detail: 'Usuario guardado', life: 3000 });
        closeUserModal();
    } catch (e) {
        userError.value = e.response?.data?.detail || e.message;
        toast.add({ severity: 'error', summary: 'Error', detail: userError.value, life: 3000 });
    } finally {
        userSaving.value = false;
    }
};

const toggleStatus = async (user) => {
    try {
        await usuariosStore.updateUser(user.id, { activo: !user.activo });
        toast.add({ severity: 'success', summary: 'Actualizado', detail: 'Estado actualizado', life: 2000 });
        // Refetch to be safe or optimistic update in store handled
        // usuariosStore.fetchUsuariosInstitucion(institucionId, ...);
    } catch(e) { /*...*/ }
};

const confirmDelete = (user) => {
    confirm.require({
        message: '¿Estás seguro de eliminar este usuario?',
        header: 'Confirmar',
        icon: 'pi pi-exclamation-triangle',
        accept: async () => {
             await usuariosStore.deleteUser(user.id);
             toast.add({ severity: 'success', summary: 'Eliminado', life: 3000 });
        }
    });
};

const toggleUpload = (event, role) => {
    uploadRole.value = role;
    fileSelected.value = false;
    op.value.toggle(event);
};

const handleUpload = async () => {
    if (!fileInput.value.files[0]) return;
    uploading.value = true;
    const formData = new FormData();
    formData.append('file', fileInput.value.files[0]);
    formData.append('rol_nombre', uploadRole.value);
    
    // Si estamos dentro de un grupo y el rol es estudiante, asignar grupo automáticamente
    if (uploadRole.value === 'estudiante' && selectedGrupo.value) {
        formData.append('grupo_id', selectedGrupo.value.id);
    }
    
    try {
        await usuariosStore.importUsers(institucionId, formData);
        toast.add({ severity: 'success', summary: 'Importación completada', life: 3000 });
        op.value.hide();
        await usuariosStore.fetchUsuariosInstitucion(institucionId, uploadRole.value);
    } catch (e) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Error en importación', life: 3000 });
    } finally {
        uploading.value = false;
    }
};

const openGroupModal = () => {
    console.log('[InstitucionDetalle] openGroupModal clicked', {
        institucionId,
        userRole: userRole.value,
        currentTab: currentTab.value
    });
    groupForm.value.nombre = '';
    showGroupModal.value = true;
    console.log('[InstitucionDetalle] showGroupModal set to true');
};

const closeGroupModal = () => {
    showGroupModal.value = false;
};

const saveGroup = async () => {
    try {
        if (!groupForm.value.nombre || !groupForm.value.nombre.trim()) {
            toast.add({ severity: 'warn', summary: 'Falta nombre', detail: 'Escribe un nombre para el grupo', life: 3000 });
            return;
        }
        await gruposStore.createGrupo({ 
            nombre: groupForm.value.nombre, 
            institucion_id: parseInt(institucionId) 
        });
        showGroupModal.value = false;
        await gruposStore.fetchGrupos(institucionId);
        toast.add({ severity: 'success', summary: 'Grupo creado', life: 3000 });
    } catch (e) {
        toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo crear grupo', life: 3000 });
    }
};

const selectGrupo = (grupo) => {
    selectedGrupo.value = grupo;
};

// Watcher para cambios en query params (Navegación Sidebar vs Link específico)
watch(() => route.query.tab, (newTab) => {
    if (newTab) {
        currentTab.value = newTab;
    } else {
        // Si no hay tab en query (ej: click en sidebar 'Mi Institución'), volver al default
        currentTab.value = 'info';
    }
});

watch(() => institucion.value.id, (newId) => {
    if (!newId) return;
    syncInstitutionInfoForm();
    institutionInfoEditMode.value = false;
}, { immediate: true });

onMounted(() => {
    console.log('[InstitucionDetalle] mounted', {
        institucionId,
        userRole: userRole.value,
        currentTab: currentTab.value
    });
    fetchData();
});
</script>

<style scoped>
.font-sans { font-family: 'Inter', sans-serif; }
.animate-in { animation-duration: 300ms; }
</style>
