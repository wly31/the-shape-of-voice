# SignTranslate 实时手语翻译系统 - 架构图

```mermaid
flowchart TB
    subgraph 前端层["前端展示层 (Frontend)"]
        direction LR
        A1[实时视频流<br/>WebCamera] --> A2[识别结果展示<br/>Result Display] --> A3[语音播报控制<br/>TTS Control]
    end

    subgraph 后端层["后端服务层 (Backend)"]
        direction LR
        B1[Django Web Server] --> B2[URL路由<br/>urls.py] --> B3[视图处理<br/>views.py] --> B4[WebSocket<br/>consumers.py] --> B5[业务逻辑<br/>gesture_model.py]
    end

    subgraph AI层["算法处理层 (AI/ML)"]
        direction LR
        C1[手部检测<br/>MediaPipe<br/>21关键点] --> C2[特征提取<br/>归一化/63维] --> C3[1D-CNN分类<br/>A-Z识别]
    end

    subgraph 数据层["数据存储层 (Data)"]
        direction LR
        D1[CNNModel.pth] --> D2[类别映射表] --> D3[用户数据]
    end

    前端层 -->|WebSocket| 后端层
    后端层 --> AI层
    AI层 --> 数据层
