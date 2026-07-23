<script setup>
import { RouterView } from 'vue-router'
import ConfirmDialog from 'primevue/confirmdialog';
</script>

<template>
  <ConfirmDialog :pt="{ root: { class: 'w-[90vw] md:w-[50vw] max-w-2xl' } }" />
  <RouterView />
</template>

<style>
/* Estilos globales mínimos si son necesarios, pero Tailwind maneja la mayoría */
</style>
