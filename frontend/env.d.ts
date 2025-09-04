/// <reference types="vite/client" />

// Vue 组件类型声明
declare module '*.vue' {
    import type { DefineComponent } from 'vue'
    const component: DefineComponent<{}, {}, any>
    export default component
}

// Vue 模块类型声明
declare module 'vue' {
    export * from '@vue/runtime-dom'
}

// Pinia 模块类型声明
declare module 'pinia' {
    export * from 'pinia/dist/pinia'
}

// TDesign Vue Next 模块类型声明
declare module 'tdesign-vue-next' {
    import type { App } from 'vue'
    const TDesign: {
        install(app: App): void
    }
    export default TDesign
    export * from 'tdesign-vue-next/es'
}

// TDesign 样式文件类型声明
declare module 'tdesign-vue-next/es/style/index.css' {
    const css: string
    export default css
}