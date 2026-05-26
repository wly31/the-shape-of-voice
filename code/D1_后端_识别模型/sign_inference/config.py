"""
路径与运行配置。默认从环境变量 SIGN_PROJECT_ROOT 读取完整项目 sign/ 目录。
"""
import os
from dataclasses import dataclass


def get_project_root() -> str:
    root = os.environ.get("SIGN_PROJECT_ROOT")
    if root and os.path.isdir(root):
        return os.path.abspath(root)
    # 开发时：本包的上两级 → SignTranslate-初步提交，再 ../sign
    here = os.path.dirname(os.path.abspath(__file__))
    guess = os.path.abspath(os.path.join(here, "..", "..", "..", "sign"))
    if os.path.isdir(guess):
        return guess
    return os.path.abspath(os.path.join(here, ".."))


@dataclass(frozen=True)
class RecognitionPaths:
    """D1：仅识别模型权重路径"""
    root: str
    gesture_weights: str
    continuous_weights: str

    @classmethod
    def from_root(cls, root: str) -> "RecognitionPaths":
        return cls(
            root=root,
            gesture_weights=os.path.join(root, "model", "CNN_model_alphabet_SIBI.pth"),
            continuous_weights=os.path.join(root, "ctcn_2", "models", "best_model.pth"),
        )


def paths() -> RecognitionPaths:
    return RecognitionPaths.from_root(get_project_root())
