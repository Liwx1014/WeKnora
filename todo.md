
# 0. 依赖与目录

**新增依赖**

```bash
pnpm add @vue-flow/core @vue-flow/minimap @vue-flow/controls marked
pnpm add -D @types/marked
```

**建议目录**

```
src/
  api/
    evidence.ts
  models/
    evidence.ts
  utils/
    transform.ts
  stores/
    useEvidenceStore.ts
  components/evidence/
    EvidenceChain.vue
    StepCard.vue
    ImagePreview.vue
    LLMResult.vue
  views/
    HomePage.vue (修改现有)
```

**实际数据结构分析（基于id=10的样例数据）**

从Terminal#727-943的数据可以看出，实际的数据结构包含：
- `log_data.image_refs`: 包含各阶段图片的MinIO存储信息
- `log_data.image_urls`: 包含预签名URL
- `log_data.analysis_results`: 包含各阶段分析结果
- `log_data.llm_output`: 包含LLM的prompt和answer
- `log_data.user_input`: 用户输入信息
- `log_data.system_info`: 系统版本信息

---

# 1. 类型定义（Graph ViewModel）

`src/models/graph.ts`

```ts
export type NodeType =
  | 'source_image' | 'detection' | 'segmentation' | 'depth' | 'distance' | 'llm';

export interface GraphNode {
  id: string;
  type: NodeType;
  label: string;
  status: 'success' | 'warning' | 'error';
  summary?: string;
  metrics?: Record<string, number | string>;
  evidence?: Array<{ id?: string; title: string; url: string }>;
  detail?: any;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
}

export interface GraphVM {
  nodes: GraphNode[];
  edges: GraphEdge[];
  llm: { prompt: string; answer: string };
}

export interface EvidenceRecord { // 后端 get_chat_record_by_id 返回
  id: number | string;
  conversation_id: string;
  user_id: string;
  session_id: string;
  created_at: string;
  log_data: {
    task_info: {
      status: string;
      task_id: string;
      timestamp: string;
      processing_time_ms: number;
    };
    image_refs: {
      [key: string]: {
        size: number;
        bucket: string;
        object_name: string;
        upload_time: string;
      };
    };
    image_urls: {
      [key: string]: string; // 预签名URL
    };
    analysis_results: {
      detection?: {
        result: {
          count: number;
          objects: Array<{
            bbox: [number, number, number, number];
            class_name: string;
            confidence: number;
          }>;
        };
        local_path: string;
      };
      segmentation?: {
        local_path: string;
      };
      depth?: {
        result: {
          depth_min: number;
          depth_max: number;
          focal_length: number;
        };
        local_path: string;
      };
      distances?: {
        result: Array<{
          status: string;
          box_index: number;
          box_coords: [number, number, number, number];
          distance_meters: number;
          reference_point: [number, number];
          nearest_wire_point: [number, number];
          calibration_factor_used: number;
        }>;
        local_path: string;
      };
    };
    llm_output: {
      prompt: string;
      answer: string;
    };
    user_input: {
      question: string;
      original_local_path: string;
    };
    system_info: {
      postgres_db: string;
      minio_bucket: string;
      python_version: string;
      vision_agent_version: string;
    };
  };
}
```

---

# 2. Axios 与接口

`src/api/http.ts`

```ts
import axios from 'axios';

const http = axios.create({
  baseURL: '/api',
  timeout: 15000,
});

// 预签名 URL 403/401 自动重试：调用后端刷新接口
http.interceptors.response.use(undefined, async (err) => {
  const cfg = err.config;
  // 约定：带 presignRefresh=true 的请求，失败后刷新一次 URL 再重试
  if (cfg?.presignRefresh && (err.response?.status === 403 || err.response?.status === 401) && !cfg.__retried) {
    cfg.__retried = true;
    // 这里假设 cfg.evidenceKey / cfg.bucket 从 params 传入
    const { data } = await http.get('/evidences/presign', {
      params: { bucket: cfg.params?.bucket, key: cfg.params?.key },
    });
    // 用新链接替换
    cfg.url = data.url;
    // 直连 MinIO URL（跨域时建议服务端代理）
    return axios(cfg);
  }
  return Promise.reject(err);
});

export default http;
```

`src/api/incidents.ts`

```ts
import http from './http';
import type { IncidentRecord, GraphVM } from '@/models/graph';

export const getEvidence = (id: string | number) =>
  http.get<EvidenceRecord>(`/evidence/${id}`).then(r => r.data);

export const getEvidenceGraph = (id: string | number) =>
  http.get<GraphVM>(`/evidence/${id}/graph`).then(r => r.data);

// 如果前端本地 transform，就不需要上面的 graph 接口
export const getPresignedUrl = (bucket: string, key: string) =>
  http.get<{ url: string }>('/evidences/presign', { params: { bucket, key } }).then(r => r.data);
```

---

# 3. 从现有 JSON 生成 GraphVM

`src/utils/transform.ts`

```ts
import type { GraphVM } from '@/models/graph';

export function toGraphVM(rec: EvidenceRecord): GraphVM {
  const L = rec.log_data ?? {};
  const A = L.analysis_results ?? {};
  const U = L.image_urls ?? {};

  const detCount = A?.detection?.result?.count ?? 0;
  const distances = (A?.distances?.result ?? []) as Array<any>;
  const minDist = distances.length ? Math.min(...distances.map(d => d.distance_meters)) : undefined;
  
  // 检测到的物体信息
  const detectedObjects = A?.detection?.result?.objects ?? [];
  const objectSummary = detectedObjects.length > 0 
    ? `检测到${detCount}个物体: ${detectedObjects.map(obj => `${obj.class_name}(${(obj.confidence * 100).toFixed(1)}%)`).join(', ')}`
    : `检测到${detCount}个物体`;

  return {
    nodes: [
      {
        id: 'n_src', type: 'source_image', label: '原始图片', status: 'success',
        summary: '输电线路巡检图像',
        evidence: U.original_url ? [{ title: '原始图片', url: U.original_url }] : [],
        detail: {
          user_question: L.user_input?.question,
          local_path: L.user_input?.original_local_path,
          task_id: L.task_info?.task_id,
          timestamp: L.task_info?.timestamp
        },
      },
      {
        id: 'n_det', type: 'detection', label: 'D-FINE 目标检测', 
        status: detCount > 0 ? 'success' : 'warning',
        summary: objectSummary,
        metrics: { 
          检测数量: detCount,
          处理状态: L.task_info?.status || 'unknown'
        },
        evidence: U.detection_url ? [{ title: '检测结果', url: U.detection_url }] : [],
        detail: A?.detection?.result,
      },
      {
        id: 'n_seg', type: 'segmentation', label: 'U-Net 线路分割',
        status: U.segmentation_url ? 'success' : 'warning',
        summary: '输电线路掩码分割',
        evidence: U.segmentation_url ? [{ title: '分割结果', url: U.segmentation_url }] : [],
        detail: { local_path: A?.segmentation?.local_path },
      },
      {
        id: 'n_dep', type: 'depth', label: 'DepPro 深度估计', 
        status: A?.depth?.result ? 'success' : 'warning',
        summary: A?.depth?.result ? `深度范围: ${A.depth.result.depth_min?.toFixed(2)}m - ${A.depth.result.depth_max?.toFixed(2)}m` : '深度估计',
        metrics: {
          最小深度: A?.depth?.result?.depth_min ? `${A.depth.result.depth_min.toFixed(2)}m` : 'N/A',
          最大深度: A?.depth?.result?.depth_max ? `${A.depth.result.depth_max.toFixed(2)}m` : 'N/A',
          焦距: A?.depth?.result?.focal_length ? `${A.depth.result.focal_length.toFixed(2)}px` : 'N/A',
        },
        evidence: U.depth_url ? [{ title: '深度图', url: U.depth_url }] : [],
        detail: A?.depth?.result,
      },
      {
        id: 'n_dist', type: 'distance', label: '距离计算',
        status: distances.length ? 'success' : 'warning',
        summary: minDist ? `最近距离: ${minDist.toFixed(2)}m` : '距离计算',
        metrics: distances.length > 0 ? {
          最近距离: `${minDist?.toFixed(2)}m`,
          检测框数量: distances.length,
          校准因子: distances[0]?.calibration_factor_used || 'N/A'
        } : {},
        evidence: U.distance_visualization_url ? [{ title: '距离可视化', url: U.distance_visualization_url }] : [],
        detail: distances,
      },
      {
        id: 'n_llm', type: 'llm', label: 'LLM 分析总结', status: 'success',
        summary: 'AI智能分析与安全评估',
        metrics: {
          处理时间: L.task_info?.processing_time_ms ? `${L.task_info.processing_time_ms}ms` : 'N/A',
          Agent版本: L.system_info?.vision_agent_version || 'N/A'
        },
        detail: L.llm_output,
      },
    ],
    edges: [
      { id: 'e1', source: 'n_src', target: 'n_det', label: '图像输入' },
      { id: 'e2', source: 'n_det', target: 'n_seg', label: '检测框 → 分割' },
      { id: 'e3', source: 'n_seg', target: 'n_dep', label: '掩码 → 深度' },
      { id: 'e4', source: 'n_dep', target: 'n_dist', label: minDist ? `深度 → 距离` : '深度处理' },
      { id: 'e5', source: 'n_dist', target: 'n_llm', label: '数据汇总' },
    ],
    llm: {
      prompt: L.llm_output?.prompt ?? '',
      answer: L.llm_output?.answer ?? '',
    },
  };
}
```

---

# 4. Pinia store（加载记录 & 转换）

`src/stores/useIncidentStore.ts`

```ts
import { defineStore } from 'pinia';
import { getEvidence } from '@/api/evidence';
import { toGraphVM } from '@/utils/transform';
import type { GraphVM, EvidenceRecord } from '@/models/evidence';

export const useEvidenceStore = defineStore('evidence', {
  state: () => ({
    record: null as EvidenceRecord | null,
    graph: null as GraphVM | null,
    loading: false,
    error: '',
  }),
  actions: {
    async fetchEvidence(id: string | number) {
      this.loading = true; this.error = '';
      try {
        const rec = await getEvidence(id);
        this.record = rec;
        this.graph = toGraphVM(rec);
      } catch (e: any) {
        this.error = e?.message ?? '加载失败';
      } finally {
        this.loading = false;
      }
    },
  },
});
```

---

# 5. 组件实现

## 5.1 证据链主组件（简化版时间线）

`src/components/evidence/EvidenceChain.vue`

```vue
<script setup lang="ts">
import { ref } from 'vue';
import type { GraphVM } from '@/models/evidence';
import StepCard from './StepCard.vue';
import ImagePreview from './ImagePreview.vue';
import LLMResult from './LLMResult.vue';

const props = defineProps<{ 
  data: GraphVM;
  compact?: boolean; // 紧凑模式，用于首页右侧
}>();

const showImagePreview = ref(false);
const showLLMResult = ref(false);
const previewImage = ref({ url: '', title: '' });

function handleImageClick(url: string, title: string) {
  previewImage.value = { url, title };
  showImagePreview.value = true;
}

function handleLLMClick() {
  showLLMResult.value = true;
}
</script>

<template>
  <div class="evidence-chain" :class="{ compact }">
    <div class="chain-header" v-if="!compact">
      <h3>推理证据链</h3>
      <div class="meta-info">
        <t-tag size="small" theme="primary">{{ data.nodes.length }}个步骤</t-tag>
        <t-tag size="small" theme="success" v-if="data.nodes.every(n => n.status === 'success')">全部成功</t-tag>
        <t-tag size="small" theme="warning" v-else>部分警告</t-tag>
      </div>
    </div>
    
    <div class="chain-timeline">
      <div 
        v-for="(node, index) in data.nodes" 
        :key="node.id"
        class="timeline-item"
        :class="{ 'is-last': index === data.nodes.length - 1 }"
      >
        <StepCard 
          :node="node"
          :step-number="index + 1"
          :compact="compact"
          @image-click="handleImageClick"
          @llm-click="handleLLMClick"
        />
      </div>
    </div>
  </div>
  
  <!-- 图片预览弹窗 -->
  <ImagePreview 
    :visible="showImagePreview"
    :image-url="previewImage.url"
    :title="previewImage.title"
    @close="showImagePreview = false"
  />
  
  <!-- LLM结果弹窗 -->
  <LLMResult 
    :visible="showLLMResult"
    :llm-data="data.llm"
    @close="showLLMResult = false"
  />
</template>

<style lang="less" scoped>
.evidence-chain {
  height: 100%;
  display: flex;
  flex-direction: column;
  
  &.compact {
    .chain-timeline {
      max-height: calc(100vh - 200px);
      overflow-y: auto;
    }
  }
}

.chain-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid var(--td-border-level-1-color);
  
  h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
  }
  
  .meta-info {
    display: flex;
    gap: 8px;
  }
}

.chain-timeline {
  flex: 1;
  position: relative;
  padding: 16px 0;
  
  &::before {
    content: '';
    position: absolute;
    left: 20px;
    top: 16px;
    bottom: 16px;
    width: 2px;
    background: var(--td-border-level-2-color);
  }
}

.timeline-item {
  position: relative;
  margin-bottom: 24px;
  
  &.is-last {
    margin-bottom: 0;
  }
}
</style>
```

## 5.2 步骤卡片组件

`src/components/evidence/StepCard.vue`

```vue
<script setup lang="ts">
import type { GraphNode } from '@/models/evidence';

const props = defineProps<{
  node: GraphNode;
  stepNumber: number;
  compact?: boolean;
}>();

const emits = defineEmits<{
  imageClick: [url: string, title: string];
  llmClick: [];
}>();

function getStatusIcon(status: string) {
  switch (status) {
    case 'success': return 'check-circle';
    case 'warning': return 'error-circle';
    case 'error': return 'close-circle';
    default: return 'time-circle';
  }
}

function getStatusColor(status: string) {
  switch (status) {
    case 'success': return 'success';
    case 'warning': return 'warning';
    case 'error': return 'error';
    default: return 'default';
  }
}
</script>

<template>
  <div class="step-card" :class="{ compact }">
    <!-- 步骤序号 -->
    <div class="step-number">
      <t-icon :name="getStatusIcon(node.status)" :color="getStatusColor(node.status)" size="16px" />
      <span class="number">{{ stepNumber }}</span>
    </div>
    
    <!-- 卡片内容 -->
    <div class="card-content">
      <div class="card-header">
        <h4 class="step-title">{{ node.label }}</h4>
        <t-tag size="small" :theme="getStatusColor(node.status)">{{ node.status }}</t-tag>
      </div>
      
      <div class="step-summary" v-if="node.summary">
        {{ node.summary }}
      </div>
      
      <!-- 指标信息 -->
      <div class="metrics" v-if="node.metrics && Object.keys(node.metrics).length">
        <div class="metric-item" v-for="(value, key) in node.metrics" :key="key">
          <span class="metric-label">{{ key }}:</span>
          <span class="metric-value">{{ value }}</span>
        </div>
      </div>
      
      <!-- 证据图片 -->
      <div class="evidence-images" v-if="node.evidence?.length">
        <div 
          v-for="evidence in node.evidence" 
          :key="evidence.url"
          class="evidence-item"
          @click="emits('imageClick', evidence.url, evidence.title)"
        >
          <img :src="evidence.url" :alt="evidence.title" class="evidence-thumb" />
          <span class="evidence-label">{{ evidence.title }}</span>
        </div>
      </div>
      
      <!-- LLM特殊处理 -->
      <div class="llm-actions" v-if="node.type === 'llm'">
        <t-button size="small" variant="outline" @click="emits('llmClick')">
          <t-icon name="chat" />查看AI分析
        </t-button>
      </div>
    </div>
  </div>
</template>

<style lang="less" scoped>
.step-card {
  display: flex;
  gap: 12px;
  
  &.compact {
    .card-content {
      padding: 12px;
    }
    
    .evidence-images {
      grid-template-columns: repeat(auto-fit, minmax(60px, 1fr));
    }
    
    .evidence-thumb {
      height: 60px;
    }
  }
}

.step-number {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--td-bg-color-container);
  border: 2px solid var(--td-border-level-1-color);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  z-index: 1;
  
  .number {
    font-size: 12px;
    font-weight: 600;
    margin-left: 4px;
  }
}

.card-content {
  flex: 1;
  background: var(--td-bg-color-container);
  border: 1px solid var(--td-border-level-1-color);
  border-radius: 8px;
  padding: 16px;
  box-shadow: var(--td-shadow-1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.step-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.step-summary {
  font-size: 12px;
  color: var(--td-text-color-secondary);
  margin-bottom: 12px;
  line-height: 1.4;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.metric-item {
  font-size: 11px;
  
  .metric-label {
    color: var(--td-text-color-secondary);
  }
  
  .metric-value {
    font-weight: 500;
    margin-left: 4px;
  }
}

.evidence-images {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.evidence-item {
  cursor: pointer;
  text-align: center;
  
  &:hover .evidence-thumb {
    transform: scale(1.05);
    box-shadow: var(--td-shadow-2);
  }
}

.evidence-thumb {
  width: 100%;
  height: 80px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid var(--td-border-level-1-color);
  transition: all 0.2s ease;
}

.evidence-label {
  display: block;
  font-size: 10px;
  color: var(--td-text-color-secondary);
  margin-top: 4px;
  line-height: 1.2;
}

.llm-actions {
  display: flex;
  gap: 8px;
}
</style>
```

## 5.3 图片预览组件

`src/components/evidence/ImagePreview.vue`

```vue
<script setup lang="ts">
const props = defineProps<{
  visible: boolean;
  imageUrl: string;
  title: string;
}>();

const emits = defineEmits<{
  close: [];
}>();
</script>

<template>
  <t-dialog 
    :visible="visible" 
    :header="title"
    width="80%"
    :footer="false"
    @close="emits('close')"
  >
    <div class="image-preview">
      <img :src="imageUrl" :alt="title" class="preview-image" />
    </div>
  </t-dialog>
</template>

<style lang="less" scoped>
.image-preview {
  display: flex;
  justify-content: center;
  align-items: center;
  max-height: 70vh;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: var(--td-shadow-2);
}
</style>
```

## 5.4 LLM结果组件

`src/components/evidence/LLMResult.vue`

```vue
<script setup lang="ts">
import { marked } from 'marked';
import { computed } from 'vue';

const props = defineProps<{
  visible: boolean;
  llmData: { prompt: string; answer: string };
}>();

const emits = defineEmits<{
  close: [];
}>();

const answerHtml = computed(() => {
  try {
    return marked.parse(props.llmData?.answer ?? '');
  } catch (e) {
    return props.llmData?.answer ?? '';
  }
});
</script>

<template>
  <t-drawer 
    :visible="visible" 
    header="AI分析结果"
    size="60%"
    :footer="false"
    @close="emits('close')"
  >
    <template #body>
      <div class="llm-result">
        <div class="section">
          <h4 class="section-title">
            <t-icon name="edit" />分析提示词
          </h4>
          <div class="prompt-content">
            <pre>{{ llmData?.prompt || '暂无提示词' }}</pre>
          </div>
        </div>
        
        <t-divider />
        
        <div class="section">
          <h4 class="section-title">
            <t-icon name="chat" />AI分析结果
          </h4>
          <div class="answer-content" v-html="answerHtml"></div>
        </div>
      </div>
    </template>
  </t-drawer>
</template>

<style lang="less" scoped>
.llm-result {
  padding: 16px;
}

.section {
  margin-bottom: 24px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  color: var(--td-text-color-primary);
}

.prompt-content {
  background: var(--td-bg-color-code);
  border: 1px solid var(--td-border-level-1-color);
  border-radius: 6px;
  padding: 12px;
  
  pre {
    margin: 0;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 12px;
    line-height: 1.5;
    white-space: pre-wrap;
    word-wrap: break-word;
  }
}

.answer-content {
  background: var(--td-bg-color-container);
  border: 1px solid var(--td-border-level-1-color);
  border-radius: 6px;
  padding: 16px;
  line-height: 1.6;
  
  :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
    margin: 16px 0 8px 0;
    font-weight: 600;
  }
  
  :deep(p) {
    margin: 8px 0;
  }
  
  :deep(ul), :deep(ol) {
    margin: 8px 0;
    padding-left: 20px;
  }
  
  :deep(li) {
    margin: 4px 0;
  }
  
  :deep(code) {
    background: var(--td-bg-color-code);
    padding: 2px 4px;
    border-radius: 3px;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 0.9em;
  }
  
  :deep(pre) {
    background: var(--td-bg-color-code);
    border: 1px solid var(--td-border-level-1-color);
    border-radius: 6px;
    padding: 12px;
    overflow-x: auto;
    
    code {
      background: none;
      padding: 0;
    }
  }
}
</style>
```

---

# 6. 页面整合

## 6.1 首页右侧证据链

`src/views/HomePage.vue` (修改右侧部分)

```vue
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useEvidenceStore } from '@/stores/useEvidenceStore';
import { toGraphVM } from '@/utils/transform';
import EvidenceChain from '@/components/evidence/EvidenceChain.vue';

const store = useEvidenceStore();
const loading = ref(true);
const selectedId = ref(10); // 默认显示id=10的数据

const evidenceData = computed(() => store.record);
const graphData = computed(() => evidenceData.value ? toGraphVM(evidenceData.value) : null);

// 模拟选择不同的证据记录
const availableIds = [10, 11, 12]; // 示例ID列表

onMounted(async () => {
  await store.fetchEvidence(selectedId.value);
  loading.value = false;
});

async function handleIdChange(newId: number) {
  loading.value = true;
  selectedId.value = newId;
  await store.fetchEvidence(newId);
  loading.value = false;
}
</script>

<template>
  <div class="home-page">
    <!-- 左侧主要内容区域 -->
    <div class="main-content">
      <!-- 这里是原有的首页内容，如统计图表、快捷操作等 -->
      <div class="dashboard-cards">
        <!-- 原有的仪表板内容 -->
      </div>
    </div>
    
    <!-- 右侧证据链展示 -->
    <div class="evidence-sidebar">
      <div class="sidebar-header">
        <h3>最新证据链</h3>
        <t-select 
          v-model="selectedId" 
          :options="availableIds.map(id => ({ label: `证据记录 #${id}`, value: id }))"
          size="small"
          style="width: 120px;"
          @change="handleIdChange"
        />
      </div>
      
      <t-loading :loading="loading" size="small">
        <EvidenceChain 
          v-if="graphData" 
          :data="graphData" 
          compact
        />
        <div v-else class="empty-state">
          <t-empty description="暂无证据数据" size="small" />
        </div>
      </t-loading>
    </div>
  </div>
</template>

<style lang="less" scoped>
.home-page {
  display: flex;
  height: calc(100vh - 64px);
  gap: 16px;
  padding: 16px;
}

.main-content {
  flex: 1;
  overflow-y: auto;
}

.dashboard-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.evidence-sidebar {
  width: 400px;
  background: var(--td-bg-color-container);
  border: 1px solid var(--td-border-level-1-color);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--td-border-level-1-color);
  background: var(--td-bg-color-container-hover);
  
  h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
  }
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}
</style>
```

---

# 9. 工程考虑

## 9.1 图片资源管理

### 预签名URL处理
```typescript
// 在 Pinia store 中实现URL缓存和自动刷新
class ImageUrlManager {
  private cache = new Map<string, { url: string; expires: number }>();
  
  async getPresignedUrl(originalUrl: string): Promise<string> {
    const cached = this.cache.get(originalUrl);
    if (cached && Date.now() < cached.expires) {
      return cached.url;
    }
    
    // 重新获取预签名URL
    const response = await api.getPresignedUrls([originalUrl]);
    const presignedUrl = response.data[originalUrl];
    
    this.cache.set(originalUrl, {
      url: presignedUrl,
      expires: Date.now() + (response.expires_in - 300) * 1000 // 提前5分钟过期
    });
    
    return presignedUrl;
  }
}
```

### 图片加载错误处理
```vue
<img 
  :src="imageUrl" 
  @error="handleImageError"
  @load="handleImageLoad"
/>

<script>
const retryCount = ref(0);
const maxRetries = 3;

async function handleImageError() {
  if (retryCount.value < maxRetries) {
    retryCount.value++;
    // 重新获取预签名URL并重试
    imageUrl.value = await imageManager.getPresignedUrl(originalUrl);
  }
}
</script>
```

## 9.2 性能优化

### 图片懒加载
```vue
<img 
  v-lazy="imageUrl"
  :alt="evidence.title"
  class="evidence-thumb"
/>
```

### 虚拟滚动（大量步骤时）
```vue
<virtual-list
  :data-sources="nodes"
  :estimate-size="120"
  item-key="id"
>
  <template #item="{ item }">
    <StepCard :node="item" />
  </template>
</virtual-list>
```

## 9.3 安全考虑

### LLM内容安全
```typescript
import DOMPurify from 'dompurify';
import { marked } from 'marked';

const answerHtml = computed(() => {
  const rawHtml = marked.parse(props.llmData?.answer ?? '');
  return DOMPurify.sanitize(rawHtml, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'code', 'pre'],
    ALLOWED_ATTR: []
  });
});
```

### MinIO访问控制
- 预签名URL过期时间：1小时
- 实现访问频率限制：每分钟最多50次请求
- 生产环境强制HTTPS
- 配置CORS策略限制域名访问

## 9.4 扩展功能

### Canvas图像标注（可选）
```vue
<template>
  <div class="image-annotation">
    <canvas 
      ref="canvasRef" 
      :width="imageWidth" 
      :height="imageHeight"
      @click="handleAnnotationClick"
    />
  </div>
</template>

<script setup lang="ts">
interface BoundingBox {
  x: number; y: number; width: number; height: number;
  label: string; confidence: number;
}

function drawBoundingBoxes(boxes: BoundingBox[]) {
  const ctx = canvasRef.value?.getContext('2d');
  if (!ctx) return;
  
  boxes.forEach(box => {
    // 绘制边界框
    ctx.strokeStyle = '#ff4444';
    ctx.lineWidth = 2;
    ctx.strokeRect(box.x, box.y, box.width, box.height);
    
    // 绘制标签
    ctx.fillStyle = '#ff4444';
    ctx.font = '12px Arial';
    ctx.fillText(
      `${box.label} (${(box.confidence * 100).toFixed(1)}%)`,
      box.x, box.y - 5
    );
  });
}

// 分割掩码叠加
function drawSegmentationMask(maskData: Uint8Array, alpha = 0.5) {
  const ctx = canvasRef.value?.getContext('2d');
  if (!ctx) return;
  
  const imageData = ctx.createImageData(imageWidth, imageHeight);
  
  for (let i = 0; i < maskData.length; i++) {
    const pixelIndex = i * 4;
    if (maskData[i] > 0) {
      imageData.data[pixelIndex] = 255;     // R
      imageData.data[pixelIndex + 1] = 0;   // G
      imageData.data[pixelIndex + 2] = 0;   // B
      imageData.data[pixelIndex + 3] = alpha * 255; // A
    }
  }
  
  ctx.putImageData(imageData, 0, 0);
}
</script>
```

### 距离可视化
```vue
<div class="distance-visualization" v-if="node.metrics?.distances">
  <div class="distance-item" v-for="(distance, key) in node.metrics.distances" :key="key">
    <span class="distance-label">{{ key }}:</span>
    <div class="distance-bar">
      <div 
        class="distance-fill" 
        :style="{ width: `${Math.min(distance / 10 * 100, 100)}%` }"
      />
    </div>
    <span class="distance-value">{{ distance.toFixed(2) }}m</span>
  </div>
</div>
```

## 9.5 监控和调试

### 性能监控
```typescript
// 图片加载时间统计
const imageLoadTimes = new Map<string, number>();

function trackImageLoad(url: string, startTime: number) {
  const loadTime = Date.now() - startTime;
  imageLoadTimes.set(url, loadTime);
  
  if (loadTime > 3000) {
    console.warn(`Slow image load: ${url} took ${loadTime}ms`);
  }
}
```

### 错误上报
```typescript
function reportError(error: Error, context: string) {
  console.error(`[EvidenceChain] ${context}:`, error);
  // 可集成错误监控服务如Sentry
}
```

---

# 8. 后端接口适配

## 8.1 获取证据记录

```typescript
// GET /api/evidence/:id
// 返回完整的 EvidenceRecord 结构
interface EvidenceResponse {
  success: boolean;
  data: EvidenceRecord;
  message?: string;
}
```

## 8.2 获取预签名URL（MinIO）

```typescript
// POST /api/evidence/presign
// 请求体: { urls: string[] }
// 返回: { [originalUrl]: presignedUrl }
interface PresignRequest {
  urls: string[];
}

interface PresignResponse {
  success: boolean;
  data: Record<string, string>;
  expires_in: number; // 过期时间（秒）
}
```

## 8.3 获取证据列表

```typescript
// GET /api/evidence?page=1&limit=10&status=success
// 用于首页下拉选择
interface EvidenceListResponse {
  success: boolean;
  data: {
    items: Array<{
      id: number;
      created_at: string;
      status: string;
      summary?: string;
    }>;
    total: number;
    page: number;
    limit: number;
  };
}
```

**现有数据字段映射：**
- `image_refs`: MinIO存储的原始信息（bucket, object_name, size等）
- `image_urls`: 预签名URL（可能过期需要刷新）
- `analysis_results`: 各阶段AI分析结果
- `llm_output`: LLM的prompt和answer
- `task_info`: 任务执行信息（状态、耗时等）
- `system_info`: 系统版本信息

---

# 9. 实施步骤

## 阶段一：基础架构（1-2天）

1. **类型定义和数据模型**
   - [ ] 创建 `src/models/evidence.ts`
   - [ ] 定义 `EvidenceRecord`、`GraphVM`、`GraphNode` 等接口
   - [ ] 实现 `toGraphVM` 转换函数

2. **Pinia Store**
   - [ ] 创建 `src/stores/evidence.ts`
   - [ ] 实现数据获取和缓存逻辑
   - [ ] 添加图片URL管理功能

3. **API服务**
   - [ ] 创建 `src/api/evidence.ts`
   - [ ] 实现证据记录获取接口
   - [ ] 实现预签名URL获取接口

## 阶段二：核心组件（2-3天）

1. **步骤卡片组件**
   - [ ] 创建 `src/components/evidence/StepCard.vue`
   - [ ] 实现状态显示、指标展示、图片预览功能
   - [ ] 添加响应式设计和紧凑模式

2. **证据链主组件**
   - [ ] 创建 `src/components/evidence/EvidenceChain.vue`
   - [ ] 实现时间线布局和步骤卡片集成
   - [ ] 添加滚动优化和性能考虑

3. **辅助组件**
   - [ ] 创建 `src/components/evidence/ImagePreview.vue`
   - [ ] 创建 `src/components/evidence/LLMResult.vue`
   - [ ] 实现弹窗交互和内容展示

## 阶段三：页面集成（1天）

1. **首页集成**
   - [ ] 修改 `src/pages/HomePage.vue`
   - [ ] 添加右侧证据链展示区域
   - [ ] 实现证据记录选择功能

2. **样式优化**
   - [ ] 调整布局和间距
   - [ ] 确保响应式设计
   - [ ] 优化加载状态和错误处理

## 阶段四：优化和测试（1-2天）

1. **性能优化**
   - [ ] 实现图片懒加载
   - [ ] 添加虚拟滚动（如需要）
   - [ ] 优化预签名URL缓存策略

2. **错误处理**
   - [ ] 添加图片加载失败重试机制
   - [ ] 实现网络错误提示
   - [ ] 添加空状态处理

3. **安全加固**
   - [ ] 集成DOMPurify处理LLM内容
   - [ ] 验证图片URL安全性
   - [ ] 添加访问频率限制

---

# 10. 总结

## 10.1 方案特点

### 🎯 **简化设计**
- 从复杂的流程图改为直观的时间线展示
- 适合首页右侧快速预览的使用场景
- 保持了完整的功能性和可扩展性

### 🚀 **性能优化**
- 图片懒加载和预签名URL缓存
- 组件级别的性能优化
- 支持大量数据的虚拟滚动

### 🔒 **安全考虑**
- LLM内容的XSS防护
- MinIO访问控制和频率限制
- 图片资源的安全加载

### 🔧 **工程实践**
- TypeScript类型安全
- 组件化和模块化设计
- 完善的错误处理和监控

## 10.2 技术栈

- **前端框架**: Vue 3 + TypeScript
- **UI组件库**: TDesign Vue Next
- **状态管理**: Pinia
- **HTTP客户端**: Axios
- **Markdown渲染**: Marked
- **内容安全**: DOMPurify
- **样式预处理**: Less

## 10.3 扩展方向

1. **Canvas图像标注**: 支持边界框和分割掩码叠加
2. **实时更新**: WebSocket推送最新证据链状态
3. **导出功能**: 支持PDF或图片格式导出
4. **协作功能**: 多用户同时查看和标注
5. **移动端适配**: 响应式设计优化

## 10.4 预期效果

- **用户体验**: 直观的证据链展示，快速理解推理过程
- **开发效率**: 组件化设计便于维护和扩展
- **系统性能**: 优化的加载策略和缓存机制
- **安全性**: 完善的安全防护和访问控制

这个方案将为LineAegis系统提供一个现代化、高性能的证据链展示功能，既满足当前需求，又为未来扩展奠定了良好基础。

---

# 11. 基于实际数据的增强功能

**检测框叠加显示：**
基于 `analysis_results.detection.result.objects` 中的 bbox 数据，可以在原图上叠加检测框：
```typescript
// 检测框数据结构
interface DetectionObject {
  bbox: [number, number, number, number]; // [x1, y1, x2, y2]
  class_name: string; // 如 "DiaoChe"
  confidence: number; // 0.9484
}
```

**距离可视化增强：**
基于 `analysis_results.distances.result` 中的数据，可以显示：
- 检测框到最近导线的距离线
- 参考点和最近导线点的坐标
- 安全距离评估（< 20m 为危险）

**分割掩码叠加：**
`segmentation` 结果为图片文件，可以作为半透明叠加层显示在原图上。

**实际应用场景：**
- 输电线路巡检
- 机械入侵检测
- 安全距离评估
- 多阶段AI分析流程展示
