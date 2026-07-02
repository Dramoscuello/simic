import { defineStore } from 'pinia';
import api from '@/api/axios';

const COLUMN_X = {
  group: 60,
  student_cluster: 340,
  student: 560,
  area: 780,
  competencia: 1020,
};

const Y_START = 80;
const Y_GAP = 110;

const EDGE_STYLE = {
  stroke: '#6366f1',
  strokeWidth: 2,
};

function makeEdgeId(source, target) {
  return `edge-${source}-${target}`;
}

function toNodeStyle(entityType) {
  const map = {
    group: { border: '1.5px solid #3b82f6', background: '#eff6ff' },
    student_cluster: { border: '1.5px solid #0ea5e9', background: '#ecfeff' },
    student: { border: '1.5px solid #10b981', background: '#ecfdf5' },
    area: { border: '1.5px solid #f59e0b', background: '#fffbeb' },
    competencia: { border: '1.5px solid #8b5cf6', background: '#f5f3ff' },
  };
  return map[entityType] || { border: '1.5px solid #94a3b8', background: '#f8fafc' };
}

function createCanvasNode(dto, x, y) {
  const meta = dto.meta || {};
  const entityType = dto.type;
  return {
    id: dto.id,
    type: 'analisisNode',
    draggable: true,
    position: { x, y },
    data: {
      entityType,
      label: dto.label,
      meta,
      loading: false,
    },
    style: {
      borderRadius: '16px',
      boxShadow: '0 8px 18px rgba(15, 23, 42, 0.08)',
      minWidth: '240px',
      padding: '12px 14px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      ...toNodeStyle(entityType),
    },
  };
}

function updateNodeLoading(nodes, nodeId, loading) {
  return nodes.map((n) => {
    if (n.id !== nodeId) return n;
    return { ...n, data: { ...n.data, loading } };
  });
}

export const useAnalisisCanvasStore = defineStore('analisisCanvas', {
  state: () => ({
    nodes: [],
    edges: [],
    loadingRoot: false,
    loadingOverlay: false,
    loadingOverlayMessage: 'Cargando...',
    error: null,
    selectedGroupId: null,
    selectedStudentId: null,
    selectedAreaCode: null,
    selectedCompetencia: null,
    areaMetrics: null,
    studentsByGroup: {},
  }),

  getters: {
    hasNodes: (state) => state.nodes.length > 0,
    panelReady: (state) => !!state.areaMetrics,
  },

  actions: {
    resetCanvas() {
      this.nodes = [];
      this.edges = [];
      this.error = null;
      this.loadingOverlay = false;
      this.loadingOverlayMessage = 'Cargando...';
      this.selectedGroupId = null;
      this.selectedStudentId = null;
      this.selectedAreaCode = null;
      this.selectedCompetencia = null;
      this.areaMetrics = null;
      this.studentsByGroup = {};
    },

    async initializeCanvas() {
      this.resetCanvas();
      this.loadingRoot = true;
      try {
        const { data } = await api.get('/analisis/canvas/grupos');
        this.nodes = data.map((dto, idx) => createCanvasNode(dto, COLUMN_X.group, Y_START + idx * Y_GAP));
      } catch (err) {
        this.error = err?.response?.data?.detail || 'No se pudieron cargar los grupos.';
      } finally {
        this.loadingRoot = false;
      }
    },

    _removeByType(types = []) {
      const typeSet = new Set(types);
      const idsToRemove = new Set(
        this.nodes.filter((n) => typeSet.has(n.data?.entityType)).map((n) => n.id),
      );
      this.nodes = this.nodes.filter((n) => !idsToRemove.has(n.id));
      this.edges = this.edges.filter((e) => !idsToRemove.has(e.source) && !idsToRemove.has(e.target));
    },

    _appendChildren(parentNodeId, dtos, entityType, yBase = Y_START) {
      const existingIds = new Set(this.nodes.map((n) => n.id));
      const x = COLUMN_X[entityType] ?? 360;
      const freshNodes = [];
      const freshEdges = [];

      dtos.forEach((dto, idx) => {
        if (!existingIds.has(dto.id)) {
          freshNodes.push(createCanvasNode(dto, x, yBase + idx * Y_GAP));
        }
        const edgeId = makeEdgeId(parentNodeId, dto.id);
        if (!this.edges.some((e) => e.id === edgeId)) {
          freshEdges.push({
            id: edgeId,
            source: parentNodeId,
            target: dto.id,
            type: 'bezier',
            style: EDGE_STYLE,
            animated: false,
            selectable: false,
          });
        }
      });

      this.nodes = [...this.nodes, ...freshNodes];
      this.edges = [...this.edges, ...freshEdges];
    },

    _upsertNode(node) {
      const index = this.nodes.findIndex((item) => item.id === node.id);
      if (index === -1) {
        this.nodes = [...this.nodes, node];
        return;
      }
      const next = [...this.nodes];
      next[index] = node;
      this.nodes = next;
    },

    _upsertEdge(edge) {
      const index = this.edges.findIndex((item) => item.id === edge.id);
      if (index === -1) {
        this.edges = [...this.edges, edge];
        return;
      }
      const next = [...this.edges];
      next[index] = edge;
      this.edges = next;
    },

    async expandGroup(node) {
      if (this.loadingOverlay) return;
      const groupId = node?.data?.meta?.grupo_id;
      if (!groupId) return;

      this.selectedGroupId = groupId;
      this.selectedStudentId = null;
      this.selectedAreaCode = null;
      this.selectedCompetencia = null;
      this.areaMetrics = null;
      this.error = null;

      this._removeByType(['student_cluster', 'student', 'area', 'competencia']);
      this.nodes = updateNodeLoading(this.nodes, node.id, true);
      this.loadingOverlay = true;
      this.loadingOverlayMessage = 'Cargando estudiantes...';
      try {
        const { data } = await api.get(`/analisis/canvas/grupos/${groupId}/estudiantes`);
        this.studentsByGroup[groupId] = data;
        const clusterNode = {
          id: `student-cluster-${groupId}`,
          type: 'student_cluster',
          label: `Estudiantes (${data.length})`,
          meta: {
            grupo_id: groupId,
            total: data.length,
          },
        };
        this._appendChildren(node.id, [clusterNode], 'student_cluster', node?.position?.y ?? Y_START);
      } catch (err) {
        this.error = err?.response?.data?.detail || 'No se pudieron cargar los estudiantes del grupo.';
      } finally {
        this.nodes = updateNodeLoading(this.nodes, node.id, false);
        this.loadingOverlay = false;
      }
    },

    selectStudentFromCluster(clusterNodeId, studentDto) {
      if (!clusterNodeId || !studentDto) return;
      const studentId = studentDto?.meta?.estudiante_id;
      if (!studentId) return;

      this.selectedStudentId = studentId;
      this.selectedAreaCode = null;
      this.selectedCompetencia = null;
      this.areaMetrics = null;
      this.error = null;

      this._removeByType(['student', 'area', 'competencia']);

      const clusterNode = this.nodes.find((node) => node.id === clusterNodeId);
      const y = clusterNode?.position?.y ?? Y_START;
      const studentNode = createCanvasNode(studentDto, COLUMN_X.student, y);
      this._upsertNode(studentNode);
      this._upsertEdge({
        id: makeEdgeId(clusterNodeId, studentDto.id),
        source: clusterNodeId,
        target: studentDto.id,
        type: 'bezier',
        style: EDGE_STYLE,
        animated: false,
        selectable: false,
      });
    },

    async expandStudent(node) {
      if (this.loadingOverlay) return;
      const studentId = node?.data?.meta?.estudiante_id;
      if (!studentId || !this.selectedGroupId) return;

      this.selectedStudentId = studentId;
      this.selectedAreaCode = null;
      this.selectedCompetencia = null;
      this.areaMetrics = null;
      this.error = null;

      this._removeByType(['area', 'competencia']);
      this.nodes = updateNodeLoading(this.nodes, node.id, true);
      this.loadingOverlay = true;
      this.loadingOverlayMessage = 'Cargando áreas del estudiante...';
      try {
        const { data } = await api.get(
          `/analisis/canvas/grupos/${this.selectedGroupId}/estudiantes/${studentId}/areas`,
        );
        this._appendChildren(node.id, data, 'area');
      } catch (err) {
        this.error = err?.response?.data?.detail || 'No se pudieron cargar las áreas del estudiante.';
      } finally {
        this.nodes = updateNodeLoading(this.nodes, node.id, false);
        this.loadingOverlay = false;
      }
    },

    async expandArea(node) {
      if (this.loadingOverlay) return;
      const areaCode = node?.data?.meta?.area;
      if (!areaCode || !this.selectedGroupId || !this.selectedStudentId) return;

      this.selectedAreaCode = areaCode;
      this.selectedCompetencia = null;
      this.error = null;
      this._removeByType(['competencia']);

      this.nodes = updateNodeLoading(this.nodes, node.id, true);
      this.loadingOverlay = true;
      this.loadingOverlayMessage = 'Cargando competencias y métricas...';
      try {
        const [compResponse, metricsResponse] = await Promise.all([
          api.get(
            `/analisis/canvas/grupos/${this.selectedGroupId}/estudiantes/${this.selectedStudentId}/areas/${areaCode}/competencias`,
          ),
          api.get(
            `/analisis/canvas/grupos/${this.selectedGroupId}/estudiantes/${this.selectedStudentId}/areas/${areaCode}/metricas`,
          ),
        ]);

        this._appendChildren(node.id, compResponse.data, 'competencia');
        this.areaMetrics = metricsResponse.data;
      } catch (err) {
        this.error = err?.response?.data?.detail || 'No se pudieron cargar las métricas del área.';
      } finally {
        this.nodes = updateNodeLoading(this.nodes, node.id, false);
        this.loadingOverlay = false;
      }
    },

    selectCompetencia(node) {
      const competencia = node?.data?.meta?.competencia || null;
      this.selectedCompetencia = competencia;
    },
  },
});
