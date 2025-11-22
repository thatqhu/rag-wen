import multiprocessing
import time
import uvicorn
import os
from api import app
from worker import start_worker_service
from ingestor import start_ingestor_service

# 也可以使用 supervisord，但在 Python 开发容器中，直接写个脚本更直观

def run_api():
    """启动 FastAPI"""
    uvicorn.run(app, host="0.0.0.0", port=8000)

def run_worker():
    """启动 Kafka 消费者"""
    # 简单的延迟重试，等待 Kafka 启动
    time.sleep(5)
    start_worker_service()

def run_ingestor():
    """启动文件监听器"""
    time.sleep(5)
    start_ingestor_service()

if __name__ == "__main__":
    print("🚀 Starting RAG All-in-One Service...")

    # 创建子进程
    p_worker = multiprocessing.Process(target=run_worker, name="Worker")
    p_ingestor = multiprocessing.Process(target=run_ingestor, name="Ingestor")

    # 启动子进程
    p_worker.start()
    p_ingestor.start()

    try:
        # 主进程运行 API (阻塞)
        run_api()
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
    finally:
        p_worker.terminate()
        p_ingestor.terminate()
        p_worker.join()
        p_ingestor.join()
