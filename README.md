# Code Agent - MCP架构演进版（第4-6步已实现）

基于LLM的CLI对话工具，采用MCP（Model Context Protocol）架构，实现了安全代码执行、文件系统工具和ReAct循环功能。

## 功能特点

- ✅ 流式对话输出（实时显示）
- ✅ **对话历史持久化**（自动保存到JSON文件）
- ✅ **会话管理**（创建、加载、查看历史会话）
- ✅ 支持系统提示词
- ✅ 彩色终端界面（使用rich库）
- ✅ 命令支持（sessions, load, new, quit）
- ✅ **MCP工具系统** - 基于Model Context Protocol标准化工具集成
- ✅ **安全代码执行** - 在Docker沙箱中隔离运行Python代码
- ✅ **文件系统工具** - 通过MCP服务器提供安全的文件操作
- ✅ **ReAct循环架构** - 多轮推理（最多20步），自动工具调用与结果整合
- ✅ **专业日志系统** - 执行日志文件

## 安装依赖

```bash
pip install -r requirements.txt
```

## 环境要求

### 必需组件
1. **Docker** - 用于安全代码执行沙箱
   ```bash
   # 确保Docker已安装并运行
   docker --version
   ```

2. **Node.js (npx)** - 用于运行MCP文件系统服务器
   ```bash
   # 确保npx可用
   npx --version
   ```

### 配置LLM API
确保你的LLM API配置已设置到.env中：
```
LLM_API_KEY=你的API密钥
LLM_BASE_URL=你的LLM API地址
LLM_MODEL=你的LLM模型名称
PROJECT_DIR=/path/to/code-agent  # 项目根目录路径
```

## MCP工具配置

项目使用MCP（Model Context Protocol）架构，通过`mcp_config.json`配置工具服务器：

```json
{
  "mcpServers": {
    "time_tools": {
      "command": "python3",
      "args": [
        "${PROJECT_DIR}/tools/time_tools_server.py"
      ]
    },
    "code_executor": {
      "command": "python3",
      "args": [
        "${PROJECT_DIR}/tools/code_executor_server.py"
      ]
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "${AGENT_WORKSPACE}"
      ]
    }
  }
}
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

### 工具使用示例

```
🤖 Code Agent - MCP架构演进版
工作空间：/path/to/workspace
成功通过 MCP 挂载 3 个工具：['get_current_time', 'get_timezone', 'execute_python_code', 'run_script_file', 'read_file', 'write_file', 'list_directory']

你: 现在几点了？
助手: 当前时间: 2026-03-16 23:15:32

你: 执行一段Python代码计算阶乘
助手: 
> ⚙️ **执行工具**: `execute_python_code`
✅ 执行成功:
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)
print(factorial(5))

120

你: 查看当前目录有什么文件
助手: 
> ⚙️ **执行工具**: `list_directory`
当前目录包含: main.py, src/, tools/, history/, logs/, ...
```

## 项目结构

```
code-agent/
├── main.py              # CLI主程序（集成MCP架构）
├── src/
│   ├── llm_client.py   # LLM客户端（支持MCP工具调用）
│   ├── mcp_client.py   # MCP客户端实现
│   ├── history_manager.py # 历史记录管理器
│   └── logger.py       # 日志系统配置
├── tools/              # MCP服务器实现
│   ├── time_tools_server.py      # 时间工具MCP服务器
│   └── code_executor_server.py   # 代码执行MCP服务器（Docker沙箱）
├── mcp_config.json     # MCP服务器配置文件
├── history/            # 历史会话存储目录
├── logs/               # 日志文件存储目录
├── requirements.txt    # Python依赖
├── README.md          # 项目说明
└── QUICK_START.md     # 快速开始指南
```

## 技术栈

- **Python 3.8+**
- **OpenAI SDK** - 用于调用LLM API（兼容OpenAI格式）
- **MCP (Model Context Protocol)** - 标准化工具协议
- **Docker SDK** - 安全代码执行沙箱
- **Rich** - 终端美化库
- **python-dotenv** - 环境变量管理
- **JSON文件存储** - 对话历史持久化
- **ReAct模式** - Reasoning and Acting循环架构（最多20步）

## 开发计划

这是8步计划中的演进版，已实现第4-6步：

1. ✅ 基础CLI对话界面
2. ✅ 对话历史持久化
3. ✅ Tool Use / Function Calling（通过MCP架构）
4. ✅ **安全代码执行工具**（Docker沙箱实现）
5. ✅ **文件系统工具集**（MCP文件系统服务器）
6. ✅ **ReAct / Agent循环**（最多20轮推理）
7. CLI交互体验升级
8. 代码库上下文优化

## 安全注意事项

### Docker沙箱安全
- 代码执行在隔离的Docker容器中进行
- 内存限制：128MB
- 网络禁用：防止恶意下载或攻击
- 临时文件自动清理

### 文件系统安全
- 路径规范化防止目录遍历攻击
- 工作区目录隔离
- 只读/读写权限控制

### 环境要求
- **Docker必须已安装并运行**
- 需要Docker守护进程权限
- 建议使用Linux/macOS环境

## 故障排除

### Docker连接问题
```bash
# 检查Docker服务状态
sudo systemctl status docker  # Linux
# 或
docker ps  # 测试Docker命令
```

### MCP服务器启动失败
1. 检查`mcp_config.json`中的路径变量是否正确
2. 确保`.env`文件中设置了`PROJECT_DIR`
3. 检查Node.js和npx是否已安装

### 工具调用失败
- 查看`logs/`目录下的日志文件
- 检查API密钥和网络连接
- 确保所有依赖已正确安装

## 许可证

MIT