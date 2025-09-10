<template>
  <div class="step-distances">
    <div class="step-header">
      <h3>Step 5 - 距离可视化</h3>
      <p>可视化距离测量结果</p>
    </div>
    
    <div class="step-content">
      <div class="distances-layout">
        <!-- 左侧：距离可视化图像 -->
        <div class="image-section">
          <t-card class="image-card">
            <div v-if="data?.imageUrl" class="image-container">
              <img
                :src="data.imageUrl"
                :alt="'距离可视化图像'"
                class="distances-image"
                @load="onImageLoad"
                @error="onImageError"
              />
            </div>
            <div v-else class="empty-state">
              <t-empty
                description="距离可视化图像不可用"
                image="https://tdesign.gtimg.com/pro-template/personal/empty.png"
              />
            </div>
          </t-card>
        </div>
        
        <!-- 右侧：距离数据表格 -->
        <div class="data-section">
          <t-card class="data-card">
            <template #header>
              <h4>距离测量结果</h4>
            </template>
            
            <div v-if="data?.result && data.result.result.length > 0" class="distances-data">
              <!-- 距离统计 -->
              <div class="distance-stats">
                <t-descriptions :column="2" size="small">
                  <t-descriptions-item label="测量点数量">
                    {{ data.result.result.length }}
                  </t-descriptions-item>
                  <t-descriptions-item label="平均距离">
                    {{ averageDistance }}
                  </t-descriptions-item>
                  <t-descriptions-item label="最小距离">
                    {{ minDistance }}
                  </t-descriptions-item>
                  <t-descriptions-item label="最大距离">
                    {{ maxDistance }}
                  </t-descriptions-item>
                </t-descriptions>
              </div>
              
              <!-- 距离表格 -->
              <div class="distance-table">
                <h5>详细测量数据</h5>
                <t-table
                  :data="data.result.result"
                  :columns="distanceColumns"
                  row-key="box_index"
                  size="small"
                  :hover="true"
                  :highlight-current-row="true"
                  @row-click="onTableRowClick"
                />
              </div>
            </div>
            
            <!-- 无距离数据 -->
            <div v-else class="no-data">
              <t-empty
                description="距离测量数据不可用"
                image="https://tdesign.gtimg.com/pro-template/personal/empty.png"
              />
            </div>
          </t-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { DistanceRow } from '@/models/chatdb-chain'

interface Props {
  data?: {
    type: string
    imageUrl?: string
    result?: {
      result: DistanceRow[]
    }
  } | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  tableRowClick: [rowIndex: number]
}>()

const imageLoaded = ref(false)
const imageError = ref(false)

// 表格列定义
const distanceColumns = [
  {
    colKey: 'box_index',
    title: '目标序号',
    width: 80
  },
  {
    colKey: 'distance_meters',
    title: '距离(m)',
    width: 100,
    render: (h: any, { row }: any) => row.distance_meters.toFixed(2)
  },
  {
    colKey: 'box_coords',
    title: '目标坐标',
    width: 150,
    render: (h: any, { row }: any) => {
      const [x, y, w, height] = row.box_coords
      return `(${x}, ${y}, ${w}, ${height})`
    }
  },
  {
    colKey: 'nearest_wire_point',
    title: '最近导线点',
    width: 120,
    render: (h: any, { row }: any) => {
      const { x, y } = row.nearest_wire_point
      return `(${x}, ${y})`
    }
  }
]

// 计算属性
const averageDistance = computed(() => {
  if (!props.data?.result?.result || !Array.isArray(props.data.result.result) || props.data.result.result.length === 0) return '—'
  const total = props.data.result.result.reduce((sum, item) => sum + item.distance_meters, 0)
  return `${(total / props.data.result.result.length).toFixed(2)}m`
})

const minDistance = computed(() => {
  if (!props.data?.result?.result || !Array.isArray(props.data.result.result) || props.data.result.result.length === 0) return '—'
  const min = Math.min(...props.data.result.result.map(item => item.distance_meters))
  return `${min.toFixed(2)}m`
})

const maxDistance = computed(() => {
  if (!props.data?.result?.result || !Array.isArray(props.data.result.result) || props.data.result.result.length === 0) return '—'
  const max = Math.max(...props.data.result.result.map(item => item.distance_meters))
  return `${max.toFixed(2)}m`
})

const onImageLoad = () => {
  imageLoaded.value = true
  imageError.value = false
  console.log('距离可视化图像加载成功')
}

const onImageError = () => {
  imageError.value = true
  imageLoaded.value = false
  console.error('距离可视化图像加载失败')
}

const onTableRowClick = (context: any) => {
  const rowIndex = context.rowIndex
  emit('tableRowClick', rowIndex)
  console.log('表格行点击:', rowIndex)
}
</script>

<style scoped>
.step-distances {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.step-header {
  margin-bottom: 20px;
  text-align: center;
}

.step-header h3 {
  margin: 0 0 8px 0;
  color: var(--td-text-color-primary);
  font-size: 20px;
  font-weight: 600;
}

.step-header p {
  margin: 0;
  color: var(--td-text-color-secondary);
  font-size: 14px;
}

.step-content {
  flex: 1;
}

.distances-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  height: 100%;
}

.image-section {
  display: flex;
  flex-direction: column;
}

.image-card {
  flex: 1;
  min-height: 400px;
}

.image-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.distances-image {
  max-width: 100%;
  max-height: 500px;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: transform 0.3s ease;
}

.distances-image:hover {
  transform: scale(1.02);
}

.data-section {
  display: flex;
  flex-direction: column;
}

.data-card {
  flex: 1;
  min-height: 400px;
}

.distances-data {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.distance-stats {
  padding: 16px;
  background: var(--td-bg-color-page);
  border-radius: 6px;
  border: 1px solid var(--td-border-level-1-color);
}

.distance-table {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.distance-table h5 {
  margin: 0 0 12px 0;
  color: var(--td-text-color-primary);
  font-size: 16px;
  font-weight: 600;
}

.empty-state,
.no-data {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

/* 表格样式优化 */
:deep(.t-table) {
  font-size: 13px;
}

:deep(.t-table__row) {
  cursor: pointer;
}

:deep(.t-table__row:hover) {
  background-color: var(--td-bg-color-container-hover);
}

:deep(.t-table__row--current) {
  background-color: var(--td-brand-color-light);
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .distances-layout {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .image-card,
  .data-card {
    min-height: 300px;
  }
  
  .image-container {
    min-height: 300px;
  }
  
  .distances-image {
    max-height: 400px;
  }
}

@media (max-width: 768px) {
  .step-header h3 {
    font-size: 18px;
  }
  
  .distances-layout {
    gap: 12px;
  }
  
  .image-card,
  .data-card {
    min-height: 250px;
  }
  
  .image-container {
    min-height: 250px;
  }
  
  .distances-image {
    max-height: 300px;
  }
  
  .distance-stats {
    padding: 12px;
  }
  
  :deep(.t-descriptions) {
    --td-descriptions-columns: 1;
  }
}
</style>
