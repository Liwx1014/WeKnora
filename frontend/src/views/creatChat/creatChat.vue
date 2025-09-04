<template>
    <div v-show="cardList.length" class="dialogue-wrap">
        <div class="dialogue-answers">
            <div class="dialogue-title">
                <span>基于知识库内容问答</span>
            </div>
            
            <!-- 历史对话记录区域 -->
            <div class="history-section" v-if="recentSessions.length > 0">
                <div class="history-title">
                    <span>最近对话</span>
                </div>
                <div class="history-grid">
                    <div 
                        v-for="session in recentSessions" 
                        :key="session.id"
                        class="history-item"
                        @click="navigateToSession(session)"
                    >
                        <div class="history-item-content">
                            <div class="history-item-title">{{ session.title || '新会话' }}</div>
                            <div class="history-item-time">{{ formatTime(session.created_at) }}</div>
                        </div>
                        <div class="history-item-arrow">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                <path d="M6 4L10 8L6 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </div>
                    </div>
                </div>
            </div>
            
            <InputField @send-msg="sendMsg"></InputField>
        </div>
    </div>
    <EmptyKnowledge v-show="!cardList.length"></EmptyKnowledge>
</template>
<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import InputField from '@/components/Input-field.vue';
import EmptyKnowledge from '@/components/empty-knowledge.vue';
import { getSessionsList, createSessions, generateSessionsTitle } from "@/api/chat/index";
import { useMenuStore } from '@/stores/menu';
import { useRoute, useRouter } from 'vue-router';
import useKnowledgeBase from '@/hooks/useKnowledgeBase';
import { getTestData } from '@/utils/request';

let { cardList } = useKnowledgeBase()
const router = useRouter();
const usemenuStore = useMenuStore();
const recentSessions = ref([]);

const sendMsg = (value: string) => {
    createNewSession(value);
}

// 获取最近的会话列表
const getRecentSessions = async () => {
    try {
        const res = await getSessionsList(1, 10); // 获取最新的10条记录
        if (res.data && res.data.length) {
            recentSessions.value = res.data.map(item => ({
                id: item.id,
                title: item.title || '新会话',
                created_at: item.created_at,
                updated_at: item.updated_at
            }));
        }
    } catch (error) {
        console.error('获取最近会话失败:', error);
    }
}

// 跳转到指定会话
const navigateToSession = (session) => {
    router.push(`/platform/chat/${session.id}`);
}

// 格式化时间显示
const formatTime = (timeStr) => {
    if (!timeStr) return '';
    const date = new Date(timeStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) {
        return '今天';
    } else if (days === 1) {
        return '昨天';
    } else if (days < 7) {
        return `${days}天前`;
    } else {
        return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
    }
}

async function createNewSession(value: string) {
    // 从localStorage获取设置中的知识库ID
    const settingsStr = localStorage.getItem("WeKnora_settings");
    let knowledgeBaseId = "";
    
    if (settingsStr) {
        try {
            const settings = JSON.parse(settingsStr);
            if (settings.knowledgeBaseId) {
                knowledgeBaseId = settings.knowledgeBaseId;
                createSessions({ knowledge_base_id: knowledgeBaseId }).then(res => {
                    if (res.data && res.data.id) {
                        getTitle(res.data.id, value);
                    } else {
                        // 错误处理
                        console.error("创建会话失败");
                    }
                }).catch(error => {
                    console.error("创建会话出错:", error);
                });
                return;
            }
        } catch (e) {
            console.error("解析设置失败:", e);
        }
    }
    
    // 如果设置中没有知识库ID，则使用测试数据
    const testData = getTestData();
    if (!testData || testData.knowledge_bases.length === 0) {
        console.error("测试数据未初始化或不包含知识库");
        return;
    }

    // 使用第一个知识库ID
    knowledgeBaseId = testData.knowledge_bases[0].id;

    createSessions({ knowledge_base_id: knowledgeBaseId }).then(res => {
        if (res.data && res.data.id) {
            getTitle(res.data.id, value)
        } else {
            // 错误处理
            console.error("创建会话失败");
        }
    }).catch(error => {
        console.error("创建会话出错:", error);
    })
}

const getTitle = (session_id: string, value: string) => {
    let obj = { title: '新会话', path: `chat/${session_id}`, id: session_id, isMore: false, isNoTitle: true }
    usemenuStore.updataMenuChildren(obj);
    usemenuStore.changeIsFirstSession(true);
    usemenuStore.changeFirstQuery(value);
    router.push(`/platform/chat/${session_id}`);
}

// 组件挂载时获取最近会话
onMounted(() => {
    getRecentSessions();
});

</script>
<style lang="less" scoped>
.dialogue-wrap {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 40px 20px;
    min-height: calc(100vh - 64px);
    box-sizing: border-box;
}

.dialogue-answers {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
    max-width: 800px;
    margin: 0 auto;

    :deep(.answers-input) {
        position: static;
        transform: translateX(0);
        width: 100%;
        max-width: 800px;
    }
}

.dialogue-title {
    display: flex;
    color: #000000;
    font-family: "PingFang SC";
    font-size: 28px;
    font-weight: 600;
    align-items: center;
    margin-bottom: 30px;

    .icon {
        display: flex;
        width: 32px;
        height: 32px;
        justify-content: center;
        align-items: center;
        border-radius: 6px;
        background: #FFF;
        box-shadow: 0 0 2px -1px #0000001f;
        margin-right: 12px;

        .logo_img {
            height: 24px;
            width: 24px;
        }
    }
}

/* 历史记录区域样式 */
.history-section {
    width: 100%;
    max-width: 800px;
    margin-bottom: 40px;
}

.history-title {
    font-size: 18px;
    font-weight: 600;
    color: #1f2937;
    margin-bottom: 16px;
    padding-left: 4px;
}

.history-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 12px;
    max-height: 400px;
    overflow-y: auto;
}

.history-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);

    &:hover {
        border-color: #3b82f6;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
        transform: translateY(-1px);
        
        .history-item-arrow {
            color: #3b82f6;
            transform: translateX(2px);
        }
    }
}

.history-item-content {
    flex: 1;
    min-width: 0;
}

.history-item-title {
    font-size: 14px;
    font-weight: 500;
    color: #1f2937;
    margin-bottom: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.history-item-time {
    font-size: 12px;
    color: #6b7280;
}

.history-item-arrow {
    color: #9ca3af;
    transition: all 0.2s ease;
    flex-shrink: 0;
    margin-left: 12px;
}

/* 科技风格创建对话页面适配 */
:root[theme-mode="tech-dark"] .dialogue-title {
    color: var(--tech-text-primary) !important;

    .icon {
        background: var(--tech-bg-card) !important;
        border: 1px solid var(--tech-border);
        box-shadow: var(--tech-shadow-card) !important;
    }
}

/* 科技风格历史记录区域适配 */
:root[theme-mode="tech-dark"] {
    .history-title {
        color: var(--tech-text-primary) !important;
    }
    
    .history-item {
        background: var(--tech-bg-card) !important;
        border-color: var(--tech-border) !important;
        box-shadow: var(--tech-shadow-card) !important;
        
        &:hover {
            border-color: var(--tech-accent-primary) !important;
            box-shadow: 0 4px 12px rgba(0, 255, 255, 0.15) !important;
        }
    }
    
    .history-item-title {
        color: var(--tech-text-primary) !important;
    }
    
    .history-item-time {
        color: var(--tech-text-secondary) !important;
    }
    
    .history-item-arrow {
        color: var(--tech-text-secondary) !important;
        
        &:hover {
            color: var(--tech-accent-primary) !important;
        }
    }
}

@media (max-width: 768px) {
    .dialogue-wrap {
        padding: 20px 16px;
    }
    
    .dialogue-answers {
        max-width: 100%;
        
        :deep(.answers-input) {
            max-width: 100%;
        }
    }
    
    .dialogue-title {
        font-size: 24px;
        text-align: center;
    }
    
    .history-section {
        margin-bottom: 30px;
    }
    
    .history-title {
        font-size: 16px;
        text-align: center;
        margin-bottom: 12px;
    }
    
    .history-grid {
        grid-template-columns: 1fr;
        gap: 8px;
        max-height: 300px;
    }
    
    .history-item {
        padding: 12px 16px;
    }
    
    .history-item-title {
        font-size: 13px;
    }
    
    .history-item-time {
        font-size: 11px;
    }
}

</style>
<style lang="less">
.del-menu-popup {
    z-index: 99 !important;

    .t-popup__content {
        width: 100px;
        height: 40px;
        line-height: 30px;
        padding-left: 14px;
        cursor: pointer;
        margin-top: 4px !important;

    }
}
</style>