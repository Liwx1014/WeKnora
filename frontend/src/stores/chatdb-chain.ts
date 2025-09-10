import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getChatRecordById } from '@/api/chatdb/index'
import { extractChain, validateChainData } from '@/utils/chatdb-extract'
import type { IncidentRecord, ChainData, ChainState, StepInfo, StepStatus, PlaybackStatus } from '@/models/chatdb-chain'

export const useChatDBChainStore = defineStore('chatdb-chain', () => {
  // 状态
  const record = ref<IncidentRecord | null>(null)
  const chainData = ref<ChainData | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  // 思维链状态
  const currentStep = ref(1)
  const playbackStatus = ref<PlaybackStatus>('stopped')
  const autoPlayInterval = ref<number | null>(null)
  
  // 步骤信息
  const steps: StepInfo[] = [
    { id: 1, title: '原始图像', description: '显示原始输入图像', status: 'pending' },
    { id: 2, title: '目标检测', description: '检测图像中的目标对象', status: 'pending' },
    { id: 3, title: '导线分割', description: '分割导线区域', status: 'pending' },
    { id: 4, title: '全图深度', description: '计算图像深度信息', status: 'pending' },
    { id: 5, title: '距离可视化', description: '可视化距离测量结果', status: 'pending' },
    { id: 6, title: '大模型输出', description: '显示AI分析结果', status: 'pending' }
  ]
  
  const stepsRef = ref<StepInfo[]>([...steps])
  
  // 计算属性
  const chainState = computed<ChainState>(() => ({
    currentStep: currentStep.value,
    steps: stepsRef.value,
    playbackStatus: playbackStatus.value,
    autoPlayInterval: autoPlayInterval.value || undefined
  }))
  
  const hasData = computed(() => record.value !== null && chainData.value !== null)
  const isValidData = computed(() => {
    if (!chainData.value) return false
    const validation = validateChainData(chainData.value)
    return validation.isValid
  })
  
  const currentStepData = computed(() => {
    if (!chainData.value) return null
    
    switch (currentStep.value) {
      case 1:
        return {
          type: 'original',
          imageUrl: chainData.value.originalImageUrl
        }
      case 2:
        return {
          type: 'detection',
          imageUrl: chainData.value.detectionImageUrl,
          result: chainData.value.detectionResult
        }
      case 3:
        return {
          type: 'segmentation',
          imageUrl: chainData.value.segmentationImageUrl,
          result: chainData.value.segmentationResult
        }
      case 4:
        return {
          type: 'depth',
          imageUrl: chainData.value.depthImageUrl,
          result: chainData.value.depthResult
        }
      case 5:
        return {
          type: 'distances',
          imageUrl: chainData.value.distanceVisualizationUrl,
          result: chainData.value.distanceResult
        }
      case 6:
        return {
          type: 'llm',
          result: chainData.value.llmOutput
        }
      default:
        return null
    }
  })
  
  // 方法
  const fetchIncident = async (id: number) => {
    loading.value = true
    error.value = null
    
    try {
      console.log('=== ChatDB Chain Store 开始获取记录 ===')
      console.log('Store - 请求记录ID:', id)
      
      const response = await getChatRecordById(id)
      console.log('Store - API响应:', response)
      
      record.value = response.data
      console.log('Store - 记录数据:', record.value)
      
      // 抽取思维链数据
      chainData.value = extractChain(record.value!)
      console.log('Store - 思维链数据:', chainData.value)
      
      // 验证数据完整性
      const validation = validateChainData(chainData.value)
      console.log('Store - 数据验证结果:', validation)
      
      if (!validation.isValid) {
        console.warn('Store - 数据不完整，缺失步骤:', validation.missingSteps)
      }
      
      // 更新步骤状态
      updateStepStatuses()
      
    } catch (err) {
      console.error('Store - 获取记录失败:', err)
      error.value = err instanceof Error ? err.message : '获取记录失败'
      record.value = null
      chainData.value = null
    } finally {
      loading.value = false
    }
  }
  
  const updateStepStatuses = () => {
    if (!chainData.value) return
    
    stepsRef.value = stepsRef.value.map(step => {
      let status: StepStatus = 'pending'
      
      switch (step.id) {
        case 1:
          status = chainData.value!.originalImageUrl ? 'completed' : 'error'
          break
        case 2:
          status = (chainData.value!.detectionImageUrl || chainData.value!.detectionResult) ? 'completed' : 'error'
          break
        case 3:
          status = (chainData.value!.segmentationImageUrl || chainData.value!.segmentationResult) ? 'completed' : 'error'
          break
        case 4:
          status = (chainData.value!.depthImageUrl || chainData.value!.depthResult) ? 'completed' : 'error'
          break
        case 5:
          status = (chainData.value!.distanceVisualizationUrl || chainData.value!.distanceResult) ? 'completed' : 'error'
          break
        case 6:
          status = chainData.value!.llmOutput ? 'completed' : 'error'
          break
      }
      
      return { ...step, status }
    })
    
    // 设置当前步骤为第一个有数据的步骤
    const firstValidStep = stepsRef.value.find(step => step.status === 'completed')
    if (firstValidStep) {
      currentStep.value = firstValidStep.id
      stepsRef.value = stepsRef.value.map(step => ({
        ...step,
        status: step.id === firstValidStep.id ? 'active' : step.status
      }))
    }
  }
  
  const setCurrentStep = (stepId: number) => {
    if (stepId < 1 || stepId > 6) return
    
    currentStep.value = stepId
    stepsRef.value = stepsRef.value.map(step => ({
      ...step,
      status: step.id === stepId ? 'active' : step.status
    }))
  }
  
  const nextStep = () => {
    if (currentStep.value < 6) {
      setCurrentStep(currentStep.value + 1)
    }
  }
  
  const prevStep = () => {
    if (currentStep.value > 1) {
      setCurrentStep(currentStep.value - 1)
    }
  }
  
  const startAutoPlay = (interval: number = 2000) => {
    if (playbackStatus.value === 'playing') return
    
    playbackStatus.value = 'playing'
    autoPlayInterval.value = window.setInterval(() => {
      if (currentStep.value < 6) {
        nextStep()
      } else {
        stopAutoPlay()
      }
    }, interval)
  }
  
  const pauseAutoPlay = () => {
    if (autoPlayInterval.value) {
      clearInterval(autoPlayInterval.value)
      autoPlayInterval.value = null
    }
    playbackStatus.value = 'paused'
  }
  
  const stopAutoPlay = () => {
    if (autoPlayInterval.value) {
      clearInterval(autoPlayInterval.value)
      autoPlayInterval.value = null
    }
    playbackStatus.value = 'stopped'
  }
  
  const reset = () => {
    record.value = null
    chainData.value = null
    loading.value = false
    error.value = null
    currentStep.value = 1
    playbackStatus.value = 'stopped'
    if (autoPlayInterval.value) {
      clearInterval(autoPlayInterval.value)
      autoPlayInterval.value = null
    }
    stepsRef.value = [...steps]
  }
  
  return {
    // 状态
    record,
    chainData,
    loading,
    error,
    currentStep,
    playbackStatus,
    autoPlayInterval,
    steps: stepsRef,
    
    // 计算属性
    chainState,
    hasData,
    isValidData,
    currentStepData,
    
    // 方法
    fetchIncident,
    setCurrentStep,
    nextStep,
    prevStep,
    startAutoPlay,
    pauseAutoPlay,
    stopAutoPlay,
    reset
  }
})
