import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 添加父目录到sys.path

import erniebot
from dotenv import find_dotenv, load_dotenv


# 加载环境变量
_ = load_dotenv(find_dotenv())

erniebot.api_type = os.environ["api_type"]
erniebot.access_token = os.environ["access_token"]

# 定义问题
subjective_question = "为什么宇宙外面是什么我们不知道"

# 定义获取模型答案的函数
def get_model_answer(question):
    prompt = (f"请仔细阅读以下问题，并给出尽可能详细和准确的答案，控制在50字之内回答。\n问题: {question}\n")

    response = erniebot.ChatCompletion.create(
        model="ernie-3.5",  # 使用 Aistudio 的模型
        messages=[{"role": "user", "content": prompt}],
    )
    answer_text = response.get_result().strip()  # 移除可能的首尾空白字符
    return answer_text


# 获取模型答案并打印
model_answer = get_model_answer(subjective_question)
print("Model Answer:", model_answer)

if __name__ == "__main__":
    # 直接调用上述函数获取答案
    model_answer = get_model_answer(subjective_question)
    # 这里不再需要进行答案评估，只需打印答案即可