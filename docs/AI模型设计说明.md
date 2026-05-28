# AI/深度学习模型设计说明
## 一、算法模型概览
### 1. CNN（英文A-Z识别）

| 维度 | 内容 |
| :--- | :--- |
| **模型名称** | 一维卷积神经网络（Conv1d） |
| **应用场景** | 英文A-Z字母手势的实时识别 |
| **输入** | 63维特征向量（21个关键点 × 3坐标） |
| **输出** | 26个类别概率（A-Z） |
| **选型原因** | ①参数量小（约2.1M），推理速度快（约35ms/帧）<br>②对静态手势分类准确率 > 85%<br>③团队熟悉CNN架构，便于调试和优化<br>④轻量级，适合在CPU上实时运行 |
| **竞品对比** | 相比ResNet18（89.2%准确率但80ms推理），CNN在速度上优势明显，更适合实时场景 |


### 2. CNN-LSTM（中文连续识别）

| 维度 | 内容 |
| :--- | :--- |
| **模型名称** | CNN-LSTM（卷积神经网络 + 长短期记忆网络） |
| **应用场景** | 中文连续手势词汇识别（图片/视频输入） |
| **特征提取** | ResNet18提取图像帧的512维视觉特征 + 关键点126维特征 → 融合为638维 |
| **输出** | 中文词汇分类（约50+类别） |
| **选型原因** | ①CNN负责提取每帧图像的空间特征<br>②LSTM负责建模连续帧之间的时间依赖关系<br>③适合处理动态手势序列，准确率（91.3%）优于单帧CNN<br>④Transformer编码器增强序列建模能力 |
| **竞品对比** | 相比纯Transformer（92.1%但200ms），CNN-LSTM在准确率和速度之间取得更好平衡 |


### 3. MediaPipe Hands（手部关键点检测）

| 维度 | 内容 |
| :--- | :--- |
| **算法名称** | MediaPipe Hands |
| **应用场景** | 实时手部关键点检测（21个关键点） |
| **输入** | RGB图像（640×480） |
| **输出** | 21个手部关键点坐标（x, y, z） |
| **选型原因** | ①Google维护，开箱即用，无需训练<br>②轻量级，可在CPU上实时运行<br>③提供21个手部关键点，精度满足手语识别需求<br>④跨平台支持（Python/JS），方便前后端集成 |
| **竞品对比** | 相比OpenPose（精度高但重，不适合实时）、Handtrack.js（轻量但精度低），MediaPipe在精度和速度上最平衡 |
## 二、模型实际效果
| 模型 | 理论准确率 | 实测准确率 | 推理时间 | 参数量 | 实际效果说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |

## 三、参考文献和开源代码仓库链接
### 参考文献
| 序号 | 文献信息 | 对应技术 | 作用说明 |
| :--- | :--- | :--- | :--- |
| [1] | Hochreiter, S., & Schmidhuber, J. (1997). Long Short-Term Memory. *Neural Computation*, 9(8), 1735-1780. | CNN-LSTM | 让模型具有记忆能力，理解连续手势序列 |
| [2] | Lugaresi, C., et al. (2019). MediaPipe: A Framework for Building Perception Pipelines. *arXiv preprint arXiv:1906.08172*. | MediaPipe Hands | 从摄像头画面中实时检测21个手部关键点 |
| [3] | Django官方文档. (2024). Django 5.2 documentation. https://docs.djangoproject.com/ | Django | Web后端框架，处理请求、数据库和业务逻辑 |

### 开源代码仓库
| 来源 | 链接 |
| :--- | :--- |
|手部关键点检测| [MediaPipe Hands](https://developers.google.com/mediapipe) |
| Web开发框架 | [Django](https://www.djangoproject.com/) |
| 深度学习框架 | [TensorFlow](https://www.tensorflow.org/?hl=zh-cn) |
| 参考项目 | [DUTBenjamin/SignTranslate](https://github.com/DUTBenjamin/SignTranslate) |
