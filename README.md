# Code Agent - 第1步

基于LLM的CLI对话工具，这是实现编码Agent的第一步。

## 功能特点

- ✅ 流式对话输出（实时显示）
- ✅ 对话历史管理
- ✅ 支持系统提示词
- ✅ 彩色终端界面（使用rich库）
- ✅ 基本命令支持（help, history, clear, quit）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置LLM API
确保你的LLM API配置已设置到.env中：
```
LLM_API_KEY=你的API密钥
LLM_BASE_URL=你的LLM API地址
LLM_MODEL=你的LLM模型名称
```

## 运行

```bash
python main.py
```

或直接运行：

```bash
./main.py
```

（需要先给文件执行权限：`chmod +x main.py`）

## 使用说明

启动程序后，你会看到一个欢迎界面。你可以：

1. **直接输入问题** - 开始与AI助手对话
2. **使用命令**：
   - `help` - 显示帮助信息
   - `history` - 显示对话历史
   - `clear` - 清空对话历史
   - `quit` 或 `exit` - 退出程序

## 项目结构

```
code-agent/
├── main.py              # 主程序入口
├── src/
│   └── llm_client.py   # LLM API客户端
├── requirements.txt     # Python依赖
└── README.md           # 项目说明
```

## 技术栈

- **Python 3.8+**
- **OpenAI SDK** - 用于调用LLM API（兼容OpenAI格式）
- **Rich** - 终端美化库
- **python-dotenv** - 环境变量管理

## 开发计划

这是8步计划中的第1步，后续步骤包括：

1. ✅ 基础CLI对话界面（当前步骤）
2. 对话历史持久化
3. Tool Use / Function Calling
4. 安全代码执行工具
5. 文件系统工具集
6. ReAct / Agent循环
7. CLI交互体验升级
8. 代码库上下文优化

## 注意事项

- 请妥善保管你的API密钥
- 本工具仅用于学习和开发目的
- 流式输出需要终端支持ANSI转义序列

## 许可证

MIT