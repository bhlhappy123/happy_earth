import os
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeVideoClip, ImageClip, VideoClip, TextClip, concatenate_videoclips
from moviepy.video.tools.subtitles import SubtitlesClip

cur_dir = os.path.dirname(os.path.abspath(__file__))

def generate_video(image_files, audio_path, output_path):
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration
    clip = ImageSequenceClip(image_files, fps=len(image_files)/duration).set_duration(duration)
    final_clip = CompositeVideoClip([clip], size=clip.size).set_audio(audio_clip)
    final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
    final_clip.close()
    audio_clip.close()

def gradient_function(t, start_color, end_color, duration):
    """根据时间t计算当前帧的颜色"""
    progress = t / duration
    return tuple(start_color[i] + progress * (end_color[i] - start_color[i]) for i in range(3))

def create_gradient_clip(start_color, end_color, duration, size=(512, 512)):
    """根据给定的起始颜色、结束颜色和时长创建渐变ColorClip"""
    def make_frame(t):
        current_color = gradient_function(t, start_color, end_color, duration)
        frame = np.full(size + (3,), current_color, dtype=np.uint8)
        return frame
    return VideoClip(make_frame, duration=duration)

def generate_gradient_video(image_files, audio_path, output_path, trans_dura=0.5):
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration
    num_images = len(image_files)
    dura_per_img = (duration - (num_images - 1) * trans_dura) / num_images
    clips = []
    for i, img_path in enumerate(image_files):
        img_clip = ImageClip(img_path, duration=dura_per_img)
        clips.append(img_clip)
        if i < num_images - 1:
            gradient = create_gradient_clip((0, 0, 0), (255, 255, 255), trans_dura, size=img_clip.size)
            clips.append(gradient)
    for clip in clips:
        print(f"Clip size: {clip.size}")  # 添加调试输出，检查每个剪辑的尺寸
    final_clip = concatenate_videoclips(clips).set_audio(audio_clip)
    final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=25)
    final_clip.close()
    audio_clip.close()
    return output_path

if __name__ == '__main__':
    audio_path = os.path.join(cur_dir, '../temp/audio_answer.wav')
    image_files = ['../temp/answer_image0.jpg', '../temp/answer_image1.jpg', '../temp/answer_image2.jpg', '../temp/answer_image3.jpg']
    image_files = [os.path.join(cur_dir, img_path) for img_path in image_files]
    # import sys
    # sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # from utils.speech_client import asr_damo_api
    # srt =  asr_damo_api(audio_path)
    # with open(audio_path.replace('.wav', '.srt'), 'w', encoding='utf-8') as f:
    #     f.write(srt)
    # generate_gradient_video(image_files, audio_path, 'output.mp4', subtitles=audio_path.replace('.wav', '.srt'))
    


