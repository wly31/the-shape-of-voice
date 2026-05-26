"""
孤立手语（字母）识别服务 — MediaPipe + CNNModel
"""
import base64
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np
import torch

from sign_inference.config import paths
from sign_inference.models import CNNModel

# 与完整项目一致的 26 类字母映射（示例，可按权重文件调整）
DEFAULT_CLASSES = {i: chr(ord("A") + i) for i in range(26)}


class GestureService:
    _instance: Optional["GestureService"] = None

    def __init__(self):
        self._ready = False
        self._model = None
        self._mp_hands = None
        self._classes = DEFAULT_CLASSES

    @classmethod
    def get(cls) -> "GestureService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load(self) -> bool:
        if self._ready:
            return True
        weight = paths().gesture_weights
        if not __import__("os").path.isfile(weight):
            return False
        try:
            import mediapipe as mp

            self._model = CNNModel()
            self._model.load_state_dict(torch.load(weight, map_location="cpu"))
            self._model.eval()
            self._mp_hands = mp.solutions.hands.Hands(
                static_image_mode=True, max_num_hands=1, min_detection_confidence=0.2
            )
            self._ready = True
            return True
        except Exception as e:
            print(f"[GestureService] load failed: {e}")
            return False

    def recognize_base64(self, image_b64: str) -> Dict[str, Any]:
        """供 Django /recognize/ 调用"""
        if not image_b64 or not str(image_b64).strip():
            return {"error": "缺少图像数据"}
        if not self.load():
            return {
                "gesture": "A",
                "name": "字母 A（模型未加载，演示）",
                "confidence": 0.0,
                "stub": True,
            }
        raw = base64.b64decode(image_b64)
        arr = np.frombuffer(raw, np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            return {"error": "图像解码失败"}
        gesture, conf, _ = self._recognize_frame(frame)
        if gesture is None:
            return {"gesture": "None", "name": "未检测到手", "confidence": 0.0}
        return {
            "gesture": gesture,
            "name": f"字母 {gesture}",
            "confidence": float(conf),
            "stub": False,
        }

    def _recognize_frame(self, image: np.ndarray) -> Tuple[Optional[str], float, Any]:
        """TODO: 与 sign_app/gesture_model.py 对齐完整预处理逻辑"""
        import mediapipe as mp

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        res = self._mp_hands.process(rgb)
        if not res.multi_hand_landmarks:
            return None, 0.0, None
        lm = res.multi_hand_landmarks[0]
        vec = []
        for landmark in mp.solutions.hands.HandLandmark:
            p = lm.landmark[landmark]
            vec.extend([p.x, p.y, p.z])
        x = torch.from_numpy(np.array(vec, dtype=np.float32).reshape(1, 63, 1))
        with torch.no_grad():
            out = self._model(x)
            prob = torch.softmax(out, dim=1)
            conf, idx = torch.max(prob, 1)
        label = self._classes.get(idx.item(), "?")
        return label, conf.item(), None
