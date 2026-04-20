from openai import OpenAI
import os
import json
from dotenv import load_dotenv
import time

# 加载环境变量
load_dotenv()

# 1. 初始化客户端和Neo4j
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# ===== 已注释：Neo4j 数据库连接（保留以便后续恢复）=====
# from py2neo import Graph
# graph_db = Graph(
#     "bolt://localhost:7687",
#     auth=("neo4j", "Dfs120900")
# )

# 2. 读取已分段的文本（从JSON文件读取133个chunks）
def read_text_chunks_from_json(file_name="text_chunks.json"):
    """
    从JSON文件读取已分割好的文本片段
    :param file_name: 保存文本片段的JSON文件路径
    :return: 文本片段列表
    """
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            text_chunks = json.load(f)
        
        # 验证数据格式（确保是列表且非空）
        if not isinstance(text_chunks, list):
            raise ValueError("JSON文件内容不是列表格式")
        if len(text_chunks) == 0:
            raise ValueError("JSON文件中没有文本片段")
        
        print(f"✅ 成功读取 {len(text_chunks)} 个文本片段")
        return text_chunks
    except FileNotFoundError:
        print(f"❌ 未找到文件：{file_name}")
        return []
    except json.JSONDecodeError:
        print(f"❌ {file_name} 不是有效的JSON文件")
        return []
    except Exception as e:
        print(f"❌ 读取文本片段失败：{e}")
        return []

# 3. 抽取单段文本的知识图谱
def extract_kg_from_chunk(chunk_text):
    """抽取单段文本的KG，带异常处理"""
    # 1. 先写死 JSON 模板（纯字符串，不带任何格式化）
    prompt_template = """
请严格按照以下JSON格式抽取文本中的多层级知识图谱，不要多余文字：
{
    "nodes": [
        {"name": "实体名称", "level": 层级数字, "type": "核心知识点/子知识点/具体知识点/属性"},
        {"name": "数据结构", "level": 1, "type": "核心知识点"},
        {"name": "数组", "level": 2, "type": "子知识点"},
        {"name": "快速排序", "level": 3, "type": "具体知识点"},
        {"name": "中等", "level": 4, "type": "属性"}
    ],
    "edges": [
        {"source": "源实体", "target": "目标实体", "type": "包含/适配题型/对应难度"}
    ]
}
抽取规则：
1. level1：核心领域（如数据结构、算法）
2. level2：子领域（如数组、链表）
3. level3：具体知识点（如快速排序、冒泡排序）
4. level4：属性（题型、难度）
5. 关系仅包含：包含/适配题型/对应难度
抽取文本：
"""
    # 2. 直接把待处理文本拼在模板后面，完全避开格式化语法
    prompt = prompt_template + chunk_text

    try:
        completion = client.chat.completions.create(
            model="qwen-plus",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},
            timeout=60
        )
        response_content = completion.choices[0].message.content.strip()
        # 清洗响应，确保是纯 JSON
        if not response_content.startswith("{"):
            response_content = response_content[response_content.find("{"):]
        if not response_content.endswith("}"):
            response_content = response_content[:response_content.rfind("}")+1]
        return json.loads(response_content)
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败：{e}，响应内容：{completion.choices[0].message.content}")
        return {"nodes": [], "edges": []}
    except Exception as e:
        print(f"❌ 抽取单段KG失败：{e}")
        return {"nodes": [], "edges": []}

# 4. 合并多段KG并去重
def merge_kg_chunks(all_kg_chunks):
    """合并多个分段的KG，去重节点和关系"""
    merged_nodes = []
    merged_edges = []
    node_names = set()  # 去重节点
    edge_keys = set()   # 去重关系（source+target+type）

    for kg in all_kg_chunks:
        # 合并节点
        for node in kg.get("nodes", []):
            if node["name"] not in node_names:
                node_names.add(node["name"])
                merged_nodes.append(node)
        # 合并关系
        for edge in kg.get("edges", []):
            edge_key = f"{edge['source']}_{edge['target']}_{edge['type']}"
            if edge_key not in edge_keys:
                edge_keys.add(edge_key)
                merged_edges.append(edge)
    return {"nodes": merged_nodes, "edges": merged_edges}

# 5. 主函数：读取已分段文本+抽取+合并+保存（覆盖原有数据）
def build_and_save_kg():
    # 读取已分段的文本（从JSON文件）
    text_chunks = read_text_chunks_from_json("text_chunks.json")
    if not text_chunks:
        print("⚠️ 没有可用的文本片段，程序终止")
        return
    
    print(f"📄 共读取到 {len(text_chunks)} 段文本，开始逐段抽取KG...")

    # 逐段抽取KG
    all_kg_chunks = []
    for i, chunk in enumerate(text_chunks):
        print(f"🔄 正在处理第 {i+1}/{len(text_chunks)} 段文本...")
        kg_chunk = extract_kg_from_chunk(chunk)
        all_kg_chunks.append(kg_chunk)
        time.sleep(1)  # 避免API调用频率超限

    # 合并所有分段的KG
    merged_kg = merge_kg_chunks(all_kg_chunks)
    if not merged_kg["nodes"] and not merged_kg["edges"]:
        print("⚠️ 合并后KG为空，请检查文本内容或Prompt！")
        return

    # 保存到本地JSON（覆盖原有文件）
    with open("kg_data.json", "w", encoding="utf-8") as f:
        json.dump(merged_kg, f, ensure_ascii=False, indent=2)
    print(f"✅ 本地JSON文件已更新：kg_data.json")

    # ===== 已注释：Neo4j 导入逻辑（保留以便后续恢复）=====
    # try:
    #     graph_db.run("MATCH (n) DETACH DELETE n")
    #     print("🗑️ 已清空Neo4j中原有知识图谱数据")
    #     node_count = 0
    #     for node in merged_kg["nodes"]:
    #         node_name = node["name"].replace("'", "\\'")
    #         graph_db.run(
    #             f"CREATE (n:{node['type']} {{name: '{node_name}', level: {node['level']}}})"
    #         )
    #         node_count += 1
    #     edge_count = 0
    #     for edge in merged_kg["edges"]:
    #         source = edge["source"].replace("'", "\\'")
    #         target = edge["target"].replace("'", "\\'")
    #         graph_db.run(
    #             f'''
    #             MATCH (s) WHERE s.name = '{source}'
    #             MATCH (t) WHERE t.name = '{target}'
    #             CREATE (s)-[:{edge['type']}]->(t)
    #             '''
    #         )
    #         edge_count += 1
    #     print("✅ 新的知识图谱已成功导入Neo4j（覆盖原有数据）！")
    #     print(f"📊 统计：节点数 {node_count}，关系数 {edge_count}")
    # except Exception as e:
    #     print(f"❌ Neo4j导入失败：{e}")

if __name__ == "__main__":
    build_and_save_kg()