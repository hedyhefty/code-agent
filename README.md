# Code Agent - 第2步（对话历史持久化）

基于LLM的CLI对话工具，这是实现编码Agent的第二步，增加了对话历史持久化功能。

## 功能特点

### 第1步已完成
- ✅ 流式对话输出（实时显示）
- ✅ 对话历史管理（内存中）
- ✅ 支持系统提示词
- ✅ 彩色终端界面（使用rich库）
- ✅ 基本命令支持

### 第2步新增
- ✅ **对话历史持久化**（JSON文件存储）
- ✅ **会话管理**（创建、加载、删除会话）
- ✅ **历史会话列表**（按时间排序）
- ✅ **自动保存**（每5条消息自动保存）
- ✅ **会话恢复**（重启后可以继续对话）

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

### 1. 直接对话
直接输入问题即可开始与AI助手对话。

### 2. 使用命令
支持以下命令（可以加`/`前缀或不加）：

| 命令 | 描述 | 示例 |
|------|------|------|
| `help` | 显示帮助信息 | `help` 或 `/help` |
| `clear` | 清空当前对话历史 | `clear` |
| `sessions` | 列出所有历史会话 | `sessions` |
| `load <id>` | 加载历史会话 | `load 2025-03-12_00123456` |
| `new` | 开始新的会话 | `new` |
| `save` | 手动保存当前会话 | `save` |
| `delete <id>` | 删除历史会话 | `delete 2025-03-12_00123456` |
| `quit`/`exit` | 退出程序 | `quit` |

### 3. 会话管理
- **自动创建**：每次启动程序会自动创建新会话
- **自动保存**：每5条消息自动保存一次，避免数据丢失
- **历史查看**：使用`sessions`命令查看所有历史会话
- **会话切换**：使用`load`命令切换到历史会话

## 项目结构

```
code-agent/
├── main.py              # 主程序入口
├── src/
│   ├── llm_client.py   # LLM API客户端（已集成历史管理）
│   └── history_manager.py # 新增：历史管理器
├── history/            # 新增：历史记录目录（自动创建）
│   ├── 2025-03-12_00123456.json
│   └── 2025-03-12_00234567.json
├── requirements.txt     # Python依赖
└── README.md           # 项目说明
```

## 数据格式

历史会话以JSON格式保存：
```json
{
  "session_id": "2025-03-12_00123456",
  "created_at": "2025-03-12T00:49:00",
  "system_prompt": "你是一个有帮助的AI助手...",
  "messages": [
    {
      "role": "user",
      "content": "你好",
      "timestamp": "2025-03-12T00:50:00"
    },
    {
      "role": "assistant", 
      "content": "你好！有什么可以帮助你的？",
      "timestamp": "2025-03-12T00:50:01"
    }
  ]
}
```

## 技术栈

- **Python 3.8+**
- **OpenAI SDK** - 用于调用LLM API（兼容OpenAI格式）
- **Rich** - 终端美化库
- **python-dotenv** - 环境变量管理
- **JSON** - 历史数据存储格式

## 开发计划

这是8步计划中的第2步，后续步骤包括：

1. ✅ 基础CLI对话界面
2. ✅ 对话历史持久化（当前步骤）
3. Tool Use / Function Calling
4. 安全代码执行工具
5. 文件系统工具集
6. ReAct / Agent循环
7. CLI交互体验升级
8. 代码库上下文优化

## 注意事项

- 请妥善保管你的API密钥
- 历史文件保存在`history/`目录中，可以手动备份或删除
- 本工具仅用于学习和开发目的
- 流式输出需要终端支持ANSI转义序列

## 许可证

MIT