#!/bin/bash

# ==============================================================================
#
# install_nvidia_container_toolkit.sh
#
# 描述:
#   该脚本用于在基于 Debian/Ubuntu 的系统上自动安装和配置
#   NVIDIA Container Toolkit，使 Docker 能够支持 GPU。
#
# 使用方法:
#   1. 保存脚本: 将此内容保存为 install_nvidia_container_toolkit.sh
#   2. 添加执行权限: chmod +x install_nvidia_container_toolkit.sh
#   3. 以 sudo 权限运行: sudo ./install_nvidia_container_toolkit.sh
#
# ==============================================================================

# 设置 -e: 如果任何命令失败，脚本将立即退出
set -e

# --- 函数定义 ---

# 打印带有颜色的信息
info() {
    echo -e "\033[32m[INFO]\033[0m $1"
}

# 打印带有颜色的错误信息并退出
error() {
    echo -e "\033[31m[ERROR]\033[0m $1" >&2
    exit 1
}

# --- 脚本开始 ---

info "开始安装 NVIDIA Container Toolkit..."

# 1. 权限检查
if [ "$(id -u)" -ne 0 ]; then
    error "此脚本需要以 root 或 sudo 权限运行。请尝试使用 'sudo ./install_nvidia_container_toolkit.sh'。"
fi

# 2. 前提条件检查
info "步骤 1/5: 检查前提条件..."

# 检查 NVIDIA 驱动 (nvidia-smi)
if ! command -v nvidia-smi &> /dev/null; then
    error "未找到 'nvidia-smi' 命令。请在运行此脚本前，先正确安装 NVIDIA 驱动。"
else
    info "  [✓] NVIDIA 驱动已安装。"
fi

# 检查 Docker
if ! command -v docker &> /dev/null; then
    error "未找到 'docker' 命令。请在运行此脚本前，先正确安装 Docker 引擎。"
else
    info "  [✓] Docker 引擎已安装。"
fi

# 3. 配置 NVIDIA 软件源
info "步骤 2/5: 配置 NVIDIA 软件源..."
distribution=$(. /etc/os-release; echo $ID$VERSION_ID) \
   && curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
   && curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
      sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
      tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
info "  [✓] 软件源配置完成。"

# 4. 安装 NVIDIA Container Toolkit
info "步骤 3/5: 更新软件包列表并安装工具包..."
apt-get update
apt-get install -y nvidia-container-toolkit
info "  [✓] NVIDIA Container Toolkit 安装成功。"

# 5. 配置 Docker 运行时
info "步骤 4/5: 配置 Docker 守护进程并重启服务..."
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker
info "  [✓] Docker 配置完成并已重启。"

# 6. 验证安装
info "步骤 5/5: 运行测试容器以验证 GPU 支持..."
info "  如果安装成功，您将看到 'nvidia-smi' 的输出..."

# 运行测试容器，并将输出直接显示在终端
if docker run --rm --gpus all nvidia/cuda:12.4.1-cudnn8-devel-ubuntu22.04 nvidia-smi; then
    echo
    info "============================================================"
    info "  祝贺您！NVIDIA Container Toolkit 已成功安装并验证！"
    info "  您的 Docker 环境现在已经准备好运行 GPU 加速的应用了。"
    info "============================================================"
else
    error "验证失败！运行测试容器时出错。请检查上面的错误日志。"
fi

exit 0