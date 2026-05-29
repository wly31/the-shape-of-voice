# 前端设计文档

## 一、前端技术选型

| 技术 | 版本 | 用途 | 选型原因 |
| :--- | :--- | :--- | :--- |
| HTML5 | HTML5 | 页面结构搭建 | 标准网页标记语言，浏览器原生支持 |
| CSS3 | CSS3 | 页面样式设计 | 实现响应式布局、动画效果 |
| JavaScript | ES6+ | 前端交互逻辑 | 浏览器原生支持，无需额外编译 |
| Bootstrap 5 | 5.x | UI组件框架 | 响应式设计、移动优先、组件丰富、快速搭建界面 |
| Bootstrap Icons | 5.x | 图标库 | 丰富的图标资源，无需额外引入图片 |
| MediaPipe JS | 0.10.21 | 手部关键点检测（前端可选） | 实时检测手部21个关键点，辅助识别 |

---

## 二、前端页面列表

| 页面名称 | 路由 | 主要功能 |
| :--- | :--- | :--- |
| 实时识别页 | `/realtime/` | 摄像头调用、A-Z字母实时手势识别、结果展示 |
| 连续识别页 | `/continuous/` | 中文图片/视频上传识别 |
| 动画生成页 | `/animation/` | 文字输入、手语动画生成、视频播放 |
| 图片识别页 | `/image_recognition/` | 多张图片上传、批量识别 |
| 视频识别页 | `/video_recognition/` | 单个视频上传识别 |
| 统计分析页 | `/statistics/` | 使用数据图表展示 |
| 技术说明页 | `/technology/` | 技术架构介绍 |
| 关于页面 | `/about/` | 项目信息展示 |

---

## 三、前端技术栈结构
前端技术栈:
├── HTML5 页面结构
├── CSS3 样式设计
├── JavaScript 交互逻辑
├── Bootstrap 5 UI组件框架
│ ├── Bootstrap Icons 图标库
│ └── Bootstrap JS 交互组件
└── MediaPipe JS 手部关键点检测
---

## 四、前端核心功能实现

### 4.1 摄像头调用与视频流处理

```javascript
// 调用摄像头
navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        const video = document.getElementById('video');
        video.srcObject = stream;
    })
    .catch(error => {
        console.error('摄像头访问失败:', error);
        alert('请允许摄像头权限后重试');
    });
