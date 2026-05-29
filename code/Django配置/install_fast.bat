@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo  手语项目 - 快速安装（清华镜像 + Python 3.10）
echo ========================================
echo.

if not exist "venv310\Scripts\python.exe" (
    echo [1/3] 创建 Python 3.10 虚拟环境...
    py -3.10 -m venv venv310
    if errorlevel 1 (
        echo 失败：未找到 Python 3.10，请安装 Python 3.10
        pause
        exit /b 1
    )
) else (
    echo [1/3] 虚拟环境 venv310 已存在，跳过创建
)

echo [2/3] 安装依赖（清华源，约 3~8 分钟，取决于网速）...
venv310\Scripts\pip.exe install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
if errorlevel 1 (
    echo 安装失败，请检查网络后重试
    pause
    exit /b 1
)

echo [3/3] 验证环境...
venv310\Scripts\python.exe -c "import django; import torch; import mediapipe as mp; assert hasattr(mp,'solutions'); print('环境 OK')"
if errorlevel 1 (
    echo 验证失败
    pause
    exit /b 1
)

echo.
echo 安装完成！双击 run.bat 启动项目
pause
