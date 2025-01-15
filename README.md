# Learning Assistant

一个基于 React + FastAPI 构建的智能学习助手应用，提供实时对话和知识管理功能。

## 项目概述

Learning Assistant 是一个现代化的全栈 Web 应用程序，采用前后端分离架构，旨在提供智能化的学习辅助功能。它使用直观的聊天界面，支持多会话管理，并提供实时的智能对话功能。

## 功能特性

- 💬 实时智能对话
- 📝 多会话管理
- 🔄 会话历史记录
- 📋 消息复制功能
- 🎨 现代化 UI 设计
- 💻 响应式布局
- ✨ 流畅的动画效果
- 🤖 接入大型语言模型
- 🌐 支持流式响应

## 技术栈

### 前端

- **前端框架**: React 18
- **构建工具**: Vite
- **UI 组件**: Ant Design
- **样式解决方案**: Tailwind CSS
- **动画效果**: Framer Motion
- **Markdown 渲染**: React Markdown
- **代码高亮**: React Syntax Highlighter
- **HTTP 客户端**: Axios

### 后端

- **框架**: FastAPI (Python)
- **ASGI 服务器**: Uvicorn
- **HTTP 客户端**: AIOHTTP
- **数据验证**: Pydantic
- **API 文档**: Swagger UI (自动生成)

## 安装说明

### 前端

1. 安装依赖：

```bash
cd learning-assistant
npm install
```

2. 创建 .env 文件并设置后端 API 地址：

```bash
VITE_API_BASE_URL=http://localhost:8000
```

3. 启动开发服务器：

```bash
npm run dev
```

### 后端

1. 使用 Conda 环境（推荐）：

```bash
cd backend
conda create -n ICS4SHU python=3.11
conda activate ICS4SHU # 激活你的 Conda 环境
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 启动后端服务器：

```bash
python -m uvicorn main:app --reload --port 8000
```

## 环境配置

### 后端配置
后端服务器配置了以下环境变量：
- API_BASE_URL: 实际的 AI 服务器地址
- API_KEY: AI 服务的认证密钥
- CHAT_ID: 对话助手的 ID

这些配置已经在 `backend/main.py` 中设置，如需修改请更新相应的常量。

### 前端配置
前端使用 `.env` 文件进行配置：
- VITE_API_BASE_URL: 后端服务器地址

## API 文档

启动后端服务器后，可以访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```text
learning-assistant/
├── src/                # 前端源代码
│   ├── components/     # React 组件
│   ├── assets/        # 静态资源
│   ├── App.jsx        # 主应用组件
│   └── main.jsx       # 应用入口
├── backend/           # 后端源代码
│   ├── main.py       # FastAPI 应用主文件
│   └── requirements.txt # Python 依赖
├── public/            # 前端公共资源
├── .env              # 环境变量配置
└── package.json      # 前端项目配置
```

## 开发命令

### 前端

- `npm run dev` - 启动开发服务器
- `npm run build` - 构建生产版本
- `npm run lint` - 运行代码检查
- `npm run preview` - 预览生产构建

### 后端

- `python -m uvicorn main:app --reload` - 启动开发服务器（支持热重载）
- `uvicorn main:app` - 启动生产服务器

## 使用流程

1. 创建新会话：
   - 点击左侧边栏的 "+" 按钮
   - 输入会话名称
   - 系统会自动创建新的会话

2. 发送消息：
   - 在底部输入框输入问题
   - 点击发送按钮或按回车键
   - 系统会实时流式返回 AI 的回答

3. 会话管理：
   - 切换会话：点击左侧会话列表中的会话
   - 删除会话：点击会话右侧的删除图标

4. 消息操作：
   - 复制消息：点击消息右侧的复制图标
   - 查看引用：部分回答会包含知识库引用信息
