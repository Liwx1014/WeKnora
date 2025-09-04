<template>
    <div class="settings-container">
        <div class="settings-header">
            <h2>系统配置</h2>
        </div>
        <div class="settings-form">
            <t-form ref="form" :data="formData" :rules="rules" @submit="onSubmit">
                <t-form-item label="API 服务端点" name="endpoint">
                    <t-input v-model="formData.endpoint" placeholder="请输入API服务端点，例如：http://localhost" />
                </t-form-item>
                <t-form-item label="API Key" name="apiKey">
                    <t-input v-model="formData.apiKey" placeholder="请输入API Key" />
                </t-form-item>
                <t-form-item label="知识库ID" name="knowledgeBaseId">
                    <t-input v-model="formData.knowledgeBaseId" placeholder="请输入知识库ID" />
                </t-form-item>
                <t-form-item>
                    <t-space>
                        <t-button theme="primary" type="submit">保存配置</t-button>
                        <t-button theme="default" @click="resetForm">重置</t-button>
                    </t-space>
                </t-form-item>
            </t-form>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { MessagePlugin } from 'tdesign-vue-next';
import { useSettingsStore } from '@/stores/settings';

const settingsStore = useSettingsStore();
const form = ref(null);

const formData = reactive({
    endpoint: '',
    apiKey: '',
    knowledgeBaseId: ''
});

const rules = {
    endpoint: [{ required: true, message: '请输入API服务端点', trigger: 'blur' }],
    apiKey: [{ required: true, message: '请输入API Key', trigger: 'blur' }],
    knowledgeBaseId: [{ required: true, message: '请输入知识库ID', trigger: 'blur' }]
};

onMounted(() => {
    // 初始化表单数据
    const settings = settingsStore.getSettings();
    formData.endpoint = settings.endpoint;
    formData.apiKey = settings.apiKey;
    formData.knowledgeBaseId = settings.knowledgeBaseId;
});

const onSubmit = ({ validateResult }) => {
    if (validateResult === true) {
        settingsStore.saveSettings({
            endpoint: formData.endpoint,
            apiKey: formData.apiKey,
            knowledgeBaseId: formData.knowledgeBaseId
        });
        MessagePlugin.success('配置保存成功');
    }
};

const resetForm = () => {
    const settings = settingsStore.getSettings();
    formData.endpoint = settings.endpoint;
    formData.apiKey = settings.apiKey;
    formData.knowledgeBaseId = settings.knowledgeBaseId;
};
</script>

<style lang="less" scoped>
.settings-container {
    padding: 20px;
    background-color: #fff;
    border-radius: 8px;
    margin: 20px;
    min-height: 80vh;

    .settings-header {
        margin-bottom: 20px;
        border-bottom: 1px solid #f0f0f0;
        padding-bottom: 16px;

        h2 {
            font-size: 20px;
            font-weight: 600;
            color: #000000;
            margin: 0;
        }
    }

    .settings-form {
        max-width: 600px;
    }
}

/* 科技风格设置页面适配 */
:root[theme-mode="tech-dark"] .settings-container {
    background-color: var(--tech-bg-card) !important;
    border: 1px solid var(--tech-border);
    box-shadow: var(--tech-shadow-card);

    .settings-header {
        border-bottom: 1px solid var(--tech-border) !important;

        h2 {
            color: var(--tech-text-primary) !important;
        }
    }

    /* 表单标签样式 */
    :deep(.t-form-item__label) {
        color: var(--tech-text-secondary) !important;
    }

    /* 输入框样式 */
    :deep(.t-input) {
        background: var(--tech-bg-secondary) !important;
        border: 1px solid var(--tech-border) !important;
        color: var(--tech-text-primary) !important;

        &:hover {
            border-color: var(--tech-primary) !important;
        }

        &:focus {
            border-color: var(--tech-primary) !important;
            box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2) !important;
        }

        &::placeholder {
            color: var(--tech-text-muted) !important;
        }
    }

    /* 按钮样式 */
    :deep(.t-button--theme-primary) {
        background: var(--tech-gradient-primary) !important;
        border: 1px solid var(--tech-primary) !important;
        color: #ffffff !important;

        &:hover {
            background: var(--tech-primary) !important;
            box-shadow: var(--tech-shadow-glow) !important;
        }
    }

    :deep(.t-button--theme-default) {
        background: var(--tech-bg-secondary) !important;
        border: 1px solid var(--tech-border) !important;
        color: var(--tech-text-secondary) !important;

        &:hover {
            background: var(--tech-bg-hover) !important;
            border-color: var(--tech-primary) !important;
            color: var(--tech-text-primary) !important;
        }
    }
}
</style>