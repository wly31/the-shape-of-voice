"""词表分词自测（无需 GPU / 权重）"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

# 指向完整 sign 项目以扫描 words-zhcn（若存在）
sign_root = os.path.abspath(os.path.join(ROOT, "..", "..", "sign"))
if os.path.isdir(sign_root):
    os.environ.setdefault("SIGN_PROJECT_ROOT", sign_root)

from sign_inference.lexicon import analyze_sentence, segment_chinese, paths_for_token


def main():
    text = "我想今天去吃饭"
    tokens = segment_chinese(text)
    compose, segments = analyze_sentence(text)
    print("输入:", text)
    print("分词:", tokens)
    print("可合成:", compose)
    print("明细:", segments)
    for w in ["你好", "吃饭", "发展"]:
        ps = paths_for_token(w)
        print(f"  {w} -> {len(ps)} 张图")


if __name__ == "__main__":
    main()
