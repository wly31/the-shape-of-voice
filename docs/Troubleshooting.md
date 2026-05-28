# 安装、设计，开发中遇到的主要问题及解决方法汇总

| 序号 | 问题名称 | 问题描述 | 原因分析 | 解决方案 |
|:---:|:-------:|:--------|:--------|:--------|
| 1 | 公网部署受限 | 本系统默认在本地或校园局域网部署演示，未做公网商用部署 | 依赖浏览器摄像头与较重深度学习推理，且当前使用Django开发服务器与HTTP本地访问。公网发布技术上可行，但需HTTPS、生产级Web服务、服务器算力及隐私合规等改造 | 课程阶段以局域网/本机验证为主，未做公网商用部署。如需公网访问需：1. 部署HTTPS证书 2. 使用Nginx+Gunicorn 3. 租用GPU云服务器 4. 完成隐私合规审查 |
| 2 | 中文手语数据集获取困难 | 国内缺乏公开的中文手语数据集，开源项目仅提供英文A-Z字母数据 | 中文手语数据集多为高校或商业机构持有，不对外公开。英文手势数据集（如ASL Alphabet）较丰富，但中文手语（CSL）数据稀缺 | 1. 注册Kaggle账号，搜索"Chinese Sign Language Dataset"下载公开数据集<br>2. 使用VPN访问Google Cloud Storage获取MediaPipe模型文件<br>3. 自行用手机拍摄50+个常用中文词汇手势视频作为补充训练数据 |
| 3 | MediaPipe Python版本不兼容 | 开源项目使用旧版API（`mp.solutions.hands`），pip安装的新版0.10.x无法运行 | MediaPipe 0.10.x版本完全重构了API，旧版`solutions`接口被废弃，改用`tasks.vision`接口，代码无法兼容 | 1. 下载新版模型文件 `hand_landmarker.task` 到本地<br>2. 重写 `gesture_model.py`，使用新API `mp.tasks.vision.HandLandmarker`<br>3. 实现延迟加载机制，避免模块导入时初始化失败 |
| 4 | 实时识别视频延迟较高 | 手势已做出，识别结果延迟1-2秒才显示，画面偶有卡顿 | 前端采用Base64编码+HTTP轮询传输图像，效率低。图像分辨率过高，帧率过快导致后端处理跟不上 | 1. 降低图像分辨率至640×480<br>2. 减少帧率至10fps<br>3. 前端压缩JPEG质量至0.8<br>4. 后端使用延迟加载，模型仅初始化一次 |
| 5 | FFmpeg视频转码失败 | 生成手语动画时提示"视频生成失败"，控制台报错ffmpeg not found | 系统未安装FFmpeg或版本不兼容，OpenCV的VideoWriter不支持h264编码 | 1. 使用Python的 `imageio-ffmpeg` 库自动管理FFmpeg依赖<br>2. 添加错误处理，转码失败时返回原始mp4格式<br>3. 将FFmpeg二进制文件放到项目目录作为备用 |
| 6 | 中文词汇量有限 | 中文连续识别仅支持50+个常用词汇，无法覆盖日常交流需求 | 时间限制（5天开发周期）和数据采集条件限制，无法收集足够多的中文手势数据 | 1. 优先实现高频词汇（你好、谢谢、再见等）<br>2. 设计可扩展架构，添加新词汇只需放入对应图片/视频素材<br>3. 使用 `difflib` 相似词匹配作为兜底，提高翻译覆盖率 |
| 7 | SQLite并发写入受限 | 多用户同时使用时偶发"database is locked"错误 | SQLite为文件级锁，不支持高并发写入操作 | 1. 使用Django ORM的 `transaction.atomic()` 管理事务<br>2. 减少写操作频率，采用批量写入<br>3. 生产环境建议替换为PostgreSQL |
| 8 | 旧版MediaPipe Hands（CDN）不稳定 | 摄像头已开，但画面上无绿线、无红点；控制台可能出现 `MediaPipe 未加载` 或模型 wasm 404 | 原方案依赖 `@mediapipe/hands` 从CDN拉取wasm/模型，国内网络或缓存失败时初始化失败。`handTracker.init()` 异步未完成就 `start()`，导致 `hands` 为空直接return。初始化失败仅 `console.warn`，页面上无明确提示 | 改用官方 `@mediapipe/tasks-vision` Hand Landmarker。将 `hand_landmarker.task` 放到本地 `static/sign_app/mediapipe/`。`start()` 内 `await ensureReady()` 并等待视频首帧；徽章显示加载/错误状态。JS加版本号 `?v=N` 避免浏览器缓存旧脚本 |
| 9 | 骨架与画面错位 | 视频画面显示正常，但手部骨架关键点标注位置与实际手部位置不匹配 | 视频使用 `object-fit: cover` 裁剪显示，而早期代码直接用 `clientWidth` 绘制关键点，未按cover规则映射坐标，导致归一化关键点坐标与画布像素不对应 | 增加 `computeCoverTransform` 函数，将归一化关键点坐标按cover裁剪规则映射到画布像素坐标系。视频与canvas同时添加 `scaleX(-1)` 镜像翻转，与前置摄像头镜像保持一致 |
| 10 | 摄像头词库识别不稳定 | 单帧误识别、抖动；真人视频比词库线稿难 | 词库图为固定线稿/示意图，摄像头为真人+背景+光照变化。单帧ResNet相似度波动大 | **多帧投票**（如5帧）；置信度与票数双阈值。**宽松模式**兜底；Top3提示。混合**ORB/轮廓**对Top-K精排。阈值常量见 `sign_lexicon.py`（`CAMERA_MIN_CONFIDENCE` 等） |
