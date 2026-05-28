# AI/深度学习模型设计说明
## 一、算法模型概览
### 一、算法与模型汇总

| 序号 | 算法/模型名称 | 应用场景 | 输入 | 输出 | 选型原因 | 竞品对比 |
|:---:|:---|:---|:---|:---|:---|:---|
| 1 | MediaPipe Hand Landmarker | 实时手部21关键点检测 | RGB图像（640×480） | 21个关键点3D坐标（x,y,z） | ①Google维护，开箱即用，无需训练<br>②轻量级，CPU实时运行<br>③精度满足手语识别需求<br>④跨平台支持Python/JS | 相比OpenPose（精度高但重）、Handtrack.js（轻量但精度低），MediaPipe在精度和速度上最平衡 |
| 2 | 1D-CNN（一维卷积神经网络） | 英文A-Z字母实时识别 | 63维特征向量（21点×3坐标） | 26个字母概率分布 | ①参数少，训练快<br>②推理快（<10ms）<br>③适合序列特征提取<br>④分类准确率>85% | 相比2D-CNN参数量减少90%，速度更快；相比ResNet18更轻量，适合实时场景 |
| 3 | CNN-LSTM + Transformer | 中文连续词汇识别 | 视频帧序列 + 手部关键点 | 中文词汇分类（50+类别） | ①多模态融合（视觉+关键点）<br>②时序建模，捕捉手势序列<br>③注意力机制关注关键帧<br>④准确率>80% | 相比纯CNN增加时序信息；相比纯Transformer计算量更小；相比单模态识别准确率更高 |
| 4 | jieba分词 | 中文文本分词 | 中文字符串 | 分词后的词汇列表 | ①准确率高（>95%）<br>②速度快（<1ms）<br>③词典丰富（20万+词汇）<br>④支持自定义词典 | 相比pkuseg更轻量；相比HanLP完全开源免费；Python生态首选 |
| 5 | Softmax | 多分类概率输出 | 神经网络原始得分（logits） | 概率分布（总和=1） | ①多分类标准输出<br>②概率值直观表示置信度<br>③与交叉熵损失配合梯度稳定 | 相比Sigmoid适合多分类；相比直接输出得分可解释性更强 |
| 6 | 坐标归一化 | 手部关键点特征预处理 | 21个关键点绝对坐标 | 归一化后的相对坐标 | ①消除手部位置偏差<br>②提高泛化能力<br>③简化特征，去除无关信息<br>④识别准确率提升10-20% | 相比绝对坐标，模型不依赖手部位置；相比MinMax归一化保留相对关系 |
| 7 | OpenCV | 图像/视频预处理 | 图像/视频文件 | 处理后的图像/视频帧 | ①功能最全（2500+函数）<br>②性能高（C++底层）<br>③跨平台支持<br>④与NumPy/PyTorch无缝配合 | 相比PIL功能更全；相比scikit-image性能更高；计算机视觉工业标准 |
## 二、模型实际效果
| 模型 | 理论准确率 | 实测准确率 | 推理时间 | 参数量 | 实际效果说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |

## 三、参考文献和开源代码仓库链接
### 参考文献

### 二、对应参考文献

| 序号 | 算法/模型名称 | 参考文献 |
|:---:|:---|:---|
| 1 | MediaPipe Hand Landmarker | Lugaresi, C., et al. (2019). MediaPipe: A Framework for Building Perception Pipelines. *arXiv preprint arXiv:1906.08172*. |
| 2 | 1D-CNN | Kiranyaz, S., et al. (2021). 1D Convolutional Neural Networks and Applications: A Survey. *Mechanical Systems and Signal Processing*, 151, 107398. |
| 3 | CNN-LSTM + Transformer | Vaswani, A., et al. (2017). Attention Is All You Need. *Advances in Neural Information Processing Systems (NeurIPS)*, 30. |
| 4 | jieba分词 | Sun, J. (2012). Jieba Chinese Word Segmentation Tool. *GitHub Repository*. https://github.com/fxsjy/jieba |
| 5 | Softmax | Goodfellow, I., Bengio, Y., & Courville, A. (2016). *Deep Learning*. MIT Press. (Chapter 6: Softmax Units for Multinoulli Output Distributions) |
| 6 | 坐标归一化 | Bishop, C. M. (2006). *Pattern Recognition and Machine Learning*. Springer. (Chapter 1: Data Preprocessing) |
| 7 | OpenCV | Bradski, G. (2000). The OpenCV Library. *Dr. Dobb's Journal of Software Tools*. |
### 开源代码仓库
| 来源 | 链接 |
| :--- | :--- |
|手部关键点检测| [MediaPipe Hands](https://developers.google.com/mediapipe) |
| Web开发框架 | [Django](https://www.djangoproject.com/) |
| 深度学习框架 | [TensorFlow](https://www.tensorflow.org/?hl=zh-cn) |
| 参考项目 | [DUTBenjamin/SignTranslate](https://github.com/DUTBenjamin/SignTranslate) |
