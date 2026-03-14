# Code Agent - 第3步：工具调用版（含ReAct循环）

基于LLM的CLI对话工具，这是实现编码Agent的第3步，增加了工具调用系统和ReAct循环功能。

## 功能特点

- ✅ 流式对话输出（实时显示）
- ✅ **对话历史持久化**（自动保存到JSON文件）
- ✅ **会话管理**（创建、加载、查看历史会话）
- ✅ 支持系统提示词
- ✅ 彩色终端界面（使用rich库）
- ✅ 命令支持（sessions, load, new, quit）
- ✅ **工具调用系统** - 支持动态加载和执行工具（时间、计算等）
- ✅ **ReAct循环架构** - 多轮推理，自动工具调用与结果整合
- ✅ **专业日志系统** - 类似Java @Slf4j，文件日志与终端分离

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
   - `sessions` - 查看所有历史会话ID
   - `load <session_id>` - 加载指定历史会话
   - `new` - 开启新会话
   - `quit` 或 `exit` 或 `q` - 退出程序

### 示例
```
🤖 Code Agent - 工具调用版
输入 'quit' 退出 | 'new' 开启新会话 | 'sessions' 查看历史 | 'load <id>' 加载

你: sessions
历史会话: ['2026-03-12_012046', '2026-03-12_012324']

你: load 2026-03-12_012324
已加载会话: 2026-03-12_012324

你: 我们之前聊了什么？
助手: 我们之前打了招呼，你说了"hi"，我回复了问候...
```

### 工具使用示例
```
你: 现在几点了？
助手: 当前时间: 2026-03-15 01:45:23

你: 计算 15 * (3 + 7)
助手: 15 * (3 + 7) = 150
```

## 项目结构

```
code-agent/
├── main.py              # 主程序入口（集成ReAct循环）
├── src/
│   ├── llm_client.py   # LLM客户端（支持ReAct循环）
│   ├── history_manager.py # 历史记录管理器
│   ├── tool_manager.py # 工具管理器（动态加载）
│   ├── base_tool.py    # 工具抽象基类
│   └── logger.py       # 日志系统配置
├── tools/              # 工具实现目录
│   ├── time_tool.py    # 时间工具
│   └── calc_tool.py    # 计算工具
├── history/            # 历史会话存储目录
├── logs/               # 日志文件存储目录
├── requirements.txt    # Python依赖
└── README.md          # 项目说明
```

## 技术栈

- **Python 3.8+**
- **OpenAI SDK** - 用于调用LLM API（兼容OpenAI格式）
- **Rich** - 终端美化库
- **python-dotenv** - 环境变量管理
- **JSON文件存储** - 对话历史持久化
- **工具系统架构** - 动态加载和执行的工具框架
- **logging模块** - 专业日志记录系统
- **ReAct模式** - Reasoning and Acting循环架构

## 开发计划

这是8步计划中的第3步，后续步骤包括：

1. ✅ 基础CLI对话界面
2. ✅ 对话历史持久化
3. ✅ Tool Use / Function Calling（当前步骤）
4. 安全代码执行工具
5. 文件系统工具集
6. ✅ ReAct / Agent循环
7. CLI交互体验升级
8. 代码库上下文优化

## 注意事项

- 请妥善保管你的API密钥
- 历史会话保存在`history/`目录下的JSON文件中
- 日志文件保存在`logs/`目录下，按日期分割
- 计算工具使用`eval()`函数，生产环境建议替换为安全计算库
- 本工具仅用于学习和开发目的
- 流式输出需要终端支持ANSI转义序列

## 许可证

MIT