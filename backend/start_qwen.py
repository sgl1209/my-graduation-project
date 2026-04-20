from transformers import AutoTokenizer, AutoModelForCausalLM
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import torch

app = FastAPI()

# # 配置CORS（解决前端跨域问题）
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173"],  # 你的前端地址
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# 模型路径（改成你自己的）
MODEL_PATH = r"D:\Develop\大模型\Qwen\Qwen-1_8B-Chat"

print("🔍 正在加载本地Qwen-1.8B模型...")

# 加载Tokenizer并消除pad_token警告
tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH,
    trust_remote_code=True
)
tokenizer.pad_token = tokenizer.eos_token  # 显式设置pad_token，消除警告

# 加载模型（CPU最快配置）
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    trust_remote_code=True,
    device_map="cpu",
    torch_dtype=torch.float32,  # CPU最兼容的精度
    low_cpu_mem_usage=True,      # 减少内存占用
)

# 对话模板（Qwen原生格式，避免默认ChatML警告）
def build_qwen_prompt(messages):
    prompt = ""
    for msg in messages:
        if msg["role"] == "user":
            prompt += f"<|user|>:{msg['content']}<|end|>\n"
        elif msg["role"] == "assistant":
            prompt += f"<|assistant|>:{msg['content']}<|end|>\n"
    prompt += "<|assistant|>:"
    return prompt

@app.post("/v1/chat/completions")
async def chat(request: Request):
    data = await request.json()
    messages = data["messages"]
    
    # 构建Qwen格式prompt
    prompt = build_qwen_prompt(messages)
    inputs = tokenizer(prompt, return_tensors="pt")
    
    # 最快生成配置（CPU专用）
    outputs = model.generate(
        **inputs,
        max_new_tokens=512,       # 可根据需求调整，越小越快
        do_sample=False,           # 贪心解码（最快）
        temperature=None,          # 关闭采样参数
        top_p=None,
        top_k=None,
        pad_token_id=tokenizer.eos_token_id,  # 显式指定，消除警告
        num_beams=1,               # 束搜索=1（最快）
        repetition_penalty=1.0,    # 关闭重复惩罚
    )
    
    # 解码输出
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    response = response.replace(prompt, "").strip()
    
    return {
        "choices": [
            {"message": {"role": "assistant", "content": response}}
        ]
    }

if __name__ == "__main__":
    # 启动服务（端口8001，和你之前一致）
    uvicorn.run(app, host="0.0.0.0", port=8001)