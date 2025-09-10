<template>
  <div class="image-gallery" v-if="imageUrls.length > 0">
    <h4>相关图片</h4>
    <div class="image-grid">
      <div 
        v-for="(image, index) in imageUrls" 
        :key="index" 
        class="image-item"
      >
        <div class="image-header">
          <span class="image-type">{{ image.type }}</span>
          <span class="image-size" v-if="image.size">{{ formatFileSize(image.size) }}</span>
        </div>
        <div class="image-container">
          <img 
            :src="image.url" 
            :alt="`${image.type} 图片`"
            class="preview-image"
            @click="openImageModal(image.url)"
            @error="handleImageError($event, image)"
          />
        </div>
      </div>
    </div>
    
    <!-- 图片模态框 -->
    <div v-if="showImageModal" class="image-modal" @click="closeImageModal">
      <div class="modal-content" @click.stop>
        <span class="close-btn" @click="closeImageModal">&times;</span>
        <img :src="currentImageUrl" alt="放大图片" class="modal-image" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface ImageInfo {
  type: string
  url: string
  size?: number
}

interface Props {
  imageRefs?: string | object | null
}

const props = defineProps<Props>()

const showImageModal = ref(false)
const currentImageUrl = ref('')

// 解析图片URL信息
const imageUrls = computed(() => {
  if (!props.imageRefs) return []
  
  try {
    // 如果imageRefs已经是对象，直接使用；如果是字符串，则解析
    const refs = typeof props.imageRefs === 'string' ? JSON.parse(props.imageRefs) : props.imageRefs
    const images: ImageInfo[] = []
    
    // 处理不同类型的图片引用
    if (refs.depth_image_url) {
      images.push({
        type: 'depth',
        url: refs.depth_image_url,
        size: refs.depth_image_size
      })
    }
    
    if (refs.original_image_url) {
      images.push({
        type: 'original',
        url: refs.original_image_url,
        size: refs.original_image_size
      })
    }
    
    if (refs.detection_image_url) {
      images.push({
        type: 'detection',
        url: refs.detection_image_url,
        size: refs.detection_image_size
      })
    }
    
    // 处理其他可能的图片类型
    Object.keys(refs).forEach(key => {
      if (key.endsWith('_image_url') && !['depth_image_url', 'original_image_url', 'detection_image_url'].includes(key)) {
        const type = key.replace('_image_url', '')
        const sizeKey = `${type}_image_size`
        images.push({
          type,
          url: refs[key],
          size: refs[sizeKey]
        })
      }
    })
    
    return images
  } catch (error) {
    console.error('解析图片引用失败:', error)
    return []
  }
})

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (!bytes) return ''
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

// 打开图片模态框
const openImageModal = (imageUrl: string) => {
  currentImageUrl.value = imageUrl
  showImageModal.value = true
}

// 关闭图片模态框
const closeImageModal = () => {
  showImageModal.value = false
  currentImageUrl.value = ''
}

// 处理图片加载错误
const handleImageError = (event: Event, image: ImageInfo) => {
  const target = event.target as HTMLImageElement
  target.style.display = 'none'
  console.error(`图片加载失败: ${image.type} - ${image.url}`)
}
</script>

<style scoped>
.image-gallery {
  margin-top: 16px;
  padding: 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background-color: #fafafa;
}

.image-gallery h4 {
  margin: 0 0 12px 0;
  color: #333;
  font-size: 14px;
  font-weight: 600;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.image-item {
  border: 1px solid #ddd;
  border-radius: 6px;
  overflow: hidden;
  background: white;
  transition: box-shadow 0.2s;
}

.image-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.image-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: #f5f5f5;
  border-bottom: 1px solid #eee;
}

.image-type {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
}

.image-size {
  font-size: 11px;
  color: #999;
}

.image-container {
  position: relative;
  height: 120px;
  overflow: hidden;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  cursor: pointer;
  transition: transform 0.2s;
}

.preview-image:hover {
  transform: scale(1.05);
}

/* 图片模态框样式 */
.image-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  position: relative;
  max-width: 90%;
  max-height: 90%;
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.close-btn {
  position: absolute;
  top: 10px;
  right: 15px;
  color: white;
  background: rgba(0, 0, 0, 0.5);
  border: none;
  font-size: 24px;
  font-weight: bold;
  cursor: pointer;
  z-index: 1001;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: rgba(0, 0, 0, 0.7);
}

.modal-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
</style>