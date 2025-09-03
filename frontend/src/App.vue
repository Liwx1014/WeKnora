<script setup lang="ts">
import { onMounted } from 'vue';

onMounted(() => {
  // 设置深色科技主题
  document.documentElement.setAttribute('theme-mode', 'tech-dark');
  document.body.setAttribute('theme-mode', 'tech-dark');
});
</script>
<template>
  <div id="app" class="tech-app">
    <RouterView />
  </div>
</template>
<style>
body,
html,
#app {
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
    font-size: 14px;
    font-family: 'SF Pro Display', 'Helvetica Neue', Arial, 'PingFang SC', 'Hiragino Sans GB',
        'Microsoft YaHei', 'SimSun', sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #16213e 100%);
    color: #ffffff;
    overflow-x: hidden;
}

.tech-app {
    position: relative;
    min-height: 100vh;
}

/* 科技风格背景网格效果 */
.tech-app::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: 
        linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px);
    background-size: 50px 50px;
    pointer-events: none;
    z-index: -1;
}

/* 科技风格光效动画 */
.tech-app::after {
    content: '';
    position: fixed;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(0, 212, 255, 0.05) 0%, transparent 70%);
    animation: tech-rotate 20s linear infinite;
    pointer-events: none;
    z-index: -1;
}

@keyframes tech-rotate {
    from {
        transform: rotate(0deg);
    }
    to {
        transform: rotate(360deg);
    }
}

/* 全局滚动条样式 */
* {
    scrollbar-width: thin;
    scrollbar-color: #00d4ff #1a1a2e;
}

*::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

*::-webkit-scrollbar-track {
    background: #1a1a2e;
    border-radius: 4px;
}

*::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #00d4ff, #0099cc);
    border-radius: 4px;
    transition: background 0.3s ease;
}

*::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #33ddff, #00d4ff);
}

*::-webkit-scrollbar-corner {
    background: #1a1a2e;
}
</style>
