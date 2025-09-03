<template>
    <div class="bot_msg tech-bot-msg">
        <div style="display: flex;flex-direction: column; gap:8px">
            <docInfo :session="session"></docInfo>
            <deepThink :deepSession="session" v-if="session.showThink"></deepThink>
        </div>
        <div ref="parentMd">
            <!-- 消息正在总结中则渲染加载gif  -->
            <img v-if="session.thinking" class="botanswer_laoding_gif" src="@/assets/img/botanswer_loading.gif"
                alt="正在总结答案……">
            <div v-for="(item, index) in processedMarkdown" :key="index">
                <img class="ai-markdown-img" @click="preview(item)" v-if="isLink(item)" :src="item" alt="">
                <div v-else class="ai-markdown-template" v-html="processMarkdown(item)"></div>
            </div>
            <div v-if="isImgLoading" class="img_loading"><t-loading size="small"></t-loading><span>加载中...</span></div>
        </div>
        <picturePreview :reviewImg="reviewImg" :reviewUrl="reviewUrl" @closePreImg="closePreImg"></picturePreview>
    </div>
</template>
<script setup>
import { onMounted, watch, computed, ref, reactive, defineProps, nextTick } from 'vue';
import { marked } from 'marked';
import docInfo from './docInfo.vue';
import deepThink from './deepThink.vue';
import picturePreview from '@/components/picture-preview.vue';
marked.use({
    mangle: false,
    headerIds: false,
});
const emit = defineEmits(['scroll-bottom'])
const renderer = new marked.Renderer();
let parentMd = ref()
let reviewUrl = ref('')
let reviewImg = ref(false)
let isImgLoading = ref(false);
const props = defineProps({
    // 必填项
    content: {
        type: String,
        required: false
    },
    session: {
        type: Object,
        required: false
    },
    isFirstEnter: {
        type: Boolean,
        required: false
    }
});
const processedMarkdown = ref([]);
const preview = (url) => {
    nextTick(() => {
        reviewUrl.value = url;
        reviewImg.value = true
    })
}
const removeImg = () => {
    nextTick(() => {
        const images = parentMd.value.querySelectorAll('img.ai-markdown-img');
        if (images) {
            images.forEach(async item => {
                const isValid = await checkImage(item.src);
                if (!isValid) {
                    item.remove();
                }
            })
        }
    })
}
const closePreImg = () => {
    reviewImg.value = false
    reviewUrl.value = '';
}
const debounce = (fn, delay) => {
    let timer
    return (...args) => {
        clearTimeout(timer)
        timer = setTimeout(() => fn(...args), delay)
    }
}
const checkImage = (url) => {
    return new Promise((resolve) => {
        const img = new Image();
        img.onload = () => {
            resolve(true);
        }
        img.onerror = () => resolve(false);
        img.src = url;
    });
};
// 处理 Markdown 中的图片
const processMarkdown = (markdownText) => {
    // 自定义渲染器处理图片
    const renderer = {
        image(href, title, text) {
            return `<img src="${href}" alt="${text}" title="${title || ''}"  class="markdown-image" style="max-width: 708px;height: 230px;">`;
        }
    };

    marked.use({ renderer });

    // 第一次渲染
    let html = marked.parse(markdownText);

    // 创建虚拟 DOM 来操作
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');

    // 检查所有图片
    // const images = doc.querySelectorAll('img');
    // images.forEach(async item => {
    //     const isValid = await checkImage(item.src);
    //     if (!isValid) {
    //         item.remove();
    //     }
    // });
    // if (props.isFirstEnter) { 
    //     emit('scroll-bottom')
    // }
    return doc.body.innerHTML;
};
const handleImg = async (newVal) => {
    let index = newVal.lastIndexOf('![');
    if (index != -1) {
        isImgLoading.value = true;
        let str = newVal.slice(index)
        if (str.includes('](') && str.includes(')')) {
            processedMarkdown.value = splitMarkdownByImages(newVal)
            isImgLoading.value = false;
        } else {
            processedMarkdown.value = splitMarkdownByImages(newVal.slice(0, index))
        }
    } else {
        processedMarkdown.value = splitMarkdownByImages(newVal)
    }
    removeImg()
}
function splitMarkdownByImages(markdown) {
    const imageRegex = /!\[.*?\]\(\s*(?:<([^>]*)>|([^)\s]*))\s*(?:["'].*?["'])?\s*\)/g;
    const result = [];
    let lastIndex = 0;
    let match;

    while ((match = imageRegex.exec(markdown)) !== null) {
        const textBefore = markdown.slice(lastIndex, match.index);
        if (textBefore) result.push(textBefore);
        const url = match[1] || match[2];
        result.push(url);
        lastIndex = imageRegex.lastIndex;
    }

    const remainingText = markdown.slice(lastIndex);
    if (remainingText) result.push(remainingText);

    return result;
}
function isLink(str) {
    const trimmedStr = str.trim();
    // 正则表达式匹配常见链接格式
    const urlPattern = /^(https?:\/\/|ftp:\/\/|www\.)(?:(?:[\w-]+(?:\.[\w-]+)*)|(?:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})|(?:\[[a-fA-F0-9:]+\]))(?::\d{1,5})?(?:[\/\w.,@?^=%&:~+#-]*[\w@?^=%&\/~+#-])?/i;
    return urlPattern.test(trimmedStr);
}

watch(() => props.content, (newVal) => {
    debounce(handleImg(newVal), 800)
}, {
    immediate: true
})

const myMarkdown = (res) => {
    return marked.parse(res, { renderer })
}

onMounted(async () => {
    processedMarkdown.value = splitMarkdownByImages(props.content);
    removeImg()
});
</script>
<style lang="less" scoped>
@import '../../../components/css/markdown.less';

:deep(.ai-markdown-template) {
    contain: content;
    line-height: 28px;
    letter-spacing: 1px;

    h1,
    h2,
    h3,
    h4 {
        line-height: 14px;
        font-size: 16px;
    }

}

.ai-markdown-img {
    border-radius: 8px;
    display: block;
    cursor: pointer;
    object-fit: scale-down;
    contain: content;
    margin-left: 16px;
    border: 0.5px solid #E7E7E7;
    max-width: 708px;
    height: 230px;
}

.bot_msg {
    background: #fff;
    border-radius: 4px;
    color: rgba(0, 0, 0, 0.9);
    font-size: 16px;
    padding: 10px 12px;
    margin-right: auto;
    max-width: 100%;
    box-sizing: border-box;
}

.botanswer_laoding_gif {
    width: 24px;
    height: 18px;
    margin-left: 16px;
}

.img_loading {
    background: #3032360f;
    height: 230px;
    width: 230px;
    color: #00000042;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    font-size: 12px;
    gap: 4px;
    margin-left: 16px;
    border-radius: 8px;
}

:deep(.t-loading__gradient-conic) {
    background: conic-gradient(from 90deg at 50% 50%, #fff 0deg, #676767 360deg) !important;
}

/* 科技风格机器人消息 */
.tech-bot-msg {
    background: var(--tech-gradient-card) !important;
    border: 1px solid var(--tech-border);
    border-radius: 12px;
    color: var(--tech-text-primary) !important;
    backdrop-filter: blur(10px);
    position: relative;
    overflow: hidden;
    box-shadow: var(--tech-shadow-card);
    transition: all 0.3s ease;
    animation: slideInLeft 0.5s ease-out;
}

.tech-bot-msg::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 2px;
    background: var(--tech-gradient-accent);
    opacity: 0.6;
    animation: pulse 2s infinite;
}

.tech-bot-msg::after {
    content: '';
    position: absolute;
    top: -1px;
    left: -1px;
    right: -1px;
    bottom: -1px;
    background: linear-gradient(45deg, transparent, var(--tech-primary), transparent);
    border-radius: 13px;
    opacity: 0;
    z-index: -1;
    transition: opacity 0.3s ease;
}

.tech-bot-msg:hover {
    border-color: var(--tech-border-glow);
    box-shadow: var(--tech-shadow-glow);
    transform: translateY(-2px);
}

.tech-bot-msg:hover::after {
    opacity: 0.2;
}

@keyframes slideInLeft {
    from {
        opacity: 0;
        transform: translateX(-30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes pulse {
    0%, 100% {
        opacity: 0.6;
    }
    50% {
        opacity: 1;
    }
}

.tech-bot-msg .ai-markdown-img {
    border: 1px solid var(--tech-border);
    border-radius: 12px;
    box-shadow: var(--tech-shadow-card);
    transition: all 0.3s ease;
}

.tech-bot-msg .ai-markdown-img:hover {
    border-color: var(--tech-primary);
    box-shadow: var(--tech-shadow-glow);
    transform: scale(1.02);
}

.tech-bot-msg .img_loading {
    background: var(--tech-bg-secondary);
    border: 1px solid var(--tech-border);
    color: var(--tech-text-muted);
    border-radius: 12px;
}

.tech-bot-msg .botanswer_laoding_gif {
    filter: brightness(0) invert(1);
    opacity: 0.8;
}

.tech-bot-msg :deep(.ai-markdown-template) {
    color: var(--tech-text-primary);
}

.tech-bot-msg :deep(.ai-markdown-template h1),
.tech-bot-msg :deep(.ai-markdown-template h2),
.tech-bot-msg :deep(.ai-markdown-template h3),
.tech-bot-msg :deep(.ai-markdown-template h4) {
    color: var(--tech-primary);
    text-shadow: 0 0 4px var(--tech-primary);
}

.tech-bot-msg :deep(.ai-markdown-template code) {
    background: var(--tech-bg-secondary);
    color: var(--tech-accent);
    border: 1px solid var(--tech-border);
    border-radius: 4px;
    padding: 2px 6px;
}

.tech-bot-msg :deep(.ai-markdown-template pre) {
    background: var(--tech-bg-secondary);
    border: 1px solid var(--tech-border);
    border-radius: 8px;
    box-shadow: var(--tech-shadow-card);
}

.tech-bot-msg :deep(.ai-markdown-template blockquote) {
    border-left: 3px solid var(--tech-primary);
    background: var(--tech-bg-secondary);
    color: var(--tech-text-secondary);
    box-shadow: 0 0 10px rgba(0, 255, 255, 0.1);
}

.tech-bot-msg :deep(.ai-markdown-template a) {
    color: var(--tech-primary);
    text-decoration: none;
    transition: all 0.3s ease;
}

.tech-bot-msg :deep(.ai-markdown-template a:hover) {
    color: var(--tech-accent);
    text-shadow: 0 0 4px var(--tech-accent);
}

.tech-bot-msg :deep(.t-loading__gradient-conic) {
    background: conic-gradient(from 90deg at 50% 50%, var(--tech-primary) 0deg, var(--tech-accent) 360deg) !important;
}
</style>