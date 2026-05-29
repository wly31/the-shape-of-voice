from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
import base64
import cv2
import numpy as np
import os
import json
from django.shortcuts import render
from .gesture_model import GestureRecognizer
from sign_Project.settings import BASE_DIR
import jieba
import re
from datetime import datetime
from django.conf import settings
import tempfile
from PIL import Image
import subprocess
import shutil
from .models import SignHistory, ActivityLog
from django.views.decorators.http import require_GET
import torch
from torchvision import transforms
import mediapipe as mp
from .CNN_LSTM import FeatureExtractor, MultiModalCNNTransformerModel
from typing import Optional, List
import random
import difflib  # 恢复 difflib 导入，为英文逻辑服务
from django.db.models import Count
from django.db.models.functions import TruncDate

# 连续手语识别模型全局变量 (保持不变)
continuous_model = None
continuous_feature_extractor = None
continuous_label_map = None
continuous_mp_hands = None


def load_continuous_model():
    """加载连续手语识别模型 (保持不变)"""
    global continuous_model, continuous_feature_extractor, continuous_label_map, continuous_mp_hands
    if continuous_model is None:
        try:
            model_path = os.path.join(BASE_DIR, 'ctcn_2', 'models', 'best_model.pth')
            checkpoint = torch.load(model_path, map_location=torch.device('cpu'))
            continuous_feature_extractor = FeatureExtractor(model_name='resnet18')
            continuous_feature_extractor.eval()
            continuous_model = MultiModalCNNTransformerModel(
                feature_dim=638,
                num_classes=len(checkpoint['index_to_label']),
                heads=2
            )
            continuous_model.load_state_dict(checkpoint['model_state_dict'])
            continuous_model.eval()
            continuous_label_map = {int(k): v for k, v in checkpoint['index_to_label'].items()}
            continuous_mp_hands = mp.solutions.hands.Hands(
                static_image_mode=True,
                max_num_hands=2
            )
            print("连续手语识别模型加载成功")
        except Exception as e:
            print(f"加载连续手语识别模型失败: {str(e)}")


load_continuous_model()


# ... (preprocess_frame, extract_keypoints 函数保持不变) ...
def preprocess_frame(frame):
    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(frame_rgb)
    return transform(pil_image)


def extract_keypoints(frame, mp_hands):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    hands_results = mp_hands.process(frame_rgb)
    keypoints = np.zeros(126, dtype=np.float32)
    if hands_results.multi_hand_landmarks:
        hands = hands_results.multi_hand_landmarks[:2]
        for hand_idx, hand in enumerate(hands):
            start = hand_idx * 63
            for lm_idx, landmark in enumerate(hand.landmark[:21]):
                pos = start + lm_idx * 3
                if pos + 2 < 126:
                    keypoints[pos] = landmark.x
                    keypoints[pos + 1] = landmark.y
                    keypoints[pos + 2] = landmark.z
    return torch.tensor(keypoints, dtype=torch.float32)


CONTINUOUS_SEQ_LEN = 170
LOW_CONFIDENCE_THRESHOLD = 0.40
# 上传视频分段识别：每段约 25 帧采样（≈2.5s@30fps、每3帧取1），步长 12 帧
VIDEO_SEGMENT_WINDOW = 25
VIDEO_SEGMENT_STRIDE = 12
VIDEO_SEGMENT_MIN_TOTAL = 18


def pad_sequence_features(combined_features, target_len=CONTINUOUS_SEQ_LEN):
    """帧数不足时重复真实帧填充，避免大量零帧导致乱猜。"""
    seq_len = combined_features.shape[1]
    if seq_len >= target_len:
        return combined_features[:, :target_len]
    if seq_len == 0:
        return combined_features
    reps = (target_len + seq_len - 1) // seq_len
    return combined_features.repeat(1, reps, 1)[:, :target_len]


def predict_continuous_sign(frames_tensor, keypoints_tensor):
    """对已预处理的帧序列运行 ctcn_2，返回标签与置信度信息。"""
    with torch.no_grad():
        visual_features = continuous_feature_extractor(
            frames_tensor.view(-1, 3, 256, 256)
        ).view(1, -1, 512)
        combined_features = torch.cat([visual_features, keypoints_tensor.unsqueeze(0)], dim=2)
        combined_features = pad_sequence_features(combined_features)
        outputs = continuous_model(combined_features)
        probs = torch.softmax(outputs, dim=1)
    confidence = probs[0].max().item()
    pred_idx = int(probs[0].argmax().item())
    label = continuous_label_map.get(pred_idx, '未知标签')
    topk = torch.topk(probs, k=min(3, probs.shape[1]), dim=1)
    top3 = [
        {
            'word': continuous_label_map.get(int(idx), '未知'),
            'confidence': f'{probs[0][idx].item():.2%}',
        }
        for idx in topk.indices[0]
    ]
    margin = (
        probs[0][topk.indices[0][0]].item() - probs[0][topk.indices[0][1]].item()
        if probs.shape[1] > 1 else confidence
    )
    frame_count = int(frames_tensor.shape[0])
    low_confidence = confidence < LOW_CONFIDENCE_THRESHOLD or margin < 0.08
    warning_parts = []
    if frame_count < 10:
        warning_parts.append(
            f'当前仅 {frame_count} 张采样帧。模型按约 {CONTINUOUS_SEQ_LEN} 帧连续动作训练，'
            '建议上传 3–15 秒、含完整手势的 MP4，或到「连续手语翻译」页用摄像头实时识别。'
        )
    if low_confidence:
        warning_parts.append(
            '置信度偏低，结果不可靠。该手势可能不在模型词表内'
            '（仅支持 100 个抽象词，如：情况、发展、民主、意义；不含你好、吃饭、我爱你等）。'
        )
    return {
        'result': label,
        'confidence': f'{confidence:.2%}',
        'top3': top3,
        'frame_count': frame_count,
        'low_confidence': low_confidence,
        'warning': ' '.join(warning_parts),
    }


def predict_continuous_sign_from_video(frames_tensor, keypoints_tensor):
    """长视频滑动窗口分段识别；短于阈值时整段识别一次。"""
    n = int(frames_tensor.shape[0])
    if n < VIDEO_SEGMENT_MIN_TOTAL:
        pred = predict_continuous_sign(frames_tensor, keypoints_tensor)
        pred['mode'] = 'single'
        pred['segments'] = []
        return pred

    raw_segments = []
    start = 0
    while start < n:
        end = min(start + VIDEO_SEGMENT_WINDOW, n)
        chunk_len = end - start
        if chunk_len < 10:
            break
        chunk_f = frames_tensor[start:end]
        chunk_k = keypoints_tensor[start:end]
        seg_pred = predict_continuous_sign(chunk_f, chunk_k)
        if not seg_pred['low_confidence']:
            raw_segments.append({
                'word': seg_pred['result'],
                'confidence': seg_pred['confidence'],
                'start_frame': start,
                'end_frame': end - 1,
                'frame_count': chunk_len,
                'top3': seg_pred['top3'],
            })
        start += VIDEO_SEGMENT_STRIDE

    merged = []
    for seg in raw_segments:
        if merged and merged[-1]['word'] == seg['word']:
            merged[-1]['end_frame'] = seg['end_frame']
            continue
        merged.append(seg)

    if not merged:
        pred = predict_continuous_sign(frames_tensor, keypoints_tensor)
        pred['mode'] = 'single'
        pred['segments'] = []
        pred['warning'] = (pred.get('warning') or '') + ' 分段置信度均偏低，已改为整段识别。'
        return pred

    text = ''.join(s['word'] for s in merged)
    warning_parts = [
        f'已对 {n} 帧采样做滑动窗口连续识别（每段约 {VIDEO_SEGMENT_WINDOW} 帧）。'
        '词表仅含 100 个抽象词，分段结果仅供参考。'
    ]
    if n < 30:
        warning_parts.insert(
            0,
            '视频较短，分段数有限；建议 5–15 秒、每个手势停顿半秒左右效果更好。',
        )
    return {
        'mode': 'segments',
        'result': text,
        'segments': merged,
        'confidence': merged[0]['confidence'],
        'top3': merged[0].get('top3', []),
        'frame_count': n,
        'low_confidence': False,
        'warning': ' '.join(warning_parts),
    }


# --- 手语视频生成工具 ---

SIGN_OUTPUT_DIR = os.path.join(settings.BASE_DIR, 'static', 'sign_app', 'output')


def ensure_sign_output_dir():
    os.makedirs(SIGN_OUTPUT_DIR, exist_ok=True)


def get_ffmpeg_executable():
    """系统 PATH 中的 ffmpeg，或 imageio-ffmpeg 自带的二进制。"""
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg:
        return ffmpeg
    try:
        import imageio_ffmpeg
        bundled = imageio_ffmpeg.get_ffmpeg_exe()
        if bundled and os.path.isfile(bundled):
            return bundled
    except ImportError:
        pass
    return None


def convert_mp4_to_h264(input_path, output_path):
    """转为浏览器可播放的 H.264（yuv420p）。"""
    ffmpeg = get_ffmpeg_executable()
    if not ffmpeg:
        print('未找到 ffmpeg，保留原始 mp4v 文件（浏览器可能无法播放）')
        if os.path.abspath(input_path) != os.path.abspath(output_path):
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(input_path, output_path)
        return output_path

    cmd = [
        ffmpeg, '-y', '-i', input_path,
        '-vcodec', 'libx264', '-pix_fmt', 'yuv420p', '-an',
        output_path,
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if os.path.exists(input_path):
            os.remove(input_path)
        return output_path
    except (subprocess.CalledProcessError, OSError) as e:
        print(f'FFmpeg转码失败: {e}')
        if os.path.exists(output_path):
            os.remove(output_path)
        if os.path.abspath(input_path) != os.path.abspath(output_path):
            os.rename(input_path, output_path)
        return output_path


# --- 英文处理逻辑 (恢复) ---

def find_similar_word(word, word_list, cutoff=0.8):
    """查找相似词 (为英文逻辑服务)"""
    matches = difflib.get_close_matches(word, word_list, n=1, cutoff=cutoff)
    return matches[0] if matches else None


def get_sign_file_en(word, word_list, base_dir=None):
    """英文：优先查找mp4，没有则查png，再没有查每个字母的png"""
    if base_dir is None:
        base_dir = os.path.join(settings.BASE_DIR, 'static', 'sign_app', 'words')
    if word in [',', '.', '!', '?', ';', ' ']:
        return None
    # 优先查找单词.mp4
    mp4_file = os.path.join(base_dir, f'{word}.mp4')
    if os.path.exists(mp4_file):
        return mp4_file
    # 查找相似词.mp4
    similar_word = find_similar_word(word, word_list)
    if similar_word:
        mp4_file = os.path.join(base_dir, f'{similar_word}.mp4')
        if os.path.exists(mp4_file):
            return mp4_file
    # 查找单词.png
    png_file = os.path.join(base_dir, f'{word}.png')
    if os.path.exists(png_file):
        return [png_file]
    # 查找相似词.png
    if similar_word:
        png_file = os.path.join(base_dir, f'{similar_word}.png')
        if os.path.exists(png_file):
            return [png_file]
    # 查找每个字母.png
    letter_dir = os.path.join(settings.BASE_DIR, 'static', 'sign_app', 'alphabet')
    letter_files = []
    for letter in word:
        letter_file = os.path.join(letter_dir, f'{letter.lower()}.png')
        if os.path.exists(letter_file):
            letter_files.append(letter_file)
    return letter_files if letter_files else None


def create_sign_language_sequence_en(words, word_list):
    """英文：支持mp4和png混合合成，输出为mp4格式"""
    ensure_sign_output_dir()
    output_dir = SIGN_OUTPUT_DIR

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    temp_output_filename = f"temp_sign_language_{timestamp}.mp4"
    temp_video_path = os.path.join(output_dir, temp_output_filename)

    width, height = 640, 480
    fps = 24
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video_path, fourcc, fps, (width, height))

    final_output_filename = f"sign_language_{timestamp}_h264.mp4"
    final_video_path = os.path.join(output_dir, final_output_filename)

    black_frame = np.zeros((height, width, 3), dtype=np.uint8)

    try:
        for word in words:
            sign_file = get_sign_file_en(word, word_list)
            if isinstance(sign_file, str) and sign_file.endswith('.mp4'):
                cap = cv2.VideoCapture(sign_file)
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret: break
                    out.write(cv2.resize(frame, (width, height)))
                cap.release()
            elif isinstance(sign_file, list) and sign_file:
                for image_path in sign_file:
                    img = load_image_bgr(image_path)
                    if img is None:
                        for _ in range(fps): out.write(black_frame)
                        continue
                    resized_img = cv2.resize(img, (width, height))
                    for _ in range(fps): out.write(resized_img)
            else:
                for _ in range(fps): out.write(black_frame)
    except Exception as e:
        print(f"生成英文视频出错: {e}")
        out.release()
        return None
    finally:
        out.release()

    try:
        if not os.path.exists(temp_video_path) or os.path.getsize(temp_video_path) == 0:
            return None
        convert_mp4_to_h264(temp_video_path, final_video_path)
        return final_video_path
    except Exception as e:
        print(f"FFmpeg 转码失败: {e}")
        return None


def load_image_bgr(image_path):
    """读取图片为 BGR；兼容中文路径与特殊 PNG。"""
    img = cv2.imread(image_path)
    if img is not None:
        return img
    try:
        with open(image_path, 'rb') as f:
            data = np.frombuffer(f.read(), dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if img is not None:
            return img
    except OSError:
        pass
    try:
        pil_img = Image.open(image_path).convert('RGB')
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception:
        return None


def create_sign_language_video_zh(text):
    """中文复杂句：分词 + 词表匹配，合成手语示意视频。"""
    from .sign_lexicon import analyze_sentence, paths_for_token

    words_dir = os.path.join(settings.BASE_DIR, 'static', 'sign_app', 'words-zhcn')
    if not os.path.isdir(words_dir):
        print(f'中文手语资源目录不存在: {words_dir}')
        return None, [], []

    compose_tokens, segments = analyze_sentence(text)
    missing = [s['word'] for s in segments if s.get('status') == 'missing']

    ensure_sign_output_dir()
    width, height, fps = 640, 480, 30
    image_duration = 1.0
    punct_pause = 0.35
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    temp_video_path = os.path.join(SIGN_OUTPUT_DIR, f'temp_sign_language_zh_{timestamp}.mp4')
    final_video_path = os.path.join(SIGN_OUTPUT_DIR, f'sign_language_zh_{timestamp}_h264.mp4')

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video_path, fourcc, fps, (width, height))
    if not out.isOpened():
        print('无法创建视频写入器')
        return None, segments, missing

    black_frame = np.zeros((height, width, 3), dtype=np.uint8)
    frames_written = 0

    for token in compose_tokens:
        if token in '，。！？；、':
            for _ in range(int(fps * punct_pause)):
                out.write(black_frame)
            continue
        for image_path in paths_for_token(token):
            img = load_image_bgr(image_path)
            if img is None:
                print(f'读取图片失败: {image_path}')
                continue
            resized_img = cv2.resize(img, (width, height))
            for _ in range(int(fps * image_duration)):
                out.write(resized_img)
                frames_written += 1
            for _ in range(int(fps * 0.15)):
                out.write(black_frame)

    out.release()
    if frames_written == 0:
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        return None, segments, missing

    convert_mp4_to_h264(temp_video_path, final_video_path)
    return final_video_path, segments, missing


def tokenize_text(text, lang='en'):
    """根据语言分词"""
    if lang == 'zh':
        tokens = []
        for fragment in re.split(r'([，。！？；])', text):
            if fragment and fragment in '，。！？；':
                tokens.append(fragment)
            elif fragment:
                tokens.extend(jieba.lcut(fragment))
        return [token for token in tokens if token.strip()]
    else:
        return re.findall(r"[\w']+|[.,!?;]", text.lower())


# --- 核心视图函数 (修改点) ---
@csrf_exempt
def generate_animation(request):
    """根据语言分流处理动画生成请求"""
    if request.method == 'POST':
        try:
            text = request.POST.get('text', '').strip()
            lang = request.POST.get('lang', 'en').strip()
            if not text:
                return JsonResponse({'error': '请输入要翻译的文本'}, status=400)

            output_video = None
            segments = []
            missing_words = []
            if lang == 'zh':
                output_video, segments, missing_words = create_sign_language_video_zh(text)
                if not output_video:
                    miss_hint = '、'.join(missing_words[:8]) if missing_words else ''
                    return JsonResponse({
                        'error': '无法生成手语视频：句中词汇暂无手语图'
                        + (f'（如：{miss_hint}）' if miss_hint else '')
                        + '。请改用词库内常用词，如：你好、我想今天去吃饭、谢谢',
                        'segments': segments,
                        'missing': missing_words,
                    }, status=400)
            else:
                words_dir_en = os.path.join(settings.BASE_DIR, 'static', 'sign_app', 'words')
                if not os.path.isdir(words_dir_en):
                    return JsonResponse({'error': '英文手语资源目录缺失'}, status=500)
                word_list_en = [
                    os.path.splitext(f)[0]
                    for f in os.listdir(words_dir_en)
                    if f.endswith(('.mp4', '.png'))
                ]
                words = tokenize_text(text, 'en')
                if not words:
                    return JsonResponse({'error': '分词结果为空，请输入英文单词或句子'}, status=400)
                output_video = create_sign_language_sequence_en(words, word_list_en)

            if output_video and os.path.exists(output_video):
                video_filename = os.path.basename(output_video)
                ts = int(datetime.now().timestamp())
                video_url = f"{settings.STATIC_URL}sign_app/output/{video_filename}?t={ts}"

                # 保存历史和日志
                SignHistory.objects.create(text=text, video_file=video_url, lang=lang)
                ActivityLog.objects.create(
                    activity_type='ANIMATION_GENERATION',
                    lang=lang,
                    details={'text': text, 'video_url': video_url}
                )
                payload = {'video_url': video_url}
                if lang == 'zh':
                    payload['segments'] = segments
                    payload['missing'] = missing_words
                    if missing_words:
                        payload['hint'] = (
                            f'已生成视频；以下词暂无手语图已跳过：{"、".join(missing_words[:10])}'
                        )
                return JsonResponse(payload)
            else:
                return JsonResponse({'error': '无法生成手语动画'}, status=500)
        except Exception as e:
            print(f"生成动画时发生严重错误: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': f'服务器内部错误: {e}'}, status=500)

    return JsonResponse({'error': '无效的请求方法'}, status=400)


# ... (其余所有视图函数和代码保持不变) ...

'''下面为手语翻译的代码'''
# 手势类别字典
classes_dict = {
    'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7, 'I': 8,
    'J': 9, 'K': 10, 'L': 11, 'M': 12, 'N': 13, 'O': 14, 'P': 15, 'Q': 16,
    'R': 17, 'S': 18, 'T': 19, 'U': 20, 'V': 21, 'W': 22, 'X': 23, 'Y': 24, 'Z': 25
}

# 加载手势详细信息
gesture_info_path = os.path.join(BASE_DIR, 'model', 'gesture_labels.json')
try:
    with open(gesture_info_path, 'r', encoding='utf-8') as f:
        gesture_info_by_index = json.load(f)
    gesture_info = {info['symbol']: {'name': info['name'], 'description': info['description']}
                    for _, info in gesture_info_by_index.items()}
    gesture_info['None'] = {'name': '未检测到手势', 'description': '请确保手在摄像头范围内'}
except Exception as e:
    print(f"加载手势信息文件时出错: {e}")
    gesture_info = {letter: {'name': f'字母 {letter}', 'description': f'这是字母 {letter} 的手势'}
                    for letter in classes_dict}
    gesture_info['None'] = {'name': '未检测到手势', 'description': '请确保手在摄像头范围内'}

# 初始化手势识别器
model_path = os.path.join(os.path.dirname(__file__), '../model/CNN_model_alphabet_SIBI.pth')
recognizer = GestureRecognizer(model_path, classes_dict)


def realtime_view(request):
    return render(request, 'sign_app/realtime.html')


def touch_demo_view(request):
    return render(request, 'sign_app/touch_demo.html')


@csrf_exempt
def get_gesture_info(request):
    return JsonResponse(gesture_info)


def _decode_post_image(request):
    images, err = _decode_post_images(request)
    if err:
        return None, err
    return images[0], None


def _decode_post_images(request):
    """支持单张 image 或多张 image（多帧投票）。"""
    raw_list = request.POST.getlist('image')
    if not raw_list:
        single = request.POST.get('image')
        if single:
            raw_list = [single]
    if not raw_list:
        return [], '未提供图像数据'
    frames = []
    for data in raw_list:
        if 'base64,' in data:
            data = data.split('base64,')[1]
        nparr = np.frombuffer(base64.b64decode(data), np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is not None:
            frames.append(image)
    if not frames:
        return [], '无法解析图像'
    return frames, None


@require_GET
def get_vocab_words(request):
    """返回词库可识别中文词列表（供摄像头页展示）。"""
    from .sign_lexicon import list_vocab_recognition_words, warm_vocab_sketch_cache

    warm_vocab_sketch_cache()
    words = list_vocab_recognition_words()
    return JsonResponse({
        'count': len(words),
        'words': words,
        'hint': (
            '摄像头词库模式：5 帧投票；建议对照 words-zhcn 文件夹里的原图摆拍。'
            '更准请用手语图片识别页上传截图。'
        ),
    })


@csrf_exempt
def recognize_gesture_vocab(request):
    """摄像头帧与 words-zhcn 词库比对（不重训模型）。"""
    if request.method != 'POST':
        return JsonResponse({'error': '无效的请求方法'}, status=400)
    try:
        from .sign_lexicon import recognize_camera_frames_via_vocabulary, warm_vocab_sketch_cache

        images, err = _decode_post_images(request)
        if err:
            return JsonResponse({'error': err}, status=400)
        warm_vocab_sketch_cache()
        payload = recognize_camera_frames_via_vocabulary(images)
        if payload.get('matched'):
            ActivityLog.objects.create(
                activity_type='REALTIME_RECOGNITION',
                lang='zh',
                details={
                    'mode': 'vocab',
                    'word': payload.get('word'),
                    'stem': payload.get('stem'),
                    'confidence': payload.get('confidence'),
                    'uncertain': payload.get('uncertain'),
                },
            )
        return JsonResponse(payload)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def recognize_gesture(request):
    if request.method == 'POST':
        try:
            image, err = _decode_post_image(request)
            if err:
                return JsonResponse({'error': err}, status=400)
            gesture_symbol, confidence, bbox = recognizer.recognize_gesture(image)
            response_data = {}
            if gesture_symbol is None:
                info = gesture_info['None']
                response_data = {'gesture': 'None', 'name': info['name'], 'description': info['description'],
                                 'confidence': 0.0}
            else:
                info = gesture_info.get(gesture_symbol,
                                        {'name': gesture_symbol, 'description': f'手势 {gesture_symbol}'})
                response_data = {'gesture': gesture_symbol, 'name': info['name'], 'description': info['description'],
                                 'confidence': confidence, 'bbox': bbox}
                ActivityLog.objects.create(activity_type='REALTIME_RECOGNITION', lang='en',
                                           details={'gesture': gesture_symbol, 'confidence': confidence})
            return JsonResponse(response_data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': '无效的请求方法'}, status=400)


def continuous_view(request): return render(request, 'sign_app/continuous.html')


def animation_view(request): return render(request, 'sign_app/animation.html')


def technology_view(request): return render(request, 'sign_app/technology.html')


def about_view(request): return render(request, 'sign_app/about.html')


@require_GET
def get_animation_history(request):
    records = SignHistory.objects.order_by('-created_at')[:10]
    data = [{'text': r.text, 'video_file': r.video_file, 'lang': r.lang,
             'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S')} for r in records]
    return JsonResponse({'history': data})


@csrf_exempt
def clear_history(request):
    if request.method == 'POST':
        SignHistory.objects.all().delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid method'})


def image_recognition_view(request): return render(request, 'sign_app/image_recognition.html')


def video_recognition_view(request): return render(request, 'sign_app/video_recognition.html')


@csrf_exempt
def handle_video_recognition(request):
    if request.method == 'POST':
        load_continuous_model()
        if 'video' not in request.FILES: return JsonResponse({'error': '未上传视频文件'}, status=400)
        video_file = request.FILES['video']
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            for chunk in video_file.chunks(): tmp_file.write(chunk)
            tmp_file_path = tmp_file.name
        try:
            cap, frames, keypoints_list, frame_count, sample_rate = cv2.VideoCapture(tmp_file_path), [], [], 0, 3
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: break
                frame_count += 1
                if frame_count % sample_rate != 0: continue
                frames.append(preprocess_frame(frame))
                keypoints_list.append(extract_keypoints(frame, continuous_mp_hands))
            cap.release()
            if not frames: return JsonResponse({'error': '未检测到有效视频帧'}, status=400)
            frames_tensor, keypoints_tensor = torch.stack(frames), torch.stack(keypoints_list)
            pred = predict_continuous_sign_from_video(frames_tensor, keypoints_tensor)
            ActivityLog.objects.create(
                activity_type='VIDEO_RECOGNITION',
                lang='zh',
                details={
                    'result': pred['result'],
                    'confidence': pred['confidence'],
                    'frame_count': pred['frame_count'],
                    'low_confidence': pred['low_confidence'],
                    'mode': pred.get('mode'),
                    'segments': pred.get('segments'),
                },
            )
            return JsonResponse({
                'result': pred['result'],
                'confidence': pred['confidence'],
                'top3': pred['top3'],
                'frame_count': pred['frame_count'],
                'low_confidence': pred['low_confidence'],
                'warning': pred['warning'],
                'mode': pred.get('mode', 'single'),
                'segments': pred.get('segments', []),
            })
        except Exception as e:
            return JsonResponse({'error': f"处理错误: {str(e)}"}, status=500)
        finally:
            if os.path.exists(tmp_file_path): os.unlink(tmp_file_path)
    return JsonResponse({'error': '无效的请求方法'}, status=400)


@csrf_exempt
def handle_image_recognition(request):
    """上传手语线稿/示意图，与 words-zhcn 词库比对识别（支持单张）。"""
    if request.method == 'POST':
        from .sign_lexicon import recognize_images_via_vocabulary

        if 'images' not in request.FILES:
            return JsonResponse({'error': '未上传图片文件'}, status=400)
        image_files = sorted(request.FILES.getlist('images'), key=lambda x: x.name)
        frames = []
        try:
            for image_file in image_files:
                frame = cv2.imdecode(np.frombuffer(image_file.read(), np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    frames.append(frame)
            if not frames:
                return JsonResponse({'error': '未检测到有效图片'}, status=400)

            summary, details, err = recognize_images_via_vocabulary(frames)
            if err:
                return JsonResponse({'error': err, 'details': details}, status=400)

            conf_values = []
            for item in details:
                if item.get('matched') and item.get('confidence'):
                    conf_values.append(float(item['confidence'].rstrip('%')) / 100.0)
            avg_conf = sum(conf_values) / len(conf_values) if conf_values else 0.0
            low_confidence = (
                avg_conf < 0.45
                or any(not d.get('matched') for d in details)
                or any(d.get('uncertain') for d in details)
            )

            top3 = []
            for item in details:
                if item.get('top3'):
                    top3 = item['top3']
                    break

            warning_parts = []
            unmatched = [d['index'] for d in details if not d.get('matched')]
            if unmatched:
                warning_parts.append(f'第 {", ".join(map(str, unmatched))} 张未匹配到词库线稿。')
            if low_confidence and conf_values:
                warning_parts.append('匹配置信度偏低，请尽量使用词库原图或清晰截图。')

            ActivityLog.objects.create(
                activity_type='IMAGE_RECOGNITION',
                lang='zh',
                details={
                    'result': summary,
                    'confidence': f'{avg_conf:.2%}',
                    'mode': 'vocabulary_sketch',
                    'frame_count': len(frames),
                    'low_confidence': low_confidence,
                },
            )
            return JsonResponse({
                'result': summary,
                'confidence': f'{avg_conf:.2%}',
                'mode': 'vocabulary_sketch',
                'top3': top3,
                'frame_count': len(frames),
                'low_confidence': low_confidence,
                'details': details,
                'warning': ' '.join(warning_parts),
                'hint': (
                    '当前为线稿识图：支持自绘手语线稿，与 words-zhcn 词库约 80 个手势比对；'
                    '单张即可。请保持白底黑线、手部完整；抽象词（情况、发展…）请用手语视频识别页。'
                ),
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': f'处理错误: {str(e)}'}, status=500)
    return JsonResponse({'error': '无效的请求方法'}, status=400)


def statistics_view(request):
    total_activities = ActivityLog.objects.count()
    activities_by_type = ActivityLog.objects.values('activity_type').annotate(count=Count('id')).order_by('-count')
    type_counts = {item['activity_type']: item['count'] for item in activities_by_type}
    daily_counts_query = ActivityLog.objects.annotate(date=TruncDate('timestamp')).values('date').annotate(
        count=Count('id')).order_by('date')
    labels = [item['date'].strftime('%Y-%m-%d') for item in daily_counts_query]
    data = [item['count'] for item in daily_counts_query]
    recent_activities = ActivityLog.objects.order_by('-timestamp')[:10]
    context = {
        'total_activities': total_activities,
        'realtime_count': type_counts.get('REALTIME_RECOGNITION', 0),
        'image_count': type_counts.get('IMAGE_RECOGNITION', 0),
        'video_count': type_counts.get('VIDEO_RECOGNITION', 0),
        'animation_count': type_counts.get('ANIMATION_GENERATION', 0),
        'chart_labels': json.dumps(labels),
        'chart_data': json.dumps(data),
        'recent_activities': recent_activities,
    }
    return render(request, 'sign_app/statistics.html', context)