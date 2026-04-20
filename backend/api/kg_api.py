from fastapi import APIRouter, Query
from json_kg_store import load_kg_graph_data, load_knowledge_points

router = APIRouter(prefix="/api/kg", tags=["知识图谱"])

# ===== 已注释：Neo4j 数据库连接（保留以便后续恢复）=====
# from py2neo import Graph
# graph_db = Graph("bolt://localhost:7687", auth=("neo4j", "Dfs120900"))

# 原有接口：获取全量图谱（字段优化，适配前端）
@router.get("/all")
def get_kg_all(limit: int = 2000):
    # ===== 已注释：Neo4j 查询逻辑（保留以便后续恢复）=====
    # node_query = """
    # MATCH (n)
    # RETURN id(n) AS id, n.name AS label, n.level AS level,
    #        coalesce(n.type, labels(n)[0]) AS type
    # LIMIT $limit
    # """
    # nodes = graph_db.run(node_query, limit=limit).data()
    #
    # edge_query = """
    # MATCH (s)-[r]->(t)
    # RETURN id(s) AS source, id(t) AS target, type(r) AS label
    # LIMIT $limit
    # """
    # edges = graph_db.run(edge_query, limit=limit).data()

    # JSON 数据读取逻辑：从本地 data JSON 中读取节点和关系
    graph_data = load_kg_graph_data(limit=limit)
    nodes = graph_data["nodes"]
    edges = graph_data["edges"]

    return {
        "code": 200,
        "data": {
            "nodes": nodes,
            "edges": edges
        }
    }

# 原有接口：按层级获取图谱（字段统一）
@router.get("/by-level")
def get_kg_by_level(levels: str = "1,2", limit: int = 300):
    level_list = [int(l) for l in levels.split(",")]

    # ===== 已注释：Neo4j 查询逻辑（保留以便后续恢复）=====
    # node_query = """
    # MATCH (n)
    # WHERE n.level IN $levels
    # RETURN id(n) AS id, n.name AS label, n.level AS level,
    #        coalesce(n.type, labels(n)[0]) AS type
    # LIMIT $limit
    # """
    # nodes = graph_db.run(node_query, levels=level_list, limit=limit).data()
    # vis_nodes = [{"id": n["id"], "label": n["label"], "type": n["type"], "level": n["level"]} for n in nodes]
    # node_ids = [n["id"] for n in nodes]
    # edge_query = """
    # MATCH (s)-[r]->(t)
    # WHERE id(s) IN $node_ids AND id(t) IN $node_ids
    # RETURN id(s) AS source, id(t) AS target, type(r) AS label
    # LIMIT $limit
    # """
    # edges = graph_db.run(edge_query, node_ids=node_ids, limit=limit).data()
    # vis_edges = [{"source": e["source"], "target": e["target"], "label": e["label"]} for e in edges]

    # JSON 数据读取逻辑：按层级筛选节点，并自动筛选边
    graph_data = load_kg_graph_data(limit=limit, levels=level_list)
    vis_nodes = [
        {"id": n["id"], "label": n["label"], "type": n["type"], "level": n["level"]}
        for n in graph_data["nodes"]
    ]
    vis_edges = graph_data["edges"]

    return {"nodes": vis_nodes, "edges": vis_edges}

# 新增接口：获取图谱内所有知识点（供题目生成前置约束使用）
@router.get("/knowledge-points")
def get_kg_knowledge_points():
    """获取Neo4j图谱中所有知识点名称，用于题目生成前置约束"""
    try:
        # ===== 已注释：Neo4j 查询逻辑（保留以便后续恢复）=====
        # query = """
        # MATCH (n)
        # WHERE n.type IN ['核心领域','子结构','具体知识点'] OR labels(n)[0] IN ['核心领域','子结构','具体知识点']
        # RETURN n.name AS name
        # """
        # result = graph_db.run(query).data()
        # kg_ks = list(set([item["name"] for item in result]))

        # JSON 数据读取逻辑：按类型过滤知识点
        kg_ks = list(load_knowledge_points({"核心领域", "子结构", "具体知识点"}))
        return {
            "code": 200,
            "data": {"knowledge_points": kg_ks},
            "msg": "获取图谱知识点成功"
        }
    except Exception as e:
        return {
            "code": 500,
            "data": None,
            "msg": f"获取图谱知识点失败：{str(e)}"
        }

# 新增接口：知识点校验（供题目生成后幻觉校验使用）
@router.post("/check-knowledge-point")
def check_knowledge_point(knowledge_point: str):
    """校验单个知识点是否在图谱中"""
    try:
        # ===== 已注释：Neo4j 查询逻辑（保留以便后续恢复）=====
        # query = """
        # MATCH (n)
        # WHERE n.name = $kp
        # AND (n.type IN ['核心领域','子结构','具体知识点'] OR labels(n)[0] IN ['核心领域','子结构','具体知识点'])
        # RETURN count(n) > 0 AS exists
        # """
        # result = graph_db.run(query, kp=knowledge_point).data()[0]["exists"]

        # JSON 数据读取逻辑：本地集合直接判断
        kg_ks = load_knowledge_points({"核心领域", "子结构", "具体知识点"})
        result = knowledge_point in kg_ks
        return {
            "code": 200,
            "data": {"exists": result},
            "msg": "知识点校验成功"
        }
    except Exception as e:
        return {
            "code": 500,
            "data": None,
            "msg": f"知识点校验失败：{str(e)}"
        }