📘 RAG Knowledge Base System

基于 Docker 的企业级 RAG（检索增强生成）知识库系统。整合了 Kafka 异步处理、LangChain 编排与 Chroma 向量存储。专为开发者设计的“单容器全栈”模式，支持 VS Code 一键 Attach 开发与调试。
🛠 技术架构
模块	技术选型	说明
API 服务	FastAPI	高性能异步 Web 框架，提供 RESTful 接口
AI 编排	LangChain	负责 RAG 链路构建、Prompt 管理与模型调用
向量库	ChromaDB	本地嵌入式向量数据库，支持持久化存储
消息队列	Kafka + Zookeeper	异步解耦文档解析与向量化任务
文档解析	PyPDF	支持 PDF 格式的文本提取与分块
容器化	Docker Compose	一键编排所有服务，环境一致性保证
🚀 快速开始
1. 环境准备

确保本地已安装：

    Docker & Docker Compose

    VS Code (推荐安装 Dev Containers 插件)

2. 配置文件

在项目根目录新建 .env 文件：

bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
CHROMA_DB_DIR=/chroma_data

3. 启动服务

bash
docker-compose up -d

    首次运行会自动构建镜像并启动 Kafka、Zookeeper 及开发容器。

4. 进入开发环境

    打开 VS Code。

    点击左侧 Docker 图标。

    右键 rag-dev 容器 -> "Attach Visual Studio Code"。

    在新窗口打开终端（Terminal），即位于容器内 /app 目录。

5. 运行应用

在容器终端内执行：

bash
python src/main.py

见如下日志即启动成功：

text
🚀 Starting RAG All-in-One Service...
👷 Worker connected to Kafka...
✅ Uvicorn running on http://0.0.0.0:8000

📂 目录结构

text
rag-integrated/
├── docker-compose.yml       # 容器编排
├── Dockerfile               # 开发环境镜像
├── requirements.txt         # 依赖列表
├── .env                     # 环境变量
└── src/
    ├── main.py              # 启动入口 (多进程管理)
    ├── api.py               # API 接口层
    ├── ingestor.py          # 文档摄入服务 (Producer)
    ├── worker.py            # 向量化服务 (Consumer)
    └── core/                # 核心组件
        ├── config.py        # 配置中心
        ├── rag.py           # RAG 业务逻辑
        └── db.py            # 数据库连接

🧪 接口测试
1. 上传文档

将 PDF 文档上传进行解析与向量化。

请求:

bash
curl -X POST "http://localhost:8000/upload" \
     -F "file=@/path/to/doc.pdf"

2. 智能问答

基于已上传文档进行 RAG 检索问答。

请求:

bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"question": "文档的主要结论是什么？"}'

响应:

json
{
  "answer": "根据文档内容，主要结论是..."
}

🐛 调试指南

    API 调试: 在容器内运行 uvicorn src.api:app --reload，修改代码即生效。

    Worker 调试: 停止主进程，单独运行 python src/worker.py，可配合断点调试。

    日志查看: 所有服务日志均输出至标准输出，直接在 VS Code 终端查看。

📝 扩展建议

    更换模型: 修改 src/core/config.py 中的 LLM_MODEL_NAME 即可切换模型。

    生产部署: 建议将 main.py 拆分为独立的 Docker 服务进行分布式部署。
