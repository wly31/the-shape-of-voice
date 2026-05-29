"""
Web 框架层视图 — 初步提交版
- 页面视图：渲染模板（模板文件由 B、C 成员提供，合并后放入 templates/）
- API 视图：返回演示 JSON，约定前后端接口格式
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
import json

from .models import SignHistory, ActivityLog


# ---------- 页面视图（仅 render，不含业务逻辑）----------

def realtime_view(request):
    return render(request, "sign_app/realtime.html")


def continuous_view(request):
    return render(request, "sign_app/continuous.html")


def image_recognition_view(request):
    return render(request, "sign_app/image_recognition.html")


def animation_view(request):
    return render(request, "sign_app/animation.html")


def video_recognition_view(request):
    return render(request, "sign_app/video_recognition.html")


def about_view(request):
    return render(request, "sign_app/about.html")


# ---------- API 桩（演示数据，供前端联调）----------

@csrf_exempt
def recognize_gesture(request):
    """孤立手语识别 API — B 端 realtime 页调用"""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    # TODO: 接入 CNN 字母模型 + MediaPipe（见完整项目 sign_app/views.py）
    return JsonResponse({
        "gesture": "A",
        "name": "字母 A（演示数据）",
        "confidence": 0.92,
    })


@csrf_exempt
def generate_animation(request):
    """手语动画生成 API — C 端 animation 页调用"""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        body = {}
    text = body.get("text", request.POST.get("text", ""))
    lang = body.get("lang", request.POST.get("lang", "zh"))
    # TODO: 接入 sign_lexicon 与视频合成（见完整项目）
    return JsonResponse({
        "success": True,
        "video_url": "/static/demo/placeholder.mp4",
        "text": text,
        "lang": lang,
        "message": "演示模式：请合并完整项目后替换为真实生成逻辑",
        "segments": [],
        "missing": [],
    })


@require_GET
def get_animation_history(request):
    records = SignHistory.objects.order_by("-created_at")[:10]
    data = [
        {
            "text": r.text,
            "video_file": r.video_file,
            "lang": r.lang,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for r in records
    ]
    return JsonResponse({"history": data})


@csrf_exempt
def clear_history(request):
    if request.method == "POST":
        SignHistory.objects.all().delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)


@csrf_exempt
def handle_image_recognition(request):
    """中文手语图片识别 API — B 端调用"""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    if "images" not in request.FILES:
        return JsonResponse({"error": "未上传图片"}, status=400)
    n = len(request.FILES.getlist("images"))
    # TODO: 接入 ctcn_2 连续手语模型
    ActivityLog.objects.create(
        activity_type="IMAGE_RECOGNITION",
        lang="zh",
        details={"result": "发展", "confidence": 0.78, "frame_count": n, "mode": "stub"},
    )
    return JsonResponse({
        "result": "发展",
        "confidence": "78.00%",
        "frame_count": n,
        "low_confidence": False,
        "mode": "stub",
        "warning": "",
        "hint": "演示数据；合并完整项目后接入真实模型。",
    })


@csrf_exempt
def handle_video_recognition(request):
    """中文手语视频识别 API — C 端调用"""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    if "video" not in request.FILES:
        return JsonResponse({"error": "未上传视频"}, status=400)
    # TODO: 接入 ctcn_2
    return JsonResponse({
        "result": "民主",
        "confidence": "81.00%",
        "low_confidence": False,
        "warning": "",
    })
