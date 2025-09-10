<template>
  <div class="step-segmentation">
    <div class="step-header">
      <h3>Step 3 - 导线分割</h3>
      <p>分割图像中的导线区域</p>
    </div>
    
    <div class="step-content">
      <div class="segmentation-layout">
        <!-- 左侧：分割结果图像 -->
        <div class="image-section">
          <t-card class="image-card">
            <div v-if="data?.imageUrl" class="image-container">
              <div v-if="!imageError">
                <img
                  :src="data.imageUrl"
                  :alt="'分割结果图像'"
                  class="segmentation-image"
                  @load="onImageLoad"
                  @error="onImageError"
                />
              </div>
              <div v-else class="image-error-state">
                <t-result
                  status="error"
                  title="图片加载失败"
                  :description="`无法加载分割结果图像: ${data.imageUrl}`"
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
                description="分割结果图像不可用"
                image="https://tdesign.gtimg.com/pro-template/personal/empty.png"
              />
            </div>
          </t-card>
        </div>
        
        <!-- 右侧：分割结果数据 -->
        <div class="data-section">
          <t-card class="data-card">
            <template #header>
              <h4>分割结果</h4>
            </template>
            
            <div v-if="data?.result" class="segmentation-data">
              <div class="result-content">
                <h5>分割分析</h5>
                <div class="result-text">
                  <p v-if="data.result.result">
                    {{ data.result.result }}
                  </p>
                  <p v-else class="no-result-text">
                    分割结果数据不可用
                  </p>
                </div>
              </div>
              
              <!-- 分割统计信息 -->
              <div class="segmentation-stats">
                <t-descriptions :column="1" size="small">
                  <t-descriptions-item label="分割状态">
                    <t-tag theme="success" variant="light">
                      已完成
                    </t-tag>
                  </t-descriptions-item>
                  <t-descriptions-item label="处理时间">
                    {{ processingTime }}
                  </t-descriptions-item>
                </t-descriptions>
              </div>
            </div>
            
            <!-- 无分割数据 -->
            <div v-else class="no-data">
              <t-empty
                description="分割数据不可用"
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
import { ref, nextTick } from 'vue'

interface Props {
  data?: {
    type: string
    imageUrl?: string
    result?: {
      result?: string
    }
  } | null
}

const props = defineProps<Props>()

const imageLoaded = ref(false)
const imageError = ref(false)
const processingTime = ref('约 0.3 秒')

const onImageLoad = () => {
  imageLoaded.value = true
  imageError.value = false
  console.log('分割图像加载成功')
}

const onImageError = (event: Event) => {
  imageError.value = true
  imageLoaded.value = false
  console.error('分割图像加载失败:', event)
  
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
.step-segmentation {
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

.segmentation-layout {
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

.segmentation-image {
  max-width: 100%;
  max-height: 500px;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: transform 0.3s ease;
}

.segmentation-image:hover {
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

.segmentation-data {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.result-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.result-content h5 {
  margin: 0 0 16px 0;
  color: var(--td-text-color-primary);
  font-size: 16px;
  font-weight: 600;
}

.result-text {
  flex: 1;
  padding: 16px;
  background: var(--td-bg-color-page);
  border-radius: 6px;
  border: 1px solid var(--td-border-level-1-color);
}

.result-text p {
  margin: 0;
  color: var(--td-text-color-primary);
  line-height: 1.6;
  white-space: pre-wrap;
}

.no-result-text {
  color: var(--td-text-color-placeholder) !important;
  font-style: italic;
}

.segmentation-stats {
  padding: 16px;
  background: var(--td-bg-color-page);
  border-radius: 6px;
  border: 1px solid var(--td-border-level-1-color);
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
  .segmentation-layout {
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
  
  .segmentation-image {
    max-height: 400px;
  }
}

@media (max-width: 768px) {
  .step-header h3 {
    font-size: 18px;
  }
  
  .segmentation-layout {
    gap: 12px;
  }
  
  .image-card,
  .data-card {
    min-height: 250px;
  }
  
  .image-container {
    min-height: 250px;
  }
  
  .segmentation-image {
    max-height: 300px;
  }
}
</style>
