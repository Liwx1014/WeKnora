<template>
    <div class="header_box tech-header">
        <div class="logo_box">
            <span class="logo_text">灵枢智联（LineAegis）：云边一体的智能巡检与风险处置引擎</span>
        </div>
        <div class="nav_box">
            <div class="menu_items">
                <div v-for="(item, index) in menuArr" :key="index" class="menu_item_wrapper">
                    <div @click="gotopage(item.path)"
                        @mouseenter="mouseenteMenu(item.path)" @mouseleave="mouseleaveMenu(item.path)"
                        :class="['menu_item', item.childrenPath && item.childrenPath == currentpath ? 'menu_item_c_active' : item.path == currentpath ? 'menu_item_active' : '']">
                        <div class="menu_item-box">
                            <div class="menu_icon">
                                <img class="icon" :src="getImgSrc(item.icon == 'home' ? homeIcon : item.icon == 'zhishiku' ? knowledgeIcon : item.icon == 'setting' ? settingIcon : prefixIcon)" alt="">
                            </div>
                            <span class="menu_title">{{ item.title }}</span>
                        </div>
                    </div>
                    <!-- 子菜单下拉 - 隐藏历史对话列表，因为已移到页面中央 -->
                    <!-- <div class="submenu_dropdown" v-if="item.children && (item.path == currentpath || item.childrenPath == currentpath)">
                        <div ref="submenuscrollContainer" @scroll="handleScroll" class="submenu">
                            <div class="submenu_item_p" v-for="(subitem, subindex) in item.children" :key="subindex"
                                @click="gotopage(subitem.path)">
                                <div :class="['submenu_item', currentSecondpath == subitem.path ? 'submenu_item_active' : '']"
                                    @mouseenter="mouseenteBotDownr(subindex)" @mouseleave="mouseleaveBotDown">
                                    <i v-if="currentSecondpath == subitem.path" class="dot"></i>
                                    <span class="submenu_title"
                                        :style="currentSecondpath == subitem.path ? 'margin-left:14px;max-width:160px;' : 'margin-left:18px;max-width:173px;'">
                                        {{ subitem.title }}
                                    </span>
                                    <t-popup v-model:visible="subitem.isMore" @overlay-click="delCard(subindex, subitem)"
                                        @visible-change="onVisibleChange" overlayClassName="del-menu-popup" trigger="click"
                                        destroy-on-close placement="top-left">
                                        <div v-if="(activeSubmenu == subindex) || (currentSecondpath == subitem.path) || subitem.isMore"
                                            @click.stop="openMore(subindex)" variant="outline" class="menu-more-wrap">
                                            <t-icon name="ellipsis" class="menu-more" />
                                        </div>
                                        <template #content>
                                            <span class="del_submenu">删除记录</span>
                                        </template>
                                    </t-popup>
                                </div>
                            </div>
                        </div>
                    </div> -->
                </div>
            </div>
        </div>
        <input type="file" @change="upload" style="display: none" ref="uploadInput"
            accept=".pdf,.docx,.doc,.txt,.md,.jpg,.jpeg,.png" />
    </div>
</template>

<script setup>
import { storeToRefs } from 'pinia';
import { onMounted, watch, computed, ref, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getSessionsList, delSession } from "@/api/chat/index";
import { useMenuStore } from '@/stores/menu';
import useKnowledgeBase from '@/hooks/useKnowledgeBase';
import { MessagePlugin } from "tdesign-vue-next";
let { requestMethod } = useKnowledgeBase()
let uploadInput = ref();
const usemenuStore = useMenuStore();
const route = useRoute();
const router = useRouter();
const currentpath = ref('');
const currentPage = ref(1);
const page_size = ref(30);
const total = ref(0);
const currentSecondpath = ref('');
const submenuscrollContainer = ref(null);
// 计算总页数
const totalPages = computed(() => Math.ceil(total.value / page_size.value));
const hasMore = computed(() => currentPage.value < totalPages.value);
const { menuArr } = storeToRefs(usemenuStore);
let activeSubmenu = ref(-1);
const loading = ref(false)
const uploadFile = () => {
    uploadInput.value.click()
}
const upload = (e) => {
    requestMethod(e.target.files[0], uploadInput)
}
const mouseenteBotDownr = (val) => {
    activeSubmenu.value = val;
}
const mouseleaveBotDown = () => {
    activeSubmenu.value = -1;
}
const onVisibleChange = (e) => {
}

const delCard = (index, item) => {
    delSession(item.id).then(res => {
        if (res && res.success) {
            menuArr.value[2].children.splice(index, 1);
            if (item.id == route.params.chatid) {
                router.push('/platform/creatChat');
            }
        } else {
            MessagePlugin.error("删除失败，请稍后再试!");
        }
    })
}
const debounce = (fn, delay) => {
    let timer
    return (...args) => {
        clearTimeout(timer)
        timer = setTimeout(() => fn(...args), delay)
    }
}
// 滚动处理
const checkScrollBottom = () => {
    const container = submenuscrollContainer.value
    if (!container) return

    const { scrollTop, scrollHeight, clientHeight } = container[0]
    const isBottom = scrollHeight - (scrollTop + clientHeight) < 100 // 触底阈值
    if (isBottom && hasMore.value) {
        currentPage.value++;
        getMessageList();
    }
}
const handleScroll = debounce(checkScrollBottom, 200)
const getMessageList = () => {
    if (loading.value) return;
    loading.value = true;
    usemenuStore.clearMenuArr();
    getSessionsList(currentPage.value, page_size.value).then(res => {
        if (res.data && res.data.length) {
            res.data.forEach(item => {
                let obj = { title: item.title ? item.title : "新会话", path: `chat/${item.id}`, id: item.id, isMore: false, isNoTitle: item.title ? false : true }
                usemenuStore.updatemenuArr(obj)
            });
            loading.value = false;
        }
        if (res.total) {
            total.value = res.total;
        }
    })
}

const openMore = (e) => { }
onMounted(() => {
    currentpath.value = route.name;
    if (route.params.chatid) {
        currentSecondpath.value = `${route.name}/${route.params.chatid}`;
    }
    getMessageList();
});

watch([() => route.name, () => route.params], (newvalue) => {
    currentpath.value = newvalue[0];
    if (newvalue[1].chatid) {
        currentSecondpath.value = `${newvalue[0]}/${newvalue[1].chatid}`;
    } else {
        currentSecondpath.value = "";
    }

});
let fileAddIcon = ref('file-add-green.svg');
let homeIcon = ref('home.svg');
let knowledgeIcon = ref('zhishiku-green.svg');
let prefixIcon = ref('prefixIcon.svg');
let settingIcon = ref('setting.svg');
let pathPrefix = ref(route.name)
const getIcon = (path) => {
    fileAddIcon.value = path == 'knowledgeBase' ? 'file-add-green.svg' : 'file-add.svg';
    homeIcon.value = path == 'home' ? 'home-green.svg' : 'home.svg';
    knowledgeIcon.value = path == 'knowledgeBase' ? 'zhishiku-green.svg' : 'zhishiku.svg';
    prefixIcon.value = path == 'creatChat' ? 'prefixIcon-green.svg' : path == 'knowledgeBase' ? 'prefixIcon-grey.svg' : 'prefixIcon.svg';
    settingIcon.value = path == 'settings' ? 'setting-green.svg' : 'setting.svg';
}
getIcon(route.name)
const gotopage = (path) => {
    pathPrefix.value = path;
    // 如果是系统设置，跳转到初始化配置页面
    if (path === 'settings') {
        router.push('/platform/initialization');
    } else {
        router.push(`/platform/${path}`);
    }
    getIcon(path)
}

const getImgSrc = (url) => {
    return new URL(`/src/assets/img/${url}`, import.meta.url).href;
}

const mouseenteMenu = (path) => {
    if (pathPrefix.value != 'knowledgeBase' && pathPrefix.value != 'creatChat' && path != 'knowledgeBase') {
        prefixIcon.value = 'prefixIcon-grey.svg';
    }
}
const mouseleaveMenu = (path) => {
    if (pathPrefix.value != 'knowledgeBase' && pathPrefix.value != 'creatChat' && path != 'knowledgeBase') {
        getIcon(route.name)
    }
}

</script>
<style lang="less" scoped>
.del_submenu {
    color: #fa5151;
    cursor: pointer;
}

/* 科技风格顶部导航栏 */
.header_box {
    width: 100%;
    height: 64px;
    padding: 0 24px;
    background: var(--tech-gradient-card) !important;
    border-bottom: 1px solid var(--tech-border);
    backdrop-filter: blur(10px);
    position: relative;
    overflow: visible;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-sizing: border-box;
    z-index: 1000;
}

.tech-header::before {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: var(--tech-gradient-accent);
    opacity: 0.8;
    z-index: 1001;
}

.logo_box {
    display: flex;
    align-items: center;
    height: 100%;
}

.logo_text {
    color: var(--tech-primary);
    font-size: 20px;
    font-weight: 700;
    font-family: 'PingFang SC', sans-serif;
    text-shadow: 0 0 10px var(--tech-primary);
    transition: all 0.3s ease;
}

.logo_text:hover {
    text-shadow: 0 0 15px var(--tech-primary), 0 0 25px var(--tech-primary);
}

.nav_box {
    display: flex;
    align-items: center;
    height: 100%;
}

.menu_items {
    display: flex;
    align-items: center;
    gap: 12px;
    height: 100%;
    padding: 0 8px;
}

.menu_item_wrapper {
    position: relative;
    height: 100%;
    display: flex;
    align-items: center;
}

.tech-header .menu_item {
    background: linear-gradient(135deg, rgba(30, 30, 46, 0.8) 0%, rgba(42, 42, 62, 0.6) 100%);
    border: 1px solid var(--tech-border);
    border-radius: 12px;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    height: 38px;
    padding: 8px 16px;
    display: flex;
    align-items: center;
    cursor: pointer;
    backdrop-filter: blur(8px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.tech-header .menu_item::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, var(--tech-primary) 0%, var(--tech-accent) 100%);
    opacity: 0;
    transition: opacity 0.4s ease;
    border-radius: 12px;
}

.tech-header .menu_item::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    width: 0;
    height: 2px;
    background: var(--tech-primary);
    transform: translateX(-50%);
    transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    border-radius: 1px;
}

.tech-header .menu_item:hover {
    background: linear-gradient(135deg, rgba(30, 30, 46, 0.95) 0%, rgba(42, 42, 62, 0.8) 100%) !important;
    border-color: var(--tech-primary);
    box-shadow: 0 4px 20px rgba(0, 255, 157, 0.2), 0 0 0 1px rgba(0, 255, 157, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.2);
    transform: translateY(-1px);
}

.tech-header .menu_item:hover::before {
    opacity: 0.1;
}

.tech-header .menu_item:hover::after {
    width: 80%;
}

.tech-header .menu_item_active {
    background: linear-gradient(135deg, rgba(0, 255, 157, 0.15) 0%, rgba(0, 255, 157, 0.05) 100%) !important;
    border-color: var(--tech-primary) !important;
    box-shadow: 0 4px 25px rgba(0, 255, 157, 0.3), 0 0 0 1px var(--tech-primary), inset 0 1px 0 rgba(255, 255, 255, 0.2);
    transform: translateY(-1px);
}

.tech-header .menu_item_active::before {
    opacity: 0.2;
}

.tech-header .menu_item_active::after {
    width: 100%;
}

.tech-header .menu_title {
    color: var(--tech-text-secondary) !important;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    font-weight: 500;
    font-size: 14px;
    letter-spacing: 0.5px;
    position: relative;
    z-index: 1;
}

.tech-header .menu_icon {
    color: var(--tech-text-secondary) !important;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    z-index: 1;
    display: flex;
    align-items: center;
    justify-content: center;
}

.tech-header .menu_icon .icon {
    width: 20px;
    height: 20px;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.tech-header .menu_item:hover .menu_title {
    color: var(--tech-primary) !important;
    text-shadow: 0 0 12px rgba(0, 255, 157, 0.6);
}

.tech-header .menu_item:hover .menu_icon {
    color: var(--tech-primary) !important;
    filter: drop-shadow(0 0 8px rgba(0, 255, 157, 0.6));
}

.tech-header .menu_item_active .menu_title {
    color: var(--tech-primary) !important;
    text-shadow: 0 0 15px rgba(0, 255, 157, 0.8);
    font-weight: 600;
}

.tech-header .menu_item_active .menu_icon {
    color: var(--tech-primary) !important;
    filter: drop-shadow(0 0 10px rgba(0, 255, 157, 0.8));
}

/* 子菜单下拉样式 */
.submenu_dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    min-width: 200px;
    z-index: 1001;
    margin-top: 4px;
}

.tech-header .submenu {
    background: var(--tech-bg-secondary);
    border-radius: 8px;
    padding: 8px;
    border: 1px solid var(--tech-border);
    box-shadow: var(--tech-shadow-glow-strong);
    backdrop-filter: blur(10px);
    max-height: 400px;
    overflow-y: auto;
}

.tech-header .submenu_item {
    color: var(--tech-text-muted) !important;
    transition: all 0.3s ease;
    border-radius: 6px;
    position: relative;
}

.tech-header .submenu_item:hover {
    background: var(--tech-bg-hover) !important;
    color: var(--tech-text-secondary) !important;
    transform: translateX(2px);
}

.tech-header .submenu_item_active {
    background: var(--tech-bg-active) !important;
    color: var(--tech-primary) !important;
    box-shadow: inset 3px 0 0 var(--tech-primary);
}

.tech-header .submenu_item .dot {
    background: var(--tech-primary) !important;
    box-shadow: 0 0 6px var(--tech-primary);
}

.aside_box {

    .logo_box {
        height: 80px;
        display: flex;
        align-items: center;
        .logo{
            width: 134px;
            height: auto;
            margin-left: 24px;
        }
    }

    .logo_img {
        margin-left: 24px;
        width: 30px;
        height: 30px;
        margin-right: 7.25px;
    }

    .logo_txt {
        transform: rotate(0.049deg);
        color: #000000;
        font-family: "TencentSans";
        font-size: 24.12px;
        font-style: normal;
        font-weight: W7;
        line-height: 21.7px;
    }

    .menu_box {
        display: flex;
        flex-direction: column;
    }


    .menu_item-box {
        display: flex;
        align-items: center;
        gap: 10px;
        position: relative;
        z-index: 1;
    }

    .tech-header .menu_item-box {
        display: flex;
        align-items: center;
        gap: 10px;
        position: relative;
        z-index: 1;
    }

    .upload-file-wrap:hover {
        background-color: #dbede4;
        color: #07C05F;

    }

    .upload-file-icon {
        width: 20px;
        height: 20px;
        color: rgba(0, 0, 0, 0.6);
    }

    .active-upload {
        color: #07C05F;
    }

    .menu_item_active {
        background: rgba(7, 192, 95, 0.15) !important;
        border-left: 3px solid #07c05f;
        box-shadow: 0 2px 8px rgba(7, 192, 95, 0.2);

        .menu_icon,
        .menu_title {
            color: #07c05f !important;
            font-weight: 600;
        }
    }

    .menu_item_c_active {

        .menu_icon,
        .menu_title {
            color: #000000e6;
        }
    }

    .menu_p {
        height: 52px;
        padding: 4px 0;
        box-sizing: border-box;
    }

    .menu_item {
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: 38px;
        padding: 8px 12px;
        box-sizing: border-box;
        margin: 2px 8px;
        border-radius: 8px;
        transition: all 0.2s ease;

        .menu_item-box {
            display: flex;
            align-items: center;
        }

        &:hover {
            background: rgba(7, 192, 95, 0.08);
            transform: translateX(2px);

            .menu_icon,
            .menu_title {
                color: #07c05f;
            }
        }
    }

    .menu_icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        margin-right: 12px;
        flex-shrink: 0;

        img {
            width: 20px;
            height: 20px;
            object-fit: contain;
        }

        .icon {
            width: 20px;
            height: 20px;
            fill: currentColor;
            overflow: hidden;
        }
    }

    .menu_title {
        font-family: "PingFang SC";
        font-size: 14px;
        font-style: normal;
        font-weight: 600;
        line-height: 22px;
        white-space: nowrap;
    }

    .submenu {
        font-family: "PingFang SC";
        font-size: 14px;
        font-style: normal;
        font-family: "PingFang SC";
        font-size: 14px;
        font-style: normal;
        overflow-y: scroll;
        scrollbar-width: none;
        height: calc(98vh - 276px);
    }

    .submenu_item_p {
        height: 44px;
        padding: 4px 8px 4px 12px;
        box-sizing: border-box;
    }


    .submenu_item {
        cursor: pointer;
        display: flex;
        align-items: center;
        color: #00000099;
        font-weight: 400;
        line-height: 22px;
        height: 36px;
        padding-left: 18px;
        padding-right: 14px;
        position: relative;

        .submenu_title {
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
        }

        .menu-more-wrap {
            margin-left: auto;
        }

        .menu-more {
            display: inline-block;
            font-weight: bold;
            color: #07C05F;
        }

        .dot {
            width: 4px;
            height: 4px;
            border-radius: 50%;
            background: #07C05F;
        }

        .sub_title {
            margin-left: 14px;
        }

        &:hover {
            background: #30323605;
            color: #00000099;
            border-radius: 3px;

            .menu-more {
                color: #00000099;
            }

            .submenu_title {
                max-width: 160px !important;

            }
        }
    }

    .submenu_item_active {
        background: #07c05f1a !important;
        color: #07c05f !important;
        border-radius: 3px;

        .menu-more {
            color: #07c05f !important;
        }
    }
}

/* 科技风格菜单适配 */
:root[theme-mode="tech-dark"] .menu {
    background: var(--tech-bg-card) !important;
    border-right: 1px solid var(--tech-border);

    .menu_icon,
    .menu_title {
        color: var(--tech-text-secondary) !important;
    }

    .submenu_item {
        color: var(--tech-text-secondary) !important;

        &:hover {
            background: var(--tech-bg-hover) !important;
            color: var(--tech-text-primary) !important;

            .menu-more {
                color: var(--tech-text-primary) !important;
            }
        }
    }

    .menu_item:hover {
        background: rgba(0, 212, 255, 0.1) !important;
        transform: translateX(2px);
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.3);

        .menu_icon,
        .menu_title {
            color: var(--tech-primary) !important;
        }
    }

    .menu_item_active {
        background: rgba(0, 212, 255, 0.2) !important;
        border-left: 3px solid var(--tech-primary);
        box-shadow: 0 2px 12px rgba(0, 212, 255, 0.4), inset 0 0 20px rgba(0, 212, 255, 0.1);

        .menu_icon,
        .menu_title {
            color: var(--tech-primary) !important;
            font-weight: 600;
            text-shadow: 0 0 8px rgba(0, 212, 255, 0.5);
        }
    }

    .submenu_item_active {
        background: rgba(0, 212, 255, 0.2) !important;
        color: var(--tech-primary) !important;

        .menu-more {
            color: var(--tech-primary) !important;
        }
    }
}
</style>
<style lang="less">
.upload-popup {
    background-color: rgba(0, 0, 0, 0.9);
    color: #FFFFFF;
    border-color: rgba(0, 0, 0, 0.9) !important;
    box-shadow: none;
    margin-bottom: 10px !important;

    .t-popup__arrow::before {
        border-color: rgba(0, 0, 0, 0.9) !important;
        background-color: rgba(0, 0, 0, 0.9) !important;
        box-shadow: none !important;
    }
}

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