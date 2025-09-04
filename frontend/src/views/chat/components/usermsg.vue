<template>
    <div class="user_msg tech-user-msg">
        {{ content }}
    </div>
</template>
<script setup>
import { ref, defineProps } from "vue";

const props = defineProps({
    // 必填项
    content: {
        type: String,
        required: false
    }
});
</script>
<style scoped lang="less">
.user_msg {
    width: max-content;
    max-width: 776px;
    display: flex;
    padding: 10px 12px;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    gap: 4px;
    flex: 1 0 0;
    border-radius: 4px;
    background: #8CE97F;
    margin-left: auto;
    color: #000000e6;
    font-size: 16px;
    text-align: justify;
    word-break: break-all;
    max-width: 100%;
    box-sizing: border-box;
}

/* 科技风格用户消息 */
.tech-user-msg {
    background: var(--tech-gradient-user) !important;
    border: 1px solid var(--tech-primary);
    border-radius: 12px;
    color: var(--tech-text-primary) !important;
    backdrop-filter: blur(10px);
    position: relative;
    overflow: hidden;
    box-shadow: var(--tech-shadow-glow);
    transition: all 0.3s ease;
    animation: slideInRight 0.5s ease-out;
}

.tech-user-msg::before {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 100%;
    height: 2px;
    background: var(--tech-gradient-accent);
    opacity: 0.8;
    animation: shimmer 2s infinite;
}

.tech-user-msg::after {
    content: '';
    position: absolute;
    top: -2px;
    right: -2px;
    bottom: -2px;
    left: -2px;
    background: var(--tech-gradient-accent);
    border-radius: 14px;
    opacity: 0;
    z-index: -1;
    transition: opacity 0.3s ease;
}

.tech-user-msg:hover {
    border-color: var(--tech-accent);
    box-shadow: var(--tech-shadow-glow-strong);
    transform: translateY(-2px) scale(1.02);
}

.tech-user-msg:hover::after {
    opacity: 0.3;
}

@keyframes slideInRight {
    from {
        opacity: 0;
        transform: translateX(30px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes shimmer {
    0% {
        transform: translateX(-100%);
    }
    100% {
        transform: translateX(100%);
    }
}
</style>