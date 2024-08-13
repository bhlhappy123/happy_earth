import base64
import requests
import numpy as np
from datetime import timedelta

url = "http://10.18.32.170:8000"
def convert_pcm_to_float(data):
    if data.dtype == np.float64:
        return data
    elif data.dtype == np.float32:
        return data.astype(np.float64)
    elif data.dtype == np.int16:
        bit_depth = 16
    elif data.dtype == np.int32:
        bit_depth = 32
    elif data.dtype == np.int8:
        bit_depth = 8
    else:
        raise ValueError("Unsupported audio data type")
    # Now handle the integer types
    max_int_value = float(2 ** (bit_depth - 1))
    if bit_depth == 8:
        data = data - 128
    return (data.astype(np.float64) / max_int_value)
    
def tts_damo_api(text, voice='zhitian_emo', out_path="output.wav"):
    headers = {'Content-Type': 'application/json'}
    data = {"text": text, "voice": voice}
    response = requests.post(url+"/tts", headers=headers, json=data)
    wav = base64.b64decode(response.json()["wav"]) # 解码成二进制
    with open(out_path, "wb") as f:
        f.write(wav)
    return out_path

def asr_damo_api(wav_path, time_stamp=1, srt=True):
    headers = {'Content-Type': 'application/json'}
    with open(wav_path, "rb") as f:
        wav = base64.b64encode(f.read()).decode()
    data = {"wav": wav, "time_stamp": time_stamp}
    response = requests.post(url+"/asr", headers=headers, json=data)
    res = response.json()['res']
    if srt:
        res = generate_srt(res)
    return res

def generate_srt(texts):
    srt_content = ''
    for index, text_item in enumerate(texts):
        # SRT文件的索引从1开始
        srt_index = index + 1
        # 格式化时间戳
        text = text_item['text']
        start = text_item['start']
        end = text_item['end']
        start_time = "%s,%03d" % (timedelta(seconds=start//1000), start % 1000 )
        end_time = "%s,%03d" % (timedelta(seconds=end//1000), end % 1000 )
        time_str = f"{start_time} --> {end_time}"
        # 将字幕合并为一个字符串，并用逗号分隔
        # 构建SRT条目
        srt_entry = f"{srt_index}\n{time_str}\n{text}\n\n"
        srt_content += srt_entry
    return srt_content

if __name__ == '__main__':
    # answer = "今天天气真好。\n你好，我是机器人。"
    # tts_damo_api(answer)
    texts = asr_damo_api("temp/audio_answer.wav")
    generate_srt(texts)