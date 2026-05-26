# 成员 D2 — 后端（词表分词 / 动画业务）

## 负责范围

| 模块 | 说明 | 对接前端 |
|------|------|----------|
| 中文词表 | `lexicon/sign_lexicon.py` — CN2EN、jieba 分词、词→图片路径 | C：`animation.html` |
| 动画规划 | `AnimationService.plan_animation()` — 解析句子、列出待合成图片 | `/generate_animation/` |
| 视频合成 | `create_video_from_images()` 接口占位 | 完整逻辑在 `sign/sign_app/views.py` |

## 目录结构

```
D2_后端_词表与动画/
├── sign_inference/
│   ├── config.py              # words-zhcn 词库路径
│   ├── lexicon/sign_lexicon.py
│   └── services/animation_service.py
├── django_integration/
│   └── views_animation_example.py
├── tests/test_lexicon.py
└── requirements.txt
```

## 资源文件

- `sign/static/sign_app/words-zhcn/*.png`（约 57 张词库图）

```bash
set SIGN_PROJECT_ROOT=c:\path\to\sign
pip install -r requirements.txt
python -m tests.test_lexicon
```

## 与成员 A 合并

将 `sign_inference/lexicon` 与 `services/animation_service.py` 并入 Django 项目的 `sign_inference/`，按 `django_integration/views_animation_example.py` 接 `generate_animation`。

## 与 D1 的关系

见根目录 `后端合并说明.md`。
