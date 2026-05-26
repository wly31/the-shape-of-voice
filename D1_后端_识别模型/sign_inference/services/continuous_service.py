"""
连续中文手语识别（ctcn_2）— 多帧图像 / 视频帧列表
"""
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import torch
from PIL import Image
from torchvision import transforms

from sign_inference.config import paths
from sign_inference.models import FeatureExtractor, MultiModalCNNTransformerModel

CONTINUOUS_SEQ_LEN = 170
LOW_CONFIDENCE_THRESHOLD = 0.40


def _preprocess_frame(frame: np.ndarray) -> torch.Tensor:
    t = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return t(Image.fromarray(rgb))


def _extract_keypoints(frame: np.ndarray, mp_hands) -> torch.Tensor:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = mp_hands.process(rgb)
    kp = np.zeros(126, dtype=np.float32)
    if res.multi_hand_landmarks:
        for hi, hand in enumerate(res.multi_hand_landmarks[:2]):
            start = hi * 63
            for i, lm in enumerate(hand.landmark[:21]):
                pos = start + i * 3
                if pos + 2 < 126:
                    kp[pos], kp[pos + 1], kp[pos + 2] = lm.x, lm.y, lm.z
    return torch.tensor(kp, dtype=torch.float32)


def _pad_sequence(combined: torch.Tensor, target: int = CONTINUOUS_SEQ_LEN) -> torch.Tensor:
    n = combined.shape[1]
    if n >= target:
        return combined[:, :target]
    reps = (target + n - 1) // n
    return combined.repeat(1, reps, 1)[:, :target]


class ContinuousSignService:
    _instance: Optional["ContinuousSignService"] = None

    def __init__(self):
        self._ready = False
        self._model = None
        self._extractor = None
        self._label_map: Dict[int, str] = {}
        self._mp_hands = None

    @classmethod
    def get(cls) -> "ContinuousSignService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load(self) -> bool:
        if self._ready:
            return True
        ckpt_path = paths().continuous_weights
        if not __import__("os").path.isfile(ckpt_path):
            return False
        try:
            import mediapipe as mp

            ckpt = torch.load(ckpt_path, map_location="cpu")
            self._extractor = FeatureExtractor()
            self._extractor.eval()
            self._model = MultiModalCNNTransformerModel(
                feature_dim=638,
                num_classes=len(ckpt["index_to_label"]),
                heads=2,
            )
            self._model.load_state_dict(ckpt["model_state_dict"])
            self._model.eval()
            self._label_map = {int(k): v for k, v in ckpt["index_to_label"].items()}
            self._mp_hands = mp.solutions.hands.Hands(static_image_mode=True, max_num_hands=2)
            self._ready = True
            return True
        except Exception as e:
            print(f"[ContinuousSignService] load failed: {e}")
            return False

    def predict_frames(self, bgr_frames: List[np.ndarray]) -> Dict[str, Any]:
        if not bgr_frames:
            return {"error": "无有效帧"}
        if not self.load():
            return {
                "result": "发展",
                "confidence": "75.00%",
                "frame_count": len(bgr_frames),
                "low_confidence": False,
                "stub": True,
                "warning": "模型权重未找到，返回演示数据。请设置 SIGN_PROJECT_ROOT 并放置 ctcn_2 权重。",
            }

        frames_t, kps = [], []
        for f in bgr_frames:
            frames_t.append(_preprocess_frame(f))
            kps.append(_extract_keypoints(f, self._mp_hands))
        ft = torch.stack(frames_t)
        kt = torch.stack(kps)

        with torch.no_grad():
            visual = self._extractor(ft.view(-1, 3, 256, 256)).view(1, -1, 512)
            combined = torch.cat([visual, kt.unsqueeze(0)], dim=2)
            combined = _pad_sequence(combined)
            logits = self._model(combined)
            probs = torch.softmax(logits, dim=1)

        conf = probs[0].max().item()
        idx = int(probs[0].argmax().item())
        label = self._label_map.get(idx, "未知")
        low = conf < LOW_CONFIDENCE_THRESHOLD
        warning = ""
        if len(bgr_frames) < 10:
            warning += f"仅 {len(bgr_frames)} 帧，建议 15–30 帧或上传视频。"
        if low:
            warning += " 置信度偏低，手势可能不在 100 类词表内。"

        return {
            "result": label,
            "confidence": f"{conf:.2%}",
            "frame_count": len(bgr_frames),
            "low_confidence": low,
            "stub": False,
            "warning": warning.strip(),
        }
