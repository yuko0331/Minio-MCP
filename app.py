import base64
import io
import os
import uuid
from minio import Minio
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 初始化 FastMCP server
mcp = FastMCP(
    "minio-image-server",
    instructions="""
    This is a MinIO storage service for uploading and managing images/files.
    
    Available tools:
    1. upload_image - Upload base64-encoded images (screenshots, photos) to MinIO and get a public URL
    2. upload_file - Upload a local file from the filesystem to MinIO and get a public URL
    3. upload_from_url - Download a file from URL and upload to MinIO (mirror/backup remote files)
    4. list_files - List all files in the MinIO bucket
    5. generate_random_string - Generate a random UUID-based string (useful for unique filenames)
    
    Common use cases:
    - Save Playwright/browser screenshots to permanent storage (use upload_image)
    - Upload temporary local files to cloud storage (use upload_file)
    - Mirror/backup files from other servers by URL (use upload_from_url)
    - Browse uploaded files (use list_files)
    - Generate unique identifiers for filenames (use generate_random_string)
    
    All uploaded files will be accessible via public URLs.
    """,
    host="0.0.0.0", 
    port=8050,
)

# ===== 环境变量验证 =====
def get_required_env(key: str) -> str:
    """获取必需的环境变量，如果不存在则抛出错误"""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"环境变量 {key} 未设置！请检查 .env 文件或环境配置。")
    return value

# ===== MinIO 客户端初始化 =====
MINIO_ENDPOINT = get_required_env("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = get_required_env("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = get_required_env("MINIO_SECRET_KEY")
PUBLIC_BASE_URL = get_required_env("PUBLIC_BASE_URL")

BUCKET = os.getenv("MINIO_BUCKET", "images")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false") == "true"

client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE
)

# 确保 bucket 存在
if not client.bucket_exists(BUCKET):
    client.make_bucket(BUCKET)


# ===== MCP Tool 定义 =====
@mcp.tool()
def upload_image(
    base64_data: str,
    filename: str = None,
    content_type: str = "image/png"
) -> str:
    """
    Upload a base64 image to MinIO and return a public URL.
    
    USE THIS TOOL WHEN:
    - You have a screenshot from Playwright browser_take_screenshot
    - You have any base64-encoded image data
    - You need to save an image to permanent cloud storage
    - You want to get a shareable URL for an image
    
    Args:
        base64_data: The base64 string of the image. 
                     This is the "data" field from Playwright screenshot response.
                     Example: "iVBORw0KGgoAAAANSUhEUgAAA..."
        filename: Custom filename like "login-page.png". 
                  If not provided, auto-generates UUID name.
        content_type: Image MIME type, default "image/png".
                      Use "image/jpeg" for JPEG images.
    
    Returns:
        Success message with the public URL, or error message.
    
    Example workflow with Playwright:
    1. Take screenshot: browser_take_screenshot() -> returns {data: "iVBORw...", mimeType: "image/png"}
    2. Upload: upload_image(base64_data="iVBORw...", filename="my-screenshot.png")
    3. Get URL: http://server/bucket/my-screenshot.png
    """
    try:
        # 处理 base64 数据
        # 1. 去除可能存在的 data URI 前缀 (data:image/png;base64,)
        data = base64_data.strip()
        if "," in data:
            # 分离 data URI 前缀
            parts = data.split(",", 1)
            if len(parts) == 2:
                data = parts[1]
        
        # 2. 清理可能的空白字符
        data = data.replace(" ", "").replace("\n", "").replace("\r", "")
        
        # 3. 解码 base64 数据
        try:
            image_bytes = base64.b64decode(data, validate=True)
        except Exception as decode_error:
            return f"Base64 decode error: {str(decode_error)}. Data length: {len(data)}, First 50 chars: {data[:50]}"
        
        # 4. 验证解码后的数据不为空
        if not image_bytes or len(image_bytes) == 0:
            return "Decoded image data is empty"
        
        # 5. 生成文件名（确保有正确的扩展名）
        if filename:
            object_name = filename
            # 确保文件名有扩展名
            if "." not in object_name:
                ext = content_type.split("/")[-1] if "/" in content_type else "png"
                object_name = f"{object_name}.{ext}"
        else:
            # 根据 content_type 决定扩展名
            ext = content_type.split("/")[-1] if "/" in content_type else "png"
            object_name = f"{uuid.uuid4().hex}.{ext}"
        
        # 6. 上传到 MinIO
        client.put_object(
            BUCKET,
            object_name,
            io.BytesIO(image_bytes),
            len(image_bytes),
            content_type=content_type
        )
        
        # 7. 返回公开访问 URL
        public_url = f"{PUBLIC_BASE_URL}/{BUCKET}/{object_name}"
        
        # 返回成功信息（简洁格式）
        return f"✅ Image uploaded successfully!\nURL: {public_url}\nSize: {len(image_bytes)} bytes\nFilename: {object_name}"
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return f"❌ Upload failed: {str(e)}\n\nDetails:\n{error_detail}"


@mcp.tool()
def upload_file(
    file_path: str,
    target_filename: str = None,
    content_type: str = None
) -> str:
    """
    Upload a local file to MinIO and return a public URL.
    
    USE THIS TOOL WHEN:
    - You have a file path on the local filesystem
    - You want to upload a temporary file to permanent storage
    - The file was saved by Playwright or other tools to disk
    - You need to move a local file to cloud storage
    
    Args:
        file_path: Absolute path to the local file.
                   Example: "/tmp/playwright-output/screenshot.png"
                   Example: "/Users/yuko/Downloads/report.pdf"
        target_filename: Optional custom name for the uploaded file.
                        If not provided, uses the original filename.
        content_type: Optional MIME type. Auto-detected if not provided.
                     Examples: "image/png", "application/pdf", "text/plain"
    
    Returns:
        Success message with the public URL, or error message.
    
    Example workflow:
    1. Playwright saves screenshot to /tmp/playwright-output/page.png
    2. Call: upload_file(file_path="/tmp/playwright-output/page.png")
    3. Get URL: http://server/bucket/page.png
    
    Supported file types: images, PDFs, text files, and more.
    """
    try:
        import mimetypes
        
        # 1. 验证文件路径
        if not file_path:
            return "❌ Error: file_path is required"
        
        # 2. 检查文件是否存在
        if not os.path.exists(file_path):
            return f"❌ Error: File not found: {file_path}"
        
        if not os.path.isfile(file_path):
            return f"❌ Error: Path is not a file: {file_path}"
        
        # 3. 读取文件内容
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        if not file_data or len(file_data) == 0:
            return f"❌ Error: File is empty: {file_path}"
        
        # 4. 确定文件名
        original_filename = os.path.basename(file_path)
        object_name = target_filename if target_filename else original_filename
        
        # 确保有扩展名
        if "." not in object_name:
            # 从原文件获取扩展名
            _, ext = os.path.splitext(original_filename)
            if ext:
                object_name = f"{object_name}{ext}"
        
        # 5. 确定 content_type
        if not content_type:
            # 自动检测 MIME 类型
            guessed_type, _ = mimetypes.guess_type(file_path)
            content_type = guessed_type or "application/octet-stream"
        
        # 6. 上传到 MinIO
        client.put_object(
            BUCKET,
            object_name,
            io.BytesIO(file_data),
            len(file_data),
            content_type=content_type
        )
        
        # 7. 返回公开访问 URL
        public_url = f"{PUBLIC_BASE_URL}/{BUCKET}/{object_name}"
        
        return f"✅ File uploaded successfully!\nURL: {public_url}\nSize: {len(file_data)} bytes\nFilename: {object_name}\nContent-Type: {content_type}"
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return f"❌ Upload failed: {str(e)}\n\nDetails:\n{error_detail}"


@mcp.tool()
def list_files(prefix: str = "") -> str:
    """
    List files in the MinIO bucket.
    
    USE THIS TOOL WHEN:
    - You want to see what files are already uploaded
    - You need to check if a file exists
    - You want to browse the bucket contents
    
    Args:
        prefix: Optional filter prefix. Only show files starting with this prefix.
                Example: "screenshots/" to list only files in screenshots folder.
    
    Returns:
        List of files with their sizes and URLs.
    """
    try:
        objects = client.list_objects(BUCKET, prefix=prefix, recursive=True)
        
        files = []
        for obj in objects:
            url = f"{PUBLIC_BASE_URL}/{BUCKET}/{obj.object_name}"
            size_kb = obj.size / 1024
            files.append(f"- {obj.object_name} ({size_kb:.1f} KB)\n  URL: {url}")
        
        if not files:
            return f"📁 Bucket '{BUCKET}' is empty" + (f" (prefix: {prefix})" if prefix else "")
        
        result = f"📁 Files in bucket '{BUCKET}'" + (f" (prefix: {prefix})" if prefix else "") + f":\n\n"
        result += "\n".join(files)
        result += f"\n\nTotal: {len(files)} files"
        
        return result
    
    except Exception as e:
        return f"❌ Error listing files: {str(e)}"


@mcp.tool()
def upload_from_url(
    url: str,
    target_filename: str = None,
    content_type: str = None
) -> str:
    """
    Download a file from URL and upload it to MinIO.
    
    USE THIS TOOL WHEN:
    - You have an image/file URL from the internet
    - You want to save a remote file to permanent storage
    - You need to backup a file from another server
    - You want to mirror/copy a file to MinIO
    
    Args:
        url: The URL of the file to download and upload.
             Example: "https://example.com/image.png"
             Example: "http://192.168.1.100/files/document.pdf"
        target_filename: Optional custom name for the uploaded file.
                        If not provided, extracts filename from URL.
        content_type: Optional MIME type. Auto-detected from response if not provided.
                     Examples: "image/png", "application/pdf", "text/plain"
    
    Returns:
        Success message with the new MinIO URL, or error message.
    
    Example:
    1. Call: upload_from_url(url="https://example.com/photo.jpg", target_filename="my-photo.jpg")
    2. Get URL: http://minio-server/bucket/my-photo.jpg
    
    Supported: Any downloadable file (images, PDFs, documents, etc.)
    """
    try:
        import urllib.request
        import urllib.parse
        import mimetypes
        
        # 1. 验证 URL
        if not url:
            return "❌ Error: url is required"
        
        if not url.startswith(('http://', 'https://')):
            return f"❌ Error: Invalid URL format. Must start with http:// or https://. Got: {url}"
        
        # 2. 下载文件
        try:
            # 创建请求，添加 User-Agent 避免被拒绝
            request = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) MinIO-MCP/1.0'
                }
            )
            
            with urllib.request.urlopen(request, timeout=30) as response:
                file_data = response.read()
                
                # 获取响应的 content-type
                response_content_type = response.headers.get('Content-Type', '')
                if response_content_type and ';' in response_content_type:
                    response_content_type = response_content_type.split(';')[0].strip()
                
        except urllib.error.HTTPError as e:
            return f"❌ HTTP Error: {e.code} {e.reason} for URL: {url}"
        except urllib.error.URLError as e:
            return f"❌ URL Error: {str(e.reason)} for URL: {url}"
        except Exception as e:
            return f"❌ Download failed: {str(e)}"
        
        # 3. 验证下载的数据
        if not file_data or len(file_data) == 0:
            return f"❌ Error: Downloaded file is empty from URL: {url}"
        
        # 4. 确定文件名
        if target_filename:
            object_name = target_filename
        else:
            # 从 URL 提取文件名
            parsed_url = urllib.parse.urlparse(url)
            path = parsed_url.path
            object_name = os.path.basename(path)
            
            # 如果没有文件名，生成一个
            if not object_name or object_name == '':
                ext = mimetypes.guess_extension(response_content_type) or '.bin'
                object_name = f"{uuid.uuid4().hex}{ext}"
        
        # 确保有扩展名
        if "." not in object_name:
            ext = mimetypes.guess_extension(response_content_type) or '.bin'
            object_name = f"{object_name}{ext}"
        
        # 5. 确定 content_type
        if not content_type:
            if response_content_type:
                content_type = response_content_type
            else:
                guessed_type, _ = mimetypes.guess_type(object_name)
                content_type = guessed_type or "application/octet-stream"
        
        # 6. 上传到 MinIO
        client.put_object(
            BUCKET,
            object_name,
            io.BytesIO(file_data),
            len(file_data),
            content_type=content_type
        )
        
        # 7. 返回公开访问 URL
        public_url = f"{PUBLIC_BASE_URL}/{BUCKET}/{object_name}"
        
        return f"✅ File uploaded from URL successfully!\nSource: {url}\nMinIO URL: {public_url}\nSize: {len(file_data)} bytes\nFilename: {object_name}\nContent-Type: {content_type}"
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return f"❌ Upload from URL failed: {str(e)}\n\nDetails:\n{error_detail}"


@mcp.tool()
def generate_random_string(length: int = 16) -> str:
    """
    Generate a random string using UUID.
    
    USE THIS TOOL WHEN:
    - You need a unique identifier for filenames
    - You want to generate random tokens or keys
    - You need a random string for testing or naming
    - You want to create unique identifiers
    
    Args:
        length: Length of the random string (1-32). Default is 16.
                The string will be lowercase hexadecimal characters.
    
    Returns:
        A random string of the specified length.
    
    Example:
    1. Call: generate_random_string(length=16)
    2. Get: "a1b2c3d4e5f6g7h8"
    
    Use cases:
    - Generate unique filenames: f"screenshot_{generate_random_string(8)}.png"
    - Create temporary identifiers
    - Generate test data
    """
    try:
        # 验证长度参数
        if not isinstance(length, int):
            return f"❌ Error: length must be an integer, got {type(length).__name__}"
        
        if length < 1:
            return "❌ Error: length must be at least 1"
        
        if length > 32:
            return "❌ Error: length cannot exceed 32"
        
        # 生成随机字符串
        random_string = uuid.uuid4().hex[:length]
        
        return f"✅ Random string generated: {random_string}"
    
    except Exception as e:
        return f"❌ Error generating random string: {str(e)}"


# ===== 启动 MCP Server =====
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
