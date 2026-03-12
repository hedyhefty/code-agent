#!/bin/bash
# Code Agent 启动脚本

echo "🚀 启动 Code Agent - 第2步：持久化版"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 检查并安装依赖（改进逻辑）
echo "📦 检查依赖..."
if ! pip show openai rich python-dotenv > /dev/null 2>&1; then
    echo "📦 安装依赖..."
    pip install -r requirements.txt
else
    echo "✅ 依赖已安装"
fi

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "⚠️  警告: .env 文件不存在"
    echo "请创建 .env 文件并添加你的API密钥:"
    echo "LLM_API_KEY=你的API密钥"
    echo "LLM_BASE_URL=你的LLM api地址"
    echo "LLM_MODEL=你的LLM model名称"
    exit 1
fi

# 运行主程序
echo "🤖 启动 CLI 对话界面..."
python main.py