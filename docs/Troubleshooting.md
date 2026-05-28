# 安装、设计，开发中遇到的主要问题及解决方法汇总

| 序号 | 问题名称 | 问题描述 | 原因分析 | 解决方案 |
|:---:|:-------:|:--------|:--------|:--------|
| 1 | 公网部署受限 | 本系统默认在本地或校园局域网部署演示，未做公网商用部署 | 依赖浏览器摄像头与较重深度学习推理，且当前使用Django开发服务器与HTTP本地访问。公网发布技术上可行，但需HTTPS、生产级Web服务、服务器算力及隐私合规等改造 | 课程阶段以局域网/本机验证为主，未做公网商用部署。为了方便团队内成员访问，我使用了ngrok网站创建临时公网以供查看|
| 2 | 中文手语数据集获取困难 | 国内缺乏公开的中文手语数据集，开源项目仅提供英文A-Z字母数据 | 中文手语数据集多为高校或商业机构持有，不对外公开。英文手势数据集（如ASL Alphabet）较丰富，但中文手语（CSL）数据稀缺 | 1. 注册Kaggle账号，搜索"Chinese Sign Language Dataset"下载公开数据集<br>2. 使用VPN访问Google Cloud Storage获取MediaPipe模型文件<br>3. 自行用手机拍摄50+个常用中文词汇手势视频作为补充训练数据 |
| 7 | SQLite并发写入受限 | 多用户同时使用时偶发"database is locked"错误 | SQLite为文件级锁，不支持高并发写入操作 | 1. 使用Django ORM的 `transaction.atomic()` 管理事务<br>2. 减少写操作频率，采用批量写入<br>3. 生产环境建议替换为PostgreSQL |
| 8 | 旧版MediaPipe Hands（CDN）不稳定 | 摄像头已开，但画面上无绿线、无红点；控制台可能出现 `MediaPipe 未加载` 或模型 wasm 404 | 原方案依赖 `@mediapipe/hands` 从CDN拉取wasm/模型，国内网络或缓存失败时初始化失败。`handTracker.init()` 异步未完成就 `start()`，导致 `hands` 为空直接return。初始化失败仅 `console.warn`，页面上无明确提示 | 改用官方 `@mediapipe/tasks-vision` Hand Landmarker。将 `hand_landmarker.task` 放到本地 `static/sign_app/mediapipe/`。`start()` 内 `await ensureReady()` 并等待视频首帧；徽章显示加载/错误状态。JS加版本号 `?v=N` 避免浏览器缓存旧脚本 |
| 9 | 骨架与画面错位 | 视频画面显示正常，但手部骨架关键点标注位置与实际手部位置不匹配 | 视频使用 `object-fit: cover` 裁剪显示，而早期代码直接用 `clientWidth` 绘制关键点，未按cover规则映射坐标，导致归一化关键点坐标与画布像素不对应 | 增加 `computeCoverTransform` 函数，将归一化关键点坐标按cover裁剪规则映射到画布像素坐标系。视频与canvas同时添加 `scaleX(-1)` 镜像翻转，与前置摄像头镜像保持一致 |
| 10 | 摄像头词库识别不稳定 | 单帧误识别、抖动；真人视频比词库线稿难 | 词库图为固定线稿/示意图，摄像头为真人+背景+光照变化。单帧ResNet相似度波动大 | **多帧投票**（如5帧）；置信度与票数双阈值。**宽松模式**兜底；Top3提示。混合**ORB/轮廓**对Top-K精排。阈值常量见 `sign_lexicon.py`（`CAMERA_MIN_CONFIDENCE` 等） |
