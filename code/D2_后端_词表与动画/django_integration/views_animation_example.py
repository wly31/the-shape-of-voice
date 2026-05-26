"""D2 负责：动画生成 API 接入示例（复制到 sign_app/views.py）"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from sign_inference.services import AnimationService


@csrf_exempt
def generate_animation(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        body = {}
    text = body.get("text", request.POST.get("text", ""))
    lang = body.get("lang", request.POST.get("lang", "zh"))
    plan = AnimationService.plan_animation(text, lang)
    # TODO: plan["image_paths"] → ffmpeg 合成 → plan["video_url"] = "..."
    return JsonResponse(plan)
