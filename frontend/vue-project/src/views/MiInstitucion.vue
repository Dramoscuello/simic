<template>
  <div class="w-full max-w-5xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold text-slate-800 dark:text-white">Mi institución</h1>

    <!-- Tabs -->
    <div class="border-b border-slate-200 dark:border-slate-700">
      <nav class="flex gap-6" aria-label="Tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          @click="activeTab = tab.key"
          :class="[
            'pb-3 text-sm font-medium transition-colors border-b-2',
            activeTab === tab.key
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
          ]"
        >
          {{ tab.label }}
        </button>
      </nav>
    </div>

    <!-- Tab: Información general -->
    <div v-if="activeTab === 'info'" class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
      <h2 class="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-4">Información general</h2>
      <div v-if="loadingInstitucion" class="text-slate-500">Cargando...</div>
      <form v-else @submit.prevent="saveInstitucion" class="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Nombre</label>
          <input v-model="institucionForm.nombre" type="text" required class="input-field" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Código DANE</label>
          <input v-model="institucionForm.codigo_dane" type="text" disabled class="input-field bg-slate-100 dark:bg-slate-700" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">NIT</label>
          <input v-model="institucionForm.nit" type="text" class="input-field" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Dirección</label>
          <input v-model="institucionForm.direccion" type="text" class="input-field" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Teléfono</label>
          <input v-model="institucionForm.telefono" type="text" class="input-field" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Email de contacto</label>
          <input v-model="institucionForm.email_contacto" type="email" required class="input-field" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Nombre del rector</label>
          <input v-model="institucionForm.nombre_rector" type="text" required class="input-field" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Email del rector</label>
          <input v-model="institucionForm.email_rector" type="email" required class="input-field" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Teléfono del rector</label>
          <input v-model="institucionForm.telefono_rector" type="text" class="input-field" />
        </div>
        <div class="md:col-span-2 flex justify-end">
          <button
            type="submit"
            :disabled="savingInstitucion"
            class="px-6 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            {{ savingInstitucion ? 'Guardando...' : 'Guardar cambios' }}
          </button>
        </div>
      </form>
    </div>

    <!-- Tab: Sedes -->
    <div v-else-if="activeTab === 'sedes'">
      <Sedes embedded />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useInstitucionesStore } from '../stores/instituciones'
import Sedes from './Sedes.vue'

const authStore = useAuthStore()
const institucionesStore = useInstitucionesStore()

const institucionId = ref(authStore.user?.institucion_id)
const loadingInstitucion = ref(false)
const savingInstitucion = ref(false)
const activeTab = ref('info')

const tabs = [
  { key: 'info', label: 'Información general' },
  { key: 'sedes', label: 'Sedes' }
]

const institucionForm = reactive({
  nombre: '',
  codigo_dane: '',
  nit: '',
  direccion: '',
  telefono: '',
  email_contacto: '',
  nombre_rector: '',
  email_rector: '',
  telefono_rector: ''
})

const fetchInstitucion = async () => {
  if (!institucionId.value) return
  loadingInstitucion.value = true
  try {
    const data = await institucionesStore.fetchInstitucion(institucionId.value)
    Object.assign(institucionForm, data)
  } catch (e) {
    console.error(e)
  } finally {
    loadingInstitucion.value = false
  }
}

const saveInstitucion = async () => {
  if (!institucionId.value) return
  savingInstitucion.value = true
  try {
    await institucionesStore.updateInstitucion(institucionId.value, { ...institucionForm })
    await authStore.fetchUser()
  } catch (e) {
    console.error(e)
  } finally {
    savingInstitucion.value = false
  }
}

onMounted(() => {
  fetchInstitucion()
})
</script>

<style scoped>
.input-field {
  @apply block w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all;
}
</style>
