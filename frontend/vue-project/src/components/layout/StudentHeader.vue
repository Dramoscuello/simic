<template>
  <header class="bg-white border-b border-slate-100 sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <!-- Logo -->
      <div class="flex items-center gap-3">
        <div class="size-9 bg-primary/10 rounded-lg flex items-center justify-center overflow-hidden">
          <img src="@/assets/logo.png" alt="SIMIC Logo" class="w-7 h-7 object-contain" />
        </div>
        <span class="font-bold text-xl tracking-tight text-slate-800">SIMIC</span>
      </div>
      
      <!-- Navigation -->
      <nav class="hidden md:flex space-x-1">
        <router-link
          v-for="item in navigationItems"
          :key="item.to"
          :to="item.to"
          :class="[
            'px-4 py-2 text-sm font-medium rounded-full transition-colors flex items-center gap-2',
            isActive(item.to)
              ? 'text-primary bg-primary/10'
              : 'text-slate-500 hover:text-slate-800 hover:bg-slate-50'
          ]"
        >
          <span v-if="item.icon && isActive(item.to)" class="material-symbols-outlined filled text-[18px]">{{ item.icon }}</span>
          <span v-else-if="item.icon" class="material-symbols-outlined text-[18px]">{{ item.icon }}</span>
          {{ item.label }}
        </router-link>
      </nav>
      
      <!-- User Section -->
      <div class="flex items-center gap-3 pl-4 border-l border-slate-100">
        <div class="flex flex-col items-end hidden sm:block">
          <span class="text-sm font-semibold text-slate-700">{{ userName }}</span>
          <span class="text-xs text-slate-400">{{ userGrade }}</span>
        </div>
        <div class="size-9 rounded-full bg-gradient-to-br from-primary to-purple-600 p-[2px] cursor-pointer shadow-sm hover:shadow-md transition-shadow">
          <div class="w-full h-full rounded-full bg-white flex items-center justify-center overflow-hidden">
            <span class="text-primary font-bold text-sm">{{ userInitials }}</span>
          </div>
        </div>
        <button @click="$emit('logout')" class="p-2 hover:bg-slate-100 rounded-full transition-colors" title="Cerrar sesión">
          <span class="material-icons-round text-slate-400 hover:text-slate-600 text-[20px]">logout</span>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();

const props = defineProps({
  userName: {
    type: String,
    required: true
  },
  userGrade: {
    type: String,
    default: 'Estudiante'
  },
  navigationItems: {
    type: Array,
    default: () => [
      { to: '/estudiante/dashboard', label: 'Mi progreso', icon: 'analytics' },
      { to: '/estudiante/simulacros', label: 'Mis simulacros', icon: 'assignment' },
      { to: '/estudiante/recursos', label: 'Recursos', icon: 'menu_book' }
    ]
  }
});

defineEmits(['logout']);

const userInitials = computed(() => {
  const name = props.userName;
  if (name.includes('@')) {
    return name.charAt(0).toUpperCase();
  }
  const parts = name.split(' ');
  if (parts.length >= 2) {
    return (parts[0].charAt(0) + parts[1].charAt(0)).toUpperCase();
  }
  return name.substring(0, 2).toUpperCase();
});

const isActive = (path) => {
  return route.path === path || route.path.startsWith(path);
};
</script>

<style scoped>
.bg-primary\/10 {
  background-color: rgba(99, 102, 241, 0.1);
}
</style>
