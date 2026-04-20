from openai import OpenAI

# 连接本地启动的 Qwen 模型服务（端口改成你实际用的，比如 8000/8001）
client = OpenAI(
    api_key="dummy_key",  # 本地模型不需要真实 API Key
    base_url="http://localhost:8001/v1"  # 大模型服务的端口，和你启动的一致！
)

# 测试 1：基础问答（验证模型能正常响应）
print("===== 测试1：基础问答 =====")
response1 = client.chat.completions.create(
    model="qwen-1.8b",  # 随便填，本地模型忽略这个参数
    messages=[{"role": "user", "content": "你好，请介绍一下自己"}],
    temperature=0.1,
    max_tokens=200
)
print(response1.choices[0].message.content)

# 测试 2：知识图谱相关（贴合你的业务场景）
print("\n===== 测试2：知识图谱抽取 =====")
test_text = "人工智能（AI）是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统的一门新的技术科学，由约翰·麦卡锡于1956年提出。"
response2 = client.chat.completions.create(
    model="qwen-1.8b",
    messages=[
        {"role": "user", "content": f"请从以下文本中抽取知识图谱的节点和关系：\n{test_text}\n格式要求：节点用[]标注，关系用→表示，例如：[人工智能]→属于→[技术科学]"}
    ],
    temperature=0.1,
    max_tokens=300
)
print(response2.choices[0].message.content)

# 测试 3：题目生成（贴合你的业务场景）
print("\n===== 测试3：智能出题 =====")
response3 = client.chat.completions.create(
    model="qwen-1.8b",
    messages=[
        {"role": "user", "content": "基于人工智能的定义，生成一道选择题，包含4个选项和正确答案"}
    ],
    temperature=0.5,
    max_tokens=300
)
print(response3.choices[0].message.content)