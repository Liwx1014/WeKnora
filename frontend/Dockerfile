# 构建阶段
FROM node:24-alpine as build-stage

WORKDIR /app

# 设置环境变量，忽略类型检查错误
ENV NODE_OPTIONS="--max-old-space-size=4096"
ENV VITE_IS_DOCKER=true

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN corepack enable
RUN pnpm install

# --- 新增命令：安装 Markdown 和 KaTeX 相关库 ---
# markdown-it: 核心 Markdown 解析器
# katex: 公式渲染引擎
# markdown-it-katex: 连接 markdown-it 和 katex 的插件
# @types/*: 为 TypeScript 提供类型定义，增强开发体验
RUN pnpm add marked-katex-extension katex
# 复制项目文件
COPY . .

# 构建应用
RUN pnpm run build

# 生产阶段
FROM nginx:stable-alpine as production-stage

# 复制构建产物到nginx服务目录
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 复制nginx配置文件
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动nginx
CMD ["nginx", "-g", "daemon off;"] 