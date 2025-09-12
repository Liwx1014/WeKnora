<template>
  <div class="step-scaffold">
    <!-- 步骤内容 -->
    <div class="step-content">
      <transition name="step-fade" mode="out-in">
        <component
          :is="getCurrentStepComponent()"
          :key="currentStep"
          :data="currentStepData"
          @bbox-click="handleBboxClick"
          @table-row-click="handleTableRowClick"
        />
      </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useChatDBChainStore } from '@/stores/chatdb-chain'
import StepOrigin from './StepOrigin.vue'
import StepDetection from './StepDetection.vue'
import StepSegmentation from './StepSegmentation.vue'
import StepDepth from './StepDepth.vue'
import StepDistances from './StepDistances.vue'
import StepLLM from './StepLLM.vue'
import type { StepStatus, PlaybackStatus } from '@/models/chatdb-chain'

// 图标组件（这里使用简单的SVG，实际项目中可以使用图标库）
const ChevronLeftIcon = () => '‹'
const ChevronRightIcon = () => '›'
const PlayIcon = () => '▶'
const PauseIcon = () => '⏸'

const store = useChatDBChainStore()

// 计算属性
const currentStep = computed(() => store.currentStep)
const steps = computed(() => store.steps)
const playbackStatus = computed(() => store.playbackStatus)
const currentStepData = computed(() => store.currentStepData)

// 方法（供外层通过步骤组件交互时使用）
const setCurrentStep = (stepId: number) => {
  store.setCurrentStep(stepId)
}

const nextStep = () => {
  store.nextStep()
}

const prevStep = () => {
  store.prevStep()
}

const toggleAutoPlay = () => {
  if (playbackStatus.value === 'playing') {
    store.pauseAutoPlay()
  } else if (playbackStatus.value === 'paused') {
    store.startAutoPlay()
  } else {
    store.startAutoPlay()
  }
}

const getStepStatus = (step: any): StepStatus => {
  return step.status
}

const getPlayButtonText = (): string => {
  switch (playbackStatus.value) {
    case 'playing':
      return '暂停'
    case 'paused':
      return '继续'
    default:
      return '自动播放'
  }
}

const getCurrentStepComponent = () => {
  switch (currentStep.value) {
    case 1:
      return StepOrigin
    case 2:
      return StepDetection
    case 3:
      return StepSegmentation
    case 4:
      return StepDepth
    case 5:
      return StepDistances
    case 6:
      return StepLLM
    default:
      return StepOrigin
  }
}

// 事件处理
const handleBboxClick = (bboxIndex: number) => {
  // 在Step5中高亮对应的表格行
  if (currentStep.value === 5) {
    // 这个事件会传递给StepDistances组件
    console.log('Bbox clicked:', bboxIndex)
  }
}

const handleTableRowClick = (rowIndex: number) => {
  // 在Step2中高亮对应的bbox
  if (currentStep.value === 2) {
    // 这个事件会传递给StepDetection组件
    console.log('Table row clicked:', rowIndex)
  }
}
</script>

<style scoped>
.step-scaffold {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 12px; /* 控制条移除后，缩小内部分隔，避免产生长条空白 */
}

.step-content {
  flex: 1;
  min-height: 400px;
  background: var(--td-bg-color-container);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: auto;
}

/* 步骤切换动画 */
.step-fade-enter-active,
.step-fade-leave-active {
  transition: all 0.3s ease;
}

.step-fade-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.step-fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .step-navigation {
    padding: 16px;
  }
  
  .step-content {
    padding: 16px;
  }
}
</style>
