from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'sign_app'

# 本项目使用 /xh/ 前缀，与开源 SignTranslate 默认路径（realtime、video_recognition 等）区分
urlpatterns = [
    path('xh/', RedirectView.as_view(url='/xh/isolated/', permanent=False)),
    path('xh/isolated/', views.realtime_view, name='realtime'),
    path('xh/demo/touch/', views.touch_demo_view, name='touch_demo'),
    path('xh/stream/', views.continuous_view, name='continuous'),
    path('xh/to-sign/', views.animation_view, name='animation'),
    path('xh/image/', views.image_recognition_view, name='image_recognition'),
    path('xh/video/', views.video_recognition_view, name='video_recognition'),
    path('xh/stats/', views.statistics_view, name='statistics'),
    path('xh/tech/', views.technology_view, name='technology'),
    path('xh/about/', views.about_view, name='about'),
    path('api/xh/recognize/', views.recognize_gesture, name='recognize'),
    path('api/xh/recognize-vocab/', views.recognize_gesture_vocab, name='recognize_vocab'),
    path('api/xh/vocab-words/', views.get_vocab_words, name='vocab_words'),
    path('api/xh/gesture-info/', views.get_gesture_info, name='gesture-info'),
    path('api/xh/animate/', views.generate_animation, name='generate-animation'),
    path('api/xh/history/', views.get_animation_history, name='get-animation-history'),
    path('api/xh/history/clear/', views.clear_history, name='clear-history'),
    path('api/xh/image/', views.handle_image_recognition, name='process_image'),
    path('api/xh/video/', views.handle_video_recognition, name='process_video'),
]
