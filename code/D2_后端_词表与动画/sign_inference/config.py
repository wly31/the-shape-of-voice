"""D2 专用配置：词库与输出目录"""
import os
from dataclasses import dataclass


def get_project_root() -> str:
    root = os.environ.get("SIGN_PROJECT_ROOT")
    if root and os.path.isdir(root):
        return os.path.abspath(root)
    here = os.path.dirname(os.path.abspath(__file__))
    guess = os.path.abspath(os.path.join(here, "..", "..", "..", "sign"))
    if os.path.isdir(guess):
        return guess
    return os.path.abspath(os.path.join(here, ".."))


@dataclass(frozen=True)
class LexiconPaths:
    root: str
    words_dir: str
    sign_output_dir: str

    @classmethod
    def from_root(cls, root: str) -> "LexiconPaths":
        return cls(
            root=root,
            words_dir=os.path.join(root, "static", "sign_app", "words-zhcn"),
            sign_output_dir=os.path.join(root, "static", "sign_app", "output"),
        )


def paths() -> LexiconPaths:
    return LexiconPaths.from_root(get_project_root())
