import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import SetupWizard from '../views/SetupWizard.vue'
import { useAuthStore } from '../stores/auth'
import { getSetupStatus } from '../api/setup'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: Login,
      meta: { requiresAuth: false }
    },
    {
      path: '/setup',
      name: 'setup',
      component: SetupWizard,
      meta: { requiresAuth: false }
    },
    // Layout Route para Vistas Protegidas (Dashboard, Listados, etc.)
    {
      path: '/',
      component: () => import('../layouts/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: '/dashboard' },
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('../views/Dashboard.vue')
        },
        {
          path: 'reportes',
          name: 'reportes',
          component: () => import('../views/ReportesDashboard.vue'),
          meta: { title: 'Panel de reportes' }
        },
        {
          path: 'reportes/historico/:tipo',
          name: 'reportes-historico',
          component: () => import('../views/ReportesHistorico.vue'),
          meta: { title: 'Histórico de reportes' }
        },
        {
          path: 'analisis',
          name: 'analisis-canvas',
          component: () => import('../views/AnalisisCanvas.vue'),
          meta: { title: 'Análisis canvas' }
        },
        {
          path: 'simulacros',
          name: 'simulacros',
          component: () => import('../views/Simulacros.vue'),
          meta: { title: 'Gestión de simulacros' }
        },
        {
          path: 'simulacros/crear',
          name: 'simulacros-crear',
          component: () => import('../views/SimulacroCreate.vue'),
          meta: { title: 'Crear nuevo simulacro' }
        },
        {
          path: 'simulacros/:id/editar',
          name: 'simulacros-editar',
          component: () => import('../views/SimulacroCreate.vue'),
          meta: { title: 'Editar simulacro' }
        },
        {
          path: 'mi-institucion',
          name: 'mi-institucion',
          component: () => import('../views/MiInstitucion.vue'),
          meta: { title: 'Mi institución' }
        },
        {
          path: 'sedes',
          name: 'sedes',
          component: () => import('../views/Sedes.vue'),
          meta: { title: 'Gestión de sedes' }
        },
        {
          path: 'estudiantes',
          name: 'estudiantes',
          component: () => import('../views/Estudiantes.vue'),
          meta: { title: 'Gestión de estudiantes' }
        },
        {
          path: 'estudiantes/:id',
          name: 'estudiante-detalle',
          component: () => import('../views/EstudianteDetalle.vue'),
          meta: { title: 'Perfil académico' }
        },

        {
          path: 'grupos',
          name: 'grupos',
          component: () => import('../views/Grupos.vue'),
          meta: { title: 'Gestión de grupos' }
        },
        {
          path: 'mensajeria',
          name: 'mensajeria',
          component: () => import('../views/Mensajeria.vue'),
          meta: { title: 'Mensajería interna' }
        },
        {
          path: 'revisiones',
          name: 'revisiones',
          component: () => import('../views/ReviewsView.vue'),
          meta: { title: 'Revisión de preguntas' }
        },
        {
          path: 'inspeccion',
          name: 'inspeccion',
          component: () => import('../views/admin/InspeccionSimulacros.vue'),
          meta: { title: 'Inspección de fraude' }
        },
        {
          path: 'crear-usuario',
          name: 'crear-usuario',
          component: () => import('../views/CrearUsuario.vue'),
          meta: { title: 'Gestión de usuarios' }
        },
        {
          path: 'perfil',
          name: 'perfil-usuario',
          component: () => import('../views/ProfileView.vue'),
          meta: { title: 'Mi perfil' }
        },
        // Agrega aquí otras rutas que necesiten Sidebar/Header (Estudiantes, Grupos, Config...)
      ]
    },
    // Rutas "Standalone" (Sin Sidebar/Header) - Ejemplo: Tomar Examen
    // Flujo de Examen
    {
      path: '/simulacros/:id',
      name: 'simulacros-instrucciones',
      component: () => import('../views/SimulacroInstrucciones.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/simulacros/:id/presentar',
      name: 'simulacros-runner',
      component: () => import('../views/SimulacroRunner.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/simulacros/:id/finalizado',
      name: 'simulacros-finalizado',
      component: () => import('../views/SimulacroMensajeFinal.vue'),
      meta: { requiresAuth: true }
    },
    // Revisión de Resultados
    {
      path: '/simulacros/:id/revision',
      name: 'simulacros-revision',
      component: () => import('../views/SimulacroRunner.vue'),
      meta: { requiresAuth: true, mode: 'review' }
    },
    // Catch-all
    { path: '/:pathMatch(.*)*', redirect: '/dashboard' }
  ],
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  // Asegurarse de que el token se lee del storage si se refresca la página
  if (!authStore.token && localStorage.getItem('token')) {
    authStore.token = localStorage.getItem('token');
  }

  // Verificar estado de configuración inicial (solo rutas públicas)
  if (!to.matched.some(record => record.meta.requiresAuth)) {
    try {
      const { data } = await getSetupStatus();
      const needsSetup = data.needs_setup;

      if (needsSetup && to.path !== '/setup') {
        next('/setup');
        return;
      }
      if (!needsSetup && to.path === '/setup') {
        next('/login');
        return;
      }
    } catch (e) {
      // Si falla el check, permitir navegación
    }
  }

  // Verificar autenticación
  // Nota: Al usar rutas anidadas, 'meta.requiresAuth' puede estar en el padre o en el hijo.
  // matched.some verifica toda la cadena.
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!authStore.isAuthenticated) {
      next('/login');
      return;
    }
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/dashboard');
    return;
  }

  next();
})

export default router
