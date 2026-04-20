import json
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


# JSON 数据读取逻辑：默认读取 data 目录下的 Neo4j 导出数据
DEFAULT_JSON_PATH = (
    Path(__file__).resolve().parent / "data" / "neo4j_query_table_data_2026-3-22.json"
)


def _read_raw_kg_json(json_path: Path = DEFAULT_JSON_PATH) -> Dict[str, Any]:
    """JSON 数据读取逻辑：读取原始 JSON，并统一成包含 nodes/relationships 的字典结构。"""
    with json_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    # 兼容两种结构：
    # 1) Neo4j query table 导出：[{ "nodes": [...], "relationships": [...] }]
    # 2) 直接对象结构：{ "nodes": [...], "relationships": [...] }
    if isinstance(payload, list):
        return payload[0] if payload else {"nodes": [], "relationships": []}
    if isinstance(payload, dict):
        return payload
    return {"nodes": [], "relationships": []}


def load_kg_graph_data(
    limit: int | None = None, levels: List[int] | None = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    JSON 数据读取逻辑：读取并转换图谱数据，输出统一结构：
    {
      "nodes": [{"id","label","level","type"}],
      "edges": [{"source","target","label"}]
    }
    """
    raw = _read_raw_kg_json()
    raw_nodes = raw.get("nodes", []) or []
    raw_relationships = raw.get("relationships", []) or []

    node_map: Dict[int, Dict[str, Any]] = {}
    for n in raw_nodes:
        node_id = n.get("identity")
        props = n.get("properties", {}) or {}
        labels = n.get("labels", []) or []
        node_type = props.get("type") or (labels[0] if labels else "未知类型")
        node_item = {
            "id": node_id,
            "label": props.get("name", ""),
            "level": props.get("level"),
            "type": node_type,
        }
        # 以 identity 去重，保留最后一次出现（通常数据一致）
        if node_id is not None:
            node_map[node_id] = node_item

    nodes = list(node_map.values())
    if levels is not None:
        level_set = set(levels)
        nodes = [n for n in nodes if n.get("level") in level_set]

    if limit is not None and limit > 0:
        nodes = nodes[:limit]

    allowed_ids: Set[int] = {n["id"] for n in nodes if n.get("id") is not None}
    edge_seen: Set[Tuple[Any, Any, Any]] = set()
    edges: List[Dict[str, Any]] = []
    for r in raw_relationships:
        source = r.get("start")
        target = r.get("end")
        label = r.get("type")
        if source not in allowed_ids or target not in allowed_ids:
            continue
        key = (source, target, label)
        if key in edge_seen:
            continue
        edge_seen.add(key)
        edges.append({"source": source, "target": target, "label": label})

    if limit is not None and limit > 0:
        edges = edges[:limit]

    return {"nodes": nodes, "edges": edges}


def load_knowledge_points(valid_types: Set[str] | None = None) -> Set[str]:
    """JSON 数据读取逻辑：读取图谱中的知识点名称集合。"""
    graph = load_kg_graph_data()
    nodes = graph.get("nodes", [])
    if valid_types:
        return {
            n["label"]
            for n in nodes
            if n.get("label") and (n.get("type") in valid_types)
        }
    return {n["label"] for n in nodes if n.get("label")}

