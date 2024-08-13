import os
import json
import gradio as gr
import requests
import random
import numpy as np
import threading
import erniebot
import websocket
from dashscope.audio.tts_v2 import *
import tempfile
import time
import cv2

import dashscope
from dotenv import find_dotenv, load_dotenv
from utils.format_html import format_welcome_html, format_story_html2, format_introduce_html
from utils.ernie_bot_client import chat_completion
from utils.bots import QuestionAnswerBot, ProblemSetBot
from utils.video_generation import generate_gradient_video
from utils.speech_client import tts_damo_api, asr_damo_api, convert_pcm_to_float

_ = load_dotenv(find_dotenv())

erniebot.api_type = os.environ["api_type"]
erniebot.access_token = os.environ["access_token"]

uid = threading.current_thread().name
dashscope.api_key = "sk-b9924d51b1c14e338cc7136d5520b893"
model = "cosyvoice-v1"
voice = "longxiaochun"

host_avatar = 'assets/host_image.png'
user_avatar = 'assets/user_image.png'
url = "https://api.siliconflow.cn/v1/stabilityai/stable-diffusion-3-medium/text-to-image"
os.makedirs('temp', exist_ok=True)
# 使用 gr.State 来存储主题选择
global_topic_value = gr.State(None)


def init_game(state):
    state['question_bot'] = QuestionAnswerBot(topic, bot_name="question_answering_bot")
    return state


def update_global_topic(new_value):
    global_topic_value.value = new_value


def transfer_text(input_text):
    return input_text  # 直接返回输入的文本


def download_image(url, save_dir):
    response = requests.get(url)
    if response.status_code == 200:
        img_name = url.split("/")[-1]
        img_path = os.path.join(save_dir, img_name)
        with open(img_path, 'wb') as f:
            f.write(response.content)
        return img_path
    else:
        return None


def generate_images(story_content):
    image_urls = image_submit_click(story_content)
    save_dir = "temp_images"
    os.makedirs(save_dir, exist_ok=True)

    image_paths = []
    for url in image_urls:
        if url != "No URL found in the response.":
            img_path = download_image(url, save_dir)
            if img_path:
                image_paths.append(img_path)

            else:
                image_paths.append(None)
        else:
            image_paths.append(None)


    return tuple(image_paths)


def story_submit_click(text_story_title, choices):  # 定义故事提交按钮点击事件处理函数
    if text_story_title.strip() == '':  # 如果故事标题为空
        return '你想听什么故事呢？不知道怎么写？看看右边大家都在关注啥'  # 返回提示信息
    prompt = f"""你是一位{choices}方面的博士,"""
    prompt += """擅长用风趣幽默的方式给小朋友讲故事，根据给你的标题：{}，编写一个小故事
                要求：
                1.直接输出故事内容;
                2.故事要有逻辑性，故事内容有趣，至少分4个具体场景;
                3.字数保持在200字左右，且要有趣味性。
            """
    response = chat_completion(prompt.format(text_story_title))  # 调用对话完成函数，生成故事内容
    return response  # 返回生成的故事内容


def story_more_click(choice):  # 定义获取更多示例按钮点击事件处理函数
    # update_global_topic(global_topic_value)
    # print("111")
    prompt = f"""我想给小朋友普及有关{choice}的知识，需要通过一个故事来引入，帮我想一个只有"一句话"的故事主题按照下面给出的【格式】。
                要求：
                1.只需要返还一个"一句话"的就可以;
                2.字数控制在25字左右;
                3.内容要有趣味性，有反问，能够吸引小朋友;
                4.【格式】:"一句话"
            """
    response1 = chat_completion(prompt)
    prompt += "故事主题要完全不一样"
    response2 = chat_completion(prompt)
    prompt += "故事主题要完全不一样"
    response3 = chat_completion(prompt)
    return response1, response2, response3


def ques_gen_click(state, value):
    prompt = f"""你现在是一个对这个世界充满好奇的小朋友，有很多的问题在你的脑海中，
                    你想知道的问题是关于{value}的
                    要求：
                    1.只需要10个字左右。
                    2.问题非常的有趣味性，和可探索性。
                """
    response1 = chat_completion(prompt)
    response2 = chat_completion(prompt)
    response3 = chat_completion(prompt)
    return (response1, response2, response3)


def ques_button_click(question_text):
    return question_text


def send_button_click(user_chat_input, state, chatbot):
    chatbot.append((user_chat_input, None))
    yield (chatbot, '')
    bot = state['question_bot']
    response = bot.get_response(user_chat_input)
    # print(response)
    state['answer_story'] = response
    # print(state['answer_story'])
    chatbot.append((None, response))
    yield (chatbot, '')


def tts_speech_synthesis(text, out_path="output.wav", max_retries=3):
    for attempt in range(max_retries):
        try:
            synthesizer = SpeechSynthesizer(model=model, voice=voice)
            audio = synthesizer.call(text)
            # print(audio)
            with open(out_path, 'wb') as f:
                f.write(audio)
                print(f"Audio saved to {out_path}")
            save_audio_file(audio, "temp/audio_story.wav")
            return out_path
        except websocket._exceptions.WebSocketConnectionClosedException as e:
            if attempt < max_retries - 1:
                print(
                    f"WebSocket connection closed. Retrying attempt {attempt + 1}/{max_retries}...")
                time.sleep(1)  # Wait before retrying
            else:
                raise e  # If retries exhausted, raise the exception


def save_audio_file(audio_data, file_path):
    with open(file_path, "wb") as audio_file:
        audio_file.write(audio_data)


def update_audio_content():
    text = text_story_content.value
    if text.strip():
        audio_file = tts_speech_synthesis(text)
        # print(audio_file)
        save_audio_file(audio_file, "temp/audio_story.wav")
        audio_story_content.value = open(audio_file, "rb").read()

    # 修改文生图API


def image_submit_click(text_story_content):
    # 格式化提示信息
    prompt = ("你是一位语言大师，精通中文和英文，擅长根据中文故事内容，拆解并总结出故事的主要情节，并用4句话英文来描述。\n"
              "故事内容：{}\n"
              "要求：\n"
              "1.输出4句完整英文的场景描述即可，优美，适合儿童观看理解。\n"
              "2.每句话都要简短，15个单词左右。\n"
              "3.每句话之间换行分隔。")

    # 获取场景描述
    response = chat_completion(prompt.format(text_story_content))

    # 将返回的描述按行分割，得到四句场景描述
    lines = response.split('\n')

    # 检查是否有至少四句描述
    if len(lines) < 4:
        # 如果不足四句，使用空字符串补齐
        lines += [""] * (4 - len(lines))

    # 分别存储每句描述到不同的变量
    response1, response2, response3, response4 = lines[0], lines[1], lines[2], lines[3]

    # 生成图像
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "Bearer sk-kqlavbqxkdeucapczvzjafeqoonaevxidspwenypcrjyflfb"
    }

    payloads = [{
        "prompt": response1,
        "image_size": "1024x1024",
        "batch_size": 1,
        "num_inference_steps": 20,
        "guidance_scale": 7.5
    }, {
        "prompt": response2,
        "image_size": "1024x1024",
        "batch_size": 1,
        "num_inference_steps": 20,
        "guidance_scale": 7.5
    }, {
        "prompt": response3,
        "image_size": "1024x1024",
        "batch_size": 1,
        "num_inference_steps": 20,
        "guidance_scale": 7.5
    }, {
        "prompt": response4,
        "image_size": "1024x1024",
        "batch_size": 1,
        "num_inference_steps": 20,
        "guidance_scale": 7.5
    }]

    image_urls = []

    for payload in payloads:
        response = requests.post(url, json=payload, headers=headers)
        response_data = json.loads(response.text)
        urls = response_data.get("images", [])

        if urls:
            image_urls.append(urls[0].get("url"))
        else:
            image_urls.append("No URL found in the response.")

    return (image_urls[0], image_urls[1], image_urls[2], image_urls[3])


def generate_keywords_click(state):
    messages = state['question_bot'].messages
    if len(messages) == 0:
        return '今天还没有聊天哦，快去模块二和机器人探索未知世界吧！'
    contents = [mes['content'] for mes in messages if mes['role'] == 'assistant']
    if 'answer_story' in state:
        # print(state['answer_story'])
        contents.append(state['answer_story'])
    content = '\n'.join(contents)
    prompt = f"""根据所给的文本内容，提取2-3个有关{global_topic_value.value}的关键字。"""
    prompt += """内容：{}
                要求：
                1.只需要输出2-3个关键词即可。
                2.关键词之间用换行符隔开。
                3.直接输出关键词
            """
    keywords = chat_completion(prompt.format(content))
    return keywords


def generate_problem_click(keywords_text, state):
    keywords = keywords_text.split('\n')
    keywords = [word.strip() for word in keywords if len(word.strip()) > 0]
    if len(keywords) == 0:
        keywords = []
    keyword = random.choice(keywords)
    # print(str(global_topic_value.value))
    problemset.generate_problem(keyword, global_topic_value.value)
    question = "## " + problemset.question
    options = ["A." + problemset.choices[0], "B." + problemset.choices[1],
               "C." + problemset.choices[2], "D." + problemset.choices[3]]
    radio = gr.Radio(options, label="选择你认为正确的一项")
    state['answer_submit'] = False
    return (question, radio, problemset.subject, problemset.difficulty, problemset.analysis)


def answer_submit_click(choices_radio, state):
    response = problemset.checkAnswer(choices_radio)
    state['answer_submit'] = True
    return response


def save_problem_click(state):
    if 'answer_submit' in state and state['answer_submit']:
        question_df = problemset.save_question()
        return question_df
    else:
        return []


def save_record_click():
    file_name = problemset.save_xlsx()
    return file_name


def clear_record_click():
    question_df = problemset.clear_xlsx()
    return question_df


def main_ui(state, topic):
    state['topic'] = topic
    global global_topic_value
    global_topic_value.value = topic
    return {welcome_tab: gr.update(visible=False), main_tab: gr.update(visible=True)}


def welcome_ui(state, topic):
    state['topic'] = topic
    return {welcome_tab: gr.update(visible=True), main_tab: gr.update(visible=False)}


def tts_speech_synthesis1(text, max_retries=3):
    for attempt in range(max_retries):
        try:
            synthesizer = SpeechSynthesizer(model=model, voice=voice)
            answer = text[-1][-1]
            audio2 = synthesizer.call(answer)
            save_audio_file(audio2, "temp/audio_story.wav")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                f.write(audio2)
                return f.name
        except websocket._exceptions.WebSocketConnectionClosedException as e:
            if attempt < max_retries - 1:
                print(
                    f"WebSocket connection closed. Retrying attempt {attempt + 1}/{max_retries}...")
                time.sleep(1)  # Wait before retrying
            else:
                raise e  # If retries exhausted, raise the exception


def update_audio_content1():
    text = user_chatbot.value
    if text.strip():
        audio_file = tts_speech_synthesis(text)
        answer_audio.value = open(audio_file, "rb").read()


def generate_images1(story_content, state):
    image_urls = answer_image_gen_click(story_content)
    save_dir = "temp_images"
    os.makedirs(save_dir, exist_ok=True)

    image_paths = []
    for url in image_urls:
        if url != "No URL found in the response.":
            img_path = download_image(url, save_dir)
            print(img_path)
            if img_path:
                image_paths.append(img_path)
            else:
                image_paths.append(None)
        else:
            image_paths.append(None)
    print(image_paths)
    print(state)
    state['answer_images'] = image_paths  # 将图片路径存储到 state 中
    print(state['answer_images'])

    return tuple(image_paths)


def answer_video_gen_click(state):
    answer_story = state['answer_story']
    print(answer_story)
    audio_path = tts_speech_synthesis(answer_story, out_path='temp/audio_story.wav')
    image_files = state['answer_images']
    print(image_files)
    output_path = generate_gradient_video(image_files, audio_path, output_path='temp/video_story.mp4')
    return output_path

def answer_image_gen_click(chatbot):
    text_story_content = chatbot[-1][-1]
    # 格式化提示信息
    prompt = ("你是一位语言大师，精通中文和英文，擅长根据中文故事内容，拆解并总结出故事的主要情节，并用4句话英文来描述。\n"
              "故事内容：{}\n"
              "要求：\n"
              "1.输出4句完整英文的场景描述即可，优美，适合儿童观看理解。\n"
              "2.每句话都要简短，15个单词左右。\n"
              "3.每句话之间换行分隔。")

    # 获取场景描述
    response = chat_completion(prompt.format(text_story_content))

    # 将返回的描述按行分割，得到四句场景描述
    lines = response.split('\n')

    # 检查是否有至少四句描述
    if len(lines) < 2:
        # 如果不足四句，使用空字符串补齐
        lines += [""] * (2 - len(lines))

    # 分别存储每句描述到不同的变量
    text1, text2 = lines[0], lines[1]

    # 生成图像
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "Bearer sk-kqlavbqxkdeucapczvzjafeqoonaevxidspwenypcrjyflfb"
    }

    payloads = [{
        "prompt": text1,
        "image_size": "1024x1024",
        "batch_size": 1,
        "num_inference_steps": 20,
        "guidance_scale": 7.5
    }, {
        "prompt": text2,
        "image_size": "1024x1024",
        "batch_size": 1,
        "num_inference_steps": 20,
        "guidance_scale": 7.5
    }]

    image_urls = []

    for payload in payloads:
        response = requests.post(url, json=payload, headers=headers)
        response_data = json.loads(response.text)
        urls = response_data.get("images", [])
        if urls:
            image_urls.append(urls[0].get("url"))
        else:
            image_urls.append("No URL found in the response.")

    return (image_urls[0], image_urls[1])


# 创建 Gradio 界面
theme = gr.Theme.load('assets/theme.json')
with gr.Blocks(css="assets/app.css", theme=theme) as demo:
    state = gr.State({'session_seed': uid})
    demo.load(init_game, inputs=[state], outputs=[state])
    warning_html_code = """
        <div class="hint" style="background-color: rgba(255, 255, 0, 0.15); padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid #ffcc00;">
            <p>\N{fire} Powered by <a href="https://github.com/PaddlePaddle/ERNIE-Bot-SDK/">ErnieBot and ErnieBot Agent</a>\N{fire}</p>
        </div>
        """
    gr.HTML(warning_html_code)
    welcome_tab = gr.Tab('游戏介绍')
    with welcome_tab:
        user_chat_bot_cover = gr.HTML(format_welcome_html())
        with gr.Row():
            topic = gr.Dropdown(
                choices=["天文主题", "动物主题", "古生物主题", "海洋主题", "生命主题", "植物主题", "航空主题"],
                # 创建下拉菜单选择主题
                value=None,
                label="📖 探索主题",
                interactive=True,
                allow_custom_value=True)
            start_button = gr.Button(value='🚀登陆星球🚀', variant='primary')

    main_tab = gr.Tab('应用主界面', visible=False)
    with main_tab:
        with gr.Row():
            with gr.Column():
                gr.HTML(format_story_html2())
                with gr.Tabs() as tabs:
                    # 开始第1个模块
                    story_tab = gr.Tab(label="睡前小故事", id=1)
                    with story_tab:
                        with gr.Row():
                            with gr.Column():
                                text_story_title = gr.Textbox(lines=5, label='一句话生成故事')
                                story_submit = gr.Button("开始故事创作", variant='primary')
                                with gr.Row():
                                    audio_submit = gr.Button("生成语音", variant='primary')
                                    image_submit = gr.Button("生成剧照", variant='primary')
                            with gr.Column():
                                with gr.Accordion("不知道怎么写？看看大家都在关注啥", open=True):
                                    with gr.Row():
                                        text_more_story_title1 = gr.Textbox(placeholder='问题1', lines=1, label='问题',
                                                                            scale=5, show_label=False)
                                        choose_story1 = gr.Button("采纳", scale=1, variant='primary', min_width=1)
                                    with gr.Row():
                                        text_more_story_title2 = gr.Textbox(placeholder='问题2', lines=1, label='问题',
                                                                            scale=5, show_label=False)
                                        choose_story2 = gr.Button("采纳", scale=1, variant='primary', min_width=1)
                                    with gr.Row():
                                        text_more_story_title3 = gr.Textbox(placeholder='问题3', lines=1,
                                                                            show_label=False, label='问题', scale=5)
                                        choose_story3 = gr.Button("采纳", scale=1, variant='primary', min_width=1)

                                    story_more = gr.Button("故事主题")
                        with gr.Row():
                            with gr.Column(scale=1):
                                text_story_content = gr.Textbox(lines=6, label='故事内容')
                            with gr.Column(scale=1):
                                audio_story_content = gr.Audio(label="故事音频", autoplay=True)
                        with gr.Row():
                            image0 = gr.Image(label="照片1",
                                              type="filepath",  # 输出类型也是图像
                                              )
                            image1 = gr.Image(label="照片2",
                                              type="filepath",  # 输出类型也是图像
                                              )
                            image2 = gr.Image(label="照片3",
                                              type="filepath",  # 输出类型也是图像
                                              )
                            image3 = gr.Image(label="照片4",
                                              type="filepath",  # 输出类型也是图像
                                              )


                    # 开始第2个模块
                    question_tab = gr.Tab(label="好奇三千问", id=2)
                    with question_tab:
                        with gr.Row():
                            with gr.Column(scale=1):
                                user_chatbot = gr.Chatbot(
                                    value=[[None,
                                            '欢迎来到 快乐星球-好奇三千问，刚刚的故事还过瘾吗，快来和我探索更多未知世界吧！']],
                                    elem_classes="app-chatbot",
                                    avatar_images=[host_avatar, user_avatar],
                                    label="问答探索区",
                                    show_label=True,
                                    bubble_full_width=False, )
                            with gr.Column(scale=1):
                                with gr.Accordion("不知道怎么提问？让AI引导你吧", open=True):
                                    with gr.Row():
                                        with gr.Column(scale=3):
                                            ques_text_1 = gr.Textbox(label='问题1', show_label=False,
                                                                     placeholder='问题1')
                                        with gr.Column(min_width=70, scale=1):
                                            ques_button_1 = gr.Button("采纳", )
                                    with gr.Row():
                                        with gr.Column(scale=3):
                                            ques_text_2 = gr.Textbox(label='问题2', show_label=False,
                                                                     placeholder='问题2')
                                        with gr.Column(min_width=70, scale=1):
                                            ques_button_2 = gr.Button("采纳")
                                    with gr.Row():
                                        with gr.Column(scale=3):
                                            ques_text_3 = gr.Textbox(label='问题3', show_label=False,
                                                                     placeholder='问题3')
                                        with gr.Column(min_width=70, scale=1):
                                            ques_button_3 = gr.Button("采纳")
                                ques_gen_button = gr.Button("帮我生成问题", variant='primary')
                                with gr.Row():
                                    with gr.Column():
                                        user_chat_input = gr.Textbox(
                                            label='问题输入区',
                                            placeholder='你想问我点什么呢？',
                                            show_label=True,
                                            lines=4)
                                with gr.Column():
                                    send_button = gr.Button('📣提问📣', variant='primary', min_width=0)
                        with gr.Row():
                            answer_audio_gen_button = gr.Button("生成音频", variant='primary')
                            answer_image_gen_button = gr.Button("生成照片", variant='primary')
                            answer_video_gen_button = gr.Button("生成视频", variant='primary')
                            # answer_video_gen_button = gr.Button("生成视频", variant='primary')
                        with gr.Row():
                            answer_audio = gr.Audio(label="音频回答", interactive=False, autoplay=True)  # 创建音频播放器组件
                            answer_image0 = gr.Image(label="照片1")  # 创建图片展示组件，用于显示剧照0
                            answer_image1 = gr.Image(label="照片2")  # 创建图片展示组件，用于显示剧照1
                            answer_video = gr.Video(label="故事解说", interactive=False,
                                                    autoplay=True)  # 创建视频播放器组件，用于播放故事解说

                    # 开始第3个模块
                    game_tab = gr.Tab(label="知识大挑战", id=3)
                    with game_tab:
                        problemset = ProblemSetBot(global_topic_value)
                        with gr.Row():
                            with gr.Column():
                                with gr.Tab("AI出题区"):
                                    keywords_text = gr.Textbox(label="今日关键词", lines=5,
                                                               info="点击【生成今日关键词】，看看AI总结的你还满意吗？\n你也可以输入想要出题的知识关键词。\n点击【生成新题目】看看AI给你出了什么题吧！")
                                    generate_keywords_button = gr.Button("生成关键词", variant='primary')
                                    generate_problem_button = gr.Button("生成新题目", variant='primary')

                            with gr.Column():
                                with gr.Tab("答题区"):
                                    with gr.Row():
                                        subject = gr.Textbox(label="科目", value=problemset.subject)
                                        difficulty = gr.Textbox(label="难度", value=problemset.difficulty)
                                    question_markdown = gr.Markdown("## " + problemset.question)
                                    options = ["A." + problemset.choices[0], "B." + problemset.choices[1],
                                               "C." + problemset.choices[2], "D." + problemset.choices[3]]
                                    choices_radio = gr.Radio(options, label="选择你认为正确的一项")

                                    answer_submit_button = gr.Button("✏️ 选好啦，提交答案✏️ ", variant='primary')
                                    answer_result = gr.Textbox(label="答题结果")
                                    save_problem_button = gr.Button("保存本题记录")
                                    with gr.Accordion("查看解析", open=False):
                                        analysis = gr.Textbox(label="解析", lines=3, interactive=False,
                                                              value=problemset.analysis)
                        with gr.Row():
                            with gr.Tab("答题记录"):
                                with gr.Row():
                                    with gr.Column(scale=1):
                                        save_file = gr.File(label="生成的答题记录文件(xslx)")
                                    with gr.Column(scale=2):
                                        questions = gr.Dataframe(headers=problemset.ques_header, interactive=False,
                                                                 row_count=3)
                                        save_record_button = gr.Button("生成答题记录", variant='primary')
                                        clear_record_button = gr.Button("清空答题记录")
                    with gr.Row():
                        return_welcome_button = gr.Button(value="↩️返回首页")
    introduce_tab = gr.Tab('作品介绍')
    with introduce_tab:
        gr.HTML(format_introduce_html())
        with gr.Row():
            return_welcome_button2 = gr.Button(value="↩️返回首页", )

    # 存储所有需要清空的Textbox组件引用
    all_textboxes = [
        text_story_title, text_story_content,
        text_more_story_title1, text_more_story_title2, text_more_story_title3,
        keywords_text, subject, difficulty,
        ques_text_1, ques_text_2, ques_text_3, user_chat_input,
    ]

    start_button.click(main_ui, inputs=[state, topic], outputs=[welcome_tab, main_tab])
    return_welcome_button.click(welcome_ui, inputs=[state, topic], outputs=[welcome_tab, main_tab])
    return_welcome_button2.click(welcome_ui, inputs=[state, topic], outputs=[welcome_tab, main_tab])
    story_submit.click(story_submit_click, inputs=[text_story_title, topic], outputs=[text_story_content])
    # print(global_topic_value.value)
    # update_global_topic(global_topic_value)
    story_more.click(story_more_click, inputs=[topic],
                     outputs=[text_more_story_title1, text_more_story_title2,
                              text_more_story_title3])
    audio_submit.click(tts_speech_synthesis, inputs=[text_story_content],
                       outputs=[audio_story_content])
    image_submit.click(generate_images, inputs=[text_story_content],
                       outputs=[image0, image1, image2, image3])
    choose_story1.click(transfer_text, inputs=[text_more_story_title1], outputs=[text_story_title])
    choose_story2.click(transfer_text, inputs=[text_more_story_title2], outputs=[text_story_title])
    choose_story3.click(transfer_text, inputs=[text_more_story_title3], outputs=[text_story_title])
    generate_keywords_button.click(generate_keywords_click, inputs=[state], outputs=[keywords_text])
    generate_problem_button.click(generate_problem_click, inputs=[keywords_text, state],
                                  outputs=[question_markdown, choices_radio, subject, difficulty,
                                           analysis])
    answer_submit_button.click(answer_submit_click, inputs=[choices_radio, state],
                               outputs=[answer_result])
    save_problem_button.click(save_problem_click, inputs=[state], outputs=[questions])
    save_record_button.click(save_record_click, outputs=[save_file])
    clear_record_button.click(clear_record_click, outputs=[questions])
    ques_gen_button.click(ques_gen_click, inputs=[state, topic],
                          outputs=[ques_text_1, ques_text_2, ques_text_3])
    ques_button_1.click(ques_button_click, inputs=[ques_text_1], outputs=[user_chat_input])
    ques_button_2.click(ques_button_click, inputs=[ques_text_2], outputs=[user_chat_input])
    ques_button_3.click(ques_button_click, inputs=[ques_text_3], outputs=[user_chat_input])
    send_button.click(send_button_click, inputs=[user_chat_input, state, user_chatbot],
                      outputs=[user_chatbot, user_chat_input])
    answer_audio_gen_button.click(tts_speech_synthesis1, inputs=[user_chatbot],
                                  outputs=[answer_audio])
    answer_image_gen_button.click(generate_images1, inputs=[user_chatbot,state],
                                  outputs=[answer_image0, answer_image1])
    answer_video_gen_button.click(answer_video_gen_click, inputs=[state], outputs=[answer_video])
demo.launch(server_name='127.0.0.1', server_port=7861)
