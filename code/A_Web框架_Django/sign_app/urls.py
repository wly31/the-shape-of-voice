from django.urls import path
from . import views

app_name = "sign_app"

urlpatterns = [
    # 页面路由（模板由 B、C 提供）
    path("realtime/", views.realtime_view, name="realtime"),
    path("continuous/", views.continuous_view, name="continuous"),
    path("image_recognition/", views.image_recognition_view, name="image_recognition"),
    path("animation/", views.animation_view, name="animation"),
    path("video_recognition/", views.video_recognition_view, name="video_recognition"),
    path("about/", views.about_view, name="about"),
    # API 路由（当前为桩实现，后续接真实模型）
    path("recognize/", views.recognize_gesture, name="recognize"),
    path("generate_animation/", views.generate_animation, name="generate-animation"),
    path("get_animation_history/", views.get_animation_history, name="get-animation-history"),
    path("clear_history/", views.clear_history, name="clear-history"),
    path("process_image/", views.handle_image_recognition, name="process_image"),
    path("process_video/", views.handle_video_recognition, name="process_video"),
]
