from fastapi import APIRouter,Depends
from pydantic import BaseModel
from openai import OpenAI
import os
import json
import re
from dotenv import load_dotenv
from json_kg_store import load_knowledge_points
from sqlalchemy.orm import Session
from question import Question
from database import SessionLocal
from typing import List
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
# 加载环境变量
load_dotenv()

# 初始化 OpenAI 客户端（通义千问）
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# ===== 已注释：Neo4j 数据库连接（保留以便后续恢复）=====
# from py2neo import Graph
# graph_db = Graph("bolt://localhost:7687", auth=("neo4j", "Dfs120900"))

# 创建路由实例
router = APIRouter(
    prefix="/api/generate-question",
    tags=["题目生成"],
    responses={404: {"description": "Not found"}}
)

# ===================== 新增：数据库依赖 =====================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 定义请求模型
class QuestionRequest(BaseModel):
    text: str  # 参考文本/知识点
    type: str  # 题型：single/multiple/blank/code

# 定义校验请求模型（新增）
class IllusionCheckRequest(BaseModel):
    question_content: str  # 题干内容

# ========== 核心修复：JSON清洗函数 ==========
def clean_and_parse_json(raw_content: str):
    """
    清洗大模型返回的内容，提取并解析其中的 JSON 部分
    解决 JSON 格式错误、多余字符、单引号、换行/空格等问题
    """
    try:
        # 步骤1：移除首尾多余字符（空格、换行、markdown标记）
        clean_str = raw_content.strip()
        # 移除markdown代码块标记（包括 ```json 开头）
        clean_str = re.sub(r"^```(json)?", "", clean_str)
        clean_str = re.sub(r"```$", "", clean_str)
        clean_str = clean_str.strip()
        
        # 步骤2：贪婪匹配完整的 JSON 块（从第一个 { 到最后一个 }）
        json_match = re.search(r'\{[\s\S]*\}', clean_str)
        if not json_match:
            raise ValueError("返回内容中未找到有效的 JSON 结构")
        json_str = json_match.group(0)
        
        # 步骤3：修复常见 JSON 格式错误（重点处理换行/空格）
        json_str = json_str.replace("'", "\"")  # 单引号转双引号
        json_str = re.sub(r",\s*}", "}", json_str)  # 移除最后一个逗号（对象）
        json_str = re.sub(r",\s*]", "]", json_str)  # 移除最后一个逗号（数组）
        json_str = re.sub(r"\n\s*", "", json_str)  # 移除所有换行+缩进（核心修复！）
        json_str = re.sub(r"\t", "", json_str)     # 移除制表符
        json_str = re.sub(r"\\n", "\\\\n", json_str) # 保留代码中的换行符转义
        
        # 步骤4：严格解析 JSON
        return json.loads(json_str)
    
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON解析失败: {str(e)} (原始内容片段: {raw_content[:100]})")
    except Exception as e:
        raise ValueError(f"处理JSON失败: {str(e)}")

# 新增：抽取文本中的知识点（用于生成前校验）
def extract_input_knowledge_points(input_text: str):
    """从用户输入的文本中抽取知识点，用于生成前幻觉拦截"""
    try:
        prompt = f"""
        从以下文本中抽取所有核心知识点，仅返回逗号分隔的名称，无任何多余文字：
        {input_text}
        """
        completion = client.chat.completions.create(
            model="qwen-plus",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1  # 低随机性保证抽取准确
        )
        extract_ks = [ks.strip() for ks in completion.choices[0].message.content.split(",") if ks.strip()]
        return extract_ks
    except Exception as e:
        raise ValueError(f"抽取输入知识点失败：{str(e)}")

# 新增：抽取题干中的知识点（供后置校验使用）
def extract_question_knowledge_points(question_content: str):
    """从题干中抽取知识点，供后置校验使用"""
    try:
        prompt = f"""
        从以下题干中抽取所有知识点，仅返回逗号分隔的名称，无任何多余文字：
        {question_content}
        """
        completion = client.chat.completions.create(
            model="qwen-plus",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1  # 低随机性保证抽取准确
        )
        extract_ks = [ks.strip() for ks in completion.choices[0].message.content.split(",") if ks.strip()]
        return extract_ks
    except Exception as e:
        raise ValueError(f"抽取题干知识点失败：{str(e)}")

# ========== 新增：知识点模糊匹配函数 ==========
def is_knowledge_point_exists(extract_ks: str, kg_ks: set) -> bool:
    """
    模糊匹配知识点：
    1. 完全相等 → 匹配
    2. 包含关系（如"线性探测再散列"包含"伪随机探测再散列"）→ 匹配
    3. 别名映射（hash→哈希，散列→哈希）→ 匹配
    """
    if not extract_ks:
        return False
    
    # 归一化：统一小写、去空格、替换别名
    def normalize(s: str) -> str:
        return (s.strip().lower()
                .replace(" ", "")
                .replace("hash", "哈希")
                .replace("散列", "哈希")
                .replace("线性探测", "探测")
                .replace("伪随机探测", "探测")
                .replace("再散列", "哈希"))
    
    norm_extract = normalize(extract_ks)
    
    # 遍历所有图谱知识点，做模糊匹配
    for kg_k in kg_ks:
        norm_kg = normalize(kg_k)
        # 完全相等 或 互相包含
        if norm_extract == norm_kg or norm_extract in norm_kg or norm_kg in norm_extract:
            return True
    return False

# ========== 核心功能：生成题目（带完整幻觉抑制） ==========
@router.post("/generate", summary="生成指定类型的题目（带前置幻觉抑制）")
async def generate_question(req: QuestionRequest,db: Session = Depends(get_db)):
    try:
        # 1. 基础参数校验
        if not req.text or not req.type:
            return {
                "code": 400,
                "msg": "参数错误：text 和 type 不能为空",
                "data": None
            }
        
        # 2. 生成前幻觉拦截（核心新增）
        # 2.1 抽取用户输入的知识点
        input_ks = extract_input_knowledge_points(req.text)
        if not input_ks:
            return {
                "code": 400,
                "msg": "未能从输入文本中抽取到有效知识点",
                "data": None
            }
        
        # ===== 已注释：Neo4j 查询逻辑（保留以便后续恢复）=====
        # kg_query = """
        # MATCH (n)
        # WHERE n.type IN ['属性','子知识点','具体知识点'] OR labels(n)[0] IN ['属性','子知识点','具体知识点']
        # RETURN n.name AS name
        # """
        # kg_result = graph_db.run(kg_query).data()
        # kg_ks = set([item["name"] for item in kg_result])

        # JSON 数据读取逻辑：从本地 JSON 中读取可用知识点集合
        kg_ks = load_knowledge_points({"属性", "子知识点", "具体知识点"})
        data_ks = list(kg_ks)[5:]
        # 2.3 校验是否存在幻觉知识点（改为模糊匹配）
        illusion_ks = []
        valid_ks = []
        for ks in input_ks:
            if is_knowledge_point_exists(ks, kg_ks):
                valid_ks.append(ks)
            else:
                illusion_ks.append(ks)
        
        # 2.4 如果有幻觉知识点，直接拦截返回
        if illusion_ks:
            return {
                "code": 403,
                "msg": f"检测到幻觉知识点：{','.join(illusion_ks)}请更换知识点重试",
                "data": None,
                "illusion_ks": illusion_ks,
                "valid_ks": valid_ks
            }
        
        # 3. 映射题型名称
        type_mapping = {
            "single": "单选",
            "multiple": "多选",
            "blank": "填空",
            "code": "编程"
        }
        question_type = type_mapping.get(req.type, "单选")
        
        # 4. 构造数据结构专用Prompt（替换掉机器学习模板）
        ks_str = ",".join(kg_ks) if kg_ks else "数据结构基础知识点"
        base_prompt = """
你是数据结构专业出题老师，必须基于以下要求生成一道完整的{q_type}题：
1. 所有内容必须原创，禁止出现模板占位文字
2. 仅使用图谱内知识点：{ks_str}，禁止出现任何图谱外内容
3. 严格围绕用户输入的知识点：{text}，禁止偏离主题
4. 仅返回标准JSON格式，无任何多余文字、解释、换行或markdown标记
5. 内容必须是数据结构相关，禁止出现机器学习等无关领域内容

输出格式（直接替换为原创内容，无多余字符）：
{json_template}
"""
        # 数据结构专用模板（核心修改）
        type_config = {
            "单选": {
                "json_template": '''{"title":"数据结构单选题","content":"题干","options":[{"key":"A","value":"选项A"},{"key":"B","value":"选项B"},{"key":"C","value":"选项C"},{"key":"D","value":"选项D"}],"answer":"B","difficulty":2,"knowledgePoint":"{text}","chapter":1,"analysis":"解析说明"}'''
            },
            "多选": {
                "json_template": '''{"title":"数据结构多选题","content":"题干","options":[{"key":"A","value":"选项A"},{"key":"B","value":"选项B"},{"key":"C","value":"选项C"},{"key":"D","value":"选项D"}],"answer":"ABC","difficulty":2,"knowledgePoint":"{text}","chapter":1,"analysis":"解析说明"}'''
            },
            "填空": {
                "json_template": '''{"title":"数据结构填空题","content":"题干______","answer":"答案","difficulty":2,"knowledgePoint":"{text}","chapter":1,"analysis":"解析说明"}'''
            },
            "编程": {
                "json_template": '''{"title":"数据结构编程题","content":"题干要求","options":[],"answer":"代码实现","difficulty":2,"knowledgePoint":"{text}","chapter":1,"analysis":"解析说明"}'''
            }
        }
        
        # 5. 构造最终Prompt
        config = type_config[question_type]
        prompt = base_prompt.format(
            q_type=question_type,
            ks_str=ks_str,
            text=req.text,
            json_template=config["json_template"]
        ).strip()
        
        # 6. 调用通义千问生成题目
        completion = client.chat.completions.create(
            model="qwen-plus",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            response_format={"type": "json_object"},
            max_tokens=2048
        )
        
        # 7. 清洗并解析返回结果
        raw_content = completion.choices[0].message.content.strip()
        data = clean_and_parse_json(raw_content)
        
        # 8. 补充默认字段
        data.setdefault("difficulty", 2)
        data.setdefault("knowledgePoint", req.text[:20])
        data.setdefault("chapter", 1)
        data.setdefault("options", [])
        data["ks"] = data_ks  # 新增：返回有效知识点列表
        # data.setdefault("ks", kg_ks)  # 新增：返回有效知识点列表
        # ===================== 新增：保存题目到本地MySQL =====================
        db_question = Question(
            title=data.get("title", ""),
            content=data.get("content", ""),
            options=data.get("options", []),
            answer=data.get("answer", ""),
            difficulty=data.get("difficulty", 2),
            knowledge_point=data.get("knowledgePoint", ""),
            chapter=data.get("chapter", 1),
            analysis=data.get("analysis", ""),
            ks=data["ks"]
        )
        db.add(db_question)
        db.commit()  # 提交保存到数据库
        db.refresh(db_question)
        # 9. 返回成功结果
        return {
            "code": 200,
            "msg": "题目生成成功（已做前置幻觉抑制）",
            "data": data,
            "kg_constraint": f"已基于图谱内{len(kg_ks)}个知识点生成题目"
        }
    
    except SQLAlchemyError:
        db.rollback()  # 必须回滚，解决事务报错
        print(f"数据库错误详情：{str(e)}")
        return {"code": 500, "msg": "数据库保存失败", "data": None}

    except ValueError as e:
        return {"code": 400, "msg": f"生成失败：{str(e)}", "data": None}

    except Exception as e:
        print(f"服务器错误详情：{str(e)}")
        return {"code": 500, "msg": "题目生成失败，请稍后重试", "data": None}

# ========== 幻觉校验接口（后置校验） ==========
@router.post("/check-illusion", summary="校验题目是否含幻觉知识点")
async def check_question_illusion(req: IllusionCheckRequest):
    try:
        # 1. 抽取题干中的知识点
        extract_ks = extract_question_knowledge_points(req.question_content)
        if not extract_ks:
            return {
                "code": 400,
                "msg": "未从题干中抽取到知识点",
                "data": None
            }
        
        # ===== 已注释：Neo4j 查询逻辑（保留以便后续恢复）=====
        # kg_query = """
        # MATCH (n)
        # WHERE n.type IN ['属性','子知识点','具体知识点'] OR labels(n)[0] IN ['属性','子知识点','具体知识点']
        # RETURN n.name AS name
        # """
        # kg_result = graph_db.run(kg_query).data()
        # kg_ks = set([item["name"] for item in kg_result])

        # JSON 数据读取逻辑：从本地 JSON 中读取可用知识点集合
        kg_ks = load_knowledge_points({"属性", "子知识点", "具体知识点"})
        
        # 3. 比对校验（改为模糊匹配）
        valid_ks = []
        illusion_ks = []
        for ks in extract_ks:
            if is_knowledge_point_exists(ks, kg_ks):
                valid_ks.append(ks)
            else:
                illusion_ks.append(ks)
        
        total_ks = len(extract_ks)
        match_rate = round(len(valid_ks)/total_ks*100, 2) if total_ks > 0 else 0.0
        
        # 4. 生成建议
        if not illusion_ks:
            suggestion = "无幻觉知识点，校验通过"
        else:
            kg_ks_list = list(kg_ks)[:5]
            suggestion = f"含幻觉知识点：{','.join(illusion_ks)}，建议替换为图谱内知识点：{','.join(kg_ks_list)}"
        
        # 5. 返回校验结果
        return {
            "code": 200,
            "msg": "幻觉校验成功",
            "data": {
                "has_illusion": len(illusion_ks) > 0,
                "valid_ks": valid_ks,
                "illusion_ks": illusion_ks,
                "match_rate": match_rate,
                "suggestion": suggestion
            }
        }
    except Exception as e:
        print(f"幻觉校验错误：{str(e)}")
        return {
            "code": 500,
            "msg": "幻觉校验失败，请稍后重试",
            "data": None
        }
# 响应模型
class QuestionResp(BaseModel):
    id: int
    title: str
    content: str
    options: list
    answer: str
    difficulty: int
    knowledge_point: str
    chapter: int
    analysis: str
    ks: list
    created_at: str

    class Config:
        orm_mode = True
# 查询所有历史题目（从本地MySQL读取）
@router.get("/history", summary="获取所有历史生成的题目")
def get_history_questions(db: Session = Depends(get_db)):
    try:
        questions = db.query(Question).order_by(Question.created_at.desc()).all()
        
        result = []
        for q in questions:
            item = {
                "id": q.id,
                "title": q.title,
                "content": q.content,
                "options": q.options,
                "answer": q.answer,
                "difficulty": q.difficulty,
                "knowledge_point": q.knowledge_point,
                "chapter": q.chapter,
                "analysis": q.analysis,
                "ks": q.ks,
                # 手动转字符串，彻底解决类型错误
                "created_at": q.created_at.strftime("%Y-%m-%d %H:%M:%S") if q.created_at else None
            }
            result.append(item)

        return {
            "code": 200,
            "msg": "获取历史题目成功",
            "data": result
        }
    except Exception as e:
        print(f"获取历史题目错误：{str(e)}")
        return {
            "code": 500,
            "msg": "获取历史题目失败",
            "data": []
        }