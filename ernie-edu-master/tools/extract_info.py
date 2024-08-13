import os
import json
from bs4 import BeautifulSoup

"""
这个函数extract_title的主要目的是从指定目录中的HTML文件中提取特定的标题文本，并将这些标题文本保存到一个JSON文件中
"""


def extract_title(html_dir):
    # 获取指定目录中的所有文件和文件夹
    htmls = os.listdir(html_dir)
    questions = []

    # 遍历筛选后的HTML文件列表
    for html in htmls:
        print(html)
        # 以读取模式打开每个HTML文件，使用UTF-8编码
        with open(os.path.join(html_dir, html), 'r', encoding='utf-8') as f:
            html_content = f.read()

        # 使用BeautifulSoup解析HTML内容
        soup = BeautifulSoup(html_content, 'html.parser')
        # 查找所有类名为"bodycontent-second-title1"和"bodycontent-second-title"的元素
        titles = soup.find_all(class_=["bodycontent-second-title1", "bodycontent-second-title"])

        # 遍历这些元素并获取它们的文本内容，去除前后空白
        for title in titles:
            questions.append(title.get_text(strip=True))

    print(questions)

    # 将提取的问题列表写入JSON文件
    with open('../assets/questions_all.json', 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False)


if __name__ == '__main__':
    # 调用函数，传入HTML文件所在的目录
    extract_title('D:/python/pythonProject/ernie-edu-master/htmlData')
