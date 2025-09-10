<template>
  <div class="step-origin">
    <div class="step-header">
      <h3>Step 1 - 原始图像</h3>
      <p>显示用户上传的原始输入图像</p>
    </div>
    
    <div class="step-content">
      <t-card class="image-card">
        <div v-if="data?.imageUrl" class="image-container">
          <img
            :src="data.imageUrl"
            :alt="'原始图像'"
            class="original-image"
            @load="onImageLoad"
            @error="onImageError"
          />
        </div>
        <div v-else class="empty-state">
          <t-empty
            description="原始图像不可用"
            image="https://tdesign.gtimg.com/pro-template/personal/empty.png"
          />
        </div>
      </t-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  data?: {
    type: string
    imageUrl?: string
  } | null
}

const props = defineProps<Props>()

const imageLoaded = ref(false)
const imageError = ref(false)

const onImageLoad = () => {
  imageLoaded.value = true
  imageError.value = false
  console.log('原始图像加载成功')
}

const onImageError = () => {
  imageError.value = true
  imageLoaded.value = false
  console.error('原始图像加载失败')
}
</script>

<style scoped>
.step-origin {
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
  display: flex;
  justify-content: center;
  align-items: center;
}

.image-card {
  width: 100%;
  max-width: 800px;
  min-height: 400px;
}

.image-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.original-image {
  max-width: 100%;
  max-height: 600px;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: transform 0.3s ease;
}

.original-image:hover {
  transform: scale(1.02);
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .step-header h3 {
    font-size: 18px;
  }
  
  .image-card {
    min-height: 300px;
  }
  
  .image-container {
    min-height: 300px;
  }
  
  .original-image {
    max-height: 400px;
  }
}
</style>
