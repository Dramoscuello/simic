<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center p-4">
    <div class="w-full max-w-3xl bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-8">
      <!-- Header -->
      <div class="text-center mb-8">
        <div class="flex items-center justify-center gap-3 mb-4">
          <div class="w-12 h-12 bg-indigo-600 rounded-xl flex items-center justify-center">
            <img src="@/assets/logo.png" alt="SIMIC" class="w-9 h-9 object-contain" />
          </div>
          <span class="text-2xl font-bold text-slate-900 dark:text-white">SIMIC</span>
        </div>
        <h1 class="text-2xl font-bold text-slate-900 dark:text-white">Configuración inicial</h1>
        <p class="text-slate-500 dark:text-slate-400 mt-1">Paso {{ step }} de 2</p>
      </div>

      <!-- Progress -->
      <div class="flex items-center justify-between mb-8">
        <div
          v-for="s in 2"
          :key="s"
          class="flex-1 h-2 rounded-full mx-1 transition-colors"
          :class="s <= step ? 'bg-indigo-600' : 'bg-slate-200 dark:bg-slate-700'"
        />
      </div>

      <!-- Error global -->
      <div
        v-if="error"
        class="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center gap-2"
      >
        <span class="material-icons-round text-red-500">error_outline</span>
        <p class="text-red-600 dark:text-red-400 text-sm">{{ error }}</p>
      </div>

      <!-- Slide 1: Institución -->
      <div v-if="step === 1" class="space-y-5">
        <h2 class="text-lg font-semibold text-slate-800 dark:text-slate-100">Datos de la institución</h2>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div class="md:col-span-2">
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Nombre de la institución</label>
            <input v-model="form.institucion.nombre" type="text" required class="input-field" placeholder="Ej: Colegio San José" />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Código DANE (12 dígitos)</label>
            <input
              v-model="form.institucion.codigo_dane"
              type="text"
              maxlength="12"
              required
              class="input-field"
              placeholder="123456789012"
              @input="form.institucion.codigo_dane = form.institucion.codigo_dane.replace(/\D/g, '')"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">NIT</label>
            <input v-model="form.institucion.nit" type="text" required class="input-field" placeholder="900.123.456-7" />
          </div>

          <div class="md:col-span-2">
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Dirección</label>
            <input v-model="form.institucion.direccion" type="text" required class="input-field" placeholder="Calle 123 # 45-67" />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Teléfono</label>
            <input v-model="form.institucion.telefono" type="text" class="input-field" placeholder="601 123 4567" />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Email de contacto</label>
            <input v-model="form.institucion.email_contacto" type="email" required class="input-field" placeholder="contacto@institucion.edu.co" />
          </div>

          <div class="md:col-span-2 border-t border-slate-200 dark:border-slate-700 pt-5 mt-2">
            <h3 class="text-md font-medium text-slate-800 dark:text-slate-100 mb-3">Datos del Rector</h3>
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Nombre del rector</label>
            <input v-model="form.institucion.nombre_rector" type="text" required class="input-field" placeholder="Nombre completo" />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Email del rector</label>
            <input v-model="form.institucion.email_rector" type="email" required class="input-field" placeholder="rector@institucion.edu.co" />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Teléfono del rector</label>
            <input v-model="form.institucion.telefono_rector" type="text" class="input-field" placeholder="300 123 4567" />
          </div>
        </div>
      </div>

      <!-- Slide 2: Administrador -->
      <div v-if="step === 2" class="space-y-5">
        <h2 class="text-lg font-semibold text-slate-800 dark:text-slate-100">Datos del Administrador</h2>

        <label class="flex items-center gap-3 p-4 border border-slate-200 dark:border-slate-700 rounded-lg cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
          <input v-model="form.admin.es_rector" type="checkbox" class="w-5 h-5 text-indigo-600 rounded" />
          <span class="text-slate-700 dark:text-slate-300">El administrador es el mismo rector</span>
        </label>

        <div v-if="!form.admin.es_rector" class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Cargo</label>
            <input v-model="form.admin.cargo" type="text" class="input-field" placeholder="Ej: Coordinador académico" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Nombres</label>
            <input v-model="form.admin.nombres" type="text" class="input-field" placeholder="Nombres" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Apellidos</label>
            <input v-model="form.admin.apellidos" type="text" class="input-field" placeholder="Apellidos" />
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div class="md:col-span-2">
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Correo electrónico</label>
            <input
              v-model="form.admin.email"
              type="email"
              required
              class="input-field"
              :class="{ 'bg-slate-100 dark:bg-slate-600 cursor-not-allowed': form.admin.es_rector }"
              placeholder="admin@institucion.edu.co"
              :readonly="form.admin.es_rector"
            />
            <p v-if="form.admin.es_rector" class="text-xs text-indigo-600 dark:text-indigo-400 mt-1">Correo copiado del rector.</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Contraseña</label>
            <input v-model="form.admin.password" type="password" required class="input-field" placeholder="••••••••" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Confirmar contraseña</label>
            <input v-model="form.admin.password_confirm" type="password" required class="input-field" placeholder="••••••••" />
          </div>
        </div>
      </div>

      <!-- Botones -->
      <div class="flex justify-between mt-8">
        <button
          v-if="step > 1"
          type="button"
          @click="step--"
          class="px-6 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
        >
          Anterior
        </button>
        <div v-else />

        <button
          v-if="step < 2"
          type="button"
          @click="nextStep"
          class="px-6 py-2.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition-colors"
        >
          Siguiente
        </button>

        <button
          v-else
          type="button"
          @click="submit"
          :disabled="loading"
          class="px-6 py-2.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ loading ? 'Guardando...' : 'Finalizar configuración' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { createSetup } from '../api/setup'

const router = useRouter()
const step = ref(1)
const loading = ref(false)
const error = ref('')

const form = reactive({
  institucion: {
    nombre: '',
    codigo_dane: '',
    nit: '',
    direccion: '',
    telefono: '',
    email_contacto: '',
    nombre_rector: '',
    email_rector: '',
    telefono_rector: ''
  },
  admin: {
    es_rector: false,
    cargo: '',
    nombres: '',
    apellidos: '',
    email: '',
    password: '',
    password_confirm: ''
  }
})

const validateStep = () => {
  error.value = ''

  if (step.value === 1) {
    const i = form.institucion
    if (!i.nombre || !i.codigo_dane || !i.nit || !i.direccion || !i.email_contacto || !i.nombre_rector || !i.email_rector) {
      error.value = 'Por favor completa todos los campos obligatorios de la institución.'
      return false
    }
    if (i.codigo_dane.length !== 12 || !/^\d{12}$/.test(i.codigo_dane)) {
      error.value = 'El código DANE debe tener exactamente 12 dígitos numéricos.'
      return false
    }
  }

  if (step.value === 2) {
    const a = form.admin
    if (!a.es_rector && (!a.nombres || !a.apellidos)) {
      error.value = 'Por favor ingresa nombres y apellidos del administrador.'
      return false
    }
    if (!a.email || !a.password || !a.password_confirm) {
      error.value = 'Por favor completa todos los campos del administrador.'
      return false
    }
    const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/
    if (!passwordRegex.test(a.password)) {
      error.value = 'La contraseña debe tener al menos 8 caracteres, incluir letras, números y un carácter especial.'
      return false
    }
    if (a.password !== a.password_confirm) {
      error.value = 'Las contraseñas no coinciden.'
      return false
    }
  }

  return true
}

watch(
  () => form.admin.es_rector,
  (esRector) => {
    if (esRector) {
      form.admin.email = form.institucion.email_rector
    } else {
      form.admin.email = ''
    }
  }
)

watch(
  () => form.institucion.email_rector,
  (emailRector) => {
    if (form.admin.es_rector) {
      form.admin.email = emailRector
    }
  }
)

const nextStep = () => {
  if (validateStep()) {
    step.value++
  }
}

const submit = async () => {
  if (!validateStep()) return

  loading.value = true
  error.value = ''

  try {
    const payload = {
      institucion: { ...form.institucion },
      admin: { ...form.admin }
    }

    await createSetup(payload)
    router.push('/login?setup=success')
  } catch (err) {
    const msg = err.response?.data?.detail
    if (Array.isArray(msg)) {
      error.value = msg.map(e => e.msg || e).join('. ')
    } else {
      error.value = msg || 'Ocurrió un error al guardar la configuración.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.input-field {
  @apply block w-full px-4 py-2.5 rounded-lg border border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all;
}
</style>
