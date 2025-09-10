<template>
  <div class="image-gallery" v-if="imageUrls.length > 0">
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
            @error="handleImageError(image, $event)"
            @load="handleImageLoad(image, $event)"
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
  <div v-else class="no-images">
    <div class="debug-info" style="background: #ffe6e6; padding: 10px; margin-bottom: 10px; font-size: 12px;">
      <strong>调试信息:</strong> 未找到图片数据
      <div>imageRefs 类型: {{ typeof imageRefs }}</div>
      <div>imageRefs 内容: {{ imageRefs ? JSON.stringify(imageRefs).substring(0, 200) + '...' : 'null/undefined' }}</div>
    </div>
    <p>暂无图片</p>
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
  console.log('=== ImageGallery Debug Start ===')
  console.log('ImageGallery - Raw imageRefs:', props.imageRefs)
  console.log('ImageGallery - imageRefs type:', typeof props.imageRefs)
  console.log('ImageGallery - imageRefs length:', props.imageRefs ? Object.keys(props.imageRefs as any).length : 0)
  
  if (!props.imageRefs) {
    console.log('ImageGallery - No imageRefs provided, returning empty array')
    return []
  }
  
  try {
    // 如果imageRefs已经是对象，直接使用；如果是字符串，则解析
    let refs: any
    if (typeof props.imageRefs === 'string') {
      refs = JSON.parse(props.imageRefs)
      console.log('ImageGallery - Successfully parsed string imageRefs:', refs)
    } else {
      refs = props.imageRefs
      console.log('ImageGallery - Using object imageRefs:', refs)
    }
    
    console.log('ImageGallery - Available keys in refs:', Object.keys(refs))
    
    const images: ImageInfo[] = []
    
    // 优先处理后端生成的预签名URL（image_urls字段）
    if (refs.image_urls) {
      console.log('ImageGallery - Found image_urls field')
      console.log('ImageGallery - image_urls type:', typeof refs.image_urls)
      console.log('ImageGallery - image_urls is array:', Array.isArray(refs.image_urls))
      console.log('ImageGallery - image_urls content:', refs.image_urls)
      console.log('ImageGallery - image_urls keys:', Object.keys(refs.image_urls))
      
      if (Array.isArray(refs.image_urls)) {
        console.log('ImageGallery - Processing image_urls array with', refs.image_urls.length, 'items')
        refs.image_urls.forEach((url: string, index: number) => {
          console.log(`ImageGallery - Processing image_urls[${index}]:`, url)
          if (url && typeof url === 'string') {
            // 从 image_refs 获取对应的 size 信息
            let size: number | undefined
            if (refs.image_refs && Array.isArray(refs.image_refs) && refs.image_refs[index]) {
              const ref = refs.image_refs[index]
              console.log(`ImageGallery - Found image_refs[${index}]:`, ref)
              if (ref.size) {
                size = ref.size
                console.log(`ImageGallery - Using size from image_refs[${index}]:`, size)
              }
            }
            
            const imageObj = {
              type: `image_${index + 1}`,
              url: url,
              size: size
            }
            console.log(`ImageGallery - Adding image object:`, imageObj)
            images.push(imageObj)
          } else {
            console.warn(`ImageGallery - Skipping invalid URL at index ${index}:`, url)
          }
        })
      } else {
        console.log('ImageGallery - Processing image_urls as object')
        Object.keys(refs.image_urls).forEach((key: string) => {
          const url = refs.image_urls[key]
          console.log(`ImageGallery - Processing key '${key}':`, url)
          
          if (url && typeof url === 'string' && (url.startsWith('http') || url.startsWith('/'))) {
            // 尝试从image_refs中获取对应的size信息
            let size: number | undefined
            if (refs.image_refs && refs.image_refs[key]) {
              size = refs.image_refs[key].size
              console.log(`ImageGallery - Found size for ${key}:`, size)
            }
            
            const imageObj = {
              type: key,
              url: url,
              size: size
            }
            console.log(`ImageGallery - Adding image from object:`, imageObj)
            images.push(imageObj)
          } else {
            console.warn(`ImageGallery - Skipping invalid URL for key ${key}:`, url)
          }
        })
      }
    } else {
      console.log('ImageGallery - No image_urls field found')
    }
    
    // 如果没有image_urls字段，则处理直接的图片URL字段（向后兼容）
    if (images.length === 0) {
      console.log('ImageGallery - No images from image_urls, trying legacy fields')
      
      // 处理不同类型的图片引用
      if (refs.depth_image_url) {
        console.log('ImageGallery - Found depth_image_url:', refs.depth_image_url)
        images.push({
          type: 'depth',
          url: refs.depth_image_url,
          size: refs.depth_image_size
        })
      }
      
      if (refs.original_image_url) {
        console.log('ImageGallery - Found original_image_url:', refs.original_image_url)
        images.push({
          type: 'original',
          url: refs.original_image_url,
          size: refs.original_image_size
        })
      }
      
      if (refs.detection_image_url) {
        console.log('ImageGallery - Found detection_image_url:', refs.detection_image_url)
        images.push({
          type: 'detection',
          url: refs.detection_image_url,
          size: refs.detection_image_size
        })
      }
      
      // 处理其他可能的图片类型
      const imageUrlKeys = Object.keys(refs).filter(key => key.endsWith('_image_url'))
      console.log('ImageGallery - Found _image_url keys:', imageUrlKeys)
      
      imageUrlKeys.forEach(key => {
        if (!['depth_image_url', 'original_image_url', 'detection_image_url'].includes(key)) {
          console.log(`ImageGallery - Processing legacy field ${key}:`, refs[key])
          const type = key.replace('_image_url', '')
          const sizeKey = `${type}_image_size`
          images.push({
            type,
            url: refs[key],
            size: refs[sizeKey]
          })
        }
      })
    }
    
    console.log('ImageGallery - Final processed images count:', images.length)
    console.log('ImageGallery - Final processed images:', images)
    console.log('=== ImageGallery Debug End ===')
    return images
  } catch (error) {
    console.error('ImageGallery - 解析图片引用失败:', error)
    console.error('ImageGallery - Raw imageRefs content:', props.imageRefs)
    return []
  }
})

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  console.log('ImageGallery - formatFileSize called with:', bytes, typeof bytes)
  if (!bytes) {
    console.log('ImageGallery - formatFileSize returning empty string for falsy bytes')
    return ''
  }
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  const result = Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
  console.log('ImageGallery - formatFileSize result:', result)
  return result
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

// 处理图片加载成功
const handleImageLoad = (image: ImageInfo, event: Event) => {
  const target = event.target as HTMLImageElement
  console.log('=== 图片加载成功 ===')
  console.log('ImageGallery - 图片加载成功:', {
    type: image.type,
    url: image.url,
    size: image.size,
    naturalWidth: target.naturalWidth,
    naturalHeight: target.naturalHeight,
    timestamp: new Date().toISOString()
  })
}

// 处理图片加载错误
const handleImageError = (image: ImageInfo, event: Event) => {
  const target = event.target as HTMLImageElement
  console.log('=== 图片加载失败 ===')
  const errorDetails = {
    type: image.type,
    url: image.url,
    size: image.size,
    error: event,
    errorType: event.type,
    timestamp: new Date().toISOString()
  }
  
  console.error('ImageGallery - 图片加载失败详情:', errorDetails)
  
  // URL格式检查
  if (!image.url) {
    console.error('ImageGallery - 错误原因: URL为空')
  } else if (!image.url.startsWith('http')) {
    console.error('ImageGallery - 错误原因: URL格式可能有问题，不是以http开头:', image.url)
  } else {
    console.error('ImageGallery - 错误原因: 可能是网络错误或图片不存在')
    console.error('ImageGallery - 完整URL:', image.url)
    
    // 尝试手动测试URL
    fetch(image.url, { method: 'HEAD' })
      .then(response => {
        console.log('ImageGallery - URL可访问性测试结果:', {
          status: response.status,
          statusText: response.statusText,
          headers: Object.fromEntries(response.headers.entries())
        })
      })
      .catch(fetchError => {
        console.error('ImageGallery - URL不可访问:', fetchError)
      })
  }
  
  // 隐藏加载失败的图片
  if (target) {
    target.style.display = 'none'
    target.parentElement?.classList.add('image-error')
  }
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