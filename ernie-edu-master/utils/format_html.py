import base64  # 导入base64模块，用于编码和解码base64数据


"""
这个程序主要包含两个部分：

将图像文件转换为base64编码：通过读取图像文件的二进制内容，并将其转换为base64编码，生成可以直接在HTML中使用的base64 URL。
生成HTML内容：定义了两个函数，分别用于生成欢迎页面和故事页面的HTML内容。这些函数利用预定义的配置信息和base64编码的图像，
                            生成结构化的HTML代码，用于展示信息。
"""
# 定义一个函数，用于将图像文件转换为base64编码
def covert_image_to_base64(image_path):
    # 获取文件的后缀名
    ext = image_path.split(".")[-1]
    if ext not in ["gif", "jpeg", "png"]:
        ext = "jpeg"  # 如果后缀名不在指定列表中，则默认使用jpeg
    with open(image_path, "rb") as image_file:
        # 读取图像文件的二进制内容
        encoded_string = base64.b64encode(image_file.read())
        # 将字节数据转换为字符串
        base64_data = encoded_string.decode("utf-8")
        # 生成base64编码的地址
        base64_url = f"data:image/{ext};base64,{base64_data}"
        return base64_url  # 返回base64编码的URL

# 定义一个函数，用于生成欢迎页面的HTML内容
def format_welcome_html():
    # 配置参数
    config = {
        'name': "快乐星球",  # 名称
        'description': '\N{fire}欢迎登陆快乐星球，这里有一群由多个大模型驱动的智能体，快来探索你的好奇心吧\N{fire}',  # 描述
        'introduction_label': "<br>使用说明",  # 说明标签
        'rule_label': "<br>选择主题",  # 规则标签
        'intro1': '睡前小故事：一句话生成故事，剧照，视频，激发好奇心',  # 介绍1
        'intro2': '好奇三千问：基于故事的智能问答，让小盆友对提问上瘾',  # 介绍2
        'intro3': '知识大挑战：基于本次互动的游戏问答，让小盆友玩中学',  # 介绍3
        'rule1': '选择你喜欢的主题，准备开始吧！😊',  # 规则1
    }
    # 将图像文件转换为base64编码
    image_src = covert_image_to_base64('assets/logo.png')
    # 返回HTML内容
    return f"""
        <div class="bot_cover" ,background-image: #000000;">
            <div class="bot_avatar">
                <img src={image_src} />
            </div>
            <div class="bot_name">{config.get("name")}</div>
            <div class="bot_desc">{config.get("description")}</div>
            <div class="bot_intro_label">{config.get("introduction_label")}</div>
            <div class="bot_intro_ctx">
                <ul>
                    <li>{config.get("intro1")}</li>
                    <li>{config.get("intro2")}</li>
                    <li>{config.get("intro3")}</li>
                </ul>
            </div>
            <div class="bot_intro_label">{config.get("rule_label")}</div>
            <div class="bot_intro_ctx">
                <ul>
                    <li>{config.get("rule1")}</li>
                </ul>
            </div>
        </div>
        """

# 定义一个函数，用于生成故事页面的HTML内容
def format_story_html2():
    # 将图像文件转换为base64编码
    image_src = covert_image_to_base64('assets/logo.png')
    return f"""
    <div style='color:#FF8800;font-size:25px;text-align:center;font-weight:bold;'>欢 迎 登 陆 快 乐 星 球 主 题 乐 园 ^_^</div>
    """

def format_introduce_html():
    return f"""
<iframe src='https://g5b4uupmby.feishu.cn/wiki/F3REwiI46iSOa0kGFfecPN3jnxc' style='width:100%;height:800px;'></iframe>"""