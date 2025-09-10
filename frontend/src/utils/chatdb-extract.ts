import type { IncidentRecord, ChainData, ImageURLs, AnalysisResults, DetectionResult, SegmentationResult, DepthResult, DistanceResult, LLMOutput } from '@/models/chatdb-chain'

/**
 * 从ChatDB记录中抽取思维链数据
 * @param record 原始记录
 * @returns 思维链数据
 */
export function extractChain(record: IncidentRecord): ChainData {
  const logData = record.log_data || {}
  
  // 抽取图像URLs
  const imageUrls = extractImageURLs(logData)
  
  // 抽取分析结果
  const analysisResults = extractAnalysisResults(logData)
  
  // 抽取LLM输出
  const llmOutput = extractLLMOutput(logData)
  
  return {
    // Step 1 - 原始图像
    originalImageUrl: imageUrls.original_url,
    
    // Step 2 - 目标检测
    detectionImageUrl: imageUrls.detection_url,
    detectionResult: analysisResults.detection,
    
    // Step 3 - 导线分割
    segmentationImageUrl: imageUrls.segmentation_url,
    segmentationResult: analysisResults.segmentation,
    
    // Step 4 - 全图深度
    depthImageUrl: imageUrls.depth_url,
    depthResult: analysisResults.depth?.result,
    
    // Step 5 - 距离可视化
    distanceVisualizationUrl: imageUrls.distance_visualization_url,
    distanceResult: analysisResults.distances,
    
    // Step 6 - 大模型输出
    llmOutput: llmOutput
  }
}

/**
 * 抽取图像URLs
 */
function extractImageURLs(logData: any): ImageURLs {
  const imageUrls: ImageURLs = {}
  
  // 检查image_urls字段
  if (logData.image_urls) {
    const urls = logData.image_urls
    
    // 处理不同的URL字段名格式
    imageUrls.original_url = urls.original_image_url || urls.original_url || urls.original
    imageUrls.detection_url = urls.detection_image_url || urls.detection_url || urls.detection
    imageUrls.segmentation_url = urls.segmentation_image_url || urls.segmentation_url || urls.segmentation
    imageUrls.depth_url = urls.depth_image_url || urls.depth_url || urls.depth
    imageUrls.distance_visualization_url = urls.distance_visualization_image_url || urls.distance_visualization_url || urls.distance_visualization
  }
  
  // 兼容旧格式：直接使用image_url字段
  if (!imageUrls.original_url && logData.image_url) {
    imageUrls.original_url = logData.image_url
  }
  
  return imageUrls
}

/**
 * 抽取分析结果
 */
function extractAnalysisResults(logData: any): AnalysisResults {
  const results: AnalysisResults = {}
  
  // 抽取检测结果
  if (logData.analysis_results?.detection) {
    results.detection = extractDetectionResult(logData.analysis_results.detection)
  }
  
  // 抽取分割结果
  if (logData.analysis_results?.segmentation) {
    results.segmentation = extractSegmentationResult(logData.analysis_results.segmentation)
  }
  
  // 抽取深度结果
  if (logData.analysis_results?.depth) {
    results.depth = {
      result: extractDepthResult(logData.analysis_results.depth.result || logData.analysis_results.depth)
    }
  }
  
  // 抽取距离结果
  if (logData.analysis_results?.distances) {
    results.distances = extractDistanceResult(logData.analysis_results.distances)
  }
  
  return results
}

/**
 * 抽取检测结果
 */
function extractDetectionResult(detectionData: any): DetectionResult {
  const result: DetectionResult = {
    count: 0,
    objects: []
  }
  
  // 处理result字段（可能是字符串或对象）
  if (detectionData.result) {
    if (typeof detectionData.result === 'string') {
      result.result = detectionData.result
    } else if (typeof detectionData.result === 'object') {
      // 尝试解析结构化数据
      if (detectionData.result.count !== undefined) {
        result.count = detectionData.result.count
      }
      if (Array.isArray(detectionData.result.objects)) {
        result.objects = detectionData.result.objects.map((obj: any) => ({
          bbox: obj.bbox || [0, 0, 0, 0],
          class_name: obj.class_name || obj.class || 'unknown',
          confidence: obj.confidence || obj.conf || 0
        }))
      }
    }
  }
  
  // 直接处理count和objects字段
  if (detectionData.count !== undefined) {
    result.count = detectionData.count
  }
  if (Array.isArray(detectionData.objects)) {
    result.objects = detectionData.objects.map((obj: any) => ({
      bbox: obj.bbox || [0, 0, 0, 0],
      class_name: obj.class_name || obj.class || 'unknown',
      confidence: obj.confidence || obj.conf || 0
    }))
  }
  
  return result
}

/**
 * 抽取分割结果
 */
function extractSegmentationResult(segmentationData: any): SegmentationResult {
  return {
    result: segmentationData.result || segmentationData
  }
}

/**
 * 抽取深度结果
 */
function extractDepthResult(depthData: any): DepthResult {
  return {
    depth_min: depthData.depth_min || depthData.min_depth,
    depth_max: depthData.depth_max || depthData.max_depth,
    focal_length: depthData.focal_length || depthData.focal
  }
}

/**
 * 抽取距离结果
 */
function extractDistanceResult(distanceData: any): DistanceResult {
  const result: DistanceResult = {
    result: []
  }
  
  if (Array.isArray(distanceData.result)) {
    result.result = distanceData.result.map((item: any) => ({
      box_index: item.box_index || item.index || 0,
      distance_meters: item.distance_meters || item.distance || 0,
      box_coords: item.box_coords || item.bbox || [0, 0, 0, 0],
      nearest_wire_point: {
        x: item.nearest_wire_point?.x || item.wire_point?.x || 0,
        y: item.nearest_wire_point?.y || item.wire_point?.y || 0
      }
    }))
  }
  
  return result
}

/**
 * 抽取LLM输出
 */
function extractLLMOutput(logData: any): LLMOutput | undefined {
  if (logData.llm_output?.answer) {
    return {
      answer: logData.llm_output.answer
    }
  }
  
  // 兼容其他可能的字段名
  if (logData.answer) {
    return {
      answer: logData.answer
    }
  }
  
  if (logData.response) {
    return {
      answer: logData.response
    }
  }
  
  return undefined
}

/**
 * 验证思维链数据的完整性
 */
export function validateChainData(chainData: ChainData): { isValid: boolean; missingSteps: string[] } {
  const missingSteps: string[] = []
  
  // 检查每个步骤的数据
  if (!chainData.originalImageUrl) {
    missingSteps.push('Step 1: 原始图像')
  }
  
  if (!chainData.detectionImageUrl && !chainData.detectionResult) {
    missingSteps.push('Step 2: 目标检测')
  }
  
  if (!chainData.segmentationImageUrl && !chainData.segmentationResult) {
    missingSteps.push('Step 3: 导线分割')
  }
  
  if (!chainData.depthImageUrl && !chainData.depthResult) {
    missingSteps.push('Step 4: 全图深度')
  }
  
  if (!chainData.distanceVisualizationUrl && !chainData.distanceResult) {
    missingSteps.push('Step 5: 距离可视化')
  }
  
  if (!chainData.llmOutput) {
    missingSteps.push('Step 6: 大模型输出')
  }
  
  return {
    isValid: missingSteps.length === 0,
    missingSteps
  }
}
