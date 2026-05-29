# AI/深度学习模型设计说明
## 一、算法模型概览

| 序号 | 算法/模型名称 | 应用场景 | 输入 | 输出 | 选型原因 | 竞品对比 |
|:---:|:---|:---|:---|:---|:---|:---|
| 1 |OpenCV + MediaPipe Hand Landmarker |图像/视频预处理 + 实时手部21关键点检测 | RGB图像（640×480） | 21个关键点3D坐标（x,y,z） | ①功能最全（2500+函数）<br>②性能高（C++底层）<br>③跨平台支持<br>④与NumPy/PyTorch无缝配合 | 相比PIL功能更全；相比scikit-image性能更高；计算机视觉工业标准<br>③Google维护，开箱即用，无需训练<br>②轻量级，CPU实时运行<br>④精度满足手语识别需求<br>⑤跨平台支持Python/JS | 相比OpenPose（精度高但重）、Handtrack.js（轻量但精度低），MediaPipe在精度和速度上最平衡 |
| 2 | 1D-CNN（一维卷积神经网络） | 英文A-Z字母实时识别 | 63维特征向量（21点×3坐标） | 26个字母概率分布 | ①参数少，训练快<br>②推理快（<10ms）<br>③适合序列特征提取<br>④分类准确率>85% | 相比2D-CNN参数量减少90%，速度更快；相比ResNet18更轻量，适合实时场景 |
| 3 | ResNet18 | 中文连续手势视觉特征提取 | 视频帧图像（256×256×3） | 512维视觉特征向量 | ①预训练模型可用，无需从头训练<br>②深度适中，推理速度较快<br>③在图像识别任务上准确率高<br>④适合作为手势的特征提取器 | 相比VGG16（参数多，推理慢）、MobileNet（轻量但准确率略低），ResNet18在准确率和速度之间最平衡 |
## 二、模型实际效果
| 模型 | 理论准确率 | 实测准确率 | 推理时间 | 参数量 | 实际效果说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |

## 三、参考文献和开源代码仓库链接

### 1、对应参考文献
| 序号 | 算法/模型名称 | 参考文献 |
|:---:|:---|:---|
| 1 | MediaPipe Hand Landmarker | Lugaresi, C., et al. (2019). MediaPipe: A Framework for Building Perception Pipelines. *arXiv preprint arXiv:1906.08172*. |
| 2 | 1D-CNN | Kiranyaz, S., et al. (2021). 1D Convolutional Neural Networks and Applications: A Survey. *Mechanical Systems and Signal Processing*, 151, 107398. |
| 3 | ResNet18 | He, K., Zhang, X., Ren, S., & Sun, J. (2016). Deep Residual Learning for Image Recognition. *Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)*, 770-778. |
| 4 | OpenCV | Bradski, G. (2000). The OpenCV Library. *Dr. Dobb's Journal of Software Tools*. |

### 2.开源代码仓库
| 来源 | 链接 |
| :--- | :--- |
|手部关键点检测| [MediaPipe Hands](https://developers.google.com/mediapipe) |
| Web开发框架 | [Django](https://www.djangoproject.com/) |
| 深度学习框架 | [TensorFlow](https://www.tensorflow.org/?hl=zh-cn) |
| 参考项目 | [DUTBenjamin/SignTranslate](https://github.com/DUTBenjamin/SignTranslate) |
