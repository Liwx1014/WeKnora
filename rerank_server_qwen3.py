import torch
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import List, Optional

# --- 1. API 数据结构定义 (与您的Go客户端兼容) ---
class RerankRequest(BaseModel):
    query: str
    documents: List[str]
    instruction: Optional[str] = None # 添加一个可选的 instruction 字段

class DocumentInfo(BaseModel):
    text: str

class RankResult(BaseModel):
    index: int
    document: DocumentInfo
    score: float

class FinalResponse(BaseModel):
    results: List[RankResult]

# --- 2. 加载模型和全局变量 (在服务启动时执行一次) ---
print("正在加载 Qwen/Qwen3-Reranker-4B 模型，请稍候...")

# 确定设备
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"使用的设备: {device}")

# 模型路径
# 如果您将模型下载到了本地，请使用本地路径以加快加载速度
# model_path = '/path/to/your/local/Qwen3-Reranker-4B'
model_path = "/data1/home/lwx/work/Download/Qwen3-Reranker-4B"

try:
    # 加载 Tokenizer 和 Model
    tokenizer = AutoTokenizer.from_pretrained(model_path, padding_side='left', trust_remote_code=True)
    
    # 推荐的加载方式：使用 bfloat16 和 flash_attention_2 以获得最佳性能
    # 如果您的GPU不支持 flash_attention_2，可以移除 attn_implementation 参数
    if torch.cuda.is_available() and torch.cuda.get_device_capability()[0] >= 8:
        print("GPU支持Flash Attention 2，将以此模式加载模型。")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16, # 使用 bfloat16 以节省显存
            trust_remote_code=True
        ).to(device).eval()
    else:
        print("GPU不支持Flash Attention 2或非GPU环境，将以标准模式加载模型。")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            trust_remote_code=True
        ).to(device).eval()

    # --- 模型特定的全局变量 ---
    token_false_id = tokenizer.convert_tokens_to_ids("no")
    token_true_id = tokenizer.convert_tokens_to_ids("yes")
    max_length = 8192

    prefix = "<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n<|im_start|>user\n"
    suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
    prefix_tokens = tokenizer.encode(prefix, add_special_tokens=False)
    suffix_tokens = tokenizer.encode(suffix, add_special_tokens=False)

    print("模型及相关配置加载成功！")

except Exception as e:
    print(f"模型加载失败: {e}")
    exit()

# --- 3. 创建 FastAPI 应用 ---
app = FastAPI(
    title="Qwen3 Reranker API",
    description="一个使用 Qwen/Qwen3-Reranker-4B 模型进行文本重排序的API服务",
    version="2.0.0"
)

# --- 4. 辅助函数 (将示例代码中的逻辑封装起来) ---
def format_instruction(instruction: Optional[str], query: str, doc: str) -> str:
    """根据输入格式化模型的指令字符串"""
    if instruction is None:
        # 提供一个高质量的默认指令
        instruction = 'Given a search query, retrieve relevant passages that answer the query'
    return f"<Instruct>: {instruction}\n<Query>: {query}\n<Document>: {doc}"

def process_inputs(pairs: List[str]):
    """对批量输入进行分词和填充，并添加特殊的前后缀Token"""
    # 截断时优先截断最长的部分（通常是文档）
    inputs = tokenizer(
        pairs, padding=False, truncation='longest_first',
        return_attention_mask=False, max_length=max_length - len(prefix_tokens) - len(suffix_tokens)
    )
    # 添加前缀和后缀
    for i in range(len(inputs['input_ids'])):
        inputs['input_ids'][i] = prefix_tokens + inputs['input_ids'][i] + suffix_tokens
    
    # 填充到统一长度
    inputs = tokenizer.pad(inputs, padding=True, return_tensors="pt", max_length=max_length)
    
    # 将数据移动到模型所在的设备
    for key in inputs:
        inputs[key] = inputs[key].to(device)
    return inputs

@torch.no_grad()
def compute_scores(inputs) -> List[float]:
    """使用模型进行推理并计算最终的相关性分数"""
    # 模型前向传播，只取最后一个Token的logits
    logits = model(**inputs).logits[:, -1, :]
    
    # 提取 "yes" 和 "no" 两个Token的logit值
    true_logits = logits[:, token_true_id]
    false_logits = logits[:, token_false_id]
    
    # 将它们组合成 [batch_size, 2] 的形状
    combined_logits = torch.stack([false_logits, true_logits], dim=1)
    
    # 应用 LogSoftmax (数值上比直接Softmax更稳定)
    log_probs = torch.nn.functional.log_softmax(combined_logits, dim=1)
    
    # 取 "yes" (在索引1的位置) 的对数概率，然后用 exp() 转换回原始概率
    scores = log_probs[:, 1].exp().tolist()
    
    return scores

# --- 5. 定义 API 端点 ---
@app.post("/rerank", response_model=FinalResponse)
def rerank_endpoint(request: RerankRequest):
    """
    接收查询和文档列表，返回经过重排序的、带有相关性分数的结果列表。
    """
    # 1. 格式化所有输入对
    pairs = [format_instruction(request.instruction, request.query, doc) for doc in request.documents]
    
    # 2. 对输入进行分词和填充
    inputs = process_inputs(pairs)
    
    # 3. 计算分数
    scores = compute_scores(inputs)

    # 4. 构建并排序结果
    results = []
    for i, (doc_text, score_val) in enumerate(zip(request.documents, scores)):
        doc_info = DocumentInfo(text=doc_text)
        result = RankResult(
            index=i,
            document=doc_info,
            score=score_val
        )
        results.append(result)
        
    sorted_results = sorted(results, key=lambda x: x.score, reverse=True)
    
    # 5. 返回最终的响应体
    return {"results": sorted_results}

@app.get("/")
def read_root():
    return {"status": "Qwen3 Reranker API is running"}

# --- 6. 启动服务 ---
if __name__ == "__main__":
    # 建议使用 gunicorn 等生产级服务器来运行
    # uvicorn reranker_server:app --host 0.0.0.0 --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)