<template>
  <div class="step-depth">
    <div class="step-header">
      <h3>Step 4 - 全图深度</h3>
      <p>计算图像深度信息</p>
    </div>
    
    <div class="step-content">
      <div class="depth-layout">
        <!-- 左侧：深度图像 -->
        <div class="image-section">
          <t-card class="image-card">
            <div v-if="data?.imageUrl" class="image-container">
              <div v-if="!imageError">
                <img
                  :src="data.imageUrl"
                  :alt="'深度图像'"
                  class="depth-image"
                  @load="onImageLoad"
                  @error="onImageError"
                />
              </div>
              <div v-else class="image-error-state">
                <t-result
                  status="error"
                  title="图片加载失败"
                  :description="`无法加载深度图像: ${data.imageUrl}`"
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
                description="深度图像不可用"
                image="https://tdesign.gtimg.com/pro-template/personal/empty.png"
              />
            </div>
          </t-card>
        </div>
        
        <!-- 右侧：深度数据 -->
        <div class="data-section">
          <t-card class="data-card">
            <template #header>
              <h4>深度信息</h4>
            </template>
            
            <div v-if="data?.result" class="depth-data">
              <!-- 深度统计 -->
              <div class="depth-stats">
                <h5>深度统计</h5>
                <t-descriptions :column="1" size="small">
                  <t-descriptions-item label="最小深度">
                    <span class="depth-value">
                      {{ data.result.depth_min !== undefined ? `${data.result.depth_min.toFixed(2)}m` : '—' }}
                    </span>
                  </t-descriptions-item>
                  <t-descriptions-item label="最大深度">
                    <span class="depth-value">
                      {{ data.result.depth_max !== undefined ? `${data.result.depth_max.toFixed(2)}m` : '—' }}
                    </span>
                  </t-descriptions-item>
                  <t-descriptions-item label="焦距">
                    <span class="depth-value">
                      {{ data.result.focal_length !== undefined ? `${data.result.focal_length.toFixed(2)}mm` : '—' }}
                    </span>
                  </t-descriptions-item>
                </t-descriptions>
              </div>
              
              <!-- 深度范围可视化 -->
              <div class="depth-range">
                <h5>深度范围</h5>
                <div class="range-bar">
                  <div class="range-track">
                    <div 
                      class="range-fill"
                      :style="{ width: depthRangePercentage + '%' }"
                    />
                  </div>
                  <div class="range-labels">
                    <span class="min-label">{{ minDepthText }}</span>
                    <span class="max-label">{{ maxDepthText }}</span>
                  </div>
                </div>
              </div>
              
              <!-- 深度分析 -->
              <div class="depth-analysis">
                <h5>深度分析</h5>
                <div class="analysis-content">
                  <p v-if="depthAnalysisText">
                    {{ depthAnalysisText }}
                  </p>
                  <p v-else class="no-analysis">
                    深度分析数据不可用
                  </p>
                </div>
              </div>
            </div>
            
            <!-- 无深度数据 -->
            <div v-else class="no-data">
              <t-empty
                description="深度数据不可用"
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
import { ref, computed, nextTick } from 'vue'
import type { DepthResult } from '@/models/chatdb-chain'

interface Props {
  data?: {
    type: string
    imageUrl?: string
    result?: DepthResult
  } | null
}

const props = defineProps<Props>()

const imageLoaded = ref(false)
const imageError = ref(false)

// 计算属性
const minDepthText = computed(() => {
  return props.data?.result?.depth_min !== undefined 
    ? `${props.data.result.depth_min.toFixed(2)}m` 
    : '0.00m'
})

const maxDepthText = computed(() => {
  return props.data?.result?.depth_max !== undefined 
    ? `${props.data.result.depth_max.toFixed(2)}m` 
    : '0.00m'
})

const depthRangePercentage = computed(() => {
  const min = props.data?.result?.depth_min || 0
  const max = props.data?.result?.depth_max || 0
  if (max === 0) return 0
  return Math.min((min / max) * 100, 100)
})

const depthAnalysisText = computed(() => {
  const result = props.data?.result
  if (!result) return ''
  
  const min = result.depth_min
  const max = result.depth_max
  const focal = result.focal_length
  
  if (min === undefined || max === undefined) return ''
  
  const range = max - min
  const avgDepth = (min + max) / 2
  
  let analysis = `深度范围: ${range.toFixed(2)}m，平均深度: ${avgDepth.toFixed(2)}m。`
  
  if (focal !== undefined) {
    analysis += ` 使用焦距: ${focal.toFixed(2)}mm。`
  }
  
  if (range < 1) {
    analysis += ' 场景深度变化较小，适合近距离分析。'
  } else if (range < 5) {
    analysis += ' 场景具有中等深度变化。'
  } else {
    analysis += ' 场景具有较大深度变化，需要关注远近物体的差异。'
  }
  
  return analysis
})

const onImageLoad = () => {
  imageLoaded.value = true
  imageError.value = false
  console.log('深度图像加载成功')
}

const onImageError = (event: Event) => {
  imageError.value = true
  imageLoaded.value = false
  console.error('深度图像加载失败:', event)
  
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
  // 触发重新渲染
  nextTick(() => {
    // 图片会自动重新加载
  })
}
</script>

<style scoped>
.step-depth {
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

.depth-layout {
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

.depth-image {
  max-width: 100%;
  max-height: 500px;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: transform 0.3s ease;
}

.depth-image:hover {
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

.depth-data {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.depth-stats,
.depth-range,
.depth-analysis {
  padding: 16px;
  background: var(--td-bg-color-page);
  border-radius: 6px;
  border: 1px solid var(--td-border-level-1-color);
}

.depth-stats h5,
.depth-range h5,
.depth-analysis h5 {
  margin: 0 0 16px 0;
  color: var(--td-text-color-primary);
  font-size: 16px;
  font-weight: 600;
}

.depth-value {
  font-weight: 600;
  color: var(--td-brand-color);
}

.range-bar {
  margin-top: 12px;
}

.range-track {
  height: 8px;
  background: var(--td-bg-color-component);
  border-radius: 4px;
  position: relative;
  overflow: hidden;
}

.range-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--td-brand-color), var(--td-warning-color));
  border-radius: 4px;
  transition: width 0.3s ease;
}

.range-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: var(--td-text-color-secondary);
}

.analysis-content p {
  margin: 0;
  color: var(--td-text-color-primary);
  line-height: 1.6;
}

.no-analysis {
  color: var(--td-text-color-placeholder) !important;
  font-style: italic;
}

.empty-state,
.no-data {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .depth-layout {
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
  
  .depth-image {
    max-height: 400px;
  }
}

@media (max-width: 768px) {
  .step-header h3 {
    font-size: 18px;
  }
  
  .depth-layout {
    gap: 12px;
  }
  
  .image-card,
  .data-card {
    min-height: 250px;
  }
  
  .image-container {
    min-height: 250px;
  }
  
  .depth-image {
    max-height: 300px;
  }
}
</style>
