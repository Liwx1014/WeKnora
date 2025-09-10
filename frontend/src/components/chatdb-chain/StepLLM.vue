<template>
  <div class="step-llm">
    <div class="step-header">
      <h3>Step 6 - 大模型输出</h3>
      <p>显示AI分析结果和推理过程</p>
    </div>
    
    <div class="step-content">
      <t-card class="llm-card">
        <template #header>
          <div class="card-header">
            <h4>AI分析结果</h4>
            <div class="header-actions">
              <t-button
                theme="primary"
                variant="base"
                size="small"
                class="btn-strong"
                @click="copyToClipboard"
              >
                <template #icon>
                  <CopyIcon />
                </template>
                复制
              </t-button>
              <t-button
                theme="primary"
                variant="base"
                size="small"
                class="btn-strong"
                @click="toggleFullscreen"
              >
                <template #icon>
                  <FullscreenIcon />
                </template>
                {{ isFullscreen ? '退出全屏' : '全屏' }}
              </t-button>
            </div>
          </div>
        </template>
        
        <div v-if="data?.result" class="llm-content">
          <!-- 渲染Markdown内容 -->
          <div 
            ref="markdownContainer"
            class="markdown-content"
            v-html="renderedMarkdown"
          />
        </div>
        
        <!-- 无LLM数据 -->
        <div v-else class="no-data">
          <t-empty
            description="AI分析结果不可用"
            image="https://tdesign.gtimg.com/pro-template/personal/empty.png"
          />
        </div>
      </t-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'
import type { LLMOutput } from '@/models/chatdb-chain'

interface Props {
  data?: {
    type: string
    result?: LLMOutput
  } | null
}

const props = defineProps<Props>()

const markdownContainer = ref<HTMLDivElement>()
const isFullscreen = ref(false)

// 配置marked
marked.setOptions({
  breaks: true,
  gfm: true,
  sanitize: false,
  highlight: function(code: string, lang: string) {
    // 简单的代码高亮，实际项目中可以使用highlight.js
    return `<pre><code class="language-${lang}">${code}</code></pre>`
  }
})

// 计算属性
const renderedMarkdown = computed(() => {
  if (!props.data?.result?.answer) return ''
  
  try {
    return marked(props.data.result.answer)
  } catch (error) {
    console.error('Markdown渲染失败:', error)
    return `<p>${props.data.result.answer}</p>`
  }
})

// 方法
const copyToClipboard = async () => {
  if (!props.data?.result?.answer) return
  
  try {
    await navigator.clipboard.writeText(props.data.result.answer)
    // 这里可以添加成功提示
    console.log('内容已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    // 降级方案
    const textArea = document.createElement('textarea')
    textArea.value = props.data.result.answer
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
  }
}

const toggleFullscreen = () => {
  if (!markdownContainer.value) return
  
  if (!isFullscreen.value) {
    if (markdownContainer.value.requestFullscreen) {
      markdownContainer.value.requestFullscreen()
    }
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen()
    }
  }
}

// 监听全屏状态变化
const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement
}

onMounted(() => {
  document.addEventListener('fullscreenchange', handleFullscreenChange)
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
})

// 图标组件
const CopyIcon = () => '📋'
const FullscreenIcon = () => isFullscreen.value ? '⤓' : '⤢'
</script>

<style scoped>
.step-llm {
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
  min-height: 0;
}

.llm-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h4 {
  margin: 0;
  color: var(--td-text-color-primary);
  font-size: 16px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.llm-content {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.markdown-content {
  padding: 20px;
  line-height: 1.6;
  color: var(--td-text-color-primary);
  font-size: 14px;
}

/* Markdown样式 */
.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  margin: 24px 0 16px 0;
  color: var(--td-text-color-primary);
  font-weight: 600;
  line-height: 1.4;
}

.markdown-content :deep(h1) {
  font-size: 24px;
  border-bottom: 2px solid var(--td-border-level-1-color);
  padding-bottom: 8px;
}

.markdown-content :deep(h2) {
  font-size: 20px;
  border-bottom: 1px solid var(--td-border-level-1-color);
  padding-bottom: 6px;
}

.markdown-content :deep(h3) {
  font-size: 18px;
}

.markdown-content :deep(h4) {
  font-size: 16px;
}

.markdown-content :deep(h5) {
  font-size: 14px;
}

.markdown-content :deep(h6) {
  font-size: 13px;
}

.markdown-content :deep(p) {
  margin: 16px 0;
  color: var(--td-text-color-primary);
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 16px 0;
  padding-left: 24px;
}

.markdown-content :deep(li) {
  margin: 8px 0;
  color: var(--td-text-color-primary);
}

.markdown-content :deep(blockquote) {
  margin: 16px 0;
  padding: 12px 16px;
  background: var(--td-bg-color-page);
  border-left: 4px solid var(--td-brand-color);
  border-radius: 4px;
}

.markdown-content :deep(blockquote p) {
  margin: 0;
  color: var(--td-text-color-secondary);
  font-style: italic;
}

.markdown-content :deep(code) {
  padding: 2px 6px;
  background: var(--td-bg-color-component);
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  color: var(--td-error-color);
}

.markdown-content :deep(pre) {
  margin: 16px 0;
  padding: 16px;
  background: var(--td-bg-color-component);
  border-radius: 6px;
  overflow-x: auto;
  border: 1px solid var(--td-border-level-1-color);
}

.markdown-content :deep(pre code) {
  padding: 0;
  background: transparent;
  color: var(--td-text-color-primary);
  font-size: 13px;
  line-height: 1.5;
}

.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
  border: 1px solid var(--td-border-level-1-color);
  border-radius: 6px;
  overflow: hidden;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--td-border-level-1-color);
}

.markdown-content :deep(th) {
  background: var(--td-bg-color-page);
  font-weight: 600;
  color: var(--td-text-color-primary);
}

.markdown-content :deep(td) {
  color: var(--td-text-color-primary);
}

.markdown-content :deep(tr:last-child td) {
  border-bottom: none;
}

.markdown-content :deep(a) {
  color: var(--td-brand-color);
  text-decoration: none;
}

.markdown-content :deep(a:hover) {
  text-decoration: underline;
}

.markdown-content :deep(strong) {
  font-weight: 600;
  color: var(--td-text-color-primary);
}

.markdown-content :deep(em) {
  font-style: italic;
  color: var(--td-text-color-secondary);
}

.no-data {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .step-header h3 {
    font-size: 18px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .markdown-content {
    padding: 16px;
    font-size: 13px;
  }
  
  .markdown-content :deep(h1) {
    font-size: 20px;
  }
  
  .markdown-content :deep(h2) {
    font-size: 18px;
  }
  
  .markdown-content :deep(h3) {
    font-size: 16px;
  }
}
</style>
