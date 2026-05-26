"""D1 负责：识别类 API 接入示例（复制到 sign_app/views.py）"""
import cv2
import numpy as np
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from sign_inference.services import GestureService, ContinuousSignService


@csrf_exempt
def recognize_gesture(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    image_b64 = request.POST.get("image", "")
    data = GestureService.get().recognize_base64(image_b64)
    if "error" in data:
        return JsonResponse(data, status=400)
    return JsonResponse(data)


@csrf_exempt
def handle_image_recognition(request):
    if request.method != "POST" or "images" not in request.FILES:
        return JsonResponse({"error": "未上传图片"}, status=400)
    frames = []
    for f in sorted(request.FILES.getlist("images"), key=lambda x: x.name):
        img = cv2.imdecode(np.frombuffer(f.read(), np.uint8), cv2.IMREAD_COLOR)
        if img is not None:
            frames.append(img)
    pred = ContinuousSignService.get().predict_frames(frames)
    if "error" in pred:
        return JsonResponse(pred, status=400)
    return JsonResponse(pred)


@csrf_exempt
def handle_video_recognition(request):
    # TODO: cv2.VideoCapture 抽帧后调用 ContinuousSignService.get().predict_frames(frames)
    return JsonResponse({"error": "见完整项目 views.handle_video_recognition"}, status=501)
