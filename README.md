# MinIO MCP Server

一个使用 FastMCP 构建的 Model Context Protocol (MCP) 服务器，用于将图片和文件上传到 MinIO 对象存储。

## 🎯 功能特性

| 工具 | 功能 | 使用场景 |
|------|------|---------|
| **upload_image** | 上传 base64 图片 | Playwright 截图、相机照片 |
| **upload_file** | 上传本地文件 | 临时文件持久化、日志文件 |
| **upload_from_url** | URL 转存 | 镜像远程图片、备份网络文件 |
| **list_files** | 列出文件 | 浏览已上传内容、检查文件 |
| **generate_random_string** | 生成随机字符串 | 唯一文件名、临时标识 |

## 🚀 核心特点

- ✅ **完整的 MCP 协议支持** - 标准化的工具定义，AI 模型可直接理解
- 🔄 **多种上传方式** - 支持 base64、本地文件、远程 URL
- 🌐 **Streamable HTTP** - 通过 HTTP 接口访问，易于集成
- 🐳 **Docker 部署** - 一键部署，开箱即用
- 📦 **MinIO 存储** - 开源对象存储，兼容 S3 API

## 📦 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `MINIO_ENDPOINT` | MinIO 服务器地址 | 必填 |
| `MINIO_ACCESS_KEY` | MinIO 访问密钥 | 必填 |
| `MINIO_SECRET_KEY` | MinIO 密钥 | 必填 |
| `MINIO_BUCKET` | 存储桶名称 | `images` |
| `MINIO_SECURE` | 是否使用 HTTPS | `false` |
| `PUBLIC_BASE_URL` | 公开访问的基础 URL | 必填 |

## 🚀 快速开始

### Docker 部署（推荐）

1. **使用 Docker Compose 启动：**
```bash
docker-compose up -d
```

2. **验证服务：**
```bash
curl http://localhost:8050/mcp
```

3. **配置 AI 客户端（如 Claude Desktop）：**
```json
{
  "mcpServers": {
    "minio-image-server": {
      "transport": "streamable-http",
      "url": "http://localhost:8050/mcp"
    }
  }
}
```

### 本地运行

1. **安装依赖：**
```bash
pip install -r requirements.txt
```

2. **配置环境变量：**
```bash
cp .env.example .env
# 编辑 .env 文件
```

3. **启动服务：**
```bash
python app.py
```

服务将在 `http://0.0.0.0:8050` 启动。

## 📋 工具详解

### 1️⃣ upload_image - 上传 base64 图片

**用途：** 上传 base64 编码的图片到 MinIO，特别适合 Playwright 截图。

**参数：**
```python
upload_image(
    base64_data: str,      # Base64 图片数据（必填）
    filename: str = None,  # 文件名（可选，默认 UUID）
    content_type: str = "image/png"  # MIME 类型
)
```

**示例：**
```python
# Playwright 截图后上传
upload_image(
    base64_data="iVBORw0KGgoAAAANS...",
    filename="login-page.png"
)

# 返回
"""
✅ Image uploaded successfully!
URL: http://192.168.1.37:9100/snapshoot/login-page.png
Size: 87293 bytes
Filename: login-page.png
"""
```

**常见场景：**
- 📸 网页截图持久化
- 🧪 自动化测试截图保存
- 📊 可视化图表存储
- 📝 文档图片管理

---

### 2️⃣ upload_file - 上传本地文件

**用途：** 上传本地文件系统中的文件到 MinIO。

**参数：**
```python
upload_file(
    file_path: str,               # 本地文件路径（必填）
    target_filename: str = None,  # 目标文件名（可选）
    content_type: str = None      # MIME 类型（可选，自动检测）
)
```

**示例：**
```python
# 上传临时文件
upload_file(
    file_path="/tmp/playwright-output/screenshot.png"
)

# 上传并重命名
upload_file(
    file_path="/tmp/report.pdf",
    target_filename="monthly-report-2024.pdf"
)

# 返回
"""
✅ File uploaded successfully!
URL: http://192.168.1.37:9100/snapshoot/monthly-report-2024.pdf
Size: 102400 bytes
Filename: monthly-report-2024.pdf
Content-Type: application/pdf
"""
```

**常见场景：**
- 📁 临时文件持久化
- 📄 日志文件备份
- 🗂️ 报告文件归档
- 💾 数据文件存储

---

### 3️⃣ upload_from_url - URL 转存

**用途：** 从远程 URL 下载文件并上传到 MinIO。

**参数：**
```python
upload_from_url(
    url: str,                     # 文件 URL（必填）
    target_filename: str = None,  # 目标文件名（可选）
    content_type: str = None      # MIME 类型（可选，自动检测）
)
```

**示例：**
```python
# 镜像网络图片
upload_from_url(
    url="https://example.com/photo.jpg",
    target_filename="my-photo.jpg"
)

# 返回
"""
✅ File uploaded from URL successfully!
Source: https://example.com/photo.jpg
MinIO URL: http://192.168.1.37:9100/snapshoot/my-photo.jpg
Size: 156789 bytes
Filename: my-photo.jpg
Content-Type: image/jpeg
"""
```

**常见场景：**
- 🖼️ 镜像网络图片
- 💾 备份远程文件
- 🔄 文件迁移到 MinIO
- 📦 资源本地化

---

### 4️⃣ list_files - 列出文件

**用途：** 查看 MinIO bucket 中的文件列表。

**参数：**
```python
list_files(
    prefix: str = ""  # 文件名前缀过滤（可选）
)
```

**示例：**
```python
# 列出所有文件
list_files()

# 过滤特定前缀
list_files(prefix="screenshots/")

# 返回
"""
📁 Files in bucket 'snapshoot':

- screenshot1.png (45.2 KB)
  URL: http://192.168.1.37:9100/snapshoot/screenshot1.png
- report.pdf (102.4 KB)
  URL: http://192.168.1.37:9100/snapshoot/report.pdf

Total: 2 files
"""
```

---

### 5️⃣ generate_random_string - 生成随机字符串

**用途：** 生成指定长度的随机字符串，基于 UUID。

**参数：**
```python
generate_random_string(
    length: int = 16  # 字符串长度（1-32），默认 16
)
```

**示例：**
```python
# 生成默认 16 位随机字符串
generate_random_string()
# 返回: ✅ Random string generated: a1b2c3d4e5f6g7h8

# 生成 8 位随机字符串
generate_random_string(length=8)
# 返回: ✅ Random string generated: a1b2c3d4

# 生成 24 位随机字符串
generate_random_string(length=24)
# 返回: ✅ Random string generated: a1b2c3d4e5f6g7h8i9j0k1l2
```

**常见场景：**
- 🏷️ 生成唯一文件名
- 🔑 创建临时标识符
- 🎲 生成测试数据
- 📛 批量命名文件

**实际应用：**
```python
# 为截图生成唯一文件名
random_id = generate_random_string(8)
filename = f"screenshot_{random_id}.png"
upload_image(base64_data="...", filename=filename)
# 结果: screenshot_a1b2c3d4.png

# 批量生成唯一文件名
for i in range(5):
    unique_name = generate_random_string(12)
    # 用于文件命名或标识
```

## 🔧 配置 AI 客户端

### Claude Desktop

**配置文件位置：**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Streamable HTTP 模式（推荐）：**
```json
{
  "mcpServers": {
    "minio-image-server": {
      "transport": "streamable-http",
      "url": "http://localhost:8050/mcp",
      "description": "MinIO image and file upload server"
    }
  }
}
```

**重启 Claude Desktop 后生效。**

## 🐳 Docker 构建

```bash
# 构建镜像
docker build -t yukojiangjiang/minio-mcp:v2.0.0 .

# 推送到 Docker Hub
docker push yukojiangjiang/minio-mcp:v2.0.0

# 运行容器
docker run -d \
  -p 8050:8050 \
  -e MINIO_ENDPOINT="192.168.1.37:9100" \
  -e MINIO_ACCESS_KEY="minioadmin" \
  -e MINIO_SECRET_KEY="minioadmin" \
  -e MINIO_BUCKET="snapshoot" \
  -e PUBLIC_BASE_URL="http://192.168.1.37:9100" \
  yukojiangjiang/minio-mcp:v2.0.0
```

## 🧪 测试 API

```bash
# 健康检查
curl http://localhost:8050/health

# MCP 端点
curl http://localhost:8050/mcp

# 查看工具列表
curl -X POST http://localhost:8050/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

## 📚 使用示例

### 完整工作流程

```python
# 1. 生成唯一文件名
random_id = generate_random_string(8)
filename = f"test_{random_id}.png"

# 2. 使用 Playwright 截图并上传
screenshot_result = browser_take_screenshot(filename="page.png", fullPage=True)
upload_image(
    base64_data=screenshot_result["data"],
    filename=filename,
    content_type=screenshot_result["mimeType"]
)

# 3. 查看已上传的文件
list_files()
```

### 与 Playwright MCP 集成

```python
# 1. 使用 Playwright 截图
screenshot_result = browser_take_screenshot(filename="login.png", fullPage=True)
# 返回: {data: "iVBORw0KG...", mimeType: "image/png"}

# 2. 上传到 MinIO
upload_image(
    base64_data=screenshot_result["data"],
    filename="login-screenshot.png",
    content_type=screenshot_result["mimeType"]
)
# 返回: URL: http://192.168.1.37:9100/snapshoot/login-screenshot.png

# 3. 图片现在可以永久访问
```

### 批量处理文件

```python
# 1. 生成多个唯一文件名
filenames = []
for i in range(3):
    random_id = generate_random_string(8)
    filenames.append(f"report_{random_id}.pdf")

# 2. 列出当前文件
list_files()

# 3. 上传多个本地文件
for filename in filenames:
    upload_file(file_path=f"/tmp/{filename}")

# 4. 从 URL 镜像文件
upload_from_url(url="https://example.com/data.csv")

# 5. 再次列出验证
list_files()
```

### 高级用例：动态文件名生成

```python
# 场景：为每次测试运行生成唯一截图
test_run_id = generate_random_string(12)

# 多个测试步骤的截图
screenshots = [
    f"login_{test_run_id}.png",
    f"dashboard_{test_run_id}.png",
    f"logout_{test_run_id}.png"
]

# 依次上传
for filename in screenshots:
    # 执行截图并上传
    result = browser_take_screenshot()
    upload_image(base64_data=result["data"], filename=filename)

# 列出这次测试的所有截图
list_files(prefix=f"{test_run_id}")
```

## 🔍 故障排查

### 服务无法启动

```bash
# 检查端口占用
lsof -i :8050

# 查看日志
docker logs minio-mcp

# 验证环境变量
docker exec minio-mcp env | grep MINIO
```

### Claude Desktop 无法连接

1. 确认服务正在运行：`curl http://localhost:8050/mcp`
2. 重启 Claude Desktop
3. 检查配置文件 JSON 格式
4. 查看 Claude Desktop 日志

### 文件上传失败

- 检查 MinIO 服务是否可访问
- 验证 ACCESS_KEY 和 SECRET_KEY
- 确认 BUCKET 存在且有权限
- 检查网络连接

## 📄 License

MIT

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📮 联系

- GitHub: [@yukojiangjiang](https://github.com/yukojiangjiang)
- Docker Hub: [yukojiangjiang/minio-mcp](https://hub.docker.com/r/yukojiangjiang/minio-mcp)
