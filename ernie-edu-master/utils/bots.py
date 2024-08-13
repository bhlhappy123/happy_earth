import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import re
import json
import pandas as pd
import erniebot
from dotenv import find_dotenv, load_dotenv
from erniebot_agent.extensions.langchain.embeddings import ErnieEmbeddings
from utils.faiss_search import FaissSearch

_ = load_dotenv(find_dotenv())
erniebot.api_type = os.environ["api_type"]
erniebot.access_token = os.environ["access_token"]

cur_dir = os.path.dirname(os.path.abspath(__file__))


class QuestionAnswerBot:
    def __init__(self,value, bot_name="question_answering_bot", num_message_limit=10):
        self.bot_name = bot_name
        self.num_message_limit = num_message_limit
        self.messages = []
        self.embeddings = ErnieEmbeddings(aistudio_access_token=erniebot.access_token, chunk_size=16)
        self.faiss_search = FaissSearch(self.embeddings)
        self.faiss_search.load_db(os.path.join(cur_dir, '../all_index'))
        self.model = 'ernie-3.5'
        self.system_prompt = f"""
        你是一位{value}博士，我将提供来自小朋友的【问题】以及来自《十万个为什么》的【参考答案】，请你回答小朋友的问题。
            """
        self.system_prompt+="""要求：
            1. 回答时要依据参考答案，不要胡编乱造；
            2. 回答要简洁明了，控制在100字以内，适当口语化，且要有趣味性。
            """

    def get_response(self, question):
        retrieval_results = self.faiss_search.search(question, top_k=5)
        answer = '【参考答案】'
        for i in range(len(retrieval_results)):
            answer += '{}：{}\n'.format(i, retrieval_results[i]['content'])
        user_content = '【问题】:{}\n'.format(question) + answer
        self.messages.append({"role": "user", "content": user_content})
        response = erniebot.ChatCompletion.create(
            model=self.model,
            messages=self.messages,
            system=self.system_prompt,
        )
        response = response.get_result()
        self.messages.append({"role": "assistant", "content": response})
        if len(self.messages) > self.num_message_limit:
            self.messages = self.messages[-self.num_message_limit:]
        return response


class ProblemSetBot:
    def __init__(self,value):
        self.value = value
        self.question_json = {
            "题干": "                            ",
            "选项": [
                "",
                "",
                "",
                ""
            ],
            "答案": "",
            "解析": "",
            "难度": "",
            "评论": "",
            "科目": "",
            "知识点标签": []
        }
        self.question = self.question_json["题干"]
        self.choices = self.question_json["选项"]
        self.answer = self.question_json["答案"]
        # print(self.answer)
        self.analysis = self.question_json["解析"]
        self.difficulty = self.question_json["难度"]
        self.comment = self.question_json["评论"]
        self.subject = self.question_json["科目"]
        self.tags = self.question_json["知识点标签"]
        self.ques_header = ["题序", "题干", "选项A", "选项B", "选项C", "选项D", "答案", "解析", "难度", "评论", "科目",
                            "知识点标签"]
        self.question_num = 0
        self.question_df = []
        self.temp_dir = os.path.join(cur_dir, '../temp')
        os.makedirs(self.temp_dir, exist_ok=True)
        self.embeddings = ErnieEmbeddings(aistudio_access_token=erniebot.access_token, chunk_size=16)
        self.faiss_search = FaissSearch(self.embeddings)
        self.faiss_search.load_db(os.path.join(cur_dir, '../all_index'))
        self.model = 'ernie-3.5'
        self.system_prompt = f"""
            你是一位{value}博士，请严格按照给你的【出题格式】，基于给你的【出题内容】，出一道相关的题目。"""
        self.system_prompt+="""
            【出题格式】：{}
            【出题内容】：{}
            要求：
            1. 只需要返回json形式的题目信息，题目信息包括题干、选项、答案、解析、难度、评论、科目、知识点标签的信息；
            2. 生成的答案中必须包含选项A或者B或者C或者D。
            3. 以json形式返回。
            """


    def checkAnswer(self, choice):
        # print(self.answer)
        user_answer = choice[0]  # 取出第一个字符，一定是ABCD中的一个
        true_answer = self.answer[0]  # 取出答案中的第一个字符
        if true_answer in ['1', '2', '3', '4']:
            true_answer = chr(int(true_answer) + ord('A') - 1)
        if user_answer == true_answer.upper():
            return "恭喜你答对啦！再接再厉！"
        else:
            return "很抱歉你回答错误啦，再试一次吧！记得记录错题~"

    def update_self(self, data_dict,value):
        self.question = data_dict.get("题干", '题目生成失败，请重新生成')
        self.choices = data_dict.get("选项", ['', '', '', ''])
        self.answer = data_dict.get("答案", '')
        self.analysis = data_dict.get("解析", '')
        self.difficulty = data_dict.get("难度", '')
        self.comment = data_dict.get("评论", '')
        self.subject = data_dict.get("科目", '')
        self.tags = data_dict.get("知识点标签", [])
        # print(value)
        self.value=value
        # print(value)

    def generate_problem(self, key_word,value):
        # print(value)

        allKey = key_word + value
        # print(allKey)
        retrieval_results = self.faiss_search.search(allKey, top_k=5)
        retrieval_info = '【出题内容】：'
        for i in range(len(retrieval_results)):
            retrieval_info += '{}：{}\n'.format(i, retrieval_results[i]['content'])
        example = json.dumps(self.question_json, ensure_ascii=False)
        content = self.system_prompt.format(example, retrieval_info)
        response = erniebot.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": content}],
        )
        response_text = response.get_result()
        # print(response_text)
        if not response_text.endswith('```'):
            response_text += '```'
        json_str_match = re.search(r'```json(.+?)```', response_text, re.DOTALL)
        if json_str_match:
            json_str = json_str_match.group(1).strip().replace('\n', '')
            data_dict = json.loads(json_str)
        else:
            data_dict = self.question_json
            data_dict['题干'] = '题目生成失败，请重新生成'
            data_dict['选项'] = ['', '', '', '']
            data_dict['答案'] = ''
            data_dict['解析'] = ''
        self.update_self(data_dict,value)
        # print(data_dict)

    def get_df_question(self):
        df_question = [self.question_num, self.question, self.choices[0], self.choices[1], self.choices[2],
                       self.choices[3],
                       self.answer, self.analysis, self.difficulty, self.comment, self.subject, self.tags]
        return df_question

    def save_question(self):
        self.question_num += 1
        self.question_df.append(self.get_df_question())
        return self.question_df

    def save_xlsx(self):
        df = pd.DataFrame(self.question_df, columns=self.ques_header)
        file_name = os.path.join(self.temp_dir, "question.xlsx")
        df.to_excel(file_name, index=False)
        return file_name

    def clear_xlsx(self):
        self.question_df = []
        self.question_num = 0
        return self.question_df


# if __name__ == '__main__':
#     bot = ProblemSetBot("生命主题")
#     bot.generate_problem("精子")
#     print(bot.question, bot.choices)
