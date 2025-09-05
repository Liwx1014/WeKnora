import os
import json
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

class ChatCleanupService:
    """用于清理聊天记录的服务类"""
    
    def __init__(self):
        """初始化服务，连接数据库和MinIO"""
        print("正在初始化ChatCleanupService...")
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
            
            # 检查bucket是否存在
            if not self.minio_client.bucket_exists(MINIO_BUCKET_NAME):
                print(f"警告: MinIO bucket '{MINIO_BUCKET_NAME}' 不存在")
            
            # 初始化PostgreSQL连接
            self.db_connection = psycopg2.connect(DB_CONNECTION_STRING)
            self.db_connection.autocommit = True
            print("✅ 数据库和MinIO连接成功")
            
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            raise
    
    def __del__(self):
        """析构函数，关闭数据库连接"""
        if hasattr(self, 'db_connection'):
            self.db_connection.close()
            print("数据库连接已关闭")
    
    def get_all_record_ids(self):
        """获取所有聊天记录的ID和基本信息"""
        try:
            cursor = self.db_connection.cursor()
            
            # 查询所有记录的ID、请求ID、会话ID、角色和创建时间
            query = """
            SELECT id, request_id, session_id, role, created_at 
            FROM messages 
            WHERE deleted_at IS NULL
            ORDER BY created_at DESC
            """
            
            cursor.execute(query)
            records = cursor.fetchall()
            cursor.close()
            
            return records
            
        except Exception as e:
            print(f"❌ 获取记录ID失败: {e}")
            return []
    
    def delete_record_by_id(self, record_id: str):
        """根据ID删除单个聊天记录（软删除）"""
        try:
            cursor = self.db_connection.cursor()
            
            # 首先检查记录是否存在且未被删除
            cursor.execute("SELECT id, content FROM messages WHERE id = %s AND deleted_at IS NULL", (record_id,))
            result = cursor.fetchone()
            
            if not result:
                print(f"❌ 记录ID {record_id} 不存在或已被删除")
                return False
            
            # 软删除记录（设置deleted_at时间戳）
            cursor.execute("UPDATE messages SET deleted_at = CURRENT_TIMESTAMP WHERE id = %s", (record_id,))
            
            if cursor.rowcount > 0:
                print(f"✅ 已删除记录ID: {record_id}")
                cursor.close()
                return True
            else:
                print(f"❌ 删除记录ID {record_id} 失败")
                cursor.close()
                return False
                
        except Exception as e:
            print(f"❌ 删除记录ID {record_id} 时发生错误: {e}")
            return False
    
    def delete_multiple_records(self, record_ids: list):
        """批量删除多个聊天记录"""
        success_count = 0
        failed_count = 0
        
        print(f"\n开始批量删除 {len(record_ids)} 条记录...")
        
        for record_id in record_ids:
            if self.delete_record_by_id(record_id):
                success_count += 1
            else:
                failed_count += 1
        
        print(f"\n批量删除完成: 成功 {success_count} 条，失败 {failed_count} 条")
        return success_count, failed_count

def display_records(records):
    """显示记录列表"""
    if not records:
        print("❌ 没有找到任何记录")
        return
    
    print(f"\n📋 找到 {len(records)} 条聊天记录:")
    print("-" * 100)
    print(f"{'序号':<4} {'ID':<38} {'请求ID':<38} {'会话ID':<38} {'角色':<10} {'创建时间':<20}")
    print("-" * 100)
    
    for idx, record in enumerate(records, 1):
        record_id, request_id, session_id, role, created_at = record
        # 截断长字符串以适应显示
        record_id_short = record_id[:35] + '...' if len(record_id) > 38 else record_id
        request_id_short = request_id[:35] + '...' if len(request_id) > 38 else request_id
        session_id_short = session_id[:35] + '...' if len(session_id) > 38 else session_id
        created_at_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"{idx:<4} {record_id_short:<38} {request_id_short:<38} {session_id_short:<38} {role:<10} {created_at_str:<20}")

def get_user_selection(records):
    """获取用户选择的ID列表"""
    print("\n请选择要删除的记录:")
    print("- 输入序号: 例如 '1' (删除第1条记录)")
    print("- 输入多个序号: 例如 '1,3,5,7'")
    print("- 输入序号范围: 例如 '1-10'")
    print("- 输入 'all' 删除所有记录")
    print("- 输入 'q' 或 'quit' 退出")
    
    while True:
        user_input = input("\n请输入您的选择: ").strip()
        
        if user_input.lower() in ['q', 'quit']:
            return None
        
        if user_input.lower() == 'all':
            confirm = input("⚠️ 确认要删除所有记录吗？(输入 'yes' 确认): ")
            if confirm.lower() == 'yes':
                return 'all'
            else:
                print("操作已取消")
                continue
        
        try:
            selected_indices = []
            
            # 处理逗号分隔的序号
            if ',' in user_input:
                indices = user_input.split(',')
                for idx_str in indices:
                    idx = int(idx_str.strip())
                    if 1 <= idx <= len(records):
                        selected_indices.append(idx - 1)  # 转换为0基索引
                    else:
                        print(f"❌ 序号 {idx} 超出范围 (1-{len(records)})")
                        selected_indices = []
                        break
            
            # 处理范围输入
            elif '-' in user_input and user_input.count('-') == 1:
                start, end = user_input.split('-')
                start_idx = int(start.strip())
                end_idx = int(end.strip())
                if 1 <= start_idx <= end_idx <= len(records):
                    selected_indices = list(range(start_idx - 1, end_idx))  # 转换为0基索引
                else:
                    print(f"❌ 范围输入错误: 序号应在1-{len(records)}之间，且起始序号应小于等于结束序号")
                    continue
            
            # 处理单个序号
            else:
                idx = int(user_input)
                if 1 <= idx <= len(records):
                    selected_indices = [idx - 1]  # 转换为0基索引
                else:
                    print(f"❌ 序号 {idx} 超出范围 (1-{len(records)})")
                    continue
            
            if selected_indices:
                # 获取对应的记录ID
                selected_ids = [records[i][0] for i in selected_indices]
                selected_info = [(i+1, records[i][0][:8] + '...') for i in selected_indices]
                print(f"您选择了以下记录: {selected_info}")
                confirm = input("确认删除这些记录吗？(输入 'yes' 确认): ")
                if confirm.lower() == 'yes':
                    return selected_ids
                else:
                    print("操作已取消")
                    continue
            
        except ValueError:
            print("❌ 输入格式错误，请重新输入")
            continue

if __name__ == "__main__":
    print("=== WeKnora 聊天记录清理工具 ===")
    
    try:
        # 初始化服务
        service = ChatCleanupService()
        
        # 获取所有记录
        print("\n正在获取所有聊天记录...")
        records = service.get_all_record_ids()
        
        if not records:
            print("❌ 数据库中没有找到任何聊天记录")
            exit()
        
        # 显示记录
        display_records(records)
        
        # 获取所有记录ID用于验证
        all_record_ids = [record[0] for record in records]
        
        # 获取用户选择
        selected_ids = get_user_selection(records)
        
        if selected_ids is None:
            print("\n👋 程序已退出")
            exit()
        
        # 处理删除操作
        if selected_ids == 'all':
            selected_ids = all_record_ids
        
        # 所有选择的ID都是有效的（因为是从现有记录中选择的）
        valid_ids = selected_ids
        
        # 执行删除
        success_count, failed_count = service.delete_multiple_records(valid_ids)
        
        print(f"\n🎉 清理完成！")
        print(f"总共处理: {len(valid_ids)} 条记录")
        print(f"成功删除: {success_count} 条")
        print(f"删除失败: {failed_count} 条")
        
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，程序已退出")
    except Exception as e:
        print(f"\n❌ 程序执行过程中发生错误: {e}")