<template>
  <div class="w-full max-w-5xl mx-auto space-y-8">
    <Toast />
    <h1 v-if="!embedded" class="text-2xl font-bold text-slate-800 dark:text-white">Gestión de sedes</h1>

    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-slate-800 dark:text-slate-100">Sedes de la institución</h2>
        <button @click="openModal()" class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm">
          + Agregar sede
        </button>
      </div>

      <div v-if="loading" class="text-slate-500">Cargando sedes...</div>
      <div v-else-if="sedes.length === 0" class="text-slate-500">No hay sedes registradas.</div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-left text-sm">
          <thead>
            <tr class="border-b border-slate-200 dark:border-slate-700">
              <th class="py-2">Nombre</th>
              <th class="py-2">Dirección</th>
              <th class="py-2">Teléfono</th>
              <th class="py-2 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in sedes" :key="s.id" class="border-b border-slate-100 dark:border-slate-700">
              <td class="py-3 font-medium">{{ s.nombre }}</td>
              <td class="py-3 text-slate-600 dark:text-slate-400">{{ s.direccion || '—' }}</td>
              <td class="py-3 text-slate-600 dark:text-slate-400">{{ s.telefono || '—' }}</td>
              <td class="py-3 text-right space-x-2">
                <button @click="openModal(s)" class="text-indigo-600 hover:text-indigo-800 text-sm">Editar</button>
                <button @click="eliminar(s.id)" class="text-red-500 hover:text-red-700 text-sm">Eliminar</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
      <div class="bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-md p-6">
        <h3 class="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-4">
          {{ editing ? 'Editar sede' : 'Agregar sede' }}
        </h3>
        <form @submit.prevent="guardar" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Nombre</label>
            <input v-model="form.nombre" type="text" required class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Dirección</label>
            <input v-model="form.direccion" type="text" class="input-field" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Teléfono</label>
            <input v-model="form.telefono" type="text" class="input-field" />
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="showModal = false" class="px-4 py-2 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-50">Cancelar</button>
            <button type="submit" :disabled="saving" class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50">
              {{ saving ? 'Guardando...' : 'Guardar' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import Toast from 'primevue/toast';
import { useToast } from 'primevue/usetoast';
import { useConfirm } from 'primevue/useconfirm';
import api from '../api/axios'

const props = defineProps({
  embedded: { type: Boolean, default: false }
})

const sedes = ref([])
const loading = ref(false)
const showModal = ref(false)
const saving = ref(false)
const editing = ref(null)
const toast = useToast()
const confirm = useConfirm()

const form = reactive({
  nombre: '',
  direccion: '',
  telefono: ''
})

const fetchSedes = async () => {
  loading.value = true
  try {
    const { data } = await api.get('/sedes/')
    sedes.value = Array.isArray(data) ? data : []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const openModal = (sede = null) => {
  editing.value = sede
  if (sede) {
    Object.assign(form, {
      nombre: sede.nombre,
      direccion: sede.direccion || '',
      telefono: sede.telefono || ''
    })
  } else {
    Object.assign(form, { nombre: '', direccion: '', telefono: '' })
  }
  showModal.value = true
}

const guardar = async () => {
  saving.value = true
  try {
    if (editing.value) {
      await api.put(`/sedes/${editing.value.id}`, { ...form })
    } else {
      await api.post('/sedes/', { ...form })
    }
    showModal.value = false
    await fetchSedes()
  } catch (e) {
    console.error(e)
  } finally {
    saving.value = false
  }
}

const eliminar = (id) => {
  confirm.require({
    message: '¿Eliminar esta sede?',
    header: 'Confirmar eliminación',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Eliminar',
    rejectLabel: 'Cancelar',
    acceptProps: { severity: 'danger' },
    accept: async () => {
      try {
        await api.delete(`/sedes/${id}`)
        await fetchSedes()
      } catch (e) {
        console.error(e)
        toast.add({ severity: 'error', summary: 'Error', detail: 'No se pudo eliminar la sede', life: 5000 })
      }
    }
  })
}

onMounted(() => {
  fetchSedes()
})
</script>

<style scoped>
.input-field {
  @apply block w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all;
}
</style>
