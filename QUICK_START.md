# Code Agent - MCP架构演进版（快速开始）

基于LLM的CLI对话工具，采用MCP（Model Context Protocol）架构，实现了安全代码执行、文件系统工具和ReAct循环功能。

## 🚀 快速开始

### 1. 环境准备
确保已安装以下组件：
```bash
# 检查Docker（必需）
docker --version

# 检查Node.js/npx（用于文件系统工具）
npx --version

# 检查Python 3.8+
python --version
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置API密钥
创建或编辑`.env`文件：
```
LLM_API_KEY=你的API密钥
LLM_BASE_URL=你的LLM API地址
LLM_MODEL=你的LLM模型名称
PROJECT_DIR=/path/to/code-agent  # 项目根目录绝对路径
```

### 4. 运行程序
```bash
python main.py
```

## 📋 核心功能

- **MCP工具系统** - 标准化工具协议，支持动态加载
- **安全代码执行** - Docker沙箱隔离，内存限制128MB
- **文件系统工具** - 安全的文件读写和目录操作
- **ReAct循环** - 最多20轮推理，自动工具调用
- **历史会话管理** - 保存、加载、查看对话历史

## 🛠️ 基本使用

启动后，你可以：
- **直接对话** - 输入问题与AI助手交互
- **管理会话** - 使用`sessions`、`load <id>`、`new`命令
- **退出程序** - 输入`quit`、`exit`或`q`

### 示例对话
```
🤖 Code Agent - MCP架构演进版
工作空间：/path/to/workspace
成功通过 MCP 挂载 3 个工具

你: 现在几点了？
助手: 当前时间: 2026-03-16 23:15:32

你: 执行Python代码计算2的10次方
助手: 
> ⚙️ **执行工具**: `execute_python_code`
✅ 执行成功:
print(2 ** 10)

1024
```

## ⚙️ MCP工具配置

工具通过`mcp_config.json`配置：
- **时间工具** - 获取当前时间和时区
- **代码执行器** - Docker沙箱执行Python代码
- **文件系统** - 安全的文件操作（需要Node.js）

## 🏗️ 项目结构概览

```
code-agent/
├── main.py              # 主程序入口
├── src/                 # 核心模块
├── tools/               # MCP服务器
├── mcp_config.json      # 工具配置
├── history/             # 会话历史
└── logs/                # 系统日志
```

## 🔧 开发状态

已实现步骤：
1. ✅ 基础CLI对话界面
2. ✅ 对话历史持久化  
3. ✅ Tool Use / Function Calling（MCP架构）
4. ✅ **安全代码执行工具**（Docker沙箱）
5. ✅ **文件系统工具集**（MCP服务器）
6. ✅ **ReAct / Agent循环**（20轮推理）

## ⚠️ 重要提示

### 必需条件
- **Docker必须已安装并运行**
- 需要Docker守护进程权限
- 建议使用Linux/macOS环境

### 故障排除
```bash
# Docker问题
sudo systemctl status docker  # Linux系统检查
docker ps                     # 测试Docker连接

# 工具加载失败
检查 .env 中的 PROJECT_DIR 设置
查看 logs/ 目录下的错误日志
```

## 📚 更多信息

详细文档请查看[README.md](./README.md)，包含：
- 完整的功能说明
- 安全注意事项
- 技术架构详解
- 开发计划详情

## 许可证

MIT