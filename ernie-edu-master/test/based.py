import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 添加父目录到sys.path
import re
import json
import pandas as pd
import erniebot
from dotenv import find_dotenv, load_dotenv
from utils.faiss_search import FaissSearch
from erniebot_agent.extensions.langchain.embeddings import ErnieEmbeddings

# 加载环境变量
_ = load_dotenv(find_dotenv())

erniebot.api_type = os.environ["api_type"]
erniebot.access_token = os.environ["access_token"]

# 初始化 FAISS 搜索
cur_dir = os.path.dirname(os.path.abspath(__file__))
embeddings = ErnieEmbeddings(aistudio_access_token=os.environ["access_token"], chunk_size=16)
faiss_search = FaissSearch(embeddings)
faiss_search.load_db(os.path.join(cur_dir, 'D:/python/pythonProject/ernie-edu-master/faiss_index_tianwen'))
import re

# 示例问题和背景信息
subjective_question = "为什么宇宙外面是什么我们不知道"

# 检索数据集获取背景信息的函数
def get_context(content):
    retrieval_results = faiss_search.search(content, top_k=1)
    context = "\n".join([result['content'] for result in retrieval_results])
    return context

# 定义获取模型答案的函数
def get_model_answer(question, context):
    prompt = f"你现在什么都不懂，严格按照背景信息，用50字回答以下问题\n问题: {question}\n背景信息:\n{context}\n"

    response = erniebot.ChatCompletion.create(
        model="ernie-3.5",
        messages=[{'role': 'user', 'content': prompt}],
        temperature=0.5  # 调整温度参数
    )

    answer_text = response.get_result().strip()  # 移除可能的首尾空白字符
    return answer_text

# 获取背景信息
context_info = get_context(subjective_question)

# 使用检索到的背景信息获取模型答案
model_answer = get_model_answer(subjective_question, context_info)
print("Model Answer:", model_answer)

if __name__ == "__main__":
    # 直接使用示例问题调用get_model_answer函数
    model_answer = get_model_answer(subjective_question, get_context(subjective_question))