import os  # 导入os模块，用于与操作系统交互
import erniebot  # 导入erniebot模块，用于与文心一言接口交互
from dotenv import find_dotenv, load_dotenv  # 从dotenv模块导入find_dotenv和load_dotenv，用于加载环境变量


"""
这个程序主要是用于与ERNIEBot（文心一言）接口交互。它包括以下功能：

加载环境变量：通过dotenv模块加载.env文件中的API类型和访问令牌。
聊天完成功能：定义chat_completion函数，向ERNIEBot发送聊天消息并获取响应。
生成文本嵌入表示：定义embedding函数，生成输入文本的嵌入表示。
估算文本token数：定义get_num_tokens函数，估算输入文本的token数。
主程序入口：在__main__部分，提供了调用这些功能的示例代码（目前被注释掉），并最终调用get_num_tokens函数估算默认文本的token数。
"""
# 加载环境变量文件（.env）
_ = load_dotenv(find_dotenv())

# 从环境变量中读取api_type和access_token，并设置到erniebot模块中
erniebot.api_type = os.environ["api_type"]
erniebot.access_token = os.environ["access_token"]

# 定义一个函数chat_completion，用于生成聊天完成的响应
def chat_completion(text='', messages=[], model='ernie-3.5'):
    # 如果messages为空，则使用默认的用户输入内容
    if not messages:
        messages = [{'role': 'user', 'content': text}]
    # 调用erniebot的ChatCompletion接口，生成聊天完成的响应
    response = erniebot.ChatCompletion.create(
        model=model,
        messages=messages,
    )
    # 返回生成的响应结果
    return response.get_result()

# 定义一个函数embedding，用于生成文本的嵌入表示
def embedding(text):
    # 调用erniebot的Embedding接口，生成文本嵌入表示
    response = erniebot.Embedding.create(
        model="ernie-text-embedding",
        input=[text])
    # 返回生成的嵌入结果
    return response.get_result()

# 定义一个函数get_num_tokens，用于估算文本的token数
def get_num_tokens(text="你好，我是文心一言。"):
    # 使用token_helper.approx_num_tokens函数估算token数，汉字数 + 单词数 * 1.3
    num_tokens = erniebot.utils.token_helper.approx_num_tokens(text)
    # 返回估算的token数
    return num_tokens

# 主程序入口
if __name__ == '__main__':
    # print(embedding("七大行星是啥")) # 调用embedding函数，生成文本嵌入表示，返回的是嵌入表示的列表
    # question = '为什么天文学家老是要给星星拍照' # 定义一个问题
    # answer = '在照相技术发明以前，天文学家都是用眼睛观测，素描记录。伽利略就在纸上记录过木星与其4颗主要卫星位置的图。但素描记录毕竟速度慢、误差大。照相术发明以后，天文学家终于有了可以实时记录观测目标的工具。通过对照片的分析，天文学家可以细致地研究星星长什么样，温度有多高，运动速度有多快，甚至分析星星的年龄、内部化学元素的组成等天文课题。为此，天文学家设计了各种特殊的照相机，它们拍的照片主要可分为三个大类，天体的形态拍摄（成像），天体的光谱拍摄（成谱），天体随时间的变化（光变）。通过这些照片，我们可以看到千姿百态的恒星、星云、星系，可以研究它们的结构，例如旋涡星系的核心结构、旋臂结构、周围晕的结构等；可以了解它们的化学组成和物理状态，比如含有什么元素，温度有多高；还可以通过不同时间拍的照片，了解它们的亮度变化。' # 定义一个答案
    # erniebotInput = f"使用以下文段来回答最后的问题。仅根据给定的文段生成答案。如果你在给定的文段中没有找到任何与问题相关的信息，就说你不知道，不要试图编造答案。保持你的答案富有表现力。用户的问题是：{question}。给定的文段是：{answer}。" # 构建一个输入给erniebot的文本
    # res = chat_completion(erniebotInput) # 调用chat_completion函数，生成聊天完成的响应
    # print(res) # 输出响应结果
    # print(erniebot.Model.list()) # 列出所有可用的模型
    print(get_num_tokens()) # 调用get_num_tokens函数，估算默认文本的token数，并输出结果
