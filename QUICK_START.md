# 快速开始指南

## 1. 进入项目目录
```bash
cd code-agent
```

## 2. 设置虚拟环境（一次性）
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
```

## 3. 安装依赖
```bash
pip install -r requirements.txt
```

## 4. 配置LLM API
确保你的LLM API配置已设置到.env中：
```
LLM_API_KEY=你的API密钥
LLM_BASE_URL=你的LLM API地址
LLM_MODEL=你的LLM模型名称
```

## 5. 运行程序
```bash
python main.py
```

## 6. 基本使用
启动后你会看到欢迎界面，然后可以：
- 直接输入问题开始对话
- 输入 `help` 查看帮助
- 输入 `history` 查看对话历史
- 输入 `clear` 清空历史
- 输入 `quit` 或 `exit` 退出

## 常用命令示例
```
你: 你好
助手: [流式显示回复...]

你: help
[显示帮助信息]

你: history
[显示对话历史]

你: clear
[清空历史]

你: quit
[退出程序]
```

## 故障排除
1. **API连接失败**：检查`.env`文件中的API密钥
2. **依赖安装失败**：确保使用Python 3.8+
3. **流式输出不显示**：确保终端支持ANSI转义序列
4. **程序崩溃**：检查错误信息，可能需要重新安装依赖

## 下一步
完成第1步后，可以开始第2步：加入对话历史持久化功能。