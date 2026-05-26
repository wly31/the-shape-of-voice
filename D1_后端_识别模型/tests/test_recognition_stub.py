"""D1 自测：无权重时返回 stub"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
os.environ.pop("SIGN_PROJECT_ROOT", None)

import numpy as np
from sign_inference.services import GestureService, ContinuousSignService


def main():
    g = GestureService.get().recognize_base64("xx")
    print("gesture:", "error" in g or "stub" in g)
    c = ContinuousSignService.get().predict_frames([np.zeros((100, 100, 3), np.uint8)])
    print("continuous:", c.get("result"), "stub=", c.get("stub"))
    print("OK")


if __name__ == "__main__":
    main()
