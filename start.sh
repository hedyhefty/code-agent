#!/bin/bash
# Code Agent 启动脚本 - MCP架构演进版

echo "🚀 启动 Code Agent - MCP架构演进版（第4-6步已实现）"

# 1. 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 2. 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 3. 检查Docker环境
echo "🐳 检查Docker环境..."
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker未安装"
    echo "请先安装Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ 错误: Docker守护进程未运行"
    echo "请启动Docker服务:"
    echo "  Linux: sudo systemctl start docker"
    echo "  macOS: 打开Docker Desktop应用"
    exit 1
fi
echo "✅ Docker已安装并运行"

# 4. 检查Node.js环境
echo "📦 检查Node.js环境..."
if ! command -v npx &> /dev/null; then
    echo "⚠️  警告: npx未安装，文件系统工具将不可用"
    echo "建议安装Node.js: https://nodejs.org/"
    echo "继续运行其他工具..."
fi

# 5. 检查并安装依赖
echo "📦 检查依赖..."
if ! pip show openai rich python-dotenv mcp docker > /dev/null 2>&1; then
    echo "📦 安装依赖..."
    pip install -r requirements.txt
else
    echo "✅ 依赖已安装"
fi

# 6. 检查.env文件
if [ ! -f ".env" ]; then
    echo "⚠️  警告: .env 文件不存在"
    echo "请创建 .env 文件并添加配置:"
    echo "LLM_API_KEY=你的API密钥"
    echo "LLM_BASE_URL=你的LLM API地址"
    echo "LLM_MODEL=你的LLM模型名称"
    echo "PROJECT_DIR=$(pwd)  # 项目根目录路径"
    exit 1
else
    if ! grep -q "PROJECT_DIR=" .env; then
        echo "⚠️  警告: .env 中缺少 PROJECT_DIR 配置"
        echo "请在 .env 中添加:"
        echo "PROJECT_DIR=$(pwd)"
        echo "或手动设置项目根目录路径"
        exit 1
    fi
fi

# 7. 检查MCP配置
echo "🔧 检查MCP配置..."
if [ ! -f "mcp_config.json" ]; then
    echo "⚠️  警告: mcp_config.json 文件不存在"
    echo "MCP工具系统需要配置文件"
    exit 1
fi

if [ ! -f "tools/time_tools_server.py" ]; then
    echo "⚠️  警告: 时间工具服务器文件不存在"
    exit 1
fi

if [ ! -f "tools/code_executor_server.py" ]; then
    echo "⚠️  警告: 代码执行器服务器文件不存在"
    exit 1
fi

# 8. 运行主程序
echo "🤖 启动 CLI 对话界面（MCP架构演进版）..."
echo "📋 已实现功能:"
echo "  - ✅ 安全代码执行（Docker沙箱）"
echo "  - ✅ 文件系统工具（MCP服务器）"
echo "  - ✅ ReAct循环（最多20轮推理）"
python main.py