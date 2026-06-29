<script setup>
import { RouterView } from 'vue-router'
import ConfirmDialog from 'primevue/confirmdialog';
</script>

<template>
  <ConfirmDialog />
  <RouterView />
</template>

<style>
/* Estilos globales mínimos si son necesarios, pero Tailwind maneja la mayoría */
</style>
