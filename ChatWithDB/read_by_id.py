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
    # 入库 逻辑
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
    # 出库 逻辑
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

                # 检查记录中是否包含图片引用（支持多个图片）
                image_refs = result.get("log_data", {}).get("image_refs")
                if image_refs:  # 当存在图片引用时（非空字典）
                    # 初始化存储图片URL的字段（兼容旧数据格式）
                    result["log_data"]["image_urls"] = {}
                    
                    # 遍历每个图片引用（如depth/original/detection等）
                    for ref_key, ref_info in image_refs.items():
                        # 提取关键信息（object_name和bucket是生成URL的必要字段）
                        object_name = ref_info.get("object_name")
                        bucket = ref_info.get("bucket")
                        
                        if not (object_name and bucket):
                            print(f"图片引用 '{ref_key}' 缺少必要字段（object_name或bucket），跳过生成URL。")
                            result["log_data"]["image_urls"][f"{ref_key}_url"] = None
                            continue
                        
                        try:
                            # 生成12小时有效的预签名URL
                            presigned_url = self.minio_client.get_presigned_url(
                                "GET",
                                bucket,
                                object_name,
                                expires=timedelta(hours=12)
                            )
                            # 以"原引用键_url"的格式存储URL（如depth_url/original_url）
                            result["log_data"]["image_urls"][f"{ref_key}_url"] = presigned_url
                            print(f"成功为图片 '{object_name}'（引用键：{ref_key}）生成临时访问URL。")
                        except S3Error as exc:
                            error_msg = f"为图片 '{object_name}'（引用键：{ref_key}）生成预签名URL失败: {exc}"
                            print(error_msg)
                            result["log_data"]["image_urls"][f"{ref_key}_url"] = None

                return result
        except Exception as exc:
            print(f"从PostgreSQL获取记录失败: {exc}")
            return None


if __name__ == "__main__":
    
    print("--- 开始执行演示 ---")
    try:
        # 1. 实例化服务 (会自动加载配置并建立连接)
        service = ChatStorageService()
        
        new_id = 1
        if new_id:
            # 4. 如果入库成功，执行“出库”操作
        
            retrieved_record = service.get_chat_record_by_id(new_id)

            if retrieved_record:
                print("\n--- ✅ 演示成功！获取到的完整记录如下 (包含模型思考过程) ---")
                # 使用json.dumps美化输出，方便查看
                print(json.dumps(retrieved_record, indent=2, ensure_ascii=False))

    except (ValueError, Exception) as e:
        print(f"\n❌ 演示过程中发生错误: {e}")