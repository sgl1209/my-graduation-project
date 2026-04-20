# 安装依赖：pip install fastapi uvicorn openai python-dotenv neo4j
from openai import OpenAI
import os
import json
import re
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from dotenv import load_dotenv
from api.kg_api import router as kg_router
from api.question_api import router as question_router

# ===== 已注释：Neo4j 驱动导入（保留以便后续恢复）=====
# from neo4j import GraphDatabase, basic_auth

# 1. 加载环境变量
load_dotenv()

# 2. 初始化 OpenAI 客户端（通义千问）
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    # base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# 3. 初始化 Neo4j 连接（优化：使用上下文管理器，自动关闭连接）
# ===== 已注释：Neo4j 连接逻辑（保留以便后续恢复）=====
# def get_neo4j_driver():
#     return GraphDatabase.driver(
#         "bolt://localhost:7687",
#         auth=basic_auth("neo4j", "Dfs120900")
#     )

# 4. 创建 FastAPI 应用



# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # ========== 启动逻辑（替代 startup） ==========
#     print("=== 服务启动，初始化大模型 ===")
#     try:
#         # 你的大模型初始化/测试逻辑
#         test_completion = client.chat.completions.create(
#             model="qwen-turbo",
#             messages=[{"role": "user", "content": "测试连接"}]
#         )
#         print("✅ 大模型就绪")
#     except Exception as e:
#         print(f"❌ 大模型初始化失败: {e}")
#         raise

#     yield  # 服务运行中

#     # ========== 关闭逻辑（替代 shutdown） ==========
#     print("=== 服务关闭，清理资源 ===")
#     # 关闭 Neo4j 等
#     driver = get_neo4j_driver()
#     driver.close()

app = FastAPI(title="智能出题系统", disable_swagger_ui=True)
# 解决跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(kg_router)   # 知识图谱相关接口
app.include_router(question_router)  # 问题相关接口

# 10. 启动服务
if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, timeout_keep_alive=120)