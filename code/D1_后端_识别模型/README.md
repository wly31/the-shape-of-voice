# 成员 D1 — 后端（手语识别 / 模型推理）

## 负责范围

| 模块 | 说明 | 对接前端 |
|------|------|----------|
| 孤立手语 CNN | `GestureService` — MediaPipe + 字母模型 | B：`realtime.html` → `/recognize/` |
| 连续手语 ctcn | `ContinuousSignService` — 多帧识别约 100 类 | B：`image_recognition` → `/process_image/`；C：`video_recognition` → `/process_video/` |
| 模型结构 | `models/cnn_gesture.py`、`models/continuous_model.py` | — |

## 目录结构

```
D1_后端_识别模型/
├── sign_inference/
│   ├── config.py              # 权重路径
│   ├── models/
│   ├── services/
│   │   ├── gesture_service.py
│   │   └── continuous_service.py
├── django_integration/
│   └── views_recognition_example.py
├── tests/test_recognition_stub.py
└── requirements.txt
```

## 权重文件（不打进 zip，答辩前从完整项目复制）

- `sign/model/CNN_model_alphabet_SIBI.pth`
- `sign/ctcn_2/models/best_model.pth`

```bash
set SIGN_PROJECT_ROOT=c:\path\to\sign
pip install -r requirements.txt
python -m tests.test_recognition_stub
```

## 与成员 A 合并

将 `sign_inference/` 复制到 Django 项目根目录，按 `django_integration/views_recognition_example.py` 修改 `views.py` 中识别相关接口。

## 与 D2 的关系

- **D1（本包）**：手语 → 文字（模型推理）
- **D2**：文字 → 手语（词表分词 + 动画资源）
- 合并后两个 `sign_inference` 子目录拼成完整包（见根目录 `后端合并说明.md`）
