import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 添加父目录到sys.path
import json
from dotenv import find_dotenv, load_dotenv
from utils.faiss_search import FaissSearch
from erniebot_agent.extensions.langchain.embeddings import ErnieEmbeddings
from zhipuai import ZhipuAI

client = ZhipuAI(api_key="0edb55bf838a42f2598487d15a2fa25f.M9bUh3LjGt3pKt0L")  # 请填写您自己的APIKey

# 加载环境变量
_ = load_dotenv(find_dotenv())

# 初始化 FAISS 搜索
cur_dir = os.path.dirname(os.path.abspath(__file__))
embeddings = ErnieEmbeddings(aistudio_access_token=os.environ["access_token"], chunk_size=16)
faiss_search = FaissSearch(embeddings)
faiss_search.load_db(os.path.join(cur_dir, 'D:/python/pythonProject/ernie-edu-master/faiss_index_tianwen'))
import re


def get_model_answer(question, choices, context):
    prompt = f"你现在什么都不懂，请仔细阅读以下的背景信息，并严格按照背景信息，直接从提供的选项中选择一个最符合问题要求的答案字母。\n问题: {question}\n选项:\n"
    for idx, choice in enumerate(choices):
        prompt += f"{chr(65 + idx)}. {choice}\n"
    prompt += f"背景信息:\n{context}\n"

    # 假设client已经被正确配置和初始化
    response = client.chat.completions.create(
        model="glm-4",
        messages=[{'role': 'user', 'content': prompt}],
        temperature=0.5,  # 调整温度参数，值越小输出越稳定
    )

    answer_text = response.choices[0].message.content
    # 使用正则表达式更严格地匹配答案
    print(answer_text)
    match = re.search(r'[A-D]', answer_text)
    return match.group(0) if match else None


# 读取 JSON 文件
def load_questions(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


# 检索数据集获取背景信息
def get_context(question_with_choices):
    retrieval_results = faiss_search.search(question_with_choices, top_k=30)
    context = "\n".join([result['content'] for result in retrieval_results])
    return context


# 判断模型答案的正确率
def evaluate_model(questions):
    total_questions = len(questions)
    correct_answers = 0

    for question_data in questions:
        question = question_data["题干"]
        choices = question_data["选项"]
        correct_answer = question_data["答案"]

        # 将选项加入到问题中
        question_with_choices = question.join(choices)
        context = get_context(question_with_choices)
        model_answer = get_model_answer(question, choices, context)
        print(f"Question: {question}")
        print(f"Model Answer: {model_answer}")
        print(f"Correct Answer: {correct_answer}")

        if model_answer == correct_answer:
            correct_answers += 1

    accuracy = correct_answers / total_questions
    return accuracy


if __name__ == "__main__":
    json_file = "astronomy_questions（hard）.json"  # 替换为你的 JSON 文件路径
    questions = load_questions(json_file)
    accuracy = evaluate_model(questions)
    print(f"使用通义千问模型基于 RAG 的准确率: {accuracy * 100:.2f}%")