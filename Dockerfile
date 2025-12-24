# 使用轻量级的 Python 镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（如果以后需要处理图片处理库如 Pillow，可能需要一些底层库）
# # 这里只保留最基础的
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# 复制依赖文件（推荐做法是先复制 requirements.txt）
# 如果你没有 requirements.txt，可以直接在 RUN pip install 中写明
RUN pip install --no-cache-dir \
    fastmcp \
    minio \
    python-dotenv

# 复制业务代码
COPY app.py .

# 暴露 MCP SSE 服务的端口
EXPOSE 8050

# 设置环境变量默认值（也可以在 docker-compose 中设置）
ENV PYTHONUNBUFFERED=1

# 直接运行 python 脚本
# 因为你在代码里写了 mcp.run(transport="sse", port=8000)
# 这会自动启动一个高性能的生产级服务器
CMD ["python", "app.py"]