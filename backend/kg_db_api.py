from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from json_kg_store import load_kg_graph_data

# 加载环境变量（可选，也可直接写死）
load_dotenv()

# 初始化FastAPI
app = FastAPI(title="知识图谱API")

# 解决跨域问题（前端能访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有前端地址，生产环境指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 已注释：Neo4j 数据库连接（保留以便后续恢复）=====
# from py2neo import Graph
# graph_db = Graph(
#     "bolt://localhost:7687",
#     auth=("neo4j", "Dfs120900")
# )

# 接口1：获取所有知识图谱数据（节点+关系）
@app.get("/api/kg/all")
def get_kg_all(limit: int = 500):  # 限制数量避免前端卡顿
    # ===== 已注释：Neo4j 查询逻辑（保留以便后续恢复）=====
    # node_query = """
    # MATCH (n)
    # RETURN id(n) AS id, n.name AS label, n.level AS level, n.type AS group
    # LIMIT $limit
    # """
    # nodes = graph_db.run(node_query, limit=limit).data()

    # JSON 数据读取逻辑：读取本地节点数据
    graph_data = load_kg_graph_data(limit=limit)
    nodes = graph_data["nodes"]
    # 转换节点格式（适配vis-network）
    vis_nodes = [
        {
            "id": node["id"],
            "label": node["label"],
            "level": node["level"],
            "group": node["type"],  # 用type分组，前端可按group设置颜色
            "title": f"类型：{node['type']}<br>层级：{node['level']}"  # 鼠标悬停提示
        }
        for node in nodes
    ]

    # ===== 已注释：Neo4j 查询逻辑（保留以便后续恢复）=====
    # edge_query = """
    # MATCH (s)-[r]->(t)
    # RETURN id(s) AS from, id(t) AS to, type(r) AS label
    # LIMIT $limit
    # """
    # edges = graph_db.run(edge_query, limit=limit).data()

    # JSON 数据读取逻辑：读取本地关系数据
    edges = graph_data["edges"]
    # 转换关系格式（适配vis-network）
    vis_edges = [
        {
            "from": edge["source"],
            "to": edge["target"],
            "label": edge["label"],  # 关系名称（包含/适配题型/对应难度）
            "title": f"关系：{edge['label']}"
        }
        for edge in edges
    ]

    return {"nodes": vis_nodes, "edges": vis_edges}

# 接口2：按层级筛选（比如只查level1+level2）
@app.get("/api/kg/by-level")
def get_kg_by_level(levels: str = "1,2", limit: int = 300):
    level_list = [int(l) for l in levels.split(",")]
    # ===== 已注释：Neo4j 查询逻辑（保留以便后续恢复）=====
    # node_query = """
    # MATCH (n)
    # WHERE n.level IN $levels
    # RETURN id(n) AS id, n.name AS label, n.level AS level, n.type AS group
    # LIMIT $limit
    # """
    # nodes = graph_db.run(node_query, levels=level_list, limit=limit).data()
    # vis_nodes = [{"id": n["id"], "label": n["label"], "group": n["group"]} for n in nodes]
    # node_ids = [n["id"] for n in nodes]
    # edge_query = """
    # MATCH (s)-[r]->(t)
    # WHERE id(s) IN $node_ids AND id(t) IN $node_ids
    # RETURN id(s) AS from, id(t) AS to, type(r) AS label
    # LIMIT $limit
    # """
    # edges = graph_db.run(edge_query, node_ids=node_ids, limit=limit).data()
    # vis_edges = [{"from": e["from"], "to": e["to"], "label": e["label"]} for e in edges]

    # JSON 数据读取逻辑：按层级读取并转换返回结构
    graph_data = load_kg_graph_data(limit=limit, levels=level_list)
    vis_nodes = [
        {"id": n["id"], "label": n["label"], "group": n["type"]}
        for n in graph_data["nodes"]
    ]
    vis_edges = [
        {"from": e["source"], "to": e["target"], "label": e["label"]}
        for e in graph_data["edges"]
    ]

    return {"nodes": vis_nodes, "edges": vis_edges}

# 启动服务
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("kg_db_api:app", host="0.0.0.0", port=8002, reload=True)