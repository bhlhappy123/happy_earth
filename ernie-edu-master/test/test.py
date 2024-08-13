import os
import sys
import re
import json
import erniebot
import random
from dotenv import find_dotenv, load_dotenv
from erniebot_agent.extensions.langchain.embeddings import ErnieEmbeddings

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 添加父目录到sys.path
from utils.faiss_search import FaissSearch

# 加载环境变量
load_dotenv()

erniebot.api_type = os.environ["api_type"]
erniebot.access_token = os.environ["access_token"]


class AstronomyQuestionGenerator:
    def __init__(self):
        self.erniebot_access_token = os.environ.get("access_token")
        self.embeddings = ErnieEmbeddings(aistudio_access_token=self.erniebot_access_token, chunk_size=16)
        self.faiss_search = FaissSearch(self.embeddings)
        self.faiss_search.load_db(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../faiss_index_tianwen'))
        self.model = 'ernie-3.5'
        self.system_prompt = """
            你是一位天文博士懂得很多的天文知识，请严格按照给你的【出题格式】，基于给你的【出题内容】，出一道非常简单的相关的题目。
            【出题格式】：{}
            【出题内容】：{}
            要求：
            1. 只需要返回json形式的题目信息，题目信息包括题干、选项、答案等信息；
            2. 题目信息中的选项前面需要按照顺序排列并添加A、B、C、D；
            3. 题目信息中的答案需要用字母表示，如：A、B、C、D；
            4. 以json形式返回。
            """

    def generate_keywords(self):
        # 在这里编写生成关键字的方法，可以是一些常见的天文学术语、星座名称、天体名称等
        keywords = ['星空', '星座', '星球', '星系', '恒星', '行星', '银河', '星际', '宇宙']
        return random.choice(keywords)

    def generate_questions(self, num_questions=50):
        questions = []
        count = 0
        while count < num_questions:
            keyword = self.generate_keywords()
            retrieval_results = self.faiss_search.search(keyword, top_k=15)
            retrieval_info = '【出题内容】：'
            for i in range(len(retrieval_results)):
                retrieval_info += '{}：{}\n'.format(i, retrieval_results[i]['content'])
            response = erniebot.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": self.system_prompt.format('', retrieval_info)}],
            )
            response_text = response.get_result()
            if not response_text.endswith('```'):
                response_text += '```'
            json_str_match = re.search(r'```json(.+?)```', response_text, re.DOTALL)
            if json_str_match:
                json_str = json_str_match.group(1).strip().replace('\n', '')
                try:
                    question_data = json.loads(json_str)
                    questions.append(question_data)
                    count += 1
                except json.JSONDecodeError as e:
                    print(f"解析 JSON 时出错：{e.msg}")
                    print(f"错误的 JSON 字符串：{json_str}")
            else:
                print(f"未找到匹配的 JSON 字符串：{response_text}")
        return questions

    def save_questions_to_json(self, questions, filename):
        with open(filename, 'w', encoding='utf-8') as json_file:
            json.dump(questions, json_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    generator = AstronomyQuestionGenerator()
    questions = generator.generate_questions()
    generator.save_questions_to_json(questions, 'astronomy_questions.json')
