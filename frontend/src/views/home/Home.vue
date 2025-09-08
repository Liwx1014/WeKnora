<template>
  <div class="dashboard-container">
    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 左侧区域A -->
      <div class="left-section">
        <!-- A上：统计卡片 -->
        <div class="stats-cards">
          <div class="stat-card">
            <div class="stat-number">{{ stats.eventCount }}</div>
            <div class="stat-label">事件数目统计</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ stats.s2Count }}</div>
            <div class="stat-label">S2+数目</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ stats.placeholder1 }}</div>
            <div class="stat-label">占位1</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ stats.placeholder2 }}</div>
            <div class="stat-label">占位2</div>
          </div>
        </div>

        <!-- A中：饼图 -->
        <div class="pie-chart-section">
          <h3 class="section-title">事件类型分布</h3>
          <div class="pie-chart-container">
            <canvas ref="pieChart" width="300" height="300"></canvas>
          </div>
        </div>

        <!-- A下：柱形图 -->
        <div class="bar-chart-section">
          <h3 class="section-title">按时间统计</h3>
          <div class="bar-chart-container">
            <canvas ref="barChart" width="400" height="200"></canvas>
          </div>
        </div>
      </div>

      <!-- 中间区域B -->
      <div class="center-section">
        <!-- B上：高德地图 -->
        <div class="map-section">
          <h3 class="section-title">地图监控</h3>
          <div class="map-container" ref="mapContainer">
            <!-- 高德地图将在这里渲染 -->
          </div>
        </div>

        <!-- B下：占位区域 -->
        <div class="placeholder-section">
          <h3 class="section-title">占位区域</h3>
          <div class="placeholder-content">
            <p>后续开发功能区域</p>
          </div>
        </div>
      </div>

      <!-- 右侧区域C -->
      <div class="right-section">
        <h3 class="section-title">ChatDB 数据</h3>
        <div class="placeholder-content">
          <div v-if="chatDBLoading" class="loading">
            <p>正在加载数据...</p>
          </div>
          <div v-else-if="chatDBError" class="error">
            <p>加载失败: {{ chatDBError }}</p>
            <button @click="loadAllChatDBRecords" class="retry-btn">重试</button>
          </div>
          <div v-else-if="chatDBRecords && chatDBRecords.length > 0" class="chat-records">
            <div class="records-list">
              <div 
                v-for="record in (chatDBRecords || [])" 
                :key="record.id" 
                class="record-banner"
                @click="showRecordDetails(record.id)"
              >
                <span class="record-id">ID: {{ record.id }}</span>
                <span class="record-date">{{ new Date(record.created_at).toLocaleDateString() }}</span>
              </div>
            </div>
          </div>
          <div v-else class="no-data">
            <p>暂无数据</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 记录详情弹窗 -->
    <div v-if="showRecordDetail" class="modal-overlay" @click="closeRecordDetail">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>ChatDB 记录详情</h3>
          <button class="close-btn" @click="closeRecordDetail">×</button>
        </div>
        <div class="modal-body" v-if="selectedRecord">
          <div class="detail-item">
            <label>ID:</label>
            <span>{{ selectedRecord.id }}</span>
          </div>
          <div class="detail-item">
            <label>Conversation ID:</label>
            <span>{{ selectedRecord.conversation_id }}</span>
          </div>
          <div class="detail-item">
            <label>创建时间:</label>
            <span>{{ new Date(selectedRecord.created_at).toLocaleString() }}</span>
          </div>
          <div class="detail-item">
            <label>用户ID:</label>
            <span>{{ selectedRecord.user_id }}</span>
          </div>
          <div class="detail-item">
            <label>会话ID:</label>
            <span>{{ selectedRecord.session_id }}</span>
          </div>
          <div class="detail-item" v-if="selectedRecord.log_data">
            <label>日志数据:</label>
            <pre class="log-data">{{ JSON.stringify(selectedRecord.log_data, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import AMapLoader from '@amap/amap-jsapi-loader'
import { getChatRecordById, getAllChatRecords, type ChatDBRecord, type ChatDBListResponse } from '@/api/chatdb/index'

const router = useRouter()

// 图表引用
const pieChart = ref<HTMLCanvasElement>()
const barChart = ref<HTMLCanvasElement>()
const mapContainer = ref<HTMLDivElement>()

// 统计数据
const stats = reactive({
  eventCount: 626,
  s2Count: 90,
  placeholder1: 93.5,
  placeholder2: 270
})

// ChatDB 相关数据
const chatDBRecords = ref<ChatDBRecord[]>([])
const chatDBLoading = ref(false)
const chatDBError = ref<string | null>(null)
const selectedRecord = ref<ChatDBRecord | null>(null)
const showRecordDetail = ref(false)

// 初始化数据
const initializeData = () => {
  chatDBRecords.value = []
  chatDBLoading.value = false
  chatDBError.value = null
}

// 加载所有 ChatDB 记录
const loadAllChatDBRecords = async () => {
  chatDBLoading.value = true
  chatDBError.value = null
  
  try {
    console.log('开始加载 ChatDB 记录...')
    const response = await getAllChatRecords(50, 0)
    console.log('ChatDB API 响应:', response)
    
    if (response && response.data && Array.isArray(response.data)) {
      chatDBRecords.value = response.data
      console.log('成功加载记录数量:', chatDBRecords.value.length)
      // console.log('总记录数:', response.data.count || response.data.length)
    } else {
      console.warn('API 响应格式异常:', response)
      chatDBRecords.value = []
      chatDBError.value = 'API 响应格式异常'
    }
  } catch (error: any) {
    console.error('Failed to load ChatDB records:', error)
    chatDBRecords.value = []
    chatDBError.value = error.response?.data?.message || error.message || '加载失败'
  } finally {
    chatDBLoading.value = false
  }
}

// 显示记录详情
const showRecordDetails = async (recordId: number) => {
  try {
    const response = await getChatRecordById(recordId)
    selectedRecord.value = response.data
    showRecordDetail.value = true
  } catch (error: any) {
    console.error('Failed to load record details:', error)
    chatDBError.value = error.response?.data?.message || error.message || '加载记录详情失败'
  }
}

// 关闭详情弹窗
const closeRecordDetail = () => {
  showRecordDetail.value = false
  selectedRecord.value = null
}

// 饼图数据
const pieData = {
  labels: ['异物', '机械', '烟火'],
  data: [45, 30, 25],
  colors: ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57', '#ff9ff3']
}

// 柱形图数据
const barData = {
  labels: ['1月', '2月', '3月', '4月', '5月'],
  data: [120, 300, 500, 200, 300],
  colors: ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57']
}

// 绘制饼图
const drawPieChart = () => {
  if (!pieChart.value) return
  
  const canvas = pieChart.value
  // 调整画布尺寸以适应容器
  canvas.width = 250
  canvas.height = 250
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  const centerX = canvas.width / 2
  const centerY = canvas.height / 2
  const radius = Math.min(centerX, centerY) - 15
  
  let currentAngle = 0
  const total = pieData.data.reduce((sum, value) => sum + value, 0)
  
  // 清空画布
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  
  pieData.data.forEach((value, index) => {
    const sliceAngle = (value / total) * 2 * Math.PI
    
    // 绘制扇形
    ctx.beginPath()
    ctx.moveTo(centerX, centerY)
    ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle)
    ctx.closePath()
    
    // 使用新的丰富颜色
    const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, radius)
    gradient.addColorStop(0, pieData.colors[index])
    gradient.addColorStop(0.7, pieData.colors[index])
    gradient.addColorStop(1, pieData.colors[index] + '60')
    
    ctx.fillStyle = gradient
    ctx.fill()
    
    // 绘制边框
    ctx.strokeStyle = '#ffffff'
    ctx.lineWidth = 2
    ctx.stroke()
    
    // 绘制标签
    const labelAngle = currentAngle + sliceAngle / 2
    const labelX = centerX + Math.cos(labelAngle) * (radius * 0.7)
    const labelY = centerY + Math.sin(labelAngle) * (radius * 0.7)
    
    ctx.fillStyle = '#ffffff'
    ctx.font = 'bold 11px Arial'
    ctx.textAlign = 'center'
    ctx.shadowColor = 'rgba(0,0,0,0.5)'
    ctx.shadowBlur = 2
    ctx.fillText(`${pieData.labels[index]} ${value}%`, labelX, labelY)
    ctx.shadowBlur = 0
    
    currentAngle += sliceAngle
  })
}

// 绘制柱形图
const drawBarChart = () => {
  if (!barChart.value) return
  
  const canvas = barChart.value
  // 调整画布尺寸以适应容器
  canvas.width = 280
  canvas.height = 150
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  const padding = 30
  const chartWidth = canvas.width - 2 * padding
  const chartHeight = canvas.height - 2 * padding
  const barWidth = chartWidth / barData.data.length
  const maxValue = Math.max(...barData.data)
  
  // 清空画布
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  
  // 绘制柱形
  barData.data.forEach((value, index) => {
    const barHeight = (value / maxValue) * chartHeight
    const x = padding + index * barWidth + barWidth * 0.2
    const y = canvas.height - padding - barHeight
    const width = barWidth * 0.6
    
    // 使用新的丰富颜色渐变
    const gradient = ctx.createLinearGradient(0, y, 0, y + barHeight)
    gradient.addColorStop(0, barData.colors[index])
    gradient.addColorStop(0.5, barData.colors[index] + 'CC')
    gradient.addColorStop(1, barData.colors[index] + '80')
    
    ctx.fillStyle = gradient
    
    // 添加圆角效果
    const radius = 4
    ctx.beginPath()
    ctx.moveTo(x + radius, y)
    ctx.lineTo(x + width - radius, y)
    ctx.quadraticCurveTo(x + width, y, x + width, y + radius)
    ctx.lineTo(x + width, y + barHeight)
    ctx.lineTo(x, y + barHeight)
    ctx.lineTo(x, y + radius)
    ctx.quadraticCurveTo(x, y, x + radius, y)
    ctx.closePath()
    ctx.fill()
    
    // 添加高光效果
    const highlightGradient = ctx.createLinearGradient(0, y, 0, y + barHeight * 0.3)
    highlightGradient.addColorStop(0, 'rgba(255,255,255,0.3)')
    highlightGradient.addColorStop(1, 'rgba(255,255,255,0)')
    ctx.fillStyle = highlightGradient
    ctx.fill()
    
    // 绘制标签
    ctx.fillStyle = '#ffffff'
    ctx.font = 'bold 10px Arial'
    ctx.textAlign = 'center'
    ctx.shadowColor = 'rgba(0,0,0,0.5)'
    ctx.shadowBlur = 1
    ctx.fillText(barData.labels[index], x + width / 2, canvas.height - padding + 12)
    ctx.fillText(value.toString(), x + width / 2, y - 3)
    ctx.shadowBlur = 0
  })
}

// 初始化高德地图
const initMap = async () => {
  console.log('开始初始化地图...')
  if (!mapContainer.value) {
    console.error('地图容器不存在')
    return
  }
  
  try {
    console.log('加载高德地图API...')
    // 加载高德地图API
    const AMap = await AMapLoader.load({
      key: import.meta.env.VITE_AMAP_KEY, // 从环境变量读取高德地图API Key
      version: '2.0',
      plugins: ['AMap.Scale', 'AMap.ToolBar', 'AMap.Marker']
    })
    
    // 创建地图实例
    const map = new AMap.Map(mapContainer.value, {
      zoom: 12,
      center: [import.meta.env.VITE_AMAP_DEFAULT_LNG || 118.7778, import.meta.env.VITE_AMAP_DEFAULT_LAT || 31.9917], // 南京市雨花台云密城
      mapStyle: 'amap://styles/dark', // 暗色主题
      showLabel: true,
      showBuildingBlock: true
    })
    
    // 添加工具栏
    const toolbar = new AMap.ToolBar({
      position: {
        top: '10px',
        right: '10px'
      }
    })
    map.addControl(toolbar)
    
    // 添加比例尺
    const scale = new AMap.Scale({
      position: {
        bottom: '10px',
        left: '10px'
      }
    })
    map.addControl(scale)
    
    // 添加示例标记点
    const markers = [
      { position: [118.7778, 31.9917], title: '云密城监控点1', content: '设备状态：正常' },
      { position: [118.7828, 31.9967], title: '云密城监控点2', content: '设备状态：告警' },
      { position: [118.7728, 31.9867], title: '云密城监控点3', content: '设备状态：正常' }
    ]
    
    markers.forEach(markerData => {
      const marker = new AMap.Marker({
        position: markerData.position,
        title: markerData.title,
        icon: new AMap.Icon({
          size: new AMap.Size(25, 34),
          image: 'data:image/svg+xml;base64,' + btoa(`
            <svg width="25" height="34" viewBox="0 0 25 34" xmlns="http://www.w3.org/2000/svg">
              <path d="M12.5 0C5.6 0 0 5.6 0 12.5C0 19.4 12.5 34 12.5 34S25 19.4 25 12.5C25 5.6 19.4 0 12.5 0Z" fill="#00d4ff"/>
              <circle cx="12.5" cy="12.5" r="6" fill="white"/>
            </svg>
          `),
          imageOffset: new AMap.Pixel(-12, -34)
        })
      })
      
      // 添加信息窗体
      const infoWindow = new AMap.InfoWindow({
        content: `<div style="padding: 10px; color: #333;">
          <h4 style="margin: 0 0 5px 0; color: #00d4ff;">${markerData.title}</h4>
          <p style="margin: 0; font-size: 12px;">${markerData.content}</p>
        </div>`,
        offset: new AMap.Pixel(0, -34)
      })
      
      marker.on('click', () => {
        infoWindow.open(map, marker.getPosition())
      })
      
      map.add(marker)
    })
    
  } catch (error) {
    console.error('高德地图加载失败:', error)
    // 如果地图加载失败，显示错误信息
    if (mapContainer.value) {
      mapContainer.value.innerHTML = `
        <div style="width: 100%; height: 100%; background: linear-gradient(135deg, #1a1a2e, #16213e); display: flex; align-items: center; justify-content: center; color: #ff6b6b; font-size: 16px; text-align: center;">
          地图加载失败<br>
          <small style="color: #888; font-size: 12px;">请检查网络连接或API Key配置</small>
        </div>
      `
    }
  }
}

// 导航到指定页面
const navigateTo = (path: string) => {
  router.push(path)
}

// 组件挂载时的初始化
onMounted(async () => {
  // 初始化数据
  initializeData()
  
  await nextTick()
  
  // 确保DOM元素存在后再初始化
  if (pieChart.value) {
    drawPieChart()
  }
  
  if (barChart.value) {
    drawBarChart()
  }
  
  if (mapContainer.value) {
    initMap()
  }
  
  // 加载 ChatDB 数据
  loadAllChatDBRecords()
})
</script>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
  color: white;
  font-family: 'Arial', sans-serif;
}

/* 主要内容区域 */
.main-content {
  display: grid;
  grid-template-columns: 320px 1fr 320px;
  grid-template-rows: 1fr;
  gap: 1rem;
  padding: 1rem;
  max-width: 1600px;
  margin: 0 auto;
  height: calc(100vh - 4rem);
  box-sizing: border-box;
  overflow: hidden;
}

/* 左侧区域A */
.left-section {
  display: grid;
  grid-template-rows: 140px 1fr 180px;
  gap: 0.6rem;
  height: 100%;
  overflow: hidden;
}

.stats-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
  gap: 0.6rem;
  height: 100%;
}

.stat-card {
  background: rgba(0, 212, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 0.6rem;
  padding: 0.8rem;
  text-align: center;
  box-shadow: 0 4px 16px rgba(0, 212, 255, 0.1);
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.stat-number {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(45deg, #00d4ff, #0099cc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.2rem;
  line-height: 1.2;
}

.stat-label {
  font-size: 0.7rem;
  opacity: 0.8;
  color: #94a3b8;
  line-height: 1.2;
}

.pie-chart-section,
.bar-chart-section {
  background: rgba(0, 212, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 0.6rem;
  padding: 0.8rem;
  box-shadow: 0 4px 16px rgba(0, 212, 255, 0.1);
  display: flex;
  flex-direction: column;
}

.pie-chart-section {
  height: 100%;
}

.bar-chart-section {
  height: 100%;
}

.section-title {
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 0.6rem;
  color: #00d4ff;
  text-align: center;
  flex-shrink: 0;
}

.pie-chart-container,
.bar-chart-container {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
  min-height: 0;
}

.pie-chart-container canvas {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
}

.bar-chart-container canvas {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
}

/* 中间区域B */
.center-section {
  display: grid;
  grid-template-rows: 2fr 1fr;
  gap: 0.6rem;
  height: 100%;
  overflow: hidden;
}

.map-section {
  background: rgba(0, 212, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 0.6rem;
  padding: 0.8rem;
  box-shadow: 0 4px 16px rgba(0, 212, 255, 0.1);
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.map-container {
  flex: 1;
  border-radius: 0.4rem;
  overflow: hidden;
  min-height: 0;
}

.placeholder-section {
  background: rgba(0, 212, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 0.6rem;
  padding: 0.8rem;
  box-shadow: 0 4px 16px rgba(0, 212, 255, 0.1);
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.placeholder-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(30, 41, 59, 0.5);
  border-radius: 0.4rem;
  border: 2px dashed rgba(0, 212, 255, 0.3);
  min-height: 0;
}

.placeholder-content p {
  color: #64748b;
  font-size: 0.9rem;
  margin: 0;
}

/* 右侧区域C */
.right-section {
  background: rgba(0, 212, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 0.6rem;
  padding: 0.8rem;
  box-shadow: 0 4px 16px rgba(0, 212, 255, 0.1);
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* ChatDB 记录列表样式 */
.chat-records {
  max-height: 400px;
  overflow-y: auto;
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.record-banner {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  border-radius: 8px;
  padding: 0.75rem;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid rgba(59, 130, 246, 0.3);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.record-banner:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.record-id {
  font-weight: bold;
  color: white;
}

.record-date {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.8);
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.modal-content {
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  border-radius: 12px;
  padding: 1.5rem;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  border: 1px solid rgba(0, 212, 255, 0.3);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(0, 212, 255, 0.2);
}

.modal-header h3 {
  color: #00d4ff;
  margin: 0;
  font-size: 1.25rem;
}

.close-btn {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.modal-body {
  color: #e2e8f0;
}

.detail-item {
  display: flex;
  margin-bottom: 1rem;
  align-items: flex-start;
}

.detail-item label {
  font-weight: bold;
  color: #0ea5e9;
  min-width: 120px;
  margin-right: 1rem;
}

.detail-item span {
  color: #e2e8f0;
  word-break: break-all;
}

.log-data {
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 6px;
  padding: 1rem;
  color: #94a3b8;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  white-space: pre-wrap;
  overflow-x: auto;
  margin: 0;
}

/* ChatDB 数据样式 */
.chat-record {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  padding: 1rem;
  background: rgba(30, 41, 59, 0.5);
  border-radius: 0.4rem;
  border: 1px solid rgba(0, 212, 255, 0.2);
}

.record-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid rgba(0, 212, 255, 0.1);
}

.record-item:last-child {
  border-bottom: none;
}

.record-item label {
  font-weight: 600;
  color: #0ea5e9;
  min-width: 120px;
}

.record-item span {
  color: #e2e8f0;
  font-family: 'Courier New', monospace;
  word-break: break-all;
}

.loading, .error, .no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
}

.loading p {
  color: #0ea5e9;
  font-size: 0.9rem;
}

.error p {
  color: #ef4444;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.retry-btn {
  background: #0ea5e9;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.4rem;
  cursor: pointer;
  font-size: 0.8rem;
  transition: background-color 0.2s;
}

.retry-btn:hover {
  background: #0284c7;
}

.no-data p {
  color: #64748b;
  font-size: 0.9rem;
}

/* 响应式设计 */
@media (max-width: 1400px) {
  .main-content {
    grid-template-columns: 280px 1fr 280px;
    max-width: 100%;
    padding: 0.8rem;
    height: calc(100vh - 3rem);
  }
}

@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto;
    height: auto;
    gap: 0.8rem;
  }
  
  .left-section {
    grid-template-rows: auto auto auto;
    height: auto;
  }
  
  .center-section {
    grid-template-rows: 400px 200px;
    height: auto;
  }
  
  .right-section {
    height: 300px;
  }
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 0;
  }
  
  .main-content {
    padding: 0.5rem;
    gap: 0.5rem;
  }
  
  .stats-cards {
    grid-template-columns: 1fr;
    grid-template-rows: repeat(4, 1fr);
  }
  
  .left-section {
    grid-template-rows: auto auto auto;
  }
  
  .center-section {
    grid-template-rows: 300px 150px;
  }
  
  .right-section {
    height: 200px;
  }
}
</style>