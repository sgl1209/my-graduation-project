import json
def read_text(file_name="data/data_structure.txt", chunk_size=2000):
    """
    读取文本并按chunk_size分段（按句子分割，避免截断语义）
    :param chunk_size: 每个片段的字符数（根据模型token限制调整，1token≈1.5中文字符）
    """
    with open(file_name, "r", encoding="utf-8") as f:
        text = f.read().strip()
    
    # 分段逻辑：按句号/换行分割，避免截断完整语义
    chunks = []
    current_chunk = ""
    for sentence in text.split("。"):
        if len(current_chunk + sentence) < chunk_size:
            current_chunk += sentence + "。"
        else:
            chunks.append(current_chunk)
            current_chunk = sentence + "。"
    if current_chunk:
        chunks.append(current_chunk)
    return chunks
def save_chunks():
    text_chunks = read_text(chunk_size=3000)
    with open("text_chunks.json", "w", encoding="utf-8") as f:
        json.dump(text_chunks, f, ensure_ascii=False, indent=2)
    print(f"✅ 已将 {len(text_chunks)} 段文本保存到 text_chunks.json")


if __name__ == "__main__":
    save_chunks()