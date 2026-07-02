<template>
  <div class="mx-auto flex w-full max-w-7xl flex-col gap-6">
    <!-- Top Actions Bar -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold text-slate-800 dark:text-white">Instituciones educativas</h2>
        <p class="text-slate-500 dark:text-slate-400">Administra las instituciones registradas en el sistema</p>
      </div>
      <div class="flex items-center gap-3">
        <!-- Filter -->
        <Select 
          v-model="filterStatus" 
          :options="statusOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Todos los estados"
          class="w-40"
          :pt="{
              root: { class: 'w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-700 dark:text-white focus:ring-2 focus:ring-primary' },
              trigger: { class: 'text-slate-500 dark:text-slate-400' },
              panel: { class: 'bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600' },
              item: { class: 'text-slate-700 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-600' }
          }"
        />
        <!-- New Institution Button -->
        <button 
          @click="openCreateModal"
          class="flex items-center gap-2 bg-gradient-to-r from-primary to-indigo-600 hover:from-indigo-600 hover:to-primary text-white px-5 py-2.5 rounded-lg text-sm font-semibold shadow-md hover:shadow-lg transition-all"
        >
          <span class="material-icons-round text-[20px]">add</span>
          Nueva institución
        </button>
      </div>
    </div>
    
    <!-- Stats Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-100 dark:border-slate-700">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-slate-500 dark:text-slate-400">Total instituciones</p>
            <p class="text-2xl font-bold text-slate-800 dark:text-white mt-1">{{ instituciones.length }}</p>
          </div>
          <div class="h-10 w-10 rounded-lg bg-blue-50 dark:bg-blue-900/40 flex items-center justify-center text-blue-600 dark:text-blue-400">
            <span class="material-icons-round">domain</span>
          </div>
        </div>
      </div>
      <div class="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-100 dark:border-slate-700">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-slate-500 dark:text-slate-400">Activas</p>
            <p class="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">{{ activeCount }}</p>
          </div>
          <div class="h-10 w-10 rounded-lg bg-emerald-50 dark:bg-emerald-900/40 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
            <span class="material-icons-round">check_circle</span>
          </div>
        </div>
      </div>
      <div class="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-100 dark:border-slate-700">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-slate-500 dark:text-slate-400">Inactivas</p>
            <p class="text-2xl font-bold text-slate-400 dark:text-slate-500 mt-1">{{ inactiveCount }}</p>
          </div>
          <div class="h-10 w-10 rounded-lg bg-slate-100 dark:bg-slate-700 flex items-center justify-center text-slate-400 dark:text-slate-500">
            <span class="material-icons-round">pause_circle</span>
          </div>
        </div>
      </div>
      <div class="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-100 dark:border-slate-700">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-slate-500 dark:text-slate-400">Nuevas este mes</p>
            <p class="text-2xl font-bold text-primary dark:text-primary-400 mt-1">{{ newThisMonth }}</p>
          </div>
          <div class="h-10 w-10 rounded-lg bg-purple-50 dark:bg-purple-900/40 flex items-center justify-center text-purple-600 dark:text-purple-400">
            <span class="material-icons-round">trending_up</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Loading State -->
    <div v-if="loading" class="flex flex-col items-center justify-center py-20">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mb-4"></div>
      <p class="text-slate-500 dark:text-slate-400">Cargando instituciones...</p>
    </div>
    
    <!-- Empty State -->
    <div v-else-if="filteredInstituciones.length === 0" class="bg-white dark:bg-slate-800 rounded-2xl p-12 text-center shadow-sm border border-slate-100 dark:border-slate-700">
      <div class="w-20 h-20 bg-slate-100 dark:bg-slate-700 rounded-full flex items-center justify-center mx-auto mb-6">
        <span class="material-icons-round text-slate-400 dark:text-slate-500 text-4xl">domain_add</span>
      </div>
      <h3 class="text-xl font-bold text-slate-800 dark:text-white mb-2">No hay instituciones</h3>
      <p class="text-slate-500 dark:text-slate-400 mb-6 max-w-md mx-auto">
        {{ searchQuery || filterStatus ? 'No se encontraron instituciones con los filtros aplicados.' : 'Aún no has registrado ninguna institución.' }}
      </p>
      <button 
        @click="openCreateModal"
        class="inline-flex items-center gap-2 bg-primary hover:bg-indigo-600 text-white px-6 py-3 rounded-lg text-sm font-semibold shadow-md transition-all"
      >
        <span class="material-icons-round text-[20px]">add</span>
        Registrar primera institución
      </button>
    </div>
    
    <!-- Institutions Table -->
    <div v-else class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 overflow-hidden">
      <!-- Search inside table (added here for better UX) -->
      <div class="p-4 border-b border-slate-100 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-700/30">
        <div class="relative max-w-md">
            <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
                <span class="material-icons-round text-[20px]">search</span>
            </span>
            <input 
                v-model="searchQuery" 
                type="text" 
                placeholder="Buscar institución..." 
                class="pl-10 w-full rounded-lg border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-800 dark:text-white text-sm focus:ring-primary focus:border-primary shadow-sm placeholder-slate-400 dark:placeholder-slate-500"
            />
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left">
          <thead class="bg-slate-50 dark:bg-slate-700/50 border-b border-slate-100 dark:border-slate-700">
            <tr>
              <th class="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Institución</th>
              <th class="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Contacto</th>
              <th class="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Ubicación</th>
              <th class="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 text-center">Estado</th>
              <th class="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 text-center">Registro</th>
              <th class="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
            <tr 
              v-for="institucion in filteredInstituciones" 
              :key="institucion.id" 
              class="group hover:bg-slate-50 dark:hover:bg-indigo-900/10 transition-colors"
            >
              <td class="px-6 py-4">
                <div class="flex items-center gap-4">
                  <div class="h-10 w-10 rounded-lg bg-gradient-to-br from-primary to-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow-sm">
                    {{ getInitials(institucion.nombre) }}
                  </div>
                  <div>
                    <p class="font-semibold text-slate-800 dark:text-white">{{ institucion.nombre }}</p>
                    <p class="text-xs text-slate-400 dark:text-slate-500">Cod. DANE: {{ institucion.nit || 'N/A' }}</p>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4">
                <p class="text-sm text-slate-700 dark:text-slate-300">{{ institucion.email_contacto }}</p>
                <p class="text-xs text-slate-400 dark:text-slate-500">{{ institucion.telefono || 'Sin teléfono' }}</p>
              </td>
              <td class="px-6 py-4">
                <p class="text-sm text-slate-700 dark:text-slate-300">{{ institucion.ciudad || 'Sin ciudad' }}</p>
                <p class="text-xs text-slate-400 dark:text-slate-500">{{ institucion.departamento || '' }}</p>
              </td>
              <td class="px-6 py-4 text-center">
                <span 
                  :class="institucion.activo ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-slate-100 text-slate-500 dark:bg-slate-700/50 dark:text-slate-400'"
                  class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium"
                >
                  {{ institucion.activo ? 'Activa' : 'Inactiva' }}
                </span>
              </td>
              <td class="px-6 py-4 text-center text-sm text-slate-500 dark:text-slate-400">
                {{ formatDate(institucion.fecha_registro) }}
              </td>
              <td class="px-6 py-4">
                <div class="flex items-center justify-end gap-2">
                  <button 
                    @click="openEditModal(institucion)"
                    class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400 dark:text-slate-500 hover:text-primary dark:hover:text-primary transition-colors"
                    title="Editar"
                  >
                    <span class="material-icons-round text-[20px]">edit</span>
                  </button>
                  <button 
                    @click="toggleStatus(institucion)"
                    class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                    :class="institucion.activo ? 'text-slate-400 dark:text-slate-500 hover:text-amber-500' : 'text-slate-400 dark:text-slate-500 hover:text-emerald-500'"
                    :title="institucion.activo ? 'Desactivar' : 'Activar'"
                  >
                    <span class="material-icons-round text-[20px]">{{ institucion.activo ? 'pause_circle' : 'play_circle' }}</span>
                  </button>
                  <button 
                    @click="viewDetails(institucion)"
                    class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400 dark:text-slate-500 hover:text-blue-500 transition-colors"
                    title="Ver detalles"
                  >
                    <span class="material-icons-round text-[20px]">visibility</span>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- Pagination -->
      <div class="px-6 py-4 border-t border-slate-100 dark:border-slate-700 flex items-center justify-between">
        <p class="text-sm text-slate-500 dark:text-slate-400">
          Mostrando <strong>{{ filteredInstituciones.length }}</strong> de <strong>{{ instituciones.length }}</strong> instituciones
        </p>
      </div>
    </div>
    
    <!-- Modal Create/Edit -->
    <div v-if="showModal" class="fixed inset-0 z-50 overflow-y-auto">
      <!-- Backdrop -->
      <div class="fixed inset-0 bg-black/50 dark:bg-black/70 backdrop-blur-sm transition-opacity" @click="closeModal"></div>
      
      <!-- Modal Content -->
      <div class="flex min-h-full items-center justify-center p-4">
        <div class="relative bg-white dark:bg-slate-800 rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <!-- Modal Header -->
          <div class="sticky top-0 bg-white dark:bg-slate-800 px-6 py-4 border-b border-slate-100 dark:border-slate-700 flex items-center justify-between z-10">
            <h3 class="text-xl font-bold text-slate-800 dark:text-white flex items-center gap-3">
              <div class="h-10 w-10 rounded-lg bg-primary/10 dark:bg-primary/20 flex items-center justify-center text-primary dark:text-primary-400">
                <span class="material-icons-round">{{ editingInstitucion ? 'edit' : 'domain_add' }}</span>
              </div>
              {{ editingInstitucion ? 'Editar institución' : 'Nueva institución' }}
            </h3>
            <button @click="closeModal" class="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors">
              <span class="material-icons-round text-slate-400">close</span>
            </button>
          </div>
          
          <!-- Modal Body -->
          <form @submit.prevent="saveInstitucion" class="p-6 space-y-6">
            <!-- Basic Info -->
            <div>
              <h4 class="text-sm font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                <span class="material-icons-round text-slate-400 text-lg">info</span>
                Información básica
              </h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="md:col-span-2">
                  <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Nombre de la institución <span class="text-rose-500">*</span>
                  </label>
                  <input 
                    v-model="form.nombre" 
                    type="text" 
                    required 
                    class="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 px-4 py-3 text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:bg-white dark:focus:bg-slate-700 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all" 
                    placeholder="Ej: Colegio San José de la Salle"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Cod. DANE</label>
                  <input 
                    v-model="form.nit" 
                    type="text" 
                    class="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 px-4 py-3 text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:bg-white dark:focus:bg-slate-700 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all" 
                    placeholder="Ej: 123456789012"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Teléfono</label>
                  <input 
                    v-model="form.telefono" 
                    type="tel" 
                    class="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 px-4 py-3 text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:bg-white dark:focus:bg-slate-700 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all" 
                    placeholder="Ej: (601) 234-5678"
                  />
                </div>
              </div>
            </div>
            
            <!-- Contact -->
            <div>
              <h4 class="text-sm font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                <span class="material-icons-round text-slate-400 text-lg">mail</span>
                Contacto
              </h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="md:col-span-2">
                  <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Email de contacto <span class="text-rose-500">*</span>
                  </label>
                  <input 
                    v-model="form.email_contacto" 
                    type="email" 
                    required 
                    class="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 px-4 py-3 text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:bg-white dark:focus:bg-slate-700 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all" 
                    placeholder="contacto@colegio.edu.co"
                  />
                </div>
                <div class="md:col-span-2">
                  <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Dirección</label>
                  <input 
                    v-model="form.direccion" 
                    type="text" 
                    class="w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 px-4 py-3 text-slate-800 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:bg-white dark:focus:bg-slate-700 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all" 
                    placeholder="Calle 123 # 45-67, Barrio Centro"
                  />
                </div>
              </div>
            </div>
            
            <!-- Location -->
            <div>
              <h4 class="text-sm font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                <span class="material-icons-round text-slate-400 text-lg">location_on</span>
                Ubicación
              </h4>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Departamento</label>
                  <Select 
                    v-model="form.departamento" 
                    :options="departamentosOptions"
                    optionLabel="label"
                    optionValue="value"
                    placeholder="Seleccionar..."
                    class="w-full"
                    filter
                    :pt="{
                        root: { class: 'w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 text-slate-800 dark:text-white focus:ring-2 focus:ring-primary' },
                        trigger: { class: 'text-slate-500 dark:text-slate-400' },
                        panel: { class: 'bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600' },
                        item: { class: 'text-slate-700 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-600' },
                        filterInput: { class: 'w-full p-2 border border-slate-200 dark:border-slate-600 dark:bg-slate-800 dark:text-white rounded-md' }
                    }"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Municipio</label>
                  <Select 
                    v-model="form.ciudad" 
                    :options="municipiosOptions"
                    optionLabel="label"
                    optionValue="value"
                    placeholder="Seleccionar municipio..."
                    class="w-full"
                    filter
                    :loading="loadingMunicipios"
                    :disabled="!form.departamento"
                    :pt="{
                        root: { class: 'w-full rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/50 text-slate-800 dark:text-white focus:ring-2 focus:ring-primary' },
                        trigger: { class: 'text-slate-500 dark:text-slate-400' },
                        panel: { class: 'bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600' },
                        item: { class: 'text-slate-700 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-600' },
                        filterInput: { class: 'w-full p-2 border border-slate-200 dark:border-slate-600 dark:bg-slate-800 dark:text-white rounded-md' }
                    }"
                  />
                  <p v-if="!form.departamento" class="text-xs text-slate-400 mt-1">Selecciona un departamento primero</p>
                </div>
              </div>
            </div>
            
            <!-- Status Toggle -->
            <div>
              <label class="flex items-center justify-between p-4 rounded-xl border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700/30 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
                <div class="flex items-center gap-3">
                  <div class="h-10 w-10 rounded-lg bg-emerald-50 dark:bg-emerald-900/30 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                    <span class="material-icons-round">check_circle</span>
                  </div>
                  <div>
                    <p class="font-medium text-slate-800 dark:text-white">Institución activa</p>
                    <p class="text-sm text-slate-500 dark:text-slate-400">La institución podrá usar el sistema</p>
                  </div>
                </div>
                <div class="relative">
                  <input type="checkbox" v-model="form.activo" class="sr-only peer" />
                  <div class="w-11 h-6 bg-slate-300 dark:bg-slate-600 peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                </div>
              </label>
            </div>
            
            <!-- Error Message -->
            <div v-if="error" class="p-4 rounded-lg bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-900/50 text-rose-700 dark:text-rose-400 text-sm flex items-start gap-2">
              <span class="material-icons-round text-[18px] mt-0.5">error</span>
              {{ error }}
            </div>
          </form>
          
          <!-- Modal Footer -->
          <div class="sticky bottom-0 bg-slate-50 dark:bg-slate-800 px-6 py-4 border-t border-slate-100 dark:border-slate-700 flex items-center justify-end gap-3">
            <button 
              type="button"
              @click="closeModal"
              class="px-5 py-2.5 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-600 dark:text-slate-300 font-medium hover:bg-slate-100 dark:hover:bg-slate-600 transition-colors"
            >
              Cancelar
            </button>
            <button 
              @click="saveInstitucion"
              :disabled="saving"
              class="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-gradient-to-r from-primary to-indigo-600 text-white font-semibold shadow-md hover:shadow-lg transition-all disabled:opacity-50"
            >
              <span v-if="saving" class="material-icons-round animate-spin text-[18px]">refresh</span>
              <span v-else class="material-icons-round text-[18px]">save</span>
              {{ saving ? 'Guardando...' : (editingInstitucion ? 'Actualizar' : 'Crear institución') }}
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Details Modal -->
    <div v-if="showDetailsModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="fixed inset-0 bg-black/50 dark:bg-black/70 backdrop-blur-sm transition-opacity" @click="showDetailsModal = false"></div>
      <div class="flex min-h-full items-center justify-center p-4">
        <div class="relative bg-white dark:bg-slate-800 rounded-2xl shadow-xl max-w-lg w-full">
          <div class="p-6">
            <div class="flex items-center gap-4 mb-6">
              <div class="h-14 w-14 rounded-xl bg-gradient-to-br from-primary to-indigo-600 flex items-center justify-center text-white font-bold text-xl shadow-lg">
                {{ getInitials(selectedInstitucion?.nombre || '') }}
              </div>
              <div>
                <h3 class="text-xl font-bold text-slate-800 dark:text-white">{{ selectedInstitucion?.nombre }}</h3>
                <p class="text-sm text-slate-500 dark:text-slate-400">Cod. DANE: {{ selectedInstitucion?.nit || 'N/A' }}</p>
              </div>
              <button @click="showDetailsModal = false" class="ml-auto p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg">
                <span class="material-icons-round text-slate-400">close</span>
              </button>
            </div>
            
            <div class="space-y-4">
              <div class="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
                <span class="material-icons-round text-slate-400">mail</span>
                <span class="text-sm text-slate-700 dark:text-slate-300">{{ selectedInstitucion?.email_contacto }}</span>
              </div>
              <div class="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
                <span class="material-icons-round text-slate-400">phone</span>
                <span class="text-sm text-slate-700 dark:text-slate-300">{{ selectedInstitucion?.telefono || 'Sin teléfono' }}</span>
              </div>
              <div class="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
                <span class="material-icons-round text-slate-400">location_on</span>
                <span class="text-sm text-slate-700 dark:text-slate-300">{{ selectedInstitucion?.direccion || 'Sin dirección' }}</span>
              </div>
              <div class="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
                <span class="material-icons-round text-slate-400">map</span>
                <span class="text-sm text-slate-700 dark:text-slate-300">{{ selectedInstitucion?.ciudad || 'Sin ciudad' }}, {{ selectedInstitucion?.departamento || '' }}</span>
              </div>
              <div class="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
                <span class="material-icons-round text-slate-400">event</span>
                <span class="text-sm text-slate-700 dark:text-slate-300">Registrado: {{ formatDate(selectedInstitucion?.fecha_registro) }}</span>
              </div>
            </div>
            
            <div class="mt-6 flex gap-3">
              <button 
                @click="showDetailsModal = false; openEditModal(selectedInstitucion)"
                class="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-primary text-white font-medium hover:bg-indigo-600 transition-colors"
              >
                <span class="material-icons-round text-[18px]">edit</span>
                Editar
              </button>
              <button 
                @click="showDetailsModal = false"
                class="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-300 font-medium hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useAuthStore } from '../stores/auth';
import { useInstitucionesStore } from '../stores/instituciones'; // Pinia Store
import { useRouter } from 'vue-router';
import Select from 'primevue/select';

const authStore = useAuthStore();
const institucionesStore = useInstitucionesStore();
const router = useRouter();

// ─── API Colombia: Departamentos y Municipios ───
const departamentosApi = ref([]);     // [{ id, name }]
const municipiosApi = ref([]);       // [{ id, name }]
const loadingDepartamentos = ref(false);
const loadingMunicipios = ref(false);

const fetchDepartamentos = async () => {
  loadingDepartamentos.value = true;
  try {
    const res = await fetch('https://api-colombia.com/api/v1/Department');
    const data = await res.json();
    departamentosApi.value = data
      .map(d => ({ id: d.id, name: d.name }))
      .sort((a, b) => a.name.localeCompare(b.name));
  } catch (err) {
    console.error('Error cargando departamentos:', err);
  } finally {
    loadingDepartamentos.value = false;
  }
};

const fetchMunicipios = async (departmentId) => {
  if (!departmentId) { municipiosApi.value = []; return; }
  loadingMunicipios.value = true;
  try {
    const res = await fetch(`https://api-colombia.com/api/v1/Department/${departmentId}/cities`);
    const data = await res.json();
    municipiosApi.value = data
      .map(c => ({ id: c.id, name: c.name }))
      .sort((a, b) => a.name.localeCompare(b.name));
  } catch (err) {
    console.error('Error cargando municipios:', err);
    municipiosApi.value = [];
  } finally {
    loadingMunicipios.value = false;
  }
};

const departamentosOptions = computed(() => [
  { label: 'Seleccionar...', value: null },
  ...departamentosApi.value.map(d => ({ label: d.name, value: d.name, apiId: d.id }))
]);

const municipiosOptions = computed(() => [
  { label: 'Seleccionar municipio...', value: null },
  ...municipiosApi.value.map(m => ({ label: m.name, value: m.name }))
]);


// State from Store
const loading = computed(() => institucionesStore.loading);
const instituciones = computed(() => institucionesStore.institucionesList);
const error = ref(''); // Local error msg for modal

const saving = ref(false);
const searchQuery = ref('');
const filterStatus = ref(null);

// Opciones
const statusOptions = [
  { label: 'Todos los estados', value: null },
  { label: 'Activas', value: 'activo' },
  { label: 'Inactivas', value: 'inactivo' }
];

// UI State
const showModal = ref(false);
const showDetailsModal = ref(false);
const editingInstitucion = ref(null);
const selectedInstitucion = ref(null);

const form = reactive({
  nombre: '',
  nit: '',
  direccion: '',
  telefono: '',
  email_contacto: '',
  ciudad: '',
  departamento: '',
  activo: true
});

// Watcher: al cambiar departamento, cargar municipios
let _skipCiudadReset = false;
watch(() => form.departamento, (newDep) => {
  if (!_skipCiudadReset) {
    form.ciudad = ''; // Reset municipio on manual change
  }
  _skipCiudadReset = false;
  if (newDep) {
    const dep = departamentosApi.value.find(d => d.name === newDep);
    if (dep) fetchMunicipios(dep.id);
    else municipiosApi.value = [];
  } else {
    municipiosApi.value = [];
  }
});

// Computed Filters
const filteredInstituciones = computed(() => {
  let result = instituciones.value;
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(i => 
      i.nombre?.toLowerCase().includes(query) || 
      i.email_contacto?.toLowerCase().includes(query) ||
      i.ciudad?.toLowerCase().includes(query)
    );
  }
  
  if (filterStatus.value) {
    result = result.filter(i => {
      if (filterStatus.value === 'activo') return i.activo === true;
      if (filterStatus.value === 'inactivo') return i.activo === false;
      return true;
    });
  }
  
  return result;
});

const activeCount = computed(() => instituciones.value.filter(i => i.activo).length);
const inactiveCount = computed(() => instituciones.value.filter(i => !i.activo).length);
const newThisMonth = computed(() => {
  const now = new Date();
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
  return instituciones.value.filter(i => new Date(i.fecha_registro) >= startOfMonth).length;
});

// Methods
const getInitials = (name) => {
  if (!name) return '?';
  const parts = name.split(' ');
  if (parts.length >= 2) {
    return (parts[0].charAt(0) + parts[1].charAt(0)).toUpperCase();
  }
  return name.substring(0, 2).toUpperCase();
};

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' });
};

const resetForm = () => {
  form.nombre = '';
  form.nit = '';
  form.direccion = '';
  form.telefono = '';
  form.email_contacto = '';
  form.ciudad = '';
  form.departamento = '';
  form.activo = true;
  error.value = '';
};

const openCreateModal = () => {
  resetForm();
  editingInstitucion.value = null;
  showModal.value = true;
};

const openEditModal = (institucion) => {
  editingInstitucion.value = institucion;
  form.nombre = institucion.nombre;
  form.nit = institucion.nit || '';
  form.direccion = institucion.direccion || '';
  form.telefono = institucion.telefono || '';
  form.email_contacto = institucion.email_contacto;
  form.ciudad = institucion.ciudad || '';
  _skipCiudadReset = true; // Don't reset ciudad when setting departamento
  form.departamento = institucion.departamento || '';
  form.activo = institucion.activo;
  error.value = '';
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
  editingInstitucion.value = null;
  resetForm();
};

const viewDetails = (institucion) => {
  router.push(`/instituciones/${institucion.id}`);
};

const saveInstitucion = async () => {
  if (!form.nombre || !form.email_contacto) {
    error.value = 'Por favor completa los campos obligatorios.';
    return;
  }
  
  saving.value = true;
  error.value = '';
  
  try {
    if (editingInstitucion.value) {
      // Update via Store
      await institucionesStore.updateInstitucion(editingInstitucion.value.id, form);
    } else {
      // Create via Store
      await institucionesStore.createInstitucion(form);
    }
    closeModal();
  } catch (err) {
    console.error('Error saving institucion:', err);
    error.value = err.response?.data?.detail || 'Error al guardar la institución.';
  } finally {
    saving.value = false;
  }
};

const toggleStatus = async (institucion) => {
  try {
    await institucionesStore.updateInstitucion(institucion.id, { activo: !institucion.activo });
  } catch (err) {
    console.error('Error toggling status:', err);
    alert('Error al cambiar el estado de la institución.');
  }
};

// Lifecycle
onMounted(() => {
  // Load using store (only catches if needed)
  institucionesStore.fetchInstituciones();
  fetchDepartamentos();
});
</script>

<style scoped>
.font-sans {
  font-family: 'Inter', sans-serif;
}
</style>
