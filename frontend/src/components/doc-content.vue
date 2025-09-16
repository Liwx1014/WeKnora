<script setup lang="ts">
import { marked } from "marked";
import markedKatex from "marked-katex-extension"; 
import 'katex/dist/katex.min.css';
import { onMounted, ref, nextTick, onUnmounted, onUpdated, watch } from "vue";
import { downKnowledgeDetails } from "@/api/knowledge-base/index";
import { MessagePlugin } from "tdesign-vue-next";
import picturePreview from '@/components/picture-preview.vue';
marked.use({
  mangle: false,
  headerIds: false,
});
marked.use(markedKatex({
  throwOnError: false 
}));
const renderer = new marked.Renderer();
let page = 1;
let doc = null;
let down = ref()
let mdContentWrap = ref()
let url = ref('')
let reviewUrl = ref('')
let reviewImg = ref(false)
onMounted(() => {
  nextTick(() => {
    const drawerBody = document.querySelector('.t-drawer__body');
    if (drawerBody) {
      doc = drawerBody;
      doc.addEventListener('scroll', handleDetailsScroll);
    }
  })
})
onUpdated(() => {
  page = 1
})
onUnmounted(() => {
  if (doc) {
    doc.removeEventListener('scroll', handleDetailsScroll);
  }
})
const checkImage = (url) => {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve(true);
    img.onerror = () => resolve(false);
    img.src = url;
  });
};
renderer.image = function (href, title, text) {
  // 自定义HTML结构，图片展示带标题
  return `<figure>
                <img class="markdown-image" src="${href}" alt="${title}" title="${text}">
                <figcaption style="text-align: left;">${text}</figcaption>
            </figure>`;
};
const props = defineProps(["visible", "details"]);
const emit = defineEmits(["closeDoc", "getDoc", "deleteDoc"]);
watch(() => props.details.md, (newVal) => {
  nextTick(async () => {
    const images = mdContentWrap.value.querySelectorAll('img.markdown-image');
    if (images) {
      images.forEach(async item => {
        item.addEventListener('click', function (event) {
          reviewUrl.value = event.target.src;
          reviewImg.value = true
        })
        const isValid = await checkImage(item.src);
        if (!isValid) {
          item.remove();
        }
      })
    }
  })
}, {
  immediate: true,
  deep: true
})

// 处理 Markdown 中的图片
const processMarkdown = (markdownText) => {
  // 自定义渲染器处理图片
  marked.use({ renderer });
  let html = marked.parse(markdownText);
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, 'text/html');
  return doc.body.innerHTML;
};
const closePreImg = () => {
  reviewImg.value = false
  reviewUrl.value = '';
}
const handleClose = () => {
  emit("closeDoc", false);
  doc.scrollTop = 0;
};

const handleDelete = () => {
  emit("deleteDoc", props.details);
  emit("closeDoc", false);
};
const downloadFile = () => {
  downKnowledgeDetails(props.details.id)
    .then((result) => {
      if (result) {
        url.value = URL.createObjectURL(result);
        down.value.click();
        // const link = document.createElement("a");
        // link.style.display = "none";
        // link.setAttribute("href", url);
        // link.setAttribute("download", props.details.title);
        // link.click();
        // document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }
    })
    .catch((err) => {
      MessagePlugin.error("获取文件失败！");
    });
};
const handleDetailsScroll = () => {
  if (doc) {
    let pageNum = Math.ceil(props.details.total / 20);
    const { scrollTop, scrollHeight, clientHeight } = doc;
    if (scrollTop + clientHeight >= scrollHeight) {
      page++;
      if (props.details.md.length < props.details.total && page <= pageNum) {
        emit("getDoc", page);
      }
    }
  }
};
</script>
<template>
  <div class="doc_content" ref="mdContentWrap">
    <t-drawer :visible="visible" :zIndex="2000" :closeBtn="true" @close="handleClose">
      <template #header>{{
        details.title.substring(0, details.title.lastIndexOf("."))
      }}</template>
      <div class="doc_box">
        <a :href="url" style="display: none" ref="down" :download="details.title"></a>
        <span class="label">文档标题</span>
        <div class="download_box">
          <span class="doc_t">{{ details.title }}</span>
          <div class="icon_box" @click="downloadFile()">
            <img class="download_box" src="@/assets/img/download.svg" alt="">
          </div>
        </div>
      </div>
      <div class="content_header">
        <span class="label">文档内容</span>
        <span class="time"> 更新时间：{{ details.time }} </span>
      </div>
      <div v-if="details.md.length == 0" class="no_content">暂无数据</div>
      <div v-else class="content" v-for="(item, index) in details.md" :key="index" :style="index % 2 !== 0
        ? 'background:rgb(218, 241, 234);'
        : 'background:rgb(215, 243, 232);'
        ">
        <div class="md-content" v-html="processMarkdown(item.content)"></div>
      </div>
      <template #footer>
        <t-button theme="danger" @click="handleDelete">删除</t-button>
      </template>
    </t-drawer>
    <picturePreview :reviewImg="reviewImg" :reviewUrl="reviewUrl" @closePreImg="closePreImg"></picturePreview>
  </div>
</template>
<!-- 将你原来的 <style scoped lang="less"> 标签内容完整替换为这个 -->
<style scoped lang="less">
@import "./css/markdown.less";

/* TDesign 抽屉组件样式覆盖 */
:deep(.t-drawer .t-drawer__content-wrapper) {
  width: 654px !important;
  /* 明确设置背景为白色 */
  background-color: #ffffff; 
}

:deep(.t-drawer__header) {
  font-weight: 800;
  /* 设置头部背景、文字颜色和下边框 */
  background-color:rgb(218, 238, 227);
  color: #1a1a1a;
  border-bottom: 1px solid #f0f0f0;
}

:deep(.t-drawer__body) {
  padding: 16px 24px;
  color: #333333; /* 设置内容区域的默认文字颜色 */
}

:deep(.t-drawer__footer) {
  /* 设置脚部背景和上边框 */
  background-color:rgb(45, 65, 48);
  border-top: 1px solid #f0f0f0;
}

/* --- 以下是组件内部元素的浅色样式 --- */

.content {
  word-break: break-word;
  padding: 4px;
  gap: 4px;
  margin-top: 12px;
  border-radius: 4px;
}

.doc_box {
  display: flex;
  flex-direction: column;
}

.label {
  /* 设置标签文字颜色为深灰色 */
  color: rgba(0, 0, 0, 0.85);
  font-size: 14px;
  font-style: normal;
  font-weight: 500;
  line-height: 22px;
  margin-bottom: 8px;
}

.download_box {
  display: flex;
  align-items: center;
}

.doc_t {
  box-sizing: border-box;
  display: flex;
  padding: 5px 8px;
  align-items: center;
  border-radius: 3px;
  /* 设置浅色边框和背景 */
  border: 1px solid #dcdcdc;
  background: #f5f5f5;
  word-break: break-all;
  text-align: justify;
  /* 设置文档标题文字颜色 */
  color: rgba(0, 0, 0, 0.85);
}

.icon_box {
  margin-left: 18px;
  display: flex;
  overflow: hidden;
  /* 下载图标保持品牌绿色 */
  color: #07c05f;

  .download_box {
    width: 16px;
    height: 16px;
    fill: currentColor;
    overflow: hidden;
    cursor: pointer;
  }
}

.content_header {
  margin-top: 22px;
  margin-bottom: 24px;
}

.time {
  margin-left: 12px;
  /* 设置时间文字为较浅的灰色 */
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
  font-style: normal;
  font-weight: 400;
  line-height: 20px;
}

.no_content {
  margin-top: 12px;
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
  padding: 16px;
  /* 设置“暂无数据”的浅色背景 */
  background: #fafafa;
  text-align: center;
  border-radius: 4px;
}
</style>
