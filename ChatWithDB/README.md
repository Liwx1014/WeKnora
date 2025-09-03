# 创建记录与多模态大模型交互的日志信息，与现有的RAG隔离
这是一个数据库脚本，用于创建一个名为 `chat_service` 的数据库模式，并创建一个名为 `logs` 的表，用于存储多模态对话服务的对话记录。
## 下载数据库链接工具
[DBraver](https://www.google.com/url?sa=E&q=https%3A%2F%2Fdbeaver.io%2Fdownload%2F)
下载完后，执行以下操作：
1.  **新建数据库连接**:
    *   打开 DBeaver，点击左上角的“新建连接”图标（一个插头形状）。
    *   在弹出的窗口中，选择 “**PostgreSQL**”，然后点击“下一步”。

2.  **填写连接信息**:
    *   在“主”标签页，根据您的 `.env` 文件填写以下信息：
        *   **主机 (Host)**: `服务器IP`
        *   **端口 (Port)**: `5433`  <-- *这是关键，使用您映射出来的端口*
        *   **数据库 (Database)**: `WeKnora`
        *   **用户名 (Username)**: `postgres`
        *   **密码 (Password)**: `postgres123!@#`

3.  **测试并完成**:
    *   点击左下角的 “**测试连接**” 按钮。如果一切正常，会提示连接成功。
    *   点击 “**完成**” 保存连接。

4.  **执行SQL脚本**:
    *   在左侧的数据库导航器中，找到您刚刚创建的连接，展开它，右键点击 `WeKnora` 数据库，选择 “**SQL 编辑器**” -> “**新建SQL脚本**”。
    *   将我之前提供给您的**完整SQL脚本**复制并粘贴到打开的编辑器窗口中。
    *   点击工具栏上的“**执行SQL脚本**”按钮（通常是一个橙色的播放▶️图标）。

## 创建数据库

最简单、最可靠、保证100%成功的解决方法是：**将脚本分成两部分，分开执行。**

这会强制您的数据库客户端创建两个独立的事务，从而确保第一步的 `CREATE SCHEMA` 操作已经完全提交并对后续所有操作可见。

请严格按照以下步骤操作：

#### **第一步：创建Schema**

请先复制**下面这一行代码**，粘贴到您的SQL编辑器中，并**单独执行**它。

```sql
-- ================== PART 1: CREATE THE SCHEMA ==================
CREATE SCHEMA IF NOT EXISTS chat_service;
```

**操作指南：**
在您的数据库工具中，只用鼠标选中上面这一行 `CREATE SCHEMA...` 的代码，然后点击“执行”按钮。

执行成功后，`chat_service` 这个Schema就已经在您的数据库中真实存在了。

#### **第二步：创建表和索引**

现在，`chat_service` schema已经存在，您可以安全地在其中创建表和索引了。

请复制**下面剩余的所有代码**，粘贴到SQL编辑器中，然后**再执行一次**。

```sql
-- ================== PART 2: CREATE TABLE AND INDEXES INSIDE THE SCHEMA ==================

-- Create the table within the now-existing 'chat_service' schema
CREATE TABLE IF NOT EXISTS chat_service.logs (
    id BIGSERIAL PRIMARY KEY,
    conversation_id UUID NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    log_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Add comments for better maintainability
COMMENT ON SCHEMA chat_service IS '用于存储外部对话服务的专属数据';
COMMENT ON TABLE chat_service.logs IS '存储多模态对话服务的对话记录';
COMMENT ON COLUMN chat_service.logs.id IS '记录的唯一主键 (自增)';
COMMENT ON COLUMN chat_service.logs.conversation_id IS '标识单次完整对话的UUID';
COMMENT ON COLUMN chat_service.logs.user_id IS '发起对话的用户ID';
COMMENT ON COLUMN chat_service.logs.session_id IS '用户的单次会话ID';
COMMENT ON COLUMN chat_service.logs.log_data IS '包含用户提问、图片引用、模型推理结果等的JSON对象';
COMMENT ON COLUMN chat_service.logs.created_at IS '记录插入时的时间戳（带时区）';

-- Create indexes on the new table for performance
-- Using "IF NOT EXISTS" is the modern, safe way to do this.
CREATE INDEX IF NOT EXISTS idx_chat_service_logs_user_id ON chat_service.logs (user_id);

CREATE INDEX IF NOT EXISTS idx_chat_service_logs_log_data_gin ON chat_service.logs USING GIN (log_data);
```

## 查看创建后的表
成功创建了表之后，验证它的存在是至关重要的一步。**先刷新**，然后在**数据库导航器/对象浏览器**面板中找到它。由于我们特意将它创建在一个名为 `chat_service` 的**Schema（模式）**下


---

### 详细导航路径（以DBeaver为例）

下面是在DBeaver中找到这张表的详细步骤，其他工具（如pgAdmin, DataGrip）的布局和逻辑也基本相同。

1.  **找到数据库连接**:
    在左侧的“数据库导航”面板中，找到您连接到 `WeKnora` 数据库的那个连接。

2.  **展开数据库**:
    点击连接旁边的箭头 `>` 展开它，然后找到并展开 `Databases` 文件夹。

3.  **展开 `WeKnora` 数据库**:
    在 `Databases` 文件夹下，找到 `WeKnora` 并展开它。

4.  **关键步骤：找到 `Schemas` 文件夹**:
    在 `WeKnora` 数据库下，您会看到很多文件夹，比如 `Schemas`, `Extensions` 等。请找到并展开 `Schemas` 文件夹。

5.  **找到 `chat_service` Schema**:
    在 `Schemas` 文件夹下，您至少会看到两个Schema：`public`（默认的）和我们刚刚创建的 `chat_service`。请点击展开 `chat_service`。

6.  **找到 `Tables` 文件夹**:
    在 `chat_service` Schema下，找到并展开 `Tables` 文件夹。

7.  **看到 `logs` 表**:
    恭喜！您现在应该能看到我们创建的 `logs` 表了。

**路径总结:**
`[您的连接]` -> `Databases` -> `WeKnora` -> `Schemas` -> `chat_service` -> `Tables` -> `logs`
---

### 找到之后您可以做什么？

*   **查看表结构（列）**:
    右键点击 `logs` 表，选择“查看表”、“属性”或“DDL”，您可以看到这张表的所有列（`id`, `conversation_id`, `log_data` 等）以及它们的数据类型，确认表结构是否正确。

*   **查看数据（目前是空的）**:
    右键点击 `logs` 表，选择“查看数据”或“读取数据”。这会打开一个像Excel一样的表格视图。现在这张表是空的，但一旦您的Python服务开始写入数据，您就可以在这里实时看到插入的记录。

*   **查看索引**:
    在 `logs` 表下面，通常会有一个 `Indexes` 文件夹，展开它，您应该能看到我们创建的两个索引：`idx_chat_service_logs_user_id` 和 `idx_chat_service_logs_log_data_gin`。这证明索引也已成功创建。

### 使用SQL查询来验证

如果您更喜欢用SQL来验证，您可以打开一个新的SQL编辑器窗口，执行以下查询：

```sql
-- 查询chat_service schema下所有的表
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'chat_service';
```
这个查询应该会返回一行结果，内容是 `logs`。

或者，您可以直接尝试查询这张表（虽然现在没有数据）：

```sql
-- 从新表中查询数据（会返回0行）
SELECT * FROM chat_service.logs;
```
如果这个查询能够成功执行而不报错（即使没有返回任何数据），也证明 `chat_service.logs` 这张表确实存在。

## 代码示例，用于入库和出库
太棒了！既然表已经成功创建，现在我们可以将所有部分组合起来，提供一个完整、可直接运行的代码示例。

这个示例完全按照我们之前讨论的架构设计：
*   **配置**: 从`.env`文件动态加载，与您的环境无缝对接。
*   **数据库**: 数据会准确地存入您刚刚创建的 `chat_service.logs` 表中。
*   **入库 (Ingestion)**: 接收对话信息和图片，将图片存入MinIO，并将包含图片**引用**的对话记录存入PostgreSQL。
*   **出库 (Retrieval)**: 从PostgreSQL读取对话记录，并为其中的图片引用生成一个临时的、安全的访问URL。

---

### 准备工作

1.  **安装Python库**:
    ```bash
    pip install minio psycopg2-binary python-dotenv
    ```

2.  **创建`.env`文件**:
    在您的Python项目（与代码文件放在一起）的根目录下，创建一个名为 `.env` 的文件。将以下内容复制进去。这个文件使得您的代码无需硬编码任何敏感信息。

    ```.env
    # MinIO 配置 (从您的主 .env 文件复制)
    MINIO_ENDPOINT=localhost:9000
    MINIO_ACCESS_KEY_ID=minioadmin
    MINIO_SECRET_ACCESS_KEY=minioadmin
    # 为新服务创建一个专用的Bucket，避免数据混淆
    MINIO_BUCKET_NAME=chat-service-images

    # PostgreSQL (ParadeDB) 配置 (从您的主 .env 文件复制)
    DB_HOST=localhost # 如果Python服务在Docker内，并且与Postgres在同一网络，这里应改为 'postgres'
    DB_PORT=5433
    DB_USER=postgres
    DB_PASSWORD=postgres123!@#
    DB_NAME=WeKnora
    ```

---

### 完整代码示例

将以下代码保存为一个Python文件，例如 `chat_storage_service.py`。

```python
import os
import io
import json
import uuid
from datetime import timedelta

# --- 依赖库 ---
from minio import Minio
from minio.error import S3Error
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

# --- 1. 从.env文件加载配置信息 ---
load_dotenv()

# MinIO 配置
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY_ID")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_ACCESS_KEY")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME") 

# PostgreSQL (ParadeDB) 配置
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# 拼接数据库连接字符串
DB_CONNECTION_STRING = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

class ChatStorageService:
    """一个封装了与MinIO和PostgreSQL交互的完整服务类"""
    
    def __init__(self):
        """初始化服务，连接数据库和MinIO"""
        print("正在初始化ChatStorageService...")
        # --- 检查环境变量 ---
        required_vars = [MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET_NAME, DB_CONNECTION_STRING]
        if any(v is None for v in required_vars):
            raise ValueError("部分必要的环境变量未设置，请检查您的.env文件。")

        try:
            # 初始化MinIO客户端
            self.minio_client = Minio(
                MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=False # 如果MinIO没有配置HTTPS，则为False
            )
            # 检查并创建Bucket
            found = self.minio_client.bucket_exists(MINIO_BUCKET_NAME)
            if not found:
                self.minio_client.make_bucket(MINIO_BUCKET_NAME)
                print(f"成功创建MinIO Bucket: '{MINIO_BUCKET_NAME}'")
            else:
                print(f"MinIO Bucket '{MINIO_BUCKET_NAME}' 已存在。")
        except S3Error as exc:
            print(f"连接MinIO时出错 ({MINIO_ENDPOINT}): {exc}")
            raise
            
        try:
            # 初始化PostgreSQL连接
            self.db_conn = psycopg2.connect(DB_CONNECTION_STRING)
            print("成功连接到PostgreSQL数据库。")
        except psycopg2.OperationalError as exc:
            print(f"连接PostgreSQL时出错 ({DB_HOST}:{DB_PORT}): {exc}")
            raise

    def __del__(self):
        """在对象销毁时安全地关闭数据库连接"""
        if hasattr(self, 'db_conn') and self.db_conn and not self.db_conn.closed:
            self.db_conn.close()
            print("PostgreSQL数据库连接已关闭。")

    # =================================================================
    # 入库 (Ingestion) 逻辑
    # =================================================================
    def save_chat_record(self, user_id: str, conversation_id: str, session_id: str, log_data: dict, image_data: bytes = None, image_filename: str = None):
        """
        保存一条对话记录。如果提供了图片，则先上传图片再保存记录。
        """
        if image_data and image_filename:
            # 为图片生成一个唯一的对象名称，避免冲突
            file_extension = os.path.splitext(image_filename)[1]
            minio_object_name = f"{user_id}/{session_id}/{uuid.uuid4()}{file_extension}"

            try:
                # 上传图片到MinIO
                self.minio_client.put_object(
                    MINIO_BUCKET_NAME,
                    minio_object_name,
                    io.BytesIO(image_data),
                    len(image_data)
                )
                print(f"图片 '{minio_object_name}' 已成功上传到MinIO。")
                # 将图片的引用信息添加到log_data中
                log_data['image_ref'] = {
                    "bucket": MINIO_BUCKET_NAME,
                    "key": minio_object_name
                }
            except S3Error as exc:
                print(f"上传图片到MinIO失败: {exc}")
                return None
        
        # 将记录插入PostgreSQL
        try:
            with self.db_conn.cursor() as cur:
                # 注意：SQL语句中的表名是 schema.table_name
                insert_query = """
                    INSERT INTO chat_service.logs (user_id, conversation_id, session_id, log_data)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id;
                """
                # 使用psycopg2.extras.Json来正确处理jsonb类型
                cur.execute(insert_query, (user_id, conversation_id, session_id, Json(log_data)))
                
                record_id = cur.fetchone()[0]
                self.db_conn.commit()
                
                print(f"对话记录成功保存到PostgreSQL，新记录ID: {record_id}")
                return record_id
        except Exception as exc:
            self.db_conn.rollback() # 如果出错，回滚事务
            print(f"保存对话记录到PostgreSQL失败: {exc}")
            return None

    # =================================================================
    # 出库 (Retrieval) 逻辑
    # =================================================================
    def get_chat_record_by_id(self, record_id: int):
        """
        根据记录ID从PostgreSQL中查询对话记录，并为图片生成临时的访问URL。
        """
        try:
            with self.db_conn.cursor() as cur:
                select_query = "SELECT id, conversation_id, user_id, session_id, log_data, created_at FROM chat_service.logs WHERE id = %s;"
                cur.execute(select_query, (record_id,))
                record = cur.fetchone()

                if not record:
                    print(f"未找到ID为 {record_id} 的记录。")
                    return None
                
                # 将查询结果打包成一个易于使用的字典
                result = {
                    "id": record[0],
                    "conversation_id": str(record[1]),
                    "user_id": record[2],
                    "session_id": record[3],
                    "log_data": record[4], # psycopg2会自动将JSONB转为dict
                    "created_at": record[5].isoformat()
                }

                # 检查记录中是否包含图片引用，如果有，则生成预签名URL
                image_ref = result.get("log_data", {}).get("image_ref")
                if image_ref and image_ref.get("key"):
                    try:
                        # 生成一个有效期为1小时的预签名URL (pre-signed URL)
                        # 这是安全地提供私有对象访问权限的最佳方式
                        presigned_url = self.minio_client.get_presigned_url(
                            "GET",
                            image_ref["bucket"],
                            image_ref["key"],
                            expires=timedelta(hours=1)
                        )
                        # 将可访问的URL添加到返回结果中，供前端直接使用
                        result["log_data"]["image_url"] = presigned_url
                        print(f"已为图片 '{image_ref['key']}' 生成临时访问URL。")
                    except S3Error as exc:
                        print(f"从MinIO生成预签名URL失败: {exc}")
                        result["log_data"]["image_url"] = None

                return result
        except Exception as exc:
            print(f"从PostgreSQL获取记录失败: {exc}")
            return None


if __name__ == "__main__":
    print("--- 开始执行演示 ---")
    try:
        # 1. 实例化服务 (会自动加载配置并建立连接)
        service = ChatStorageService()
        
        # 2. 准备模拟数据
        user_id = "user-007"
        session_id = "session-alpha-beta"
        conversation_id = str(uuid.uuid4()) # 为一次完整对话生成一个唯一ID
        
        # 模拟一张图片文件
        dummy_image_content = b"This is a test image file's binary content."
        dummy_image_filename = "profile_picture.png"
        
        # 模拟对话内容和模型推理结果
        chat_log_data = {
            "prompt": "你好，请分析这张图片。",
            "model_response": {
                "model_name": "vision-transformer-v2",
                "description": "图片内容为二进制文本。",
                "tags": ["test", "binary", "text"]
            }
        }
        
        # 3. 执行“入库”操作
        print("\n[STEP 1] 正在执行“入库”操作...")
        new_id = service.save_chat_record(
            user_id=user_id,
            conversation_id=conversation_id,
            session_id=session_id,
            log_data=chat_log_data,
            image_data=dummy_image_content,
            image_filename=dummy_image_filename
        )

        if new_id:
            # 4. 如果入库成功，执行“出库”操作
            print(f"\n[STEP 2] 入库成功，新记录ID为 {new_id}。正在执行“出库”操作...")
            retrieved_record = service.get_chat_record_by_id(new_id)

            if retrieved_record:
                print("\n--- ✅ 演示成功！获取到的完整记录如下 ---")
                # 使用json.dumps美化输出，方便查看
                print(json.dumps(retrieved_record, indent=2, ensure_ascii=False))
                print("\n请特别注意 'log_data' 中的 'image_url' 字段，这是一个可以直接在浏览器中打开的临时链接。")

    except (ValueError, Exception) as e:
        print(f"\n❌ 演示过程中发生错误: {e}")

```

### 如何运行和理解结果

1.  **运行**:
    *   确保您的Docker容器（MinIO和PostgreSQL）正在运行。
    *   在终端中，进入代码文件和`.env`文件所在的目录。
    *   运行命令: `python chat_storage_service.py`

2.  **预期输出**:
    您将会看到一个清晰的执行流程：
    *   服务初始化，连接到MinIO和PostgreSQL。
    *   [STEP 1] 入库操作：上传图片，然后将记录存入数据库，并打印出新记录的ID。
    *   [STEP 2] 出库操作：使用上一步的ID查询数据库。
    *   最后，打印出一个格式化后的JSON对象。

3.  **关键结果**:
    在最后打印出的JSON中，请找到 `log_data` -> `image_url` 这个字段。它的值会是一个很长的URL，类似：
    `"http://localhost:9000/chat-service-images/user-007/session-alpha-beta/xxxx-xxxx.png?X-Amz-Algorithm=...&X-Amz-Credential=...&X-Amz-Date=...&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=..."`

    这个就是**预签名URL**。您可以将它**直接复制到您的浏览器地址栏并访问**，它会下载或显示您在代码中定义的虚拟图片内容。这个链接在1小时后会自动失效。这完美地展示了整个架构的工作流程。