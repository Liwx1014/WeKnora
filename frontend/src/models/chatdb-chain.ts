// ChatDB思维链相关类型定义

// 原始记录接口
export interface IncidentRecord {
  id: number
  conversation_id: string
  user_id: string
  session_id: string
  log_data: any
  created_at: string
}

// 图像URL集合
export interface ImageURLs {
  original_url?: string
  detection_url?: string
  segmentation_url?: string
  depth_url?: string
  distance_visualization_url?: string
}

// 检测对象
export interface DetectionObject {
  bbox: [number, number, number, number] // [x, y, width, height]
  class_name: string
  confidence: number
}

// 检测结果
export interface DetectionResult {
  count: number
  objects: DetectionObject[]
  result?: string
}

// 分割结果
export interface SegmentationResult {
  result?: string
}

// 深度结果
export interface DepthResult {
  depth_min?: number
  depth_max?: number
  focal_length?: number
}

// 距离点坐标
export interface Point {
  x: number
  y: number
}

// 距离测量结果
export interface DistanceRow {
  box_index: number
  distance_meters: number
  box_coords: [number, number, number, number]
  nearest_wire_point: Point
}

// 距离结果
export interface DistanceResult {
  result: DistanceRow[]
}

// 分析结果集合
export interface AnalysisResults {
  detection?: DetectionResult
  segmentation?: SegmentationResult
  depth?: {
    result: DepthResult
  }
  distances?: DistanceResult
}

// LLM输出
export interface LLMOutput {
  answer: string
}

// 思维链数据
export interface ChainData {
  // Step 1 - 原始图像
  originalImageUrl?: string
  
  // Step 2 - 目标检测
  detectionImageUrl?: string
  detectionResult?: DetectionResult
  
  // Step 3 - 导线分割
  segmentationImageUrl?: string
  segmentationResult?: SegmentationResult
  
  // Step 4 - 全图深度
  depthImageUrl?: string
  depthResult?: DepthResult
  
  // Step 5 - 距离可视化
  distanceVisualizationUrl?: string
  distanceResult?: DistanceResult
  
  // Step 6 - 大模型输出
  llmOutput?: LLMOutput
}

// 步骤状态
export type StepStatus = 'pending' | 'active' | 'completed' | 'error'

// 步骤信息
export interface StepInfo {
  id: number
  title: string
  description: string
  status: StepStatus
}

// 播放状态
export type PlaybackStatus = 'stopped' | 'playing' | 'paused'

// 思维链状态
export interface ChainState {
  currentStep: number
  steps: StepInfo[]
  playbackStatus: PlaybackStatus
  autoPlayInterval?: number
}
