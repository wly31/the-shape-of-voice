# 成员 A — Web 框架（Django）

## 本包包含

- Django 5.x 项目骨架 `sign_Project/`
- 应用 `sign_app/`：路由、视图桩、模型定义
- SQLite 数据库配置
- 静态/媒体目录配置

## 路由一览（`sign_app/urls.py`）

| URL | 视图 | 说明 |
|-----|------|------|
| `/realtime/` | `realtime_view` | 孤立手语识别页（模板由 B 提供） |
| `/continuous/` | `continuous_view` | 连续手语识别页（B） |
| `/image_recognition/` | `image_recognition_view` | 图片识别页（B） |
| `/animation/` | `animation_view` | 动画生成页（C） |
| `/video_recognition/` | `video_recognition_view` | 视频识别页（C） |
| `/about/` | `about_view` | 关于页（C） |
| `/recognize/` | `recognize_gesture` | POST，返回 JSON 演示数据 |
| `/generate_animation/` | `generate_animation` | POST，返回演示视频路径 |
| `/process_image/` | `handle_image_recognition` | POST，图片识别桩 |
| `/process_video/` | `handle_video_recognition` | POST，视频识别桩 |

## 本地运行（仅框架）

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

访问 `/realtime/` 可见占位模板；合并 B、C 的 templates 后为完整 UI。

## 后续接入（完整项目）

- 将 `views.py` 中的 `TODO` 替换为 `sign/` 中真实推理逻辑
- 挂载 `ctcn_2` 模型、`gesture_model.py` 等
