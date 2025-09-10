<template>
  <div class="step-detection">
    <div class="step-header">
      <h3>Step 2 - 目标检测</h3>
      <p>检测图像中的目标对象并显示边界框</p>
    </div>
    
    <div class="step-content">
      <div class="detection-layout">
        <!-- 左侧：检测结果图像 -->
        <div class="image-section">
          <t-card class="image-card">
            <div v-if="data?.imageUrl" class="image-container">
              <div v-if="!imageError" class="canvas-wrapper">
                <img
                  ref="detectionImage"
                  :src="data.imageUrl"
                  :alt="'检测结果图像'"
                  class="detection-image"
                  @load="onImageLoad"
                  @error="onImageError"
                />
                <canvas
                  ref="bboxCanvas"
                  class="bbox-canvas"
                  @click="onCanvasClick"
                />
              </div>
              <div v-else class="image-error-state">
                <t-result
                  status="error"
                  title="图片加载失败"
                  :description="`无法加载检测结果图像: ${data.imageUrl}`"
                >
                  <template #extra>
                    <t-button theme="primary" @click="retryImageLoad">
                      重试加载
                    </t-button>
                  </template>
                </t-result>
              </div>
            </div>
            <div v-else class="empty-state">
              <t-empty
                description="检测结果图像不可用"
                image="https://tdesign.gtimg.com/pro-template/personal/empty.png"
              />
            </div>
          </t-card>
        </div>
        
        <!-- 右侧：检测结果数据 -->
        <div class="data-section">
          <t-card class="data-card">
            <template #header>
              <h4>检测结果</h4>
            </template>
            
            <div v-if="data?.result" class="detection-data">
              <!-- 检测统计 -->
              <div class="detection-stats">
                <t-descriptions :column="1" size="small">
                  <t-descriptions-item label="检测对象数量">
                    {{ data.result.count || 0 }}
                  </t-descriptions-item>
                  <t-descriptions-item label="检测结果" v-if="data.result.result">
                    {{ data.result.result }}
                  </t-descriptions-item>
                </t-descriptions>
              </div>
              
              <!-- 检测对象表格 -->
              <div v-if="data.result.objects && data.result.objects.length > 0" class="objects-table">
                <h5>检测对象详情</h5>
                <t-table
                  :data="data.result.objects"
                  :columns="objectColumns"
                  row-key="index"
                  size="small"
                  :hover="true"
                  @row-click="onTableRowClick"
                />
              </div>
              
              <!-- 无检测对象 -->
              <div v-else class="no-objects">
                <t-empty
                  description="未检测到目标对象"
                  image="https://tdesign.gtimg.com/pro-template/personal/empty.png"
                />
              </div>
            </div>
            
            <!-- 无检测数据 -->
            <div v-else class="no-data">
              <t-empty
                description="检测数据不可用"
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
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import type { DetectionObject } from '@/models/chatdb-chain'

interface Props {
  data?: {
    type: string
    imageUrl?: string
    result?: {
      count: number
      objects: DetectionObject[]
      result?: string
    }
  } | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  bboxClick: [bboxIndex: number]
}>()

const detectionImage = ref<HTMLImageElement>()
const bboxCanvas = ref<HTMLCanvasElement>()

const imageLoaded = ref(false)
const imageError = ref(false)
const highlightedBbox = ref<number | null>(null)

// 表格列定义
const objectColumns = [
  {
    colKey: 'index',
    title: '序号',
    width: 60,
    render: (h: any, { rowIndex }: any) => rowIndex + 1
  },
  {
    colKey: 'class_name',
    title: '类别',
    width: 100
  },
  {
    colKey: 'confidence',
    title: '置信度',
    width: 100,
    render: (h: any, { row }: any) => `${(row.confidence * 100).toFixed(1)}%`
  },
  {
    colKey: 'bbox',
    title: '边界框',
    width: 200,
    render: (h: any, { row }: any) => {
      const [x, y, w, height] = row.bbox
      return `(${x}, ${y}, ${w}, ${height})`
    }
  }
]

const onImageLoad = () => {
  imageLoaded.value = true
  imageError.value = false
  nextTick(() => {
    drawBoundingBoxes()
  })
}

const onImageError = (event: Event) => {
  imageError.value = true
  imageLoaded.value = false
  console.error('检测图像加载失败:', event)
  
  // 显示更详细的错误信息
  const img = event.target as HTMLImageElement
  if (img) {
    console.error('失败的图片URL:', img.src)
    console.error('错误详情:', {
      naturalWidth: img.naturalWidth,
      naturalHeight: img.naturalHeight,
      complete: img.complete
    })
  }
}

const retryImageLoad = () => {
  imageError.value = false
  imageLoaded.value = false
  
  // 强制重新加载图片
  if (detectionImage.value) {
    const currentSrc = detectionImage.value.src
    detectionImage.value.src = ''
    setTimeout(() => {
      if (detectionImage.value) {
        detectionImage.value.src = currentSrc
      }
    }, 100)
  }
}

const drawBoundingBoxes = () => {
  if (!bboxCanvas.value || !detectionImage.value || !props.data?.result?.objects) return
  
  const canvas = bboxCanvas.value
  const img = detectionImage.value
  const ctx = canvas.getContext('2d')
  
  if (!ctx) return
  
  // 设置canvas尺寸与图像一致
  canvas.width = img.offsetWidth
  canvas.height = img.offsetHeight
  
  // 清空canvas
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  
  // 绘制边界框
  if (props.data.result.objects && Array.isArray(props.data.result.objects)) {
    props.data.result.objects.forEach((obj, index) => {
      const [x, y, w, h] = obj.bbox
    
    // 设置样式
    ctx.strokeStyle = highlightedBbox.value === index ? '#ff4d4f' : '#00b4d8'
    ctx.lineWidth = highlightedBbox.value === index ? 3 : 2
    ctx.fillStyle = highlightedBbox.value === index ? 'rgba(255, 77, 79, 0.2)' : 'rgba(0, 180, 216, 0.1)'
    
    // 绘制边界框
    ctx.fillRect(x, y, w, h)
    ctx.strokeRect(x, y, w, h)
    
    // 绘制标签
    ctx.fillStyle = highlightedBbox.value === index ? '#ff4d4f' : '#00b4d8'
    ctx.font = '12px Arial'
    ctx.fillText(
      `${obj.class_name} (${(obj.confidence * 100).toFixed(1)}%)`,
      x,
      y - 5
    )
    })
  }
}

const onCanvasClick = (event: MouseEvent) => {
  if (!bboxCanvas.value || !props.data?.result?.objects) return
  
  const canvas = bboxCanvas.value
  const rect = canvas.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  // 检查点击是否在某个边界框内
  const clickedIndex = props.data.result.objects && Array.isArray(props.data.result.objects) 
    ? props.data.result.objects.findIndex(obj => {
        const [bx, by, bw, bh] = obj.bbox
        return x >= bx && x <= bx + bw && y >= by && y <= by + bh
      })
    : -1
  
  if (clickedIndex !== -1) {
    highlightedBbox.value = clickedIndex
    drawBoundingBoxes()
    emit('bboxClick', clickedIndex)
  }
}

const onTableRowClick = (context: any) => {
  const rowIndex = context.rowIndex
  highlightedBbox.value = rowIndex
  drawBoundingBoxes()
  emit('bboxClick', rowIndex)
}

// 监听数据变化，重新绘制边界框
watch(() => props.data, () => {
  if (imageLoaded.value) {
    nextTick(() => {
      drawBoundingBoxes()
    })
  }
}, { deep: true })

// 监听窗口大小变化
const handleResize = () => {
  if (imageLoaded.value) {
    nextTick(() => {
      drawBoundingBoxes()
    })
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.step-detection {
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

.detection-layout {
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
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.canvas-wrapper {
  position: relative;
  display: inline-block;
}

.detection-image {
  max-width: 100%;
  max-height: 500px;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.bbox-canvas {
  position: absolute;
  top: 0;
  left: 0;
  cursor: pointer;
  border-radius: 8px;
}

.data-section {
  display: flex;
  flex-direction: column;
}

.data-card {
  flex: 1;
  min-height: 400px;
}

.detection-data {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detection-stats {
  padding: 16px;
  background: var(--td-bg-color-page);
  border-radius: 6px;
}

.objects-table {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.objects-table h5 {
  margin: 0 0 12px 0;
  color: var(--td-text-color-primary);
  font-size: 16px;
  font-weight: 600;
}

.empty-state,
.no-objects,
.no-data {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .detection-layout {
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
  
  .detection-image {
    max-height: 400px;
  }
}

@media (max-width: 768px) {
  .step-header h3 {
    font-size: 18px;
  }
  
  .detection-layout {
    gap: 12px;
  }
  
  .image-card,
  .data-card {
    min-height: 250px;
  }
  
  .image-container {
    min-height: 250px;
  }
  
  .detection-image {
    max-height: 300px;
  }
}
</style>
