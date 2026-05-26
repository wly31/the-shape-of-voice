"""
中文手语词表业务（从 sign_app/sign_lexicon.py 提炼，不依赖 Django）。
"""
import os
import re
from typing import Dict, List, Optional, Tuple

import jieba

from sign_inference.config import paths

CN2EN: Dict[str, str] = {
    "你": "you", "我": "me", "他": "he", "她": "she",
    "好": "good", "喜欢": "like", "爱": "love",
    "学习": "study", "吃": "eat", "吃饭": "eat_meal",
    "来": "come", "去": "go", "看": "see", "有": "have", "是": "yes",
    "今天": "today", "明天": "tomorrow", "谢谢": "give",
}

ZH_PARTICLES = frozenset({"的", "了", "着", "过", "吗", "呢", "吧", "啊"})
_punct_re = re.compile(r"([，。！？；、,\.!\?;])")

_vocab_cache: Optional[Dict[str, str]] = None
_match_keys_cache: Optional[List[str]] = None


def get_vocab_index(words_dir: Optional[str] = None) -> Dict[str, str]:
    global _vocab_cache, _match_keys_cache
    if _vocab_cache is not None:
        return _vocab_cache
    words_dir = words_dir or paths().words_dir
    index: Dict[str, str] = {}
    if os.path.isdir(words_dir):
        for name in os.listdir(words_dir):
            if name.lower().endswith(".png"):
                stem = os.path.splitext(name)[0]
                index[stem] = os.path.join(words_dir, name)
    _vocab_cache = index
    _match_keys_cache = sorted(set(CN2EN.keys()) | set(index.keys()), key=len, reverse=True)
    return index


def _resolve_stem(stem: str, vocab: Dict[str, str]) -> Optional[str]:
    if stem in vocab:
        return vocab[stem]
    mapped = CN2EN.get(stem)
    if mapped and mapped in vocab:
        return vocab[mapped]
    return None


def paths_for_token(token: str, words_dir: Optional[str] = None) -> List[str]:
    if not token or token in ZH_PARTICLES or _punct_re.fullmatch(token):
        return []
    vocab = get_vocab_index(words_dir)
    p = _resolve_stem(token, vocab)
    if p:
        return [p]
    out: List[str] = []
    for char in token:
        if char in ZH_PARTICLES:
            continue
        cp = _resolve_stem(char, vocab)
        if cp:
            out.append(cp)
    return out


def segment_chinese(text: str, words_dir: Optional[str] = None) -> List[str]:
    tokens: List[str] = []
    for fragment in _punct_re.split(text):
        if not fragment:
            continue
        if _punct_re.fullmatch(fragment):
            tokens.append(fragment)
            continue
        for word in jieba.lcut(fragment):
            word = word.strip()
            if word and paths_for_token(word, words_dir):
                tokens.append(word)
    return tokens


def analyze_sentence(text: str, words_dir: Optional[str] = None) -> Tuple[List[str], List[dict]]:
    """返回 (可合成 token 列表, 每词状态)"""
    compose: List[str] = []
    segments: List[dict] = []
    for fragment in _punct_re.split(text):
        if not fragment:
            continue
        if _punct_re.fullmatch(fragment):
            segments.append({"word": fragment, "status": "punct"})
            compose.append(fragment)
            continue
        for word in jieba.lcut(fragment):
            word = word.strip()
            if not word:
                continue
            if word in ZH_PARTICLES:
                segments.append({"word": word, "status": "particle"})
                continue
            ps = paths_for_token(word, words_dir)
            if ps:
                segments.append({"word": word, "status": "ok", "count": len(ps)})
                compose.append(word)
            else:
                segments.append({"word": word, "status": "missing"})
    return compose, segments
