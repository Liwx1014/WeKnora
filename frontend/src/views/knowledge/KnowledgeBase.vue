<script setup lang="ts">
import { ref, onMounted, watch, reactive } from "vue";
import DocContent from "@/components/doc-content.vue";
import InputField from "@/components/Input-field.vue";
import useKnowledgeBase from '@/hooks/useKnowledgeBase';
import { useRoute, useRouter } from 'vue-router';
import EmptyKnowledge from '@/components/empty-knowledge.vue';
import { getSessionsList, createSessions, generateSessionsTitle } from "@/api/chat/index";
import { useMenuStore } from '@/stores/menu';
import { getTestData } from '@/utils/request';
const usemenuStore = useMenuStore();
const router = useRouter();
import {
  batchQueryKnowledge,
} from "@/api/knowledge-base/index";
let { cardList, total, moreIndex, details, getKnowled, delKnowledge, openMore, onVisibleChange, getCardDetails, getfDetails, requestMethod } = useKnowledgeBase()
let uploadInput = ref()
let isCardDetails = ref(false);
let timeout = null;
let delDialog = ref(false)
let knowledge = ref({})
let knowledgeIndex = ref(-1)
let knowledgeScroll = ref()
let page = 1;
let pageSize = 35;
const getPageSize = () => {
  const viewportHeight = window.innerHeight || document.documentElement.clientHeight;
  const itemHeight = 174;
  let itemsInView = Math.floor(viewportHeight / itemHeight) * 5;
  pageSize = Math.max(35, itemsInView);
}
getPageSize()
onMounted(() => {
  getKnowled({ page: 1, page_size: pageSize });
});
watch(() => cardList.value, (newValue) => {
  let analyzeList = [];
  analyzeList = newValue.filter(item => {
    return item.parse_status == 'pending' || item.parse_status == 'processing';
  })
  clearInterval(timeout);
  timeout = null;
  if (analyzeList.length) {
    updateStatus(analyzeList)
  }
}, { deep: true })
const updateStatus = (analyzeList) => {
  let query = ``;
  for (let i = 0; i < analyzeList.length; i++) {
    query += `ids=${analyzeList[i].id}&`;
  }
  timeout = setInterval(() => {
    batchQueryKnowledge(query).then((result) => {
      if (result.success && result.data) {
        result.data.forEach(item => {
          if (item.parse_status == 'failed' || item.parse_status == 'completed') {
            let index = cardList.value.findIndex(card => card.id == item.id);
            if (index != -1) {
              cardList.value[index].parse_status = item.parse_status;
              cardList.value[index].description = item.description;
            }
          }
        });
      }
    }).catch((_err) => {
      // 错误处理
    });
  }, 1500);
};

const closeDoc = () => {
  isCardDetails.value = false;
};
const openCardDetails = (item) => {
  isCardDetails.value = true;
  getCardDetails(item);
};

const delCard = (index, item) => {
  knowledgeIndex.value = index;
  knowledge.value = item;
  delDialog.value = true;
};

const handleScroll = () => {
  const element = knowledgeScroll.value;
  if (element) {
    let pageNum = Math.ceil(total.value / pageSize)
    const { scrollTop, scrollHeight, clientHeight } = element;
    if (scrollTop + clientHeight >= scrollHeight) {
      page++;
      if (cardList.value.length < total.value && page <= pageNum) {
        getKnowled({ page, page_size: pageSize });
      }
    }
  }
};
const getDoc = (page) => {
  getfDetails(details.id, page)
};

const handleDeleteDoc = (docDetails) => {
  // 找到要删除的文档在cardList中的索引
  const index = cardList.value.findIndex(item => item.id === docDetails.id);
  if (index !== -1) {
    // 设置要删除的文档信息
    knowledgeIndex.value = index;
    knowledge.value = cardList.value[index];
    // 显示删除确认对话框
    delDialog.value = true;
  }
};

const delCardConfirm = () => {
  delDialog.value = false;
  delKnowledge(knowledgeIndex.value, knowledge.value);
};

const sendMsg = (value: string) => {
  createNewSession(value);
};

const getTitle = (session_id: string, value: string) => {
  let obj = { title: '新会话', path: `chat/${session_id}`, id: session_id, isMore: false, isNoTitle: true };
  usemenuStore.updataMenuChildren(obj);
  usemenuStore.changeIsFirstSession(true);
  usemenuStore.changeFirstQuery(value);
  router.push(`/platform/chat/${session_id}`);
};

async function createNewSession(value: string): Promise<void> {
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
  if (!testData || !testData.knowledge_bases || testData.knowledge_bases.length === 0) {
    console.error("测试数据未初始化或不包含知识库");
    return;
  }

  // 使用第一个知识库ID
  knowledgeBaseId = testData.knowledge_bases[0].id;

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
}

// 上传功能方法
const triggerFileUpload = () => {
  uploadInput.value.click();
};

const handleFileUpload = (event) => {
  const file = event.target.files[0];
  if (file) {
    requestMethod(file, uploadInput);
  }
};
</script>

<template>
  <div class="knowledge-container">
    <!-- 上传按钮区域 -->
    <div class="upload-section">
      <input type="file" ref="uploadInput" @change="handleFileUpload" accept=".pdf,.docx,.doc,.txt,.md" style="display: none" />
      <button class="upload-btn" @click="triggerFileUpload">
        <t-icon name="upload" class="upload-icon" />
        <span>上传文档</span>
      </button>
      <span class="upload-desc">支持 PDF、DOC、TXT、MD 格式，单个文件不超过 10MB</span>
    </div>
    
    <div v-show="cardList.length" class="knowledge-card-box" style="position: relative">
      <div class="knowledge-card-wrap" ref="knowledgeScroll" @scroll="handleScroll">
      <div class="knowledge-card" v-for="(item, index) in cardList" :key="index" @click="openCardDetails(item)">
        <div class="card-content">
          <div class="card-content-nav">
            <span class="card-content-title">{{ item.file_name }}</span>
            <t-popup v-model="item.isMore" @overlay-click="delCard(index, item)" overlayClassName="card-more"
              :on-visible-change="onVisibleChange" trigger="click" destroy-on-close placement="bottom-right">
              <div variant="outline" class="more-wrap" @click.stop="openMore(index)"
                :class="[moreIndex == index ? 'active-more' : '']">
                <img class="more" src="@/assets/img/more.png" alt="" />
              </div>
              <template #content>
                <t-icon class="icon svg-icon del-card" name="delete" />
                <span class="del-card" style="margin-left: 8px">删除文档</span>
              </template>
            </t-popup>
          </div>
          <div class="card-analyze" v-show="item.parse_status != 'completed'">
            <t-icon :name="item.parse_status == 'failed' ? 'close-circle' : 'loading'" class="card-analyze-loading"
              :class="[item.parse_status == 'failed' ? 'failure' : '']"></t-icon>
            <span class="card-analyze-txt" :class="[item.parse_status == 'failed' ? 'failure' : '']">{{
              item.parse_status == "failed" ? "解析失败" : "解析中..."
            }}</span>
          </div>
          <div v-show="item.parse_status == 'completed'" class="card-content-txt">
            {{ item.description }}
          </div>
        </div>
        <div class="card-bottom">
          <span class="card-time">{{ item.updated_at }}</span>
          <div class="card-type">
            <span>{{ item.file_type }}</span>
          </div>
        </div>
      </div>
      <t-dialog v-model:visible="delDialog" dialogClassName="del-knowledge" :closeBtn="false" :cancelBtn="null"
        :confirmBtn="null">
        <div class="circle-wrap">
          <div class="header">
            <img class="circle-img" src="@/assets/img/circle.png" alt="">
            <span class="circle-title">删除确认</span>
          </div>
          <span class="del-circle-txt">
            {{ `确认要删除技能"${knowledge.file_name}"，删除后不可恢复` }}
          </span>
          <div class="circle-btn">
            <span class="circle-btn-txt" @click="delDialog = false">取消</span>
            <span class="circle-btn-txt confirm" @click="delCardConfirm">确认删除</span>
          </div>
        </div>
      </t-dialog>
    </div>
      <InputField @send-msg="sendMsg"></InputField>
      <DocContent :visible="isCardDetails" :details="details" @closeDoc="closeDoc" @getDoc="getDoc" @deleteDoc="handleDeleteDoc"></DocContent>
    </div>
    <EmptyKnowledge v-show="!cardList.length"></EmptyKnowledge>
  </div>
</template>
<style>
.card-more {
  z-index: 99 !important;
}

.card-more .t-popup__content {
  width: 160px;
  height: 40px;
  line-height: 30px;
  padding-left: 14px;
  cursor: pointer;
  margin-top: 4px !important;
  color: #000000e6;
}
.card-more .t-popup__content:hover {
  color: #FA5151 !important;
}
</style>
<style scoped lang="less">
.knowledge-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.upload-section {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  gap: 16px;
  background: rgba(0, 0, 0, 0.02);
  backdrop-filter: blur(10px);
}

.upload-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #00d4aa 0%, #00a693 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 212, 170, 0.3);
}

.upload-btn:hover {
  background: linear-gradient(135deg, #00a693 0%, #008a7a 100%);
  box-shadow: 0 4px 12px rgba(0, 212, 170, 0.4);
  transform: translateY(-1px);
}

.upload-icon {
  font-size: 16px;
}

.upload-desc {
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
  font-weight: 400;
}

.knowledge-card-box {
  flex: 1;
  overflow: hidden;
}

@media (max-width: 1250px) and (min-width: 1045px) {
  .answers-input {
    transform: translateX(-329px);
  }

  :deep(.t-textarea__inner) {
    width: 654px !important;
  }
}

@media (max-width: 1045px) {
  .answers-input {
    transform: translateX(-250px);
  }

  :deep(.t-textarea__inner) {
    width: 500px !important;
  }
}

@media (max-width: 750px) {
  .answers-input {
    transform: translateX(-182px);
  }

  :deep(.t-textarea__inner) {
    width: 340px !important;
  }
}

@media (max-width: 600px) {
  .answers-input {
    transform: translateX(-164px);
  }

  :deep(.t-textarea__inner) {
    width: 300px !important;
  }
}

.knowledge-card-wrap {
  // padding: 24px 44px;
  padding: 24px 44px 80px 44px;
  box-sizing: border-box;
  display: grid;
  gap: 20px;
  overflow-y: auto;
  height: 100%;
  align-content: flex-start;
}

:deep(.del-knowledge) {
  padding: 0px !important;
  border-radius: 6px !important;

  .t-dialog__header {
    display: none;
  }

  .t-dialog__body {
    padding: 16px;
  }

  .t-dialog__footer {
    padding: 0;
  }
}

:deep(.t-dialog__position.t-dialog--top) {
  padding-top: 40vh !important;
}

.circle-wrap {
  .header {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
  }

  .circle-img {
    width: 20px;
    height: 20px;
    margin-right: 8px;
  }

  .circle-title {
    color: #000000e6;
    font-family: "PingFang SC";
    font-size: 16px;
    font-weight: 600;
    line-height: 24px;
  }

  .del-circle-txt {
    color: #00000099;
    font-family: "PingFang SC";
    font-size: 14px;
    font-weight: 400;
    line-height: 22px;
    display: inline-block;
    margin-left: 29px;
    margin-bottom: 21px;
  }

  .circle-btn {
    height: 22px;
    width: 100%;
    display: flex;
    justify-content: end;
  }

  .circle-btn-txt {
    color: #000000e6;
    font-family: "PingFang SC";
    font-size: 14px;
    font-weight: 400;
    line-height: 22px;
    cursor: pointer;
  }

  .confirm {
    color: #FA5151;
    margin-left: 40px;
  }
}


.knowledge-card {
  border: 2px solid #fbfbfb;
  height: 174px;
  border-radius: 6px;
  overflow: hidden;
  box-sizing: border-box;
  box-shadow: 0 0 8px 0 #00000005;
  background: #fff;
  position: relative;
  cursor: pointer;

  .card-content {
    padding: 10px 20px 23px;
  }

  .card-analyze {
    height: 66px;
    display: flex;
  }

  .card-analyze-loading {
    display: block;
    color: #07c05f;
    font-size: 15px;
    margin-top: 2px;
  }

  .card-analyze-txt {
    color: #07c05f;
    font-family: "PingFang SC";
    font-size: 12px;
    margin-left: 9px;
  }

  .failure {
    color: #fa5151;
  }

  .card-content-nav {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
  }

  .card-content-title {
    width: 200px;
    height: 32px;
    line-height: 32px;
    display: inline-block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: #000000e6;
    font-family: "PingFang SC";
    font-size: 14px;
    font-weight: 400;
  }

  .more-wrap {
    display: flex;
    width: 32px;
    height: 32px;
    justify-content: center;
    align-items: center;
    border-radius: 3px;
    cursor: pointer;
  }

  .more-wrap:hover {
    background: #e7e7e7;
  }

  .more {
    width: 16px;
    height: 16px;
  }

  .active-more {
    background: #e7e7e7;
  }

  .card-content-txt {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 3;
    overflow: hidden;
    color: #00000066;
    font-family: "PingFang SC";
    font-size: 12px;
    font-weight: 400;
    line-height: 20px;
  }

  .card-bottom {
    position: absolute;
    bottom: 0;
    padding: 0 20px;
    box-sizing: border-box;
    height: 32px;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: rgba(48, 50, 54, 0.02);
  }

  .card-time {
    color: #00000066;
    font-family: "PingFang SC";
    font-size: 12px;
    font-weight: 400;
  }

  .card-type {
    color: #00000066;
    font-family: "PingFang SC";
    font-size: 12px;
    font-weight: 400;
    padding: 2px 4px;
    background: #3032360f;
    border-radius: 4px;
  }
}

.knowledge-card:hover {
  border: 2px solid #07c05f;
}

.knowledge-card-upload {
  color: #000000e6;
  font-family: "PingFang SC";
  font-size: 14px;
  font-weight: 400;
  cursor: pointer;

  .btn-upload {
    margin: 33px auto 0;
    width: 112px;
    height: 32px;
    border: 1px solid #dcdcdc;
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 24px;
  }

  .svg-icon-download {
    margin-right: 8px;
  }
}

.upload-described {
  color: #00000066;
  font-family: "PingFang SC";
  font-size: 12px;
  font-weight: 400;
  text-align: center;
  display: block;
  width: 188px;
  margin: 0 auto;
}

.knowledge-card-wrap {
  grid-template-columns: 1fr;
}

.del-card {
  vertical-align: middle;
}

/* 小屏幕平板 - 2列 */
@media (min-width: 900px) {
  .knowledge-card-wrap {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 中等屏幕 - 3列 */
@media (min-width: 1250px) {
  .knowledge-card-wrap {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* 中等屏幕 - 3列 */
@media (min-width: 1600px) {
  .knowledge-card-wrap {
    grid-template-columns: repeat(4, 1fr);
  }
}

/* 大屏幕 - 4列 */
@media (min-width: 2000px) {
  .knowledge-card-wrap {
    grid-template-columns: repeat(5, 1fr);
  }
}

/* 科技风格知识库适配 */
:root[theme-mode="tech-dark"] {
  .knowledge-container {
    background: var(--tech-bg-primary);
  }

  .upload-section {
    background: var(--tech-bg-card) !important;
    border-bottom: 1px solid var(--tech-border) !important;
    backdrop-filter: blur(20px);
  }

  .upload-desc {
    color: var(--tech-text-muted) !important;
  }

  .knowledge-card {
    background: var(--tech-bg-card) !important;
    border: 1px solid var(--tech-border) !important;
    box-shadow: var(--tech-shadow-card) !important;

    &:hover {
      border-color: var(--tech-primary) !important;
      box-shadow: var(--tech-shadow-glow) !important;
    }

    .card-content-title {
      color: var(--tech-text-primary) !important;
    }

    .card-content-txt {
      color: var(--tech-text-secondary) !important;
    }

    .card-analyze-txt {
      color: var(--tech-success) !important;
    }

    .card-time,
    .card-type {
      color: var(--tech-text-muted) !important;
    }

    .card-type {
      background: var(--tech-bg-secondary) !important;
    }

    .card-bottom {
      background: var(--tech-bg-secondary) !important;
    }

    .more-wrap:hover {
      background: var(--tech-bg-hover) !important;
    }
  }

  .knowledge-card-upload {
    color: var(--tech-text-secondary) !important;

    .btn-upload {
      border-color: var(--tech-border) !important;
      background: var(--tech-bg-secondary) !important;
      color: var(--tech-text-primary) !important;

      &:hover {
        border-color: var(--tech-primary) !important;
        background: var(--tech-bg-hover) !important;
      }
    }
  }

  .upload-described {
    color: var(--tech-text-muted) !important;
  }

  .circle-wrap {
    .circle-title {
      color: var(--tech-text-primary) !important;
    }

    .del-circle-txt {
      color: var(--tech-text-secondary) !important;
    }

    .circle-btn-txt {
      color: var(--tech-text-secondary) !important;

      &.confirm {
        color: var(--tech-danger) !important;
      }
    }
  }

  .card-more .t-popup__content {
    background: var(--tech-bg-card) !important;
    border: 1px solid var(--tech-border) !important;
    color: var(--tech-text-secondary) !important;

    &:hover {
      color: var(--tech-danger) !important;
      background: var(--tech-bg-hover) !important;
    }
  }
}
</style>