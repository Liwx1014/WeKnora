import { ref, computed, reactive } from 'vue'

import { defineStore } from 'pinia';

export const useMenuStore = defineStore('menuStore', {
    state: () => ({
        menuArr: reactive([
            { title: '首页', icon: 'home', path: 'home' },
            { title: '知识', icon: 'zhishiku', path: 'knowledgeBase' },
            {
                title: '对话',
                icon: 'prefixIcon',
                path: 'creatChat',
                childrenPath: 'chat',
                children: reactive<object[]>([]),
            },
            { title: '设置', icon: 'setting', path: 'settings' }
        ]),
        isFirstSession: false,
        firstQuery: ''
    }
    ),
    actions: {
        clearMenuArr() {
            this.menuArr[2].children = reactive<object[]>([]);
        },
        updatemenuArr(obj: any) {
            this.menuArr[2].children?.push(obj);
        },
        updataMenuChildren(item: object) {
            this.menuArr[2].children?.unshift(item)
        },
        updatasessionTitle(session_id: string, title: string) {
            this.menuArr[2].children?.forEach(item => {
                if (item.id == session_id) {
                    item.title = title;
                    item.isNoTitle = false;
                }
            });
        },
        changeIsFirstSession(payload: boolean) {
            this.isFirstSession = payload;
        },
        changeFirstQuery(payload: string) {
            this.firstQuery = payload;
        }
    }
});


