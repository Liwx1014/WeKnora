<script setup lang="ts">
import { ref, defineEmits, onMounted, defineProps, defineExpose } from "vue";
import useKnowledgeBase from '@/hooks/useKnowledgeBase';
import { onBeforeRouteUpdate } from 'vue-router';
import { MessagePlugin } from "tdesign-vue-next";
let { cardList, total, getKnowled } = useKnowledgeBase()
let query = ref("");
const props = defineProps({
  isReplying: {
    type: Boolean,
    required: false
  }
});
onMounted(() => {
  getKnowled()
})
const emit = defineEmits(['send-msg']);
const createSession = (val: string) => {
  if (!val.trim()) {
    MessagePlugin.info("请先输入内容!");
    return
  }
  if (!query.value && cardList.value.length == 0) {
    MessagePlugin.info("请先上传知识库!");
    return;
  }
  if (props.isReplying) {
    return MessagePlugin.error("正在回复中，请稍后再试!");
  }
  emit('send-msg', val);
  clearvalue();
}
const clearvalue = () => {
  query.value = "";
}
const onKeydown = (val: string, event: { e: { preventDefault(): unknown; keyCode: number; shiftKey: any; ctrlKey: any; }; }) => {
  if ((event.e.keyCode == 13 && event.e.shiftKey) || (event.e.keyCode == 13 && event.e.ctrlKey)) {
    return;
  }
  if (event.e.keyCode == 13) {
    event.e.preventDefault();
    createSession(val)
  }
}
onBeforeRouteUpdate((to, from, next) => {
  clearvalue()
  next()
})

</script>
<template>
  <div class="answers-input">
    <t-textarea v-model="query" placeholder="基于知识库提问" name="description" :autosize="true" @keydown="onKeydown" />
    <div class="answers-input-source">
      <span>{{ total }}个来源</span>
    </div>
    <div @click="createSession(query)" class="answers-input-send"
      :class="[query.length && total ? '' : 'grey-out']">
      <img src="../assets/img/sending-aircraft.svg" alt="">
    </div>
  </div>
</template>
<style scoped lang="less">
.answers-input {
  position: relative;
  z-index: 99;
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
}

:deep(.t-textarea__inner) {
  width: 100% !important;
  max-height: 250px !important;
  min-height: 112px !important;
  resize: none;
  color: #000000e6;
  font-size: 16px;
  font-weight: 400;
  line-height: 24px;
  color: #000000e6;
  font-family: "PingFang SC";
  padding: 16px 12px 12px 16px;
  border-radius: 12px;
  border: 1px solid #E7E7E7;
  box-sizing: border-box;
  background: #FFF;
  box-shadow: 0 6px 6px 0 #0000000a, 0 12px 12px -1px #00000014;

  &:focus {
    border: 1px solid #07C05F;
  }

  &:placeholder {
    color: #00000066;
    font-family: "PingFang SC";
    font-size: 16px;
    font-weight: 400;
    line-height: 24px;
  }
}

.answers-input-send {
  background-color: #07C05F;
  height: 36px;
  width: 36px;
  display: flex;
  justify-content: center;
  align-items: center;
  position: absolute;
  bottom: 12px;
  right: 12px;
  cursor: pointer;
  border-radius: 8px;
}

.answers-input-source {
  position: absolute;
  bottom: 12px;
  right: 64px;
  line-height: 32px;
  color: #00000066;
  font-family: "PingFang SC";
  font-size: 12px;
  font-weight: 400;
}

.grey-out {
  background-color: #b5eccf !important;
  cursor: no-drop !important;
}

/* 科技风格输入框适配 */
.tech-chat :deep(.t-textarea__inner) {
  background: var(--tech-bg-card) !important;
  border: 1px solid var(--tech-border) !important;
  color: var(--tech-text-primary) !important;
  box-shadow: var(--tech-shadow-card) !important;
}

.tech-chat :deep(.t-textarea__inner:focus) {
  border: 1px solid var(--tech-primary) !important;
  box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2) !important;
}

.tech-chat :deep(.t-textarea__inner::placeholder) {
  color: var(--tech-text-muted) !important;
}

.tech-chat .answers-input-source {
  color: var(--tech-text-muted) !important;
}

.tech-chat .answers-input-send {
  background-color: var(--tech-primary) !important;
}

.tech-chat .grey-out {
  background-color: var(--tech-text-muted) !important;
}

</style>
