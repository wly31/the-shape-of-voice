# 成员 C — 前端（动画与展示）

## 负责页面

| 文件 | 功能 | 对接 API（A 提供） |
|------|------|-------------------|
| `animation.html` | 文字/语音 → 手语动画视频 | `POST /generate_animation/`、`GET /get_animation_history/` |
| `video_recognition.html` | 上传视频识别手语 | `POST /process_video/` |
| `about.html` | 项目介绍、技术栈说明 | 无 API |

## 依赖

- 布局继承 **成员 B** 的 `templates/sign_app/base.html`
- 样式使用 **成员 B** 的 `static/css/common.css`

合并时：先复制 B 的 `templates` + `static`，再复制本目录的 `templates/sign_app/` 下三个文件。

## 提交说明

向老师说明：完成「文字转手语」与视频识别、关于页的 **界面与接口联调骨架**；视频合成与模型由后端后续接入。
