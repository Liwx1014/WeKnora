<template>
  <div class="chatdb-chain-container">
    <!-- 页面头部 -->
    <div class="chain-header">
      <div class="header-content">
        <div class="header-title">
          <h2>ChatDB 思维链分析</h2>
          <div class="record-info" v-if="store.record">
            <span>记录ID: <span class="record-id">{{ store.record.id }}</span></span>
            <span> | 创建时间: {{ formatDate(store.record.created_at) }}</span>
          </div>
        </div>
        <div class="header-actions">
          <t-button
            theme="primary"
            variant="base"
            @click="goBack"
            class="btn-strong"
          >
            <template #icon>
              <ArrowLeftIcon />
            </template>
            返回
          </t-button>
          <t-button
            theme="primary"
            variant="base"
            @click="refreshData"
            :loading="store.loading"
            class="btn-strong"
          >
            <template #icon>
              <RefreshIcon />
            </template>
            刷新
          </t-button>

          <!-- 步骤控制：上一步 / 自动播放 / 下一步 -->
          <t-space :size="8">
            <t-button
              theme="primary"
              variant="base"
              :disabled="store.currentStep <= 1"
              @click="store.prevStep()"
              class="btn-strong"
            >
              上一步
            </t-button>
            <t-button
              theme="primary"
              variant="base"
              @click="toggleHeaderAutoPlay"
              class="btn-strong"
            >
              {{ playButtonText }}
            </t-button>
            <t-button
              theme="primary"
              variant="base"
              :disabled="store.currentStep >= 6"
              @click="store.nextStep()"
              class="btn-strong"
            >
              下一步
            </t-button>
          </t-space>
        </div>
      </div>
    </div>

    <!-- 页面内容 -->
    <div class="chain-content">
      <!-- 加载状态 -->
      <div v-if="store.loading" class="loading-state">
        <t-loading size="large" text="正在加载思维链数据..." />
      </div>

      <!-- 错误状态 -->
      <div v-else-if="store.error" class="error-state">
        <t-result
          status="error"
          title="加载失败"
          :description="store.error"
        >
          <template #extra>
            <t-button theme="primary" @click="refreshData">
              重试
            </t-button>
          </template>
        </t-result>
      </div>

      <!-- 无数据状态 -->
      <div v-else-if="!store.hasData" class="no-data-state">
        <t-result
          status="default"
          title="暂无数据"
          description="未找到对应的思维链数据"
        >
          <template #extra>
            <t-button theme="primary" @click="goBack">
              返回列表
            </t-button>
          </template>
        </t-result>
      </div>

      <!-- 思维链展示（即使数据不完整也显示主内容，并在顶部给出警告） -->
      <div v-else class="chain-display">
        <div v-if="!store.isValidData" class="data-warning">
          <t-alert
            theme="warning"
            title="数据不完整"
            :description="`以下步骤数据缺失: ${getMissingStepsText()}`"
            :closable="false"
          />
        </div>
        <StepScaffold />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChatDBChainStore } from '@/stores/chatdb-chain'
import { validateChainData } from '@/utils/chatdb-extract'
import StepScaffold from '@/components/chatdb-chain/StepScaffold.vue'

const route = useRoute()
const router = useRouter()
const store = useChatDBChainStore()

// 图标组件
const ArrowLeftIcon = () => '←'
const RefreshIcon = () => '🔄'

// 生命周期
onMounted(async () => {
  const recordId = Number(route.params.id)
  if (recordId && !isNaN(recordId)) {
    await store.fetchIncident(recordId)
    // 默认开启自动播放
    store.startAutoPlay()
  } else {
    console.error('无效的记录ID:', route.params.id)
  }
})

onUnmounted(() => {
  // 清理资源
  store.reset()
})

// 方法
const goBack = () => {
  router.back()
}

const refreshData = async () => {
  const recordId = Number(route.params.id)
  if (recordId && !isNaN(recordId)) {
    await store.fetchIncident(recordId)
  }
}

const formatDate = (dateString: string) => {
  try {
    return new Date(dateString).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (error) {
    return dateString
  }
}

const getMissingStepsText = () => {
  if (!store.chainData) return ''
  
  const validation = validateChainData(store.chainData)
  return validation.missingSteps.join(', ')
}

// 顶部播放控制
const playButtonText = computed(() => {
  switch (store.playbackStatus) {
    case 'playing':
      return '暂停'
    case 'paused':
      return '继续'
    default:
      return '自动播放'
  }
})

const toggleHeaderAutoPlay = () => {
  if (store.playbackStatus === 'playing') {
    store.pauseAutoPlay()
  } else {
    store.startAutoPlay()
  }
}
</script>

<style scoped>
.chatdb-chain-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--td-bg-color-page);
}

.chain-header {
  padding: 20px;
  background: var(--td-bg-color-container);
  border-bottom: 1px solid var(--td-border-level-1-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
}

.header-title h2 {
  margin: 0;
  color: var(--td-text-color-primary);
  font-size: 24px;
  font-weight: 600;
}

.record-info {
  margin-top: 8px;
  color: var(--td-text-color-secondary);
  font-size: 14px;
}

.record-id {
  font-weight: 600;
  color: var(--td-brand-color);
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* 提升按钮可读性 */
.btn-strong :deep(.t-button__text) {
  color: #fff !important;
}

.btn-ghost :deep(.t-button__text) {
  color: var(--td-text-color-primary) !important;
}

/* 主色按钮统一前景与背景（与其他按钮一致） */
.btn-strong:deep(.t-button) {
  background-color: var(--td-brand-color) !important;
  border-color: var(--td-brand-color) !important;
  color: #fff !important;
}

.btn-strong:deep(.t-button:hover) {
  background-color: var(--td-brand-color-hover) !important;
  border-color: var(--td-brand-color-hover) !important;
}

/* 禁用态按钮弱化背景与描边，避免突兀 */
.btn-ghost:deep(.t-button.t-is-disabled) {
  background-color: transparent !important;
  border-color: var(--td-border-level-1-color) !important;
  color: var(--td-text-color-disabled) !important;
}

.btn-ghost:deep(.t-button.t-is-disabled .t-button__text) {
  color: var(--td-text-color-disabled) !important;
}

.chain-content {
  flex: 1;
  padding: 20px;
  overflow: auto;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
}

.error-state,
.no-data-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.data-warning {
  margin-bottom: 20px;
}

.chain-display {
  height: 100%;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .chain-header {
    padding: 16px;
  }
  
  .chain-content {
    padding: 16px;
  }
}

@media (max-width: 768px) {
  .chain-header {
    padding: 12px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .chain-content {
    padding: 12px;
  }
  
  .header-title h2 {
    font-size: 20px;
  }
  
  .record-info {
    font-size: 12px;
  }
}

@media (max-width: 480px) {
  .chain-header {
    padding: 8px;
  }
  
  .chain-content {
    padding: 8px;
  }
  
  .header-title h2 {
    font-size: 18px;
  }
  
  .header-actions {
    flex-direction: column;
    gap: 8px;
  }
  
  .header-actions .t-button {
    width: 100%;
  }
}
</style>
