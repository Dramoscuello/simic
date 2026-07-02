<template>
  <aside class="flex w-64 flex-col bg-gradient-to-b from-[#1e1b4b] to-[#312e81] text-white transition-all duration-300 h-full">
    <!-- Logo Area -->
    <div class="flex h-16 items-center justify-between px-6 py-4 border-b border-white/10">
      <div class="flex items-center gap-3">
        <div class="flex flex-col">
          <h1 class="text-xl font-bold leading-none tracking-tight">SIMIC</h1>
          <span v-if="subtitle" class="text-xs text-indigo-200 font-medium">{{ subtitle }}</span>
        </div>
      </div>
      
      <!-- Close Button (Mobile Only) -->
      <button 
        @click="$emit('close-mobile')" 
        class="lg:hidden p-1 rounded-md text-indigo-200 hover:text-white hover:bg-white/10 transition-colors"
      >
        <span class="material-icons-round">close</span>
      </button>
    </div>
    
    <!-- Institution Info (only for Admin IE) -->
    <div v-if="institutionName" class="px-6 py-4 border-b border-white/10">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-full bg-white/10 flex items-center justify-center">
          <span class="material-icons-round text-indigo-200 text-lg">domain</span>
        </div>
        <div class="flex flex-col overflow-hidden">
          <span class="text-sm font-medium text-white truncate">{{ institutionName }}</span>
          <span class="text-xs text-indigo-200">Institución</span>
        </div>
      </div>
    </div>
    
    <!-- Navigation -->
    <div class="flex-1 overflow-y-auto py-6 px-4 flex flex-col gap-6">
      <!-- Dynamic Navigation Groups -->
      <div v-for="group in navigationGroups" :key="group.title">
        <p class="mb-2 px-2 text-xs font-bold uppercase tracking-wider text-indigo-300">{{ group.title }}</p>
        <div class="flex flex-col gap-1">
          <router-link 
            v-for="item in group.items" 
            :key="item.to"
            :to="item.to"
            :class="[
              'sidebar-link flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
              isActive(item.to) 
                ? 'bg-white/10 text-white shadow-sm ring-1 ring-white/10' 
                : 'text-indigo-100 hover:text-white hover:bg-white/10'
            ]"
          >
            <span class="material-icons-round text-[20px]">{{ item.icon }}</span>
            {{ item.label }}
          </router-link>
        </div>
      </div>
    </div>
    
    <!-- User Profile (Bottom Sidebar) -->
    <div class="border-t border-white/10 p-4">
      <div class="flex items-center gap-3 rounded-lg bg-black/20 p-3 hover:bg-black/30 cursor-pointer transition-colors">
        <div class="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-500 text-white font-bold text-sm border border-indigo-300">
          {{ userInitials }}
        </div>
        <div class="flex flex-col overflow-hidden flex-1">
          <span class="truncate text-sm font-semibold text-white">{{ userName }}</span>
          <span class="truncate text-xs text-indigo-200">{{ userRole }}</span>
        </div>
        <button @click="$emit('logout')" class="p-1 hover:bg-white/10 rounded transition-colors" title="Cerrar sesión">
          <span class="material-icons-round text-indigo-200 hover:text-white text-[20px]">logout</span>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();

const props = defineProps({
  subtitle: {
    type: String,
    default: ''
  },
  institutionName: {
    type: String,
    default: ''
  },
  userName: {
    type: String,
    required: true
  },
  userRole: {
    type: String,
    required: true
  },
  navigationGroups: {
    type: Array,
    required: true
  }
});

defineEmits(['logout', 'close-mobile']);

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
  if (typeof path === 'string' && path.includes('?')) {
    // Si el link tiene query params, requerimos coincidencia exacta (o al menos que incluya ese query)
    // Simplificación: comparamos con fullPath para este caso específico de tabs
    return route.fullPath === path || route.fullPath.startsWith(path + '&');
  }
  // Comportamiento standard para rutas sin query
  return route.path === path || (route.path.startsWith(path + '/') && path !== '/');
};
</script>

<style scoped>
.sidebar-link:hover {
  background-color: rgba(255, 255, 255, 0.1);
}
</style>
