from django.db import models


class SignHistory(models.Model):
    """手语动画生成历史（框架定义，供 C 端页面对接）"""
    text = models.CharField(max_length=255)
    video_file = models.CharField(max_length=255, blank=True)
    lang = models.CharField(max_length=10, default="zh")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.text} ({self.lang})"


class ActivityLog(models.Model):
    """各模块识别/生成活动日志"""
    ACTIVITY_TYPES = [
        ("REALTIME_RECOGNITION", "孤立手语识别"),
        ("IMAGE_RECOGNITION", "中文图片识别"),
        ("VIDEO_RECOGNITION", "中文视频识别"),
        ("ANIMATION_GENERATION", "手语动画生成"),
    ]
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict)
    lang = models.CharField(max_length=10, null=True, blank=True)
