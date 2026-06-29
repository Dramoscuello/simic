<template>
  <div class="mx-auto flex w-full max-w-[1800px] flex-col gap-6">
    <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <h2 class="text-2xl font-bold text-slate-800 dark:text-white">Análisis matriz</h2>
      </div>

      <div class="flex flex-col items-stretch gap-2 sm:flex-row sm:items-center">
        <Select
          v-model="selectedGroupId"
          :options="groups"
          optionLabel="label"
          optionValue="id"
          placeholder="Selecciona un grupo"
          filter
          filterPlaceholder="Buscar grupo..."
          class="w-[320px]"
          :disabled="loadingGroups || loadingMatrix"
          :pt="canvasSelectPt"
          @change="onGroupChange"
        >
          <template #option="slotProps">
            <div>{{ slotProps.option.label }} — {{ slotProps.option.meta?.sede_nombre || 'Sin sede' }}</div>
          </template>
          <template #value="slotProps">
            <div v-if="slotProps.value" class="text-sm text-slate-700 dark:text-slate-100">
              {{ getGroupLabel(slotProps.value) }}
            </div>
            <span v-else class="text-sm text-slate-400 dark:text-slate-500">Selecciona un grupo</span>
          </template>
        </Select>

        <input
          v-model="searchQuery"
          type="text"
          class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          placeholder="Buscar estudiante por nombre o documento"
          :disabled="loadingMatrix"
        >

        <button
          class="inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-white hover:bg-indigo-600"
          :disabled="!selectedGroupId || loadingMatrix"
          @click="loadGroupMatrix"
        >
          <span class="material-icons-round text-[18px]" :class="{ 'animate-spin': loadingMatrix }">refresh</span>
          Recargar
        </button>
      </div>
    </div>

    <div
      v-if="!isAuthorized"
      class="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-amber-900 dark:border-amber-900/40 dark:bg-amber-900/20 dark:text-amber-200"
    >
      Solo `admin` o `docente` tiene acceso a este módulo.
    </div>

    <template v-else>
      <div
        v-if="globalError"
        class="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700"
      >
        {{ globalError }}
      </div>

      <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <div class="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div class="text-sm text-slate-600 dark:text-slate-300">
            <span class="font-semibold text-slate-800 dark:text-slate-100">{{ filteredStudents.length }}</span>
            estudiantes visibles
            <span v-if="areaColumns.length">· {{ areaColumns.length }} áreas detectadas</span>
          </div>
          <div
            v-if="partialErrors > 0"
            class="rounded-lg border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs font-medium text-amber-700 dark:border-amber-900/40 dark:bg-amber-900/20 dark:text-amber-200"
          >
            {{ partialErrors }} estudiantes no pudieron cargar áreas
          </div>
        </div>

        <div v-if="!selectedGroupId" class="rounded-lg border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">
          Selecciona un grupo para cargar la matriz.
        </div>

        <div v-else-if="loadingMatrix" class="space-y-3">
          <div class="h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
            <div class="h-full rounded-full bg-primary transition-all" :style="{ width: `${loadingProgress}%` }"></div>
          </div>
          <p class="text-sm text-slate-600 dark:text-slate-300">
            Cargando áreas por estudiante... {{ loadProgressDone }} / {{ loadProgressTotal }}
          </p>
        </div>

        <div
          v-else
          class="max-h-[68vh] overflow-auto rounded-lg border border-slate-200 dark:border-slate-700"
          :class="['matrix-theme', { 'matrix-theme-dark': isDarkMode }]"
        >
          <table class="matrix-table">
            <thead>
              <tr>
                <th class="sticky-col left-0 min-w-[280px]">Estudiante</th>
                <th
                  v-for="area in areaColumns"
                  :key="area.code"
                  class="min-w-[210px]"
                >
                  {{ area.label }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="student in paginatedStudents" :key="student.id">
                <td class="sticky-col left-0 student-col">
                  <p class="font-semibold text-slate-800 dark:text-slate-100">{{ student.label }}</p>
                  <p v-if="student.meta?.numero_documento" class="text-xs text-slate-500 dark:text-slate-400">
                    Doc. {{ student.meta.numero_documento }}
                  </p>
                </td>

                <td
                  v-for="area in areaColumns"
                  :key="`${student.id}-${area.code}`"
                  class="align-top"
                >
                  <template v-if="getCell(student, area.code)">
                    <div class="cell-chip">
                      <div class="flex items-center justify-between gap-2">
                        <span class="text-xs text-slate-500 dark:text-slate-400">Promedio</span>
                        <span class="text-sm font-bold text-slate-800 dark:text-slate-100">
                          {{ formatPercent(getCell(student, area.code).promedio) }}
                        </span>
                      </div>
                      <div class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                        Aplicados: {{ getCell(student, area.code).intentos || 0 }}
                      </div>
                      <button
                        type="button"
                        class="mt-2 inline-flex items-center gap-1 rounded-md border border-slate-300 px-2 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-transparent dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700 dark:disabled:hover:bg-transparent"
                        :disabled="(getCell(student, area.code).intentos || 0) <= 1"
                        :title="(getCell(student, area.code).intentos || 0) <= 1 ? 'Se requieren al menos 2 aplicados para ver análisis.' : ''"
                        @click="openSummary(student, area.code, area.label)"
                      >
                        <span class="material-icons-round text-[14px]">insights</span>
                        Ver análisis
                      </button>
                    </div>
                  </template>
                  <div v-else class="text-center text-xs text-slate-400 dark:text-slate-500">--</div>
                </td>
              </tr>
            </tbody>
          </table>

          <div
            v-if="showPagination"
            class="mt-4 flex flex-col gap-2 border-t border-slate-200 pt-3 text-sm sm:flex-row sm:items-center sm:justify-between dark:border-slate-700"
          >
            <p class="text-slate-600 dark:text-slate-300">
              Mostrando {{ displayedStart }} - {{ displayedEnd }} de {{ filteredStudents.length }} estudiantes
            </p>
            <div class="flex items-center gap-2">
              <button
                type="button"
                class="matrix-page-btn"
                :disabled="currentPage <= 1"
                @click="goPrevPage"
              >
                Anterior
              </button>
              <span class="px-1 text-slate-500 dark:text-slate-400">
                Página {{ currentPage }} de {{ totalPages }}
              </span>
              <button
                type="button"
                class="matrix-page-btn"
                :disabled="currentPage >= totalPages"
                @click="goNextPage"
              >
                Siguiente
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <aside v-if="summaryOpen" class="summary-drawer" :class="{ dark: isDarkMode }">
      <div class="summary-drawer-head">
        <div>
          <h3 class="text-lg font-bold text-slate-800 dark:text-slate-100">Summary</h3>
          <p class="text-xs text-slate-500 dark:text-slate-400">{{ summaryTitle }}</p>
        </div>
        <button
          type="button"
          class="inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-300 text-slate-600 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700"
          @click="closeSummary"
        >
          <span class="material-icons-round text-[18px]">close</span>
        </button>
      </div>

      <div v-if="summaryLoading" class="rounded-lg border border-slate-200 p-4 text-sm text-slate-600 dark:border-slate-700 dark:text-slate-300">
        Cargando métricas...
      </div>

      <div
        v-else-if="summaryError"
        class="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm font-medium text-rose-700"
      >
        {{ summaryError }}
      </div>

      <template v-else-if="summaryMetrics">
        <div class="space-y-5">
          <div class="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900/40">
            <div class="flex items-center justify-between gap-2">
              <div>
                <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">Tendencia</p>
                <p class="text-sm font-bold text-slate-800 dark:text-white">{{ trendLabel }}</p>
              </div>
              <span :class="trendBadgeClass" class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold">
                <span class="material-icons-round text-[14px]">{{ trendIcon }}</span>
                {{ trendLabel }}
              </span>
            </div>
            <div class="mt-3 grid grid-cols-2 gap-2 text-xs">
              <div class="rounded-lg bg-white p-2 dark:bg-slate-800">
                <p class="text-slate-500">Pendiente</p>
                <p class="font-bold text-slate-800 dark:text-white">{{ summaryMetrics.tendencia?.pendiente }}</p>
              </div>
              <div class="rounded-lg bg-white p-2 dark:bg-slate-800">
                <p class="text-slate-500">Delta</p>
                <p class="font-bold text-slate-800 dark:text-white">{{ summaryMetrics.tendencia?.delta_primer_ultimo }}</p>
              </div>
            </div>
          </div>

          <div>
            <h4 class="mb-2 text-sm font-semibold text-slate-700 dark:text-slate-200">Rendimiento por simulacro</h4>
            <LineChart :config="scoreLineConfig" :dark-mode="isDarkMode" />
          </div>

          <div>
            <h4 class="mb-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
              Rendimiento por competencia
              <span v-if="selectedCompetencia" class="ml-1 text-xs text-primary">
                (enfoque: {{ selectedCompetencia }})
              </span>
            </h4>
            <LineChart :config="competencyLineConfig" :dark-mode="isDarkMode" />
          </div>

          <div class="max-h-[260px] overflow-y-auto rounded-lg border border-slate-200 dark:border-slate-700">
            <table class="w-full text-left text-xs">
              <thead class="sticky top-0 bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-200">
                <tr>
                  <th class="px-3 py-2 font-semibold">Competencia</th>
                  <th class="px-3 py-2 font-semibold text-right">Prom</th>
                  <th class="px-3 py-2 font-semibold text-right">Último</th>
                  <th class="px-3 py-2 font-semibold text-right">Var</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
                <tr
                  v-for="item in sortedResumenCompetencias"
                  :key="item.competencia"
                  class="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/40"
                  @click="toggleCompetenciaFocus(item.competencia)"
                >
                  <td class="px-3 py-2 font-medium text-slate-700 dark:text-slate-200">{{ item.competencia }}</td>
                  <td class="px-3 py-2 text-right">{{ Number(item.promedio).toFixed(1) }}%</td>
                  <td class="px-3 py-2 text-right">{{ Number(item.ultimo).toFixed(1) }}%</td>
                  <td class="px-3 py-2 text-right" :class="item.variacion >= 0 ? 'text-emerald-600' : 'text-rose-600'">
                    {{ item.variacion >= 0 ? '+' : '' }}{{ Number(item.variacion).toFixed(1) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
    </aside>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import api from '@/api/axios';
import { useAuthStore } from '@/stores/auth';
import LineChart from '@/components/graficos/LineChart.vue';
import Select from 'primevue/select';

const authStore = useAuthStore();

const isAuthorized = computed(() => {
    const role = authStore.user?.rol?.nombre;
    return role === 'admin' || role === 'docente';
});

const groups = ref([]);
const loadingGroups = ref(false);
const selectedGroupId = ref(null);

function getGroupLabel(id) {
    const g = groups.value.find(gr => gr.id === id);
    if (!g) return '';
    return g.meta?.sede_nombre ? `${g.label} — ${g.meta.sede_nombre}` : g.label;
}

const canvasSelectPt = {
    root: { class: 'border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 rounded-lg shadow-sm' },
    label: { class: 'text-sm text-slate-700 dark:text-slate-100 px-3 py-2' },
    dropdown: { class: 'text-slate-500 dark:text-slate-300' },
    panel: { class: 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600' },
    item: { class: 'text-slate-700 dark:text-slate-100 hover:bg-slate-50 dark:hover:bg-slate-700' }
};

const students = ref([]);
const areaColumns = ref([]);
const studentAreaMatrix = ref({});

const loadingMatrix = ref(false);
const loadProgressDone = ref(0);
const loadProgressTotal = ref(0);
const partialErrors = ref(0);
const globalError = ref('');
const searchQuery = ref('');
const itemsPerPage = 10;
const currentPage = ref(1);
const isDarkMode = ref(false);
let themeClassObserver = null;

const summaryOpen = ref(false);
const summaryLoading = ref(false);
const summaryError = ref('');
const summaryMetrics = ref(null);
const summaryContext = ref({ studentName: '', areaCode: '', areaLabel: '' });
const selectedCompetencia = ref(null);

const loadingProgress = computed(() => {
  if (!loadProgressTotal.value) return 0;
  return Math.round((loadProgressDone.value / loadProgressTotal.value) * 100);
});

const filteredStudents = computed(() => {
  const query = searchQuery.value.trim().toLowerCase();
  const rows = [...students.value].sort((a, b) => `${a.label}`.localeCompare(`${b.label}`, 'es'));
  if (!query) return rows;
  return rows.filter((student) => {
    const name = `${student?.label || ''}`.toLowerCase();
    const doc = `${student?.meta?.numero_documento || ''}`.toLowerCase();
    return name.includes(query) || doc.includes(query);
  });
});

const totalPages = computed(() => {
  const total = Math.ceil(filteredStudents.value.length / itemsPerPage);
  return Math.max(total, 1);
});

const showPagination = computed(() => filteredStudents.value.length > itemsPerPage);

const paginatedStudents = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage;
  return filteredStudents.value.slice(start, start + itemsPerPage);
});

const displayedStart = computed(() => {
  if (!filteredStudents.value.length) return 0;
  return (currentPage.value - 1) * itemsPerPage + 1;
});

const displayedEnd = computed(() => {
  if (!filteredStudents.value.length) return 0;
  return Math.min(currentPage.value * itemsPerPage, filteredStudents.value.length);
});

const summaryTitle = computed(() => {
  if (!summaryContext.value.studentName) return 'Sin selección';
  return `${summaryContext.value.studentName} · ${summaryContext.value.areaLabel || summaryContext.value.areaCode}`;
});

const trendLabel = computed(() => summaryMetrics.value?.tendencia?.estado || 'estable');
const trendIcon = computed(() => {
  if (trendLabel.value === 'subiendo') return 'trending_up';
  if (trendLabel.value === 'bajando') return 'trending_down';
  return 'trending_flat';
});
const trendBadgeClass = computed(() => {
  if (trendLabel.value === 'subiendo') return 'bg-emerald-100 text-emerald-700';
  if (trendLabel.value === 'bajando') return 'bg-rose-100 text-rose-700';
  return 'bg-slate-200 text-slate-700';
});

const sortedResumenCompetencias = computed(() => {
  const rows = summaryMetrics.value?.resumen_competencias || [];
  return [...rows].sort((a, b) => Number(a.promedio || 0) - Number(b.promedio || 0));
});

const scoreLineConfig = computed(() => {
  const series = summaryMetrics.value?.serie_puntaje || [];
  const labels = series.map((_, idx) => `${idx + 1}`);
  const datasetValues = series.map((item) => Number(item.puntaje_total || 0));
  return {
    data: {
      labels,
      datasets: [
        {
          label: 'Puntaje total (%)',
          data: datasetValues,
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.16)',
          borderWidth: 3,
          pointRadius: 4,
          tension: 0.3,
          fill: false,
        },
      ],
    },
    options: {
      plugins: { legend: { display: true } },
      scales: {
        y: {
          suggestedMin: 0,
          suggestedMax: 100,
          title: { display: true, text: 'Puntaje %' },
        },
        x: {
          title: { display: true, text: 'Intento' },
        },
      },
    },
  };
});

const colorPalette = ['#7c3aed', '#06b6d4', '#f59e0b', '#ef4444', '#10b981', '#2563eb', '#f97316', '#84cc16'];

function rgbaFromHex(hex, alpha = 1) {
  const clean = hex.replace('#', '');
  const num = Number.parseInt(clean, 16);
  const r = (num >> 16) & 255;
  const g = (num >> 8) & 255;
  const b = num & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

const competencyLineConfig = computed(() => {
  const scoreSeries = summaryMetrics.value?.serie_puntaje || [];
  const labels = scoreSeries.map((_, idx) => `${idx + 1}`);
  const indexByRespuesta = new Map(scoreSeries.map((item, idx) => [item.respuesta_id, idx]));

  const datasets = (summaryMetrics.value?.series_competencia || []).map((serie, idx) => {
    const baseColor = colorPalette[idx % colorPalette.length];
    const data = Array.from({ length: labels.length }, () => null);
    (serie.puntos || []).forEach((p) => {
      const index = indexByRespuesta.get(p.respuesta_id);
      if (index !== undefined) data[index] = Number(p.valor || 0);
    });

    const focused = !selectedCompetencia.value || selectedCompetencia.value === serie.competencia;
    return {
      label: serie.competencia,
      data,
      borderColor: focused ? baseColor : rgbaFromHex(baseColor, 0.25),
      backgroundColor: focused ? rgbaFromHex(baseColor, 0.2) : rgbaFromHex(baseColor, 0.08),
      pointRadius: focused ? 3 : 2,
      borderWidth: focused ? 2.5 : 1.5,
      tension: 0.3,
      spanGaps: true,
    };
  });

  return {
    data: { labels, datasets },
    options: {
      plugins: { legend: { display: true } },
      scales: {
        y: {
          suggestedMin: 0,
          suggestedMax: 100,
          title: { display: true, text: '% Acierto' },
        },
        x: { title: { display: true, text: 'Intento' } },
      },
    },
  };
});

function formatPercent(value) {
  if (value === null || value === undefined) return '--';
  return `${Number(value).toFixed(1)}%`;
}

function getStudentId(student) {
  return student?.meta?.estudiante_id;
}

function getCell(student, areaCode) {
  const studentId = getStudentId(student);
  if (!studentId) return null;
  return studentAreaMatrix.value[studentId]?.[areaCode] || null;
}

function toggleCompetenciaFocus(name) {
  selectedCompetencia.value = selectedCompetencia.value === name ? null : name;
}

function goPrevPage() {
  if (currentPage.value <= 1) return;
  currentPage.value -= 1;
}

function goNextPage() {
  if (currentPage.value >= totalPages.value) return;
  currentPage.value += 1;
}

function closeSummary() {
  summaryOpen.value = false;
  summaryLoading.value = false;
  summaryError.value = '';
  summaryMetrics.value = null;
  summaryContext.value = { studentName: '', areaCode: '', areaLabel: '' };
  selectedCompetencia.value = null;
}

async function loadGroups() {
  loadingGroups.value = true;
  globalError.value = '';
  try {
    const { data } = await api.get('/analisis/canvas/grupos');
    groups.value = (data || []).map((item) => ({
      id: item?.meta?.grupo_id,
      label: item?.label || `Grupo ${item?.meta?.grupo_id ?? ''}`,
      meta: item?.meta || {},
    })).filter((item) => !!item.id);
  } catch (err) {
    globalError.value = err?.response?.data?.detail || 'No se pudieron cargar los grupos.';
  } finally {
    loadingGroups.value = false;
  }
}

async function runWithConcurrency(items, limit, worker) {
  let cursor = 0;
  const runners = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (cursor < items.length) {
      const current = cursor;
      cursor += 1;
      await worker(items[current], current);
    }
  });
  await Promise.all(runners);
}

async function loadGroupMatrix() {
  if (!selectedGroupId.value) return;
  loadingMatrix.value = true;
  currentPage.value = 1;
  globalError.value = '';
  partialErrors.value = 0;
  students.value = [];
  areaColumns.value = [];
  studentAreaMatrix.value = {};
  closeSummary();

  try {
    const { data: studentDtos } = await api.get(`/analisis/canvas/grupos/${selectedGroupId.value}/estudiantes`);
    students.value = studentDtos || [];
    loadProgressTotal.value = students.value.length;
    loadProgressDone.value = 0;

    if (!students.value.length) return;

    const areaMap = new Map();
    const matrix = {};

    await runWithConcurrency(students.value, 6, async (student) => {
      const studentId = getStudentId(student);
      if (!studentId) {
        loadProgressDone.value += 1;
        return;
      }

      matrix[studentId] = {};
      try {
        const { data: areaDtos } = await api.get(
          `/analisis/canvas/grupos/${selectedGroupId.value}/estudiantes/${studentId}/areas`,
        );

        (areaDtos || []).forEach((areaDto) => {
          const areaCode = areaDto?.meta?.area || areaDto?.label;
          if (!areaCode) return;
          const label = areaDto?.label || areaCode;
          matrix[studentId][areaCode] = {
            code: areaCode,
            label,
            promedio: areaDto?.meta?.promedio ?? null,
            intentos: areaDto?.meta?.intentos ?? 0,
          };
          if (!areaMap.has(areaCode)) {
            areaMap.set(areaCode, { code: areaCode, label });
          }
        });
      } catch {
        partialErrors.value += 1;
      } finally {
        loadProgressDone.value += 1;
      }
    });

    studentAreaMatrix.value = matrix;
    areaColumns.value = [...areaMap.values()].sort((a, b) => `${a.label}`.localeCompare(`${b.label}`, 'es'));
  } catch (err) {
    globalError.value = err?.response?.data?.detail || 'No se pudo construir la matriz del grupo.';
  } finally {
    loadingMatrix.value = false;
  }
}

async function openSummary(student, areaCode, areaLabel) {
  const studentId = getStudentId(student);
  if (!studentId || !selectedGroupId.value) return;

  summaryOpen.value = true;
  summaryLoading.value = true;
  summaryError.value = '';
  summaryMetrics.value = null;
  selectedCompetencia.value = null;
  summaryContext.value = {
    studentName: student.label,
    areaCode,
    areaLabel,
  };

  try {
    const { data } = await api.get(
      `/analisis/canvas/grupos/${selectedGroupId.value}/estudiantes/${studentId}/areas/${encodeURIComponent(areaCode)}/metricas`,
    );
    summaryMetrics.value = data;
  } catch (err) {
    summaryError.value = err?.response?.data?.detail || 'No se pudo cargar el summary del estudiante.';
  } finally {
    summaryLoading.value = false;
  }
}

async function onGroupChange() {
  await loadGroupMatrix();
}

watch(searchQuery, () => {
  currentPage.value = 1;
});

watch(filteredStudents, () => {
  if (currentPage.value > totalPages.value) {
    currentPage.value = totalPages.value;
  }
});

function syncDarkModeState() {
  const root = document.documentElement;
  isDarkMode.value = root.classList.contains('dark') || root.classList.contains('my-app-dark');
}

onMounted(async () => {
  syncDarkModeState();
  themeClassObserver = new MutationObserver(syncDarkModeState);
  themeClassObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class'],
  });

  if (!isAuthorized.value) return;
  await loadGroups();
});

onBeforeUnmount(() => {
  if (themeClassObserver) {
    themeClassObserver.disconnect();
    themeClassObserver = null;
  }
});
</script>

<style scoped>
.text-primary {
  color: #6366f1;
}

.bg-primary {
  background-color: #6366f1;
}

.matrix-theme {
  --matrix-border: #e2e8f0;
  --matrix-th-bg: #f8fafc;
  --matrix-th-text: #475569;
  --matrix-td-bg: #ffffff;
  --matrix-td-text: #0f172a;
  --matrix-sticky-bg: #ffffff;
  --matrix-chip-bg: #f8fafc;
  --matrix-chip-border: #e2e8f0;
  --matrix-page-bg: #ffffff;
  --matrix-page-border: #cbd5e1;
  --matrix-page-text: #334155;
  --matrix-page-hover: #f8fafc;
}

.matrix-table {
  width: max-content;
  min-width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.matrix-table thead th {
  position: sticky;
  top: 0;
  z-index: 4;
  background: var(--matrix-th-bg);
  border-bottom: 1px solid var(--matrix-border);
  border-right: 1px solid var(--matrix-border);
  padding: 10px;
  text-align: left;
  font-size: 12px;
  font-weight: 700;
  color: var(--matrix-th-text);
}

.matrix-table tbody td {
  border-bottom: 1px solid var(--matrix-border);
  border-right: 1px solid var(--matrix-border);
  padding: 10px;
  background: var(--matrix-td-bg);
  color: var(--matrix-td-text);
  vertical-align: top;
}

.sticky-col {
  position: sticky;
  z-index: 5;
  background: var(--matrix-sticky-bg);
}

.matrix-table thead .sticky-col {
  background: var(--matrix-th-bg);
  z-index: 6;
}

.student-col {
  min-width: 280px;
}

.cell-chip {
  border: 1px solid var(--matrix-chip-border);
  border-radius: 10px;
  padding: 8px;
  background: var(--matrix-chip-bg);
}

.matrix-page-btn {
  border: 1px solid var(--matrix-page-border);
  border-radius: 8px;
  padding: 6px 12px;
  color: var(--matrix-page-text);
  background: var(--matrix-page-bg);
}

.matrix-page-btn:hover {
  background: var(--matrix-page-hover);
}

.matrix-page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.summary-drawer {
  position: fixed;
  top: 0;
  right: 0;
  width: min(460px, 96vw);
  height: 100vh;
  z-index: 40;
  overflow-y: auto;
  padding: 14px;
  border-left: 1px solid #e2e8f0;
  background: #ffffff;
  box-shadow: -18px 0 34px rgba(15, 23, 42, 0.18);
}

.summary-drawer-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e2e8f0;
}

.matrix-theme-dark {
  --matrix-border: #334155;
  --matrix-th-bg: #0f172a;
  --matrix-th-text: #cbd5e1;
  --matrix-td-bg: #111827;
  --matrix-td-text: #e2e8f0;
  --matrix-sticky-bg: #111827;
  --matrix-chip-bg: #0f172a;
  --matrix-chip-border: #334155;
  --matrix-page-bg: #111827;
  --matrix-page-border: #475569;
  --matrix-page-text: #e2e8f0;
  --matrix-page-hover: #1e293b;
}

:global(.dark) .summary-drawer {
  border-color: #334155;
  background: #111827;
}

:global(.dark) .summary-drawer-head {
  border-color: #334155;
}

.summary-drawer.dark {
  border-color: #334155;
  background: #111827;
  color: #e2e8f0;
}

.summary-drawer.dark .summary-drawer-head {
  border-color: #334155;
}
</style>
