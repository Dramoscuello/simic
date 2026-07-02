<template>
  <div class="font-sans bg-slate-50 text-slate-800 antialiased overflow-hidden">
    <div class="flex h-screen w-full">
      <!-- Sidebar -->
      <AppSidebar
        subtitle="Admin institución"
        :institutionName="institutionName"
        :userName="userName"
        userRole="Coordinador"
        :navigationGroups="navigationGroups"
        @logout="logout"
      />
      
      <!-- Main Content -->
      <main class="flex h-full flex-1 flex-col overflow-hidden bg-slate-50">
        <!-- Header -->
        <AppHeader
          title="Dashboard institucional"
          :userName="userName"
          searchPlaceholder="Buscar estudiantes, grupos..."
          :notificationCount="2"
        />
        
        <!-- Scrollable Content -->
        <div class="flex-1 overflow-y-auto p-8">
          <div class="mx-auto flex w-full max-w-7xl flex-col gap-8">
            <!-- Simulacro Selector -->
            <div class="flex items-center justify-between">
              <div>
                <h2 class="text-2xl font-bold text-slate-800">Simulacro ICFES - Enero 2026</h2>
                <p class="text-slate-500">Resultados consolidados de tu institución</p>
              </div>
              <div class="flex items-center gap-3">
                <select class="rounded-lg border-slate-200 bg-white text-sm text-slate-600 py-2 px-4 focus:ring-primary focus:border-primary shadow-sm">
                  <option>Simulacro Enero 2026</option>
                  <option>Simulacro Octubre 2025</option>
                </select>
                <button class="flex items-center gap-2 bg-primary hover:bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-semibold shadow-md transition-all">
                  <span class="material-icons-round text-[18px]">download</span>
                  Exportar Excel
                </button>
              </div>
            </div>
            
            <!-- KPI Cards -->
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <!-- Card 1 -->
              <div class="relative overflow-hidden rounded-xl bg-white p-5 shadow-sm border border-slate-100 group hover:shadow-md transition-all">
                <div class="flex items-start justify-between">
                  <div>
                    <p class="text-sm font-medium text-slate-500">Estudiantes evaluados</p>
                    <h3 class="mt-2 text-3xl font-bold text-slate-800">127 <span class="text-lg text-slate-400 font-normal">/ 150</span></h3>
                  </div>
                  <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                    <span class="material-icons-round">groups</span>
                  </div>
                </div>
                <div class="mt-4">
                  <div class="w-full bg-slate-100 rounded-full h-2">
                    <div class="bg-blue-500 h-2 rounded-full" style="width: 85%"></div>
                  </div>
                  <p class="text-xs text-slate-400 mt-1">85% de cobertura</p>
                </div>
              </div>
              
              <!-- Card 2 -->
              <div class="relative overflow-hidden rounded-xl bg-white p-5 shadow-sm border border-slate-100 group hover:shadow-md transition-all">
                <div class="flex items-start justify-between">
                  <div>
                    <p class="text-sm font-medium text-slate-500">Promedio general</p>
                    <h3 class="mt-2 text-3xl font-bold text-slate-800">68.5%</h3>
                  </div>
                  <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-50 text-purple-600">
                    <span class="material-icons-round">analytics</span>
                  </div>
                </div>
                <div class="mt-4 flex items-center gap-1 text-sm">
                  <span class="flex items-center font-medium text-emerald-600">
                    <span class="material-icons-round text-[16px] mr-0.5">trending_up</span>
                    +3.2%
                  </span>
                  <span class="text-slate-400">vs simulacro anterior</span>
                </div>
              </div>
              
              <!-- Card 3: Best Area -->
              <div class="relative overflow-hidden rounded-xl bg-white p-5 shadow-sm border border-slate-100 group hover:shadow-md transition-all">
                <div class="flex items-start justify-between">
                  <div>
                    <p class="text-sm font-medium text-slate-500">Mejor área</p>
                    <h3 class="mt-2 text-2xl font-bold text-slate-800">Matemáticas</h3>
                  </div>
                  <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
                    <span class="material-icons-round">emoji_events</span>
                  </div>
                </div>
                <div class="mt-4 flex items-center gap-2">
                  <div class="flex-1 bg-slate-100 rounded-full h-2">
                    <div class="bg-emerald-500 h-2 rounded-full" style="width: 75%"></div>
                  </div>
                  <span class="text-sm font-bold text-emerald-600">75%</span>
                </div>
              </div>
              
              <!-- Card 4: Weak Area -->
              <div class="relative overflow-hidden rounded-xl bg-white p-5 shadow-sm border border-slate-100 group hover:shadow-md transition-all">
                <div class="flex items-start justify-between">
                  <div>
                    <p class="text-sm font-medium text-slate-500">Área a reforzar</p>
                    <h3 class="mt-2 text-2xl font-bold text-slate-800">Ciencias Nat.</h3>
                  </div>
                  <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-50 text-amber-600">
                    <span class="material-icons-round">warning</span>
                  </div>
                </div>
                <div class="mt-4 flex items-center gap-2">
                  <div class="flex-1 bg-slate-100 rounded-full h-2">
                    <div class="bg-amber-500 h-2 rounded-full" style="width: 52%"></div>
                  </div>
                  <span class="text-sm font-bold text-amber-600">52%</span>
                </div>
              </div>
            </div>
            
            <!-- Charts Section -->
            <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
              <!-- Performance by Area -->
              <div class="lg:col-span-2 rounded-xl bg-white p-6 shadow-sm border border-slate-100">
                <div class="mb-6 flex items-center justify-between">
                  <h3 class="text-lg font-bold text-slate-800">Desempeño por área</h3>
                  <button class="text-primary hover:text-indigo-700 text-sm font-medium flex items-center gap-1">
                    Ver detalle <span class="material-icons-round text-sm">arrow_forward</span>
                  </button>
                </div>
                <div class="space-y-5">
                  <div>
                    <div class="flex justify-between text-sm mb-1.5">
                      <span class="font-medium text-slate-700">Matemáticas</span>
                      <span class="font-bold text-slate-900">75%</span>
                    </div>
                    <div class="w-full bg-slate-100 rounded-full h-3">
                      <div class="bg-emerald-500 h-3 rounded-full" style="width: 75%"></div>
                    </div>
                  </div>
                  <div>
                    <div class="flex justify-between text-sm mb-1.5">
                      <span class="font-medium text-slate-700">Lectura Crítica</span>
                      <span class="font-bold text-slate-900">70%</span>
                    </div>
                    <div class="w-full bg-slate-100 rounded-full h-3">
                      <div class="bg-emerald-500 h-3 rounded-full" style="width: 70%"></div>
                    </div>
                  </div>
                  <div>
                    <div class="flex justify-between text-sm mb-1.5">
                      <span class="font-medium text-slate-700">Inglés</span>
                      <span class="font-bold text-slate-900">65%</span>
                    </div>
                    <div class="w-full bg-slate-100 rounded-full h-3">
                      <div class="bg-primary h-3 rounded-full" style="width: 65%"></div>
                    </div>
                  </div>
                  <div>
                    <div class="flex justify-between text-sm mb-1.5">
                      <span class="font-medium text-slate-700">Sociales y Ciudadanas</span>
                      <span class="font-bold text-slate-900">58%</span>
                    </div>
                    <div class="w-full bg-slate-100 rounded-full h-3">
                      <div class="bg-amber-400 h-3 rounded-full" style="width: 58%"></div>
                    </div>
                  </div>
                  <div>
                    <div class="flex justify-between text-sm mb-1.5">
                      <span class="font-medium text-slate-700">Ciencias Naturales</span>
                      <span class="font-bold text-slate-900">52%</span>
                    </div>
                    <div class="w-full bg-slate-100 rounded-full h-3">
                      <div class="bg-rose-500 h-3 rounded-full" style="width: 52%"></div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Distribution -->
              <div class="rounded-xl bg-white p-6 shadow-sm border border-slate-100">
                <h3 class="text-lg font-bold text-slate-800 mb-4">Distribución de niveles</h3>
                <div class="flex items-center justify-center py-6">
                  <div class="relative w-40 h-40">
                    <div class="w-full h-full rounded-full" style="background: conic-gradient(#10b981 0% 15%, #6366f1 15% 60%, #fbbf24 60% 85%, #ef4444 85% 100%);"></div>
                    <div class="absolute inset-4 bg-white rounded-full flex flex-col items-center justify-center shadow-inner">
                      <span class="text-2xl font-bold text-slate-800">127</span>
                      <span class="text-xs text-slate-400">Estudiantes</span>
                    </div>
                  </div>
                </div>
                <div class="grid grid-cols-2 gap-3 text-sm">
                  <div class="flex items-center gap-2">
                    <span class="w-3 h-3 rounded-full bg-emerald-500"></span>
                    <span class="text-slate-600">Avanzado (15%)</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <span class="w-3 h-3 rounded-full bg-primary"></span>
                    <span class="text-slate-600">Satisfactorio (45%)</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <span class="w-3 h-3 rounded-full bg-amber-400"></span>
                    <span class="text-slate-600">Mínimo (25%)</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <span class="w-3 h-3 rounded-full bg-rose-500"></span>
                    <span class="text-slate-600">Insuficiente (15%)</span>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Tables Section -->
            <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <!-- Group Performance -->
              <div class="rounded-xl bg-white shadow-sm border border-slate-100 overflow-hidden">
                <div class="p-6 border-b border-slate-100 flex justify-between items-center">
                  <h3 class="text-lg font-bold text-slate-800">Rendimiento por grupo</h3>
                  <span class="material-icons-round text-slate-400 cursor-pointer hover:text-slate-600">more_horiz</span>
                </div>
                <div class="overflow-x-auto">
                  <table class="w-full text-sm text-left">
                    <thead class="bg-slate-50 text-slate-500 font-medium">
                      <tr>
                        <th class="px-6 py-3">Grupo</th>
                        <th class="px-6 py-3 text-center">Estudiantes</th>
                        <th class="px-6 py-3 text-center">Promedio</th>
                        <th class="px-6 py-3 text-right">Nivel</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                      <tr class="hover:bg-slate-50 transition-colors">
                        <td class="px-6 py-4 font-medium text-slate-900">11°A</td>
                        <td class="px-6 py-4 text-slate-600 text-center">32</td>
                        <td class="px-6 py-4 font-bold text-primary text-center">72%</td>
                        <td class="px-6 py-4 text-right">
                          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">Alto</span>
                        </td>
                      </tr>
                      <tr class="hover:bg-slate-50 transition-colors">
                        <td class="px-6 py-4 font-medium text-slate-900">11°B</td>
                        <td class="px-6 py-4 text-slate-600 text-center">30</td>
                        <td class="px-6 py-4 font-bold text-amber-600 text-center">65%</td>
                        <td class="px-6 py-4 text-right">
                          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">Medio</span>
                        </td>
                      </tr>
                      <tr class="hover:bg-slate-50 transition-colors">
                        <td class="px-6 py-4 font-medium text-slate-900">11°C</td>
                        <td class="px-6 py-4 text-slate-600 text-center">28</td>
                        <td class="px-6 py-4 font-bold text-rose-500 text-center">58%</td>
                        <td class="px-6 py-4 text-right">
                          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-100 text-rose-800">Bajo</span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
              
              <!-- Top Students -->
              <div class="rounded-xl bg-white shadow-sm border border-slate-100">
                <div class="p-6 border-b border-slate-100 flex justify-between items-center">
                  <h3 class="text-lg font-bold text-slate-800">Top 5 estudiantes</h3>
                  <a class="text-sm text-primary hover:underline" href="#">Ver todos</a>
                </div>
                <div class="p-4 space-y-2">
                  <div class="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 transition-colors">
                    <div class="flex items-center gap-4">
                      <div class="w-8 h-8 flex items-center justify-center rounded-full bg-yellow-100 text-yellow-700 font-bold text-sm border border-yellow-200">1</div>
                      <div>
                        <p class="font-semibold text-slate-900 text-sm">Sofía Martínez</p>
                        <p class="text-xs text-slate-500">11°A</p>
                      </div>
                    </div>
                    <div class="text-right">
                      <p class="font-bold text-slate-900">98/100</p>
                      <p class="text-xs text-emerald-500 font-medium">Sobresaliente</p>
                    </div>
                  </div>
                  <div class="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 transition-colors">
                    <div class="flex items-center gap-4">
                      <div class="w-8 h-8 flex items-center justify-center rounded-full bg-slate-200 text-slate-700 font-bold text-sm">2</div>
                      <div>
                        <p class="font-semibold text-slate-900 text-sm">Lucas Ramírez</p>
                        <p class="text-xs text-slate-500">11°B</p>
                      </div>
                    </div>
                    <div class="text-right">
                      <p class="font-bold text-slate-900">95/100</p>
                      <p class="text-xs text-emerald-500 font-medium">Sobresaliente</p>
                    </div>
                  </div>
                  <div class="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 transition-colors">
                    <div class="flex items-center gap-4">
                      <div class="w-8 h-8 flex items-center justify-center rounded-full bg-orange-100 text-orange-700 font-bold text-sm border border-orange-200">3</div>
                      <div>
                        <p class="font-semibold text-slate-900 text-sm">Valentina Castro</p>
                        <p class="text-xs text-slate-500">11°A</p>
                      </div>
                    </div>
                    <div class="text-right">
                      <p class="font-bold text-slate-900">93/100</p>
                      <p class="text-xs text-primary font-medium">Excelente</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Quick Actions Row -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <!-- Competencies -->
              <div class="lg:col-span-2 rounded-xl bg-white p-6 shadow-sm border border-slate-100">
                <h3 class="text-lg font-bold text-slate-800 mb-4">Competencias a fortalecer</h3>
                <div class="flex flex-wrap gap-3">
                  <span class="px-4 py-2 rounded-lg bg-rose-50 text-rose-700 text-sm font-medium border border-rose-100">Uso comprensivo del conocimiento científico</span>
                  <span class="px-4 py-2 rounded-lg bg-amber-50 text-amber-700 text-sm font-medium border border-amber-100">Formulación de hipótesis</span>
                  <span class="px-4 py-2 rounded-lg bg-amber-50 text-amber-700 text-sm font-medium border border-amber-100">Interpretación de gráficas</span>
                  <span class="px-4 py-2 rounded-lg bg-slate-50 text-slate-600 text-sm font-medium border border-slate-200">Razonamiento cuantitativo</span>
                </div>
              </div>
              
              <!-- Actions -->
              <div class="rounded-xl bg-gradient-to-br from-primary to-indigo-600 p-6 shadow-lg text-white">
                <h3 class="text-lg font-bold mb-4">Acciones rápidas</h3>
                <div class="space-y-3">
                  <button class="w-full bg-white/10 hover:bg-white/20 border border-white/20 px-4 py-3 rounded-lg flex items-center gap-3 transition-colors text-sm font-medium">
                    <span class="material-icons-round">description</span>
                    Generar informe grupal
                  </button>
                  <button class="w-full bg-white text-primary hover:bg-slate-50 px-4 py-3 rounded-lg flex items-center gap-3 transition-colors text-sm font-bold shadow-md">
                    <span class="material-icons-round">print</span>
                    Imprimir boletín
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useAuthStore } from '../stores/auth';
import { useRouter } from 'vue-router';
import AppSidebar from '../components/layout/AppSidebar.vue';
import AppHeader from '../components/layout/AppHeader.vue';

const authStore = useAuthStore();
const router = useRouter();

// User info
const userName = computed(() => {
  return authStore.user?.nombre || authStore.user?.email || 'Usuario';
});

const institutionName = 'Colegio San José'; // TODO: Get from auth store

// Navigation for Admin IE
const navigationGroups = [
  {
    title: 'General',
    items: [
      { to: '/admin/dashboard', icon: 'dashboard', label: 'Dashboard' },
      { to: '/admin/reportes', icon: 'bar_chart', label: 'Reportes' }
    ]
  },
  {
    title: 'Principal',
    items: [
      { to: '/admin/simulacros', icon: 'assignment', label: 'Simulacros' },
      { to: '/admin/inspeccion', icon: 'security', label: 'Inspección' },
      { to: '/admin/estudiantes', icon: 'groups', label: 'Estudiantes' },
      { to: '/admin/grupos', icon: 'class', label: 'Grupos' }
    ]
  },
  {
    title: 'Sistema',
    items: [
      { to: '/admin/configuracion', icon: 'settings', label: 'Configuración' }
    ]
  }
];

const logout = () => {
  authStore.logout();
  router.push('/login');
};
</script>

<style scoped>
.font-sans {
  font-family: 'Inter', sans-serif;
}

.bg-primary {
  background-color: #6366f1;
}

.text-primary {
  color: #6366f1;
}
</style>
