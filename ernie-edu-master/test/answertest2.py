import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 添加父目录到sys.path
import re
import json
import erniebot
from dotenv import find_dotenv, load_dotenv

# 加载环境变量
_ = load_dotenv(find_dotenv())

erniebot.api_type = os.environ["api_type"]
erniebot.access_token = os.environ["access_token"]

# 定义一个函数来调用 Aistudio 模型
def get_model_answer(question, choices):
    prompt = f"根据以下的题干和选项直接给出答案，题干: {question}\n选项:\n"
    for idx, choice in enumerate(choices):
        prompt += f"直接给出答案{chr(65 + idx)}. {choice}\n"
    response = erniebot.ChatCompletion.create(
        model="ernie-3.5",  # 使用 Aistudio 的模型
        messages=[{"role": "user", "content": prompt}],
    )

    answer_text = response.get_result().strip()
    print(answer_text)
    match = re.search(r'([A-D])', answer_text)
    return match.group(1) if match else None

# 读取 JSON 文件
def load_questions(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# 判断模型答案的正确率
def evaluate_model(questions):
    total_questions = len(questions)
    correct_answers = 0

    for question_data in questions:
        question = question_data["题干"]
        choices = question_data["选项"]
        correct_answer = question_data["答案"]

        model_answer = get_model_answer(question, choices)
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
    print(f"use ernie-3.5 Model Accuracy: {accuracy * 100:.2f}%")
