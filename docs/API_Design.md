# 接口设计：重要的业务功能（可与用户故事对应）和工具类设计
| 接口名称 | 接口功能 | 输入变量或对象 | 输出对象 | 备注 |
| --- | --- | --- | --- | --- |
### 3.5.5 接口设计：重要的业务功能（可与用户故事对应）和工具类设计

| 接口名称 | 接口功能 | 输入变量或对象 | 输出对象 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| `/recognize/` (POST) | 手势识别 | `image` (Base64编码的图像), `mode` (english/chinese, 可选) | `success`, `result` (A-Z字母), `confidence` (置信度), `bbox` (手部边界框) | 支持英文A-Z字母实时识别 |
| `/generate_animation/` (POST) | 手语动画生成 | `text` (要翻译的文字), `format` (mp4/webm, 可选) | `success`, `video_url` (视频文件URL), `duration` (视频时长), `words_count` (词汇数量) | 文字转手语动画，需配合jieba分词 |
| `/speak/` (POST) | 语音播报 | `text` (要播报的文本), `lang` (zh-CN/en-US, 可选) | `success`, `audio_url` (音频文件URL) | 将识别结果语音播报 |
| `/process_image/` (POST) | 中文图片识别 | `images` (图片文件列表, FormData) | `result` (中文词汇), `confidence` (置信度) | 支持多张图片批量识别 |
| `/process_video/` (POST) | 中文视频识别 | `video` (视频文件, FormData) | `result` (中文词汇), `confidence` (置信度) | 识别视频中的连续手语 |
| `/get_animation_history/` (GET) | 历史记录查询 | 无（需登录状态） | `history` (历史记录列表，包含text、video_file、created_at) | 查询手语动画生成历史 |
| `/clear_history/` (POST) | 清除历史记录 | 无 | `success` | 清除所有历史记录 |
| `/get_gesture_info/` (GET) | 获取手势信息 | `gesture` (手势名称/字母) | `name`, `description`, `video_url` | 查询手势的详细说明和示例 |
| `/api/recognize/` (POST) | REST API手势识别 | `image` (Base64图像), `mode` (english/chinese) | `result`, `confidence`, `bbox` | RESTful接口，返回JSON格式 |
| `/api/generate_animation/` (POST) | REST API动画生成 | `text` (文字), `format` (mp4/webm) | `video_url`, `duration`, `words_count` | RESTful接口，支持json请求 |

### WebSocket 实时接口

| 接口名称 | 接口功能 | 输入变量或对象 | 输出对象 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| `/ws/recognize/` (WebSocket) | 实时手势识别 | `type`: "frame", `image`: Base64图像数据, `timestamp`: 时间戳 | `type`: "result", `result`: 识别结果, `confidence`: 置信度, `latency_ms`: 延迟 | 低延迟实时通信，支持心跳机制(ping/pong) |
