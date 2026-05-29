"""
中文手语词表：分词、词→图片路径解析。
词库目录：static/sign_app/words-zhcn（英文文件名 + 少量中文文件名）
"""
import os
import re
import jieba
import cv2
import numpy as np
from PIL import Image
from typing import Dict, List, Optional, Tuple, Any

import torch
from torchvision import transforms

# 中文词/字 → words-zhcn 下文件名（不含 .png）
CN2EN: Dict[str, str] = {
    # 代词
    '你': 'you', '我': 'me', '他': 'he', '她': 'she', '它': 'it',
    '我们': 'we', '你们': 'you_all', '大家': 'everyone', '自己': 'self', '您': 'you_polite',
    # 常用动词
    '好': 'good', '喜欢': 'like', '爱': 'love', '明白': 'understand', '懂': 'understand',
    '知道': 'know', '认识': 'know_person', '觉得': 'think', '认为': 'think',
    '学习': 'study', '写': 'write', '读': 'read', '听': 'listen', '说': 'speak',
    '叫': 'call', '喊': 'shout', '买': 'buy', '卖': 'sell', '给': 'give',
    '要': 'want', '需要': 'need', '愿意': 'willing', '可以': 'can', '能': 'can',
    '能够': 'able', '会': 'will', '想': 'want_to', '做': 'do', '吃': 'eat',
    '喝': 'drink', '吃饭': 'eat_meal', '来': 'come', '去': 'go', '看': 'see',
    '有': 'have', '是': 'yes', '不是': 'not', '没有': 'not', '没': 'not',
    '不': 'not', '在': 'at', '当': 'when',
    # 时间/地点
    '那里': 'there', '这里': 'here', '那儿': 'there', '这儿': 'here',
    '昨天': 'yesterday', '今天': 'today', '明天': 'tomorrow', '后天': 'day_after_tomorrow',
    # 礼貌 / 日常
    '谢谢': 'give', '感谢': 'give', '请': 'give', '再见': 'go', '对不起': 'not',
    '对': 'yes', '对的': 'yes', '嗯': 'yes', '饭': 'meal', '东西': 'have',
    # 连词/副词（用已有词近似）
    '也': 'yes', '都': 'everyone', '很': 'good', '非常': 'good', '再': 'come',
    '还': 'have', '又': 'come', '就': 'yes', '才': 'can', '已经': 'yes',
    '所以': 'yes', '但是': 'not', '如果': 'when',
    # 疑问（仅映射到词库中已有的英文/中文文件名）
    '什么': 'know', '哪': 'there', '哪里': 'there', '怎么': 'think',
    '为什么': '因为', '为何': '因为',
}

# 无手势图、仅作分词用的虚词（跳过，不插入黑帧）
ZH_PARTICLES = frozenset({
    '的', '了', '着', '过', '啊', '呀', '吧', '嘛', '吗', '呢', '之', '所',
    '被', '把', '给', '让', '向', '从', '到', '和', '与', '或', '及',
})

_punct_re = re.compile(r'([，。！？；、,\.!\?;])')


def _words_dir() -> str:
    from django.conf import settings
    return os.path.join(settings.BASE_DIR, 'static', 'sign_app', 'words-zhcn')


_vocab_cache: Optional[Dict[str, str]] = None
_match_keys_cache: Optional[List[str]] = None


def get_vocab_index() -> Dict[str, str]:
    """文件名/中文名 → 图片绝对路径"""
    global _vocab_cache, _match_keys_cache
    if _vocab_cache is not None:
        return _vocab_cache

    words_dir = _words_dir()
    index: Dict[str, str] = {}
    if os.path.isdir(words_dir):
        for name in os.listdir(words_dir):
            if not name.lower().endswith('.png'):
                continue
            stem = os.path.splitext(name)[0]
            index[stem] = os.path.join(words_dir, name)

    _vocab_cache = index
    # 用于句内最长匹配：中文键 + 英文键，按长度降序
    keys = set(CN2EN.keys()) | set(index.keys())
    _match_keys_cache = sorted(keys, key=len, reverse=True)
    return index


def _resolve_stem(stem: str, vocab: Dict[str, str]) -> Optional[str]:
    if not stem:
        return None
    if stem in vocab:
        return vocab[stem]
    mapped = CN2EN.get(stem)
    if mapped and mapped in vocab:
        return vocab[mapped]
    return None


def paths_for_token(token: str) -> List[str]:
    """一个词对应 0~多张手语图路径"""
    if not token or token in ZH_PARTICLES:
        return []
    if _punct_re.fullmatch(token):
        return []

    vocab = get_vocab_index()
    paths: List[str] = []

    # 1) 整词
    p = _resolve_stem(token, vocab)
    if p:
        return [p]

    # 2) 多字：逐字收集（允许部分命中）
    if len(token) > 1:
        for char in token:
            if char in ZH_PARTICLES:
                continue
            cp = _resolve_stem(char, vocab)
            if cp:
                paths.append(cp)
        if paths:
            return paths

    # 3) 句内最长匹配（对 jieba 未切出的词再拆）
    rest = token
    while rest:
        matched = False
        for key in _match_keys_cache or []:
            if rest.startswith(key):
                mp = _resolve_stem(key, vocab)
                if mp:
                    paths.append(mp)
                rest = rest[len(key):]
                matched = True
                break
        if not matched:
            cp = _resolve_stem(rest[0], vocab)
            if cp:
                paths.append(cp)
            rest = rest[1:]

    return paths


def segment_chinese(text: str) -> List[str]:
    """复杂句：jieba 分词 + 长词二次切分"""
    tokens: List[str] = []
    for fragment in _punct_re.split(text):
        if not fragment:
            continue
        if _punct_re.fullmatch(fragment):
            tokens.append(fragment)
            continue
        for word in jieba.lcut(fragment):
            word = word.strip()
            if not word:
                continue
            if paths_for_token(word):
                tokens.append(word)
            else:
                # 整词无图：用最长匹配拆成多个可翻译片段
                sub_tokens = _greedy_split_word(word)
                tokens.extend(sub_tokens)

    return [t for t in tokens if t.strip()]


def _greedy_split_word(word: str) -> List[str]:
    """把未知词拆成更短的已知子串，便于逐段翻译"""
    if paths_for_token(word):
        return [word]

    vocab = get_vocab_index()
    keys = _match_keys_cache or []
    parts: List[str] = []
    rest = word
    while rest:
        found = False
        for key in keys:
            if len(key) < 1 or not rest.startswith(key):
                continue
            if _resolve_stem(key, vocab) or key in ZH_PARTICLES:
                parts.append(key)
                rest = rest[len(key):]
                found = True
                break
        if not found:
            parts.append(rest[0])
            rest = rest[1:]
    return parts


def analyze_sentence(text: str) -> Tuple[List[str], List[dict]]:
    """
    返回 (用于合成的 token 列表, 每词状态说明)
    status: ok | particle | missing
    """
    raw_tokens: List[str] = []
    for fragment in _punct_re.split(text):
        if not fragment:
            continue
        if _punct_re.fullmatch(fragment):
            raw_tokens.append(fragment)
            continue
        raw_tokens.extend(jieba.lcut(fragment))

    segments = []
    compose_tokens: List[str] = []

    for word in raw_tokens:
        word = word.strip()
        if not word:
            continue
        if word in ZH_PARTICLES:
            segments.append({'word': word, 'status': 'particle'})
            continue
        if _punct_re.fullmatch(word):
            segments.append({'word': word, 'status': 'punct'})
            compose_tokens.append(word)
            continue

        paths = paths_for_token(word)
        if paths:
            segments.append({'word': word, 'status': 'ok', 'count': len(paths)})
            compose_tokens.append(word)
        else:
            # 再尝试拆字
            sub_ok = False
            for char in word:
                if char in ZH_PARTICLES:
                    continue
                if paths_for_token(char):
                    sub_ok = True
            if sub_ok:
                segments.append({'word': word, 'status': 'partial'})
                compose_tokens.append(word)
            else:
                segments.append({'word': word, 'status': 'missing'})

    return compose_tokens, segments


def collect_image_paths(tokens: List[str]) -> Tuple[List[str], List[str]]:
    """汇总所有图片路径；返回 (paths, missing_words)"""
    all_paths: List[str] = []
    missing: List[str] = []
    for token in tokens:
        if token in ZH_PARTICLES or _punct_re.fullmatch(token):
            continue
        paths = paths_for_token(token)
        if paths:
            all_paths.extend(paths)
        else:
            missing.append(token)
    return all_paths, missing


def display_name_for_vocab_stem(stem: str) -> str:
    """词库文件名 → 展示用中文名（优先 CN2EN 反查）。"""
    if not stem:
        return stem
    if not stem.isascii():
        return stem
    cn_words = [zh for zh, en in CN2EN.items() if en == stem]
    if cn_words:
        cn_words.sort(key=lambda x: (-len(x), x))
        return cn_words[0]
    return stem


VOCAB_MATCH_SIZE = (224, 329)  # (宽, 高)
VOCAB_CANONICAL_SIZE = 128
VOCAB_SKETCH_SCALES = (0.85, 1.0, 1.15)
# 自绘线稿匹配阈值（ORB 特征 + 轮廓）
VOCAB_MIN_ORB_GOOD = 5
VOCAB_MIN_HYBRID_SCORE = 3.0
VOCAB_MIN_HYBRID_MARGIN = 1.5
VOCAB_MAX_SKETCH_DIST = 42.0
VOCAB_MIN_SKETCH_MARGIN = 4.0
# ResNet 深度特征（主信号）
VOCAB_MIN_EMBED_SIM = 0.68
VOCAB_MIN_EMBED_MARGIN = 0.035
VOCAB_RELAXED_EMBED_SIM = 0.52
VOCAB_RELAXED_EMBED_MARGIN = 0.02

VOCAB_REFINE_TOP_K = 6  # 仅对 embedding Top-K 做慢速轮廓比对

# 摄像头多帧投票（真人视频比线稿难，阈值低于上传识图）
CAMERA_MIN_CONFIDENCE = 0.40
CAMERA_MIN_VOTES = 2
CAMERA_RELAXED_VOTE_MIN = 0.34
CAMERA_FALLBACK_MIN = 0.36  # 宽松兜底：有候选时标为「可能」

_vocab_sketch_cache: Optional[Dict[str, Dict[str, Any]]] = None
_embed_matrix: Optional[np.ndarray] = None
_embed_row_stems: Optional[List[str]] = None
_orb_detector: Optional[cv2.ORB] = None
_embed_extractor = None
_embed_transform = None


def _get_orb() -> cv2.ORB:
    global _orb_detector
    if _orb_detector is None:
        _orb_detector = cv2.ORB_create(800)
    return _orb_detector


def _get_embed_model():
    """懒加载 ResNet18 特征提取器（与连续手语模型同源）。"""
    global _embed_extractor, _embed_transform
    if _embed_extractor is None:
        from .CNN_LSTM import FeatureExtractor

        _embed_transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])
        _embed_extractor = FeatureExtractor(model_name='resnet18')
        _embed_extractor.eval()
    return _embed_extractor, _embed_transform


def _augmented_norms_for_embed(norm_bgr: np.ndarray) -> List[np.ndarray]:
    """原图 + 水平翻转，提升左右朝向不一致时的召回。"""
    return [norm_bgr, cv2.flip(norm_bgr, 1)]


def _embeddings_batch(norm_bgr_list: List[np.ndarray]) -> np.ndarray:
    """批量提取 L2 归一化特征，一次前向传播多张图。"""
    if not norm_bgr_list:
        return np.zeros((0, 512), dtype=np.float32)
    model, tfm = _get_embed_model()
    tensors = []
    for norm in norm_bgr_list:
        rgb = cv2.cvtColor(norm, cv2.COLOR_BGR2RGB)
        tensors.append(tfm(Image.fromarray(rgb)))
    batch = torch.stack(tensors)
    with torch.inference_mode():
        vecs = model(batch).cpu().numpy().astype(np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-6)
    return vecs / norms


def _rebuild_embed_index(cache: Dict[str, Dict[str, Any]]) -> None:
    """词库特征矩阵，用于一次矩阵乘法算完全部相似度。"""
    global _embed_matrix, _embed_row_stems
    rows: List[np.ndarray] = []
    row_stems: List[str] = []
    for stem, entry in cache.items():
        norm = entry.get('norm')
        if norm is None:
            continue
        vecs = _embeddings_batch(_augmented_norms_for_embed(norm))
        for i in range(len(vecs)):
            rows.append(vecs[i])
            row_stems.append(stem)
    if rows:
        _embed_matrix = np.stack(rows, axis=0)
        _embed_row_stems = row_stems
    else:
        _embed_matrix = np.zeros((0, 512), dtype=np.float32)
        _embed_row_stems = []


def _stem_embedding_similarities(probe_norms: List[np.ndarray]) -> Dict[str, float]:
    """一次批量推理 + 矩阵乘法，返回每个词的最高余弦相似度。"""
    if _embed_matrix is None or _embed_row_stems is None or len(_embed_row_stems) == 0:
        return {}

    aug_norms: List[np.ndarray] = []
    for norm in probe_norms:
        aug_norms.extend(_augmented_norms_for_embed(norm))
    if not aug_norms:
        return {}

    probe_vecs = _embeddings_batch(aug_norms)
    col_best = probe_vecs @ _embed_matrix.T
    row_max = col_best.max(axis=0)

    stem_sim: Dict[str, float] = {}
    for idx, stem in enumerate(_embed_row_stems):
        sim = float(row_max[idx])
        if sim > stem_sim.get(stem, 0.0):
            stem_sim[stem] = sim
    return stem_sim


def _load_image_bgr(path: str) -> Optional[np.ndarray]:
    try:
        with open(path, 'rb') as f:
            buf = np.frombuffer(f.read(), dtype=np.uint8)
        return cv2.imdecode(buf, cv2.IMREAD_COLOR)
    except OSError:
        return None


def _rough_stroke_mask(gray: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, mask = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    if np.count_nonzero(mask) < 50:
        _, mask = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return mask


def _crop_to_stroke_content(image_bgr: np.ndarray, margin_ratio: float = 0.10) -> np.ndarray:
    """按笔画外接框裁剪，避免整图拉伸导致全身线稿变形。"""
    h, w = image_bgr.shape[:2]
    max_side = max(h, w)
    scale = min(1.0, 900.0 / max_side)
    if scale < 1.0:
        small = cv2.resize(
            image_bgr,
            (max(1, int(w * scale)), max(1, int(h * scale))),
            interpolation=cv2.INTER_AREA,
        )
    else:
        small = image_bgr
        scale = 1.0

    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    mask = _rough_stroke_mask(gray)
    pts = cv2.findNonZero(mask)
    if pts is None:
        return image_bgr

    x, y, bw, bh = cv2.boundingRect(pts)
    mx = int(bw * margin_ratio)
    my = int(bh * margin_ratio)
    inv = 1.0 / scale
    x1 = int(max(0, (x - mx) * inv))
    y1 = int(max(0, (y - my) * inv))
    x2 = int(min(w, (x + bw + mx) * inv))
    y2 = int(min(h, (y + bh + my) * inv))
    if x2 <= x1 or y2 <= y1:
        return image_bgr
    cropped = image_bgr[y1:y2, x1:x2]
    ch, cw = cropped.shape[:2]
    if ch > cw * 1.35:
        cropped = cropped[: int(ch * 0.76), :]
    return cropped


def _letterbox_bgr(image_bgr: np.ndarray, size_wh: Tuple[int, int] = VOCAB_MATCH_SIZE) -> np.ndarray:
    """保持宽高比缩放到目标画布，白底居中。"""
    tw, th = size_wh
    h, w = image_bgr.shape[:2]
    if h < 1 or w < 1:
        return np.full((th, tw, 3), 255, dtype=np.uint8)
    scale = min(tw / w, th / h)
    nw = max(1, int(w * scale))
    nh = max(1, int(h * scale))
    resized = cv2.resize(image_bgr, (nw, nh), interpolation=cv2.INTER_AREA)
    canvas = np.full((th, tw, 3), 255, dtype=np.uint8)
    x0 = (tw - nw) // 2
    y0 = (th - nh) // 2
    canvas[y0 : y0 + nh, x0 : x0 + nw] = resized
    return canvas


def _preprocess_for_matching(image_bgr: np.ndarray) -> np.ndarray:
    return _letterbox_bgr(_crop_to_stroke_content(image_bgr))


def _keep_main_strokes(mask: np.ndarray, min_area_ratio: float = 0.008) -> np.ndarray:
    """去掉箭头、噪点等过小连通域，保留主体笔画。"""
    n_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    if n_labels <= 1:
        return mask
    total = mask.shape[0] * mask.shape[1]
    kept = np.zeros_like(mask)
    for i in range(1, n_labels):
        if stats[i, cv2.CC_STAT_AREA] >= total * min_area_ratio:
            kept[labels == i] = 255
    return kept if np.any(kept) else mask


def _stroke_mask_from_norm(norm_bgr: np.ndarray) -> np.ndarray:
    """从已归一化画布提取笔画掩膜。"""
    gray = cv2.cvtColor(norm_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 5, 40, 40)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    if np.count_nonzero(mask) < 50:
        _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((2, 2), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return _keep_main_strokes(mask)


def _canonicalize_stroke_mask(mask: np.ndarray) -> np.ndarray:
    pts = cv2.findNonZero(mask)
    if pts is None:
        return np.zeros((VOCAB_CANONICAL_SIZE, VOCAB_CANONICAL_SIZE), np.uint8)
    x, y, w, h = cv2.boundingRect(pts)
    crop = mask[y : y + h, x : x + w]
    side = max(w, h, 1)
    pad = np.zeros((side, side), np.uint8)
    oy, ox = (side - h) // 2, (side - w) // 2
    pad[oy : oy + h, ox : ox + w] = crop
    return cv2.resize(
        pad,
        (VOCAB_CANONICAL_SIZE, VOCAB_CANONICAL_SIZE),
        interpolation=cv2.INTER_AREA,
    )


def _sketch_signature_from_norm(norm_bgr: np.ndarray) -> np.ndarray:
    mask = _canonicalize_stroke_mask(_stroke_mask_from_norm(norm_bgr))
    gray = cv2.cvtColor(norm_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = _canonicalize_stroke_mask(cv2.Canny(gray, 30, 100))
    return cv2.bitwise_or(mask, edges)


def _sketch_probes_from_image(
    image_bgr: np.ndarray,
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """生成多种裁剪/归一化探针，提升全身简笔画与词库半身图的匹配率。"""
    cropped = _crop_to_stroke_content(image_bgr)
    h, w = cropped.shape[:2]
    crop_list = [cropped]
    if h > w * 1.2:
        upper = cropped[: int(h * 0.76), :]
        if upper.size > 0:
            crop_list.append(upper)

    probes: List[Tuple[np.ndarray, np.ndarray]] = []
    seen: set = set()
    for crop in crop_list:
        norm = _letterbox_bgr(crop)
        sig = _sketch_signature_from_norm(norm)
        key = sig.tobytes()
        if key in seen:
            continue
        seen.add(key)
        probes.append((norm, sig))
    if not probes:
        norm = _preprocess_for_matching(image_bgr)
        probes.append((norm, _sketch_signature_from_norm(norm)))
    return probes


def _template_similarity(probe_norm: np.ndarray, ref_norm: np.ndarray) -> float:
    probe_gray = cv2.cvtColor(probe_norm, cv2.COLOR_BGR2GRAY)
    ref_gray = cv2.cvtColor(ref_norm, cv2.COLOR_BGR2GRAY)
    probe_inv = 255 - probe_gray
    ref_inv = 255 - ref_gray
    if probe_inv.shape != ref_inv.shape:
        ref_inv = cv2.resize(ref_inv, (probe_inv.shape[1], probe_inv.shape[0]))
    result = cv2.matchTemplate(probe_inv, ref_inv, cv2.TM_CCOEFF_NORMED)
    return float(max(0.0, result[0, 0]))


def _scale_stroke_mask(mask: np.ndarray, scale: float) -> np.ndarray:
    if abs(scale - 1.0) < 1e-3:
        return mask
    nh = max(8, int(VOCAB_CANONICAL_SIZE * scale))
    nw = max(8, int(VOCAB_CANONICAL_SIZE * scale))
    scaled = cv2.resize(mask, (nw, nh), interpolation=cv2.INTER_AREA)
    canvas = np.zeros((VOCAB_CANONICAL_SIZE, VOCAB_CANONICAL_SIZE), np.uint8)
    y0 = max(0, (VOCAB_CANONICAL_SIZE - nh) // 2)
    x0 = max(0, (VOCAB_CANONICAL_SIZE - nw) // 2)
    y1, x1 = min(VOCAB_CANONICAL_SIZE, y0 + nh), min(VOCAB_CANONICAL_SIZE, x0 + nw)
    canvas[y0:y1, x0:x1] = scaled[: y1 - y0, : x1 - x0]
    return canvas


def _probe_variants(mask: np.ndarray) -> List[np.ndarray]:
    """自绘线稿常有粗细/比例差异，生成多种形态再比对。"""
    variants = [mask]
    kernel = np.ones((3, 3), np.uint8)
    variants.append(cv2.dilate(mask, kernel, 1))
    variants.append(cv2.dilate(mask, kernel, 2))
    variants.append(cv2.erode(mask, kernel, 1))
    for scale in VOCAB_SKETCH_SCALES:
        variants.append(_scale_stroke_mask(mask, scale))
    return variants


def _chamfer_distance(a: np.ndarray, b: np.ndarray) -> float:
    def one_way(src: np.ndarray, dst: np.ndarray) -> float:
        if not np.any(src):
            return 1e3
        dt = cv2.distanceTransform(255 - dst, cv2.DIST_L2, 3)
        return float(np.mean(dt[src > 0]))

    return (one_way(a, b) + one_way(b, a)) * 0.5


def _shape_distance(a: np.ndarray, b: np.ndarray) -> float:
    cs, _ = cv2.findContours(a, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    ct, _ = cv2.findContours(b, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cs or not ct:
        return 5.0
    ca = max(cs, key=cv2.contourArea)
    cb = max(ct, key=cv2.contourArea)
    if cv2.contourArea(ca) < 20 or cv2.contourArea(cb) < 20:
        return 5.0
    return float(cv2.matchShapes(ca, cb, cv2.CONTOURS_MATCH_I1, 0))


def _iou_distance(a: np.ndarray, b: np.ndarray) -> float:
    inter = np.logical_and(a > 0, b > 0).sum()
    union = np.logical_or(a > 0, b > 0).sum()
    return 1.0 - (inter / union if union else 0.0)


def _ncc_distance(a: np.ndarray, b: np.ndarray) -> float:
    af = np.clip(a, 0, 255).astype(np.float32).ravel()
    bf = np.clip(b, 0, 255).astype(np.float32).ravel()
    af -= af.mean()
    bf -= bf.mean()
    denom = float(np.linalg.norm(af) * np.linalg.norm(bf))
    if denom < 1e-6:
        return 1.0
    return 1.0 - max(0.0, float(np.dot(af, bf) / denom))


def _sketch_distance(probe: np.ndarray, ref_mask: np.ndarray) -> float:
    best = 1e9
    for variant in _probe_variants(probe):
        dist = (
            0.35 * _chamfer_distance(variant, ref_mask)
            + 2.0 * _shape_distance(variant, ref_mask)
            + 28.0 * _iou_distance(variant, ref_mask)
            + 12.0 * _ncc_distance(variant, ref_mask)
        )
        best = min(best, dist)
    return best


def _orb_good_count(probe: np.ndarray, ref_des: Optional[np.ndarray]) -> int:
    if ref_des is None or len(ref_des) < 3:
        return 0
    orb = _get_orb()
    _, des = orb.detectAndCompute(probe, None)
    if des is None or len(des) < 3:
        return 0
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    try:
        pairs = matcher.knnMatch(des, ref_des, k=2)
    except cv2.error:
        return 0
    good = 0
    for pair in pairs:
        if len(pair) == 2 and pair[0].distance < 0.78 * pair[1].distance:
            good += 1
    return good


def get_vocab_sketch_cache() -> Dict[str, Dict[str, Any]]:
    """词库线稿掩膜 + ORB 描述子，首次调用时构建。"""
    global _vocab_sketch_cache
    if _vocab_sketch_cache is not None:
        return _vocab_sketch_cache

    words_dir = _words_dir()
    cache: Dict[str, Dict[str, Any]] = {}
    orb = _get_orb()
    if os.path.isdir(words_dir):
        for name in os.listdir(words_dir):
            if not name.lower().endswith('.png'):
                continue
            stem = os.path.splitext(name)[0]
            image = _load_image_bgr(os.path.join(words_dir, name))
            if image is None:
                continue
            norm = _preprocess_for_matching(image)
            mask = _sketch_signature_from_norm(norm)
            _, des = orb.detectAndCompute(mask, None)
            cache[stem] = {
                'mask': mask,
                'des': des,
                'norm': norm,
            }

    _vocab_sketch_cache = cache
    _rebuild_embed_index(cache)
    return cache


def warm_vocab_sketch_cache() -> None:
    """后台预热词库（首次识别不再等待数十秒）。"""
    get_vocab_sketch_cache()


def _score_against_ref(
    probe_entries: List[Tuple[np.ndarray, np.ndarray]],
    ref_entry: Dict[str, Any],
) -> Tuple[float, int, float, float]:
    ref_mask = ref_entry['mask']
    ref_des = ref_entry.get('des')
    ref_norm = ref_entry.get('norm')
    best_orb = 0
    best_sketch = 1e9
    best_template = 0.0
    for probe_norm, probe_sig in probe_entries:
        if ref_norm is not None:
            best_template = max(best_template, _template_similarity(probe_norm, ref_norm))
        for variant in _probe_variants(probe_sig):
            best_orb = max(best_orb, _orb_good_count(variant, ref_des))
            best_sketch = min(best_sketch, _sketch_distance(variant, ref_mask))
    hybrid = best_orb * 1.2 - best_sketch * 0.32 + best_template * 18.0
    return hybrid, best_orb, best_sketch, best_template


def _confidence_from_match(
    embed_sim: float,
    second_embed_sim: float,
    hybrid: float,
    sketch_dist: float,
) -> float:
    embed_margin = max(0.0, embed_sim - second_embed_sim)
    return max(
        0.0,
        min(
            1.0,
            0.62 * embed_sim
            + 0.23 * min(1.0, embed_margin / 0.12)
            + 0.15 * max(0.0, 1.0 - sketch_dist / 45.0),
        ),
    )


def _is_acceptable_match(
    embed_sim: float,
    second_embed_sim: float,
    hybrid: float,
    second_hybrid: float,
    orb_good: int,
    sketch_dist: float,
    second_sketch_dist: Optional[float] = None,
    relaxed: bool = False,
) -> bool:
    embed_margin = embed_sim - second_embed_sim
    min_sim = VOCAB_RELAXED_EMBED_SIM if relaxed else VOCAB_MIN_EMBED_SIM
    min_margin = VOCAB_RELAXED_EMBED_MARGIN if relaxed else VOCAB_MIN_EMBED_MARGIN

    if embed_sim >= min_sim and embed_margin >= min_margin:
        return True
    if embed_sim >= min_sim + 0.06:
        return True

    margin = hybrid - second_hybrid
    if hybrid >= VOCAB_MIN_HYBRID_SCORE:
        if margin >= VOCAB_MIN_HYBRID_MARGIN or orb_good >= 15:
            if not (orb_good < VOCAB_MIN_ORB_GOOD and sketch_dist > 25.0):
                return True
        elif orb_good >= VOCAB_MIN_ORB_GOOD:
            return True

    if second_sketch_dist is not None:
        sketch_margin = second_sketch_dist - sketch_dist
        if sketch_dist < VOCAB_MAX_SKETCH_DIST and sketch_margin >= VOCAB_MIN_SKETCH_MARGIN:
            return True
    return False


def _score_vocabulary_all(
    image_bgr: np.ndarray,
) -> Tuple[List[Tuple[float, float, float, int, float, float, str]], List[Tuple[np.ndarray, np.ndarray]]]:
    """
    返回按综合分排序的列表。
    每项: (final, embed_sim, hybrid, orb, sketch, template, stem)
    """
    cache = get_vocab_sketch_cache()
    probe_entries = _sketch_probes_from_image(image_bgr)
    if not any(np.any(sig) for _, sig in probe_entries):
        return [], probe_entries

    probe_norms = [norm for norm, _ in probe_entries]
    stem_embed_sims = _stem_embedding_similarities(probe_norms)
    if not stem_embed_sims:
        return [], probe_entries

    refine_stems = set(
        s for s, _ in sorted(stem_embed_sims.items(), key=lambda x: x[1], reverse=True)[
            :VOCAB_REFINE_TOP_K
        ]
    )

    scored: List[Tuple[float, float, float, int, float, float, str]] = []
    for stem, entry in cache.items():
        embed_sim = stem_embed_sims.get(stem, 0.0)
        if stem in refine_stems:
            hybrid, orb_good, sketch_dist, template = _score_against_ref(
                probe_entries, entry
            )
        else:
            hybrid, orb_good, sketch_dist, template = 0.0, 0, 50.0, embed_sim
        final = embed_sim * 100.0 + hybrid * 0.25
        scored.append((final, embed_sim, hybrid, orb_good, sketch_dist, template, stem))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored, probe_entries


def rank_vocabulary_matches(
    image_bgr: np.ndarray,
    top_k: int = 3,
    relaxed: bool = False,
) -> List[Tuple[str, str, float]]:
    """
    与 words-zhcn 线稿比对（支持自绘线稿）。
    relaxed=True 时在无高置信匹配时仍返回最佳候选（供前端标为不确定）。
    """
    if image_bgr is None or image_bgr.size == 0:
        return []

    if not get_vocab_sketch_cache():
        return []

    scored, _ = _score_vocabulary_all(image_bgr)
    if not scored:
        return []

    embed_ranked = sorted(scored, key=lambda x: x[1], reverse=True)
    sketch_ranked = sorted(scored, key=lambda x: x[4])
    best = scored[0]
    second = scored[1] if len(scored) > 1 else best
    best_embed = embed_ranked[0][1]
    second_embed = embed_ranked[1][1] if len(embed_ranked) > 1 else best_embed - 0.1
    best_sketch = sketch_ranked[0][4]
    second_sketch = sketch_ranked[1][4] if len(sketch_ranked) > 1 else best_sketch + 10.0

    accepted = _is_acceptable_match(
        best_embed,
        second_embed,
        best[2],
        second[2],
        best[3],
        best_sketch,
        second_sketch,
        relaxed=relaxed,
    )
    if not accepted and not relaxed:
        return []
    if not accepted and relaxed and best_embed < VOCAB_RELAXED_EMBED_SIM - 0.04:
        return []

    display_scored = list(embed_ranked)

    results: List[Tuple[str, str, float]] = []
    for i, item in enumerate(display_scored[:top_k]):
        _final, embed_sim, hybrid, _orb, sketch_dist, _template, stem = item
        next_embed = display_scored[i + 1][1] if i + 1 < len(display_scored) else embed_sim - 0.1
        label = display_name_for_vocab_stem(stem)
        conf = _confidence_from_match(embed_sim, next_embed, hybrid, sketch_dist)
        if relaxed and not accepted:
            conf = min(conf, 0.42)
        results.append((label, stem, conf))
    return results


def match_image_to_vocabulary(
    image_bgr: np.ndarray,
) -> Optional[Tuple[str, float, str]]:
    """与词库线稿/自绘线稿比对，返回最佳匹配。"""
    ranked = rank_vocabulary_matches(image_bgr, top_k=1)
    if not ranked:
        return None
    label, stem, confidence = ranked[0]
    return label, confidence, stem


def format_vocab_display(label: str, stem: str) -> str:
    if stem.isascii() and label != stem:
        return f'{label}（{stem}）'
    return label


def list_vocab_recognition_words() -> List[str]:
    """词库中可用于摄像头/识图比对的中文展示名（去重排序）。"""
    vocab = get_vocab_index()
    names = {display_name_for_vocab_stem(stem) for stem in vocab}
    return sorted(names, key=lambda x: (len(x), x))


def _camera_no_match_payload(
    description: str,
    warning: str = '',
    frame_count: int = 0,
    vote_detail: Optional[str] = None,
    top3: Optional[List[dict]] = None,
) -> Dict[str, Any]:
    desc = description
    if vote_detail:
        desc += f'（{vote_detail}）'
    top3 = top3 or []
    if top3:
        desc += ' · 最接近: ' + '、'.join(t['word'] for t in top3[:3])
    return {
        'mode': 'vocab',
        'matched': False,
        'gesture': 'None',
        'word': None,
        'stem': None,
        'name': '未匹配词库',
        'description': desc,
        'confidence': 0.0,
        'confidence_pct': '0%',
        'uncertain': False,
        'top3': top3,
        'warning': warning or '未达阈值。可对词库原图摆拍，或用手语图片识别页上传截图。',
        'frame_count': frame_count,
        'vote_summary': vote_detail or '',
    }


def _camera_match_payload(
    label: str,
    stem: str,
    confidence: float,
    top3: List[dict],
    uncertain: bool,
    frame_count: int = 1,
    vote_summary: str = '',
) -> Dict[str, Any]:
    display = format_vocab_display(label, stem)
    warning_parts = []
    if uncertain:
        warning_parts.append('置信度一般，请对照 Top3。')
    if vote_summary:
        warning_parts.append(vote_summary)
    if confidence < CAMERA_MIN_CONFIDENCE + 0.08:
        warning_parts.append('建议放慢动作或参考词库原图。')
    desc = f'词库匹配：{display}'
    if uncertain:
        desc += '（一般）'
    return {
        'mode': 'vocab',
        'matched': True,
        'gesture': label,
        'word': label,
        'stem': stem,
        'name': display,
        'description': desc,
        'confidence': confidence,
        'confidence_pct': f'{confidence:.2%}',
        'uncertain': uncertain,
        'top3': top3,
        'warning': ' '.join(warning_parts),
        'frame_count': frame_count,
        'vote_summary': vote_summary,
    }


def _frame_vocab_hit(
    image_bgr: np.ndarray,
    for_camera: bool = True,
) -> Optional[Tuple[str, str, float, bool]]:
    """单帧投票：摄像头用宽松阈值。"""
    ranked = rank_vocabulary_matches(image_bgr, top_k=1)
    relaxed = False
    if not ranked:
        ranked = rank_vocabulary_matches(image_bgr, top_k=1, relaxed=True)
        relaxed = True
    if not ranked:
        return None
    label, stem, conf = ranked[0]
    min_conf = CAMERA_RELAXED_VOTE_MIN if relaxed else (CAMERA_MIN_CONFIDENCE - 0.06)
    if for_camera and conf < min_conf:
        return None
    if not for_camera and relaxed and conf < VOCAB_RELAXED_EMBED_SIM - 0.04:
        return None
    return label, stem, conf, relaxed


def _camera_collect_votes(
    images: List[np.ndarray],
) -> Tuple[Dict[str, Dict[str, Any]], int]:
    from collections import defaultdict

    stats: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {'votes': 0, 'conf_sum': 0.0, 'label': '', 'relaxed': 0}
    )
    for img in images:
        hit = _frame_vocab_hit(img, for_camera=True)
        if not hit:
            continue
        label, stem, conf, relaxed = hit
        stats[stem]['votes'] += 1
        stats[stem]['conf_sum'] += conf
        stats[stem]['label'] = label
        stats[stem]['relaxed'] += int(relaxed)
    return stats, len(images)


def recognize_camera_frames_via_vocabulary(
    images: List[np.ndarray],
) -> Dict[str, Any]:
    """
    摄像头多帧投票 + 置信度门槛（减少乱猜）。
    单帧时等同严格版单帧识别。
    """
    valid = [im for im in images if im is not None and getattr(im, 'size', 0) > 0]
    if not valid:
        return _camera_no_match_payload('无法读取摄像头画面')

    ref = valid[len(valid) // 2]
    top3_ranked = rank_vocabulary_matches(ref, top_k=3)
    if not top3_ranked:
        top3_ranked = rank_vocabulary_matches(ref, top_k=3, relaxed=True)
    top3 = [
        {'word': format_vocab_display(l, s), 'stem': s, 'confidence': f'{c:.2%}'}
        for l, s, c in top3_ranked
    ]

    if len(valid) == 1:
        hit = _frame_vocab_hit(valid[0], for_camera=True)
        if not hit:
            return _camera_no_match_payload(
                '未识别到词库手势。建议：上半身入画、光线充足、对照 words-zhcn 原图摆拍。',
                frame_count=1,
                top3=top3,
            )
        label, stem, conf, relaxed = hit
        uncertain = relaxed or conf < CAMERA_MIN_CONFIDENCE + 0.06
        return _camera_match_payload(
            label, stem, conf, top3, uncertain=uncertain, frame_count=1,
        )

    stats, n = _camera_collect_votes(valid)
    if not stats:
        # 宽松兜底：每帧 relaxed Top1 再投票一次
        from collections import defaultdict
        loose: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {'votes': 0, 'conf_sum': 0.0, 'label': ''}
        )
        for img in valid:
            ranked = rank_vocabulary_matches(img, top_k=1, relaxed=True)
            if not ranked:
                continue
            label, stem, conf = ranked[0]
            if conf < CAMERA_FALLBACK_MIN - 0.04:
                continue
            loose[stem]['votes'] += 1
            loose[stem]['conf_sum'] += conf
            loose[stem]['label'] = label
        if loose:
            bs = max(loose.keys(), key=lambda s: (loose[s]['votes'], loose[s]['conf_sum']))
            b = loose[bs]
            ac = b['conf_sum'] / b['votes']
            if ac >= CAMERA_FALLBACK_MIN and b['votes'] >= 1:
                return _camera_match_payload(
                    b['label'], bs, ac, top3, uncertain=True, frame_count=n,
                    vote_summary=f'宽松模式 {b["votes"]}/{n} 帧，可能为「{format_vocab_display(b["label"], bs)}」',
                )
        return _camera_no_match_payload(
            f'已采集 {n} 帧仍未匹配。请打开 static/sign_app/words-zhcn 对照原图摆拍，或用手语图片识别上传截图。',
            frame_count=n,
            top3=top3,
        )

    best_stem = max(stats.keys(), key=lambda s: (stats[s]['votes'], stats[s]['conf_sum']))
    best = stats[best_stem]
    second_votes = max((stats[s]['votes'] for s in stats if s != best_stem), default=0)
    avg_conf = best['conf_sum'] / best['votes']
    min_votes = max(CAMERA_MIN_VOTES, min(2, (n + 1) // 2))
    vote_detail = f'{best["votes"]}/{n} 帧一致'

    matched = (
        best['votes'] >= min_votes
        and avg_conf >= CAMERA_MIN_CONFIDENCE
        and best['votes'] > second_votes
    )
    # 票数够但置信度略低：仍显示，标为可能
    if not matched and best['votes'] >= min_votes and avg_conf >= CAMERA_FALLBACK_MIN:
        matched = True

    if not matched:
        reason = []
        if best['votes'] < min_votes:
            reason.append(f'仅 {best["votes"]} 帧同意（需 ≥{min_votes}）')
        if avg_conf < CAMERA_FALLBACK_MIN:
            reason.append(f'平均 {avg_conf:.0%} 偏低')
        if best['votes'] <= second_votes:
            reason.append('多词票数接近')
        return _camera_no_match_payload(
            f'未通过：最接近「{format_vocab_display(best["label"], best_stem)}」'
            f'（{", ".join(reason)}）',
            frame_count=n,
            vote_detail=vote_detail,
            top3=top3,
        )

    uncertain = (
        best['relaxed'] > best['votes'] // 2
        or avg_conf < CAMERA_MIN_CONFIDENCE + 0.08
    )
    summary = f'{vote_detail}，{avg_conf:.0%}'
    if uncertain:
        summary += '（可能，请对照 Top3）'
    return _camera_match_payload(
        best['label'],
        best_stem,
        avg_conf,
        top3,
        uncertain=uncertain,
        frame_count=n,
        vote_summary=summary,
    )


def recognize_camera_frame_via_vocabulary(
    image_bgr: np.ndarray,
) -> Dict[str, Any]:
    """摄像头单帧（兼容旧调用，内部走多帧逻辑）。"""
    if image_bgr is None or image_bgr.size == 0:
        return _camera_no_match_payload('无法读取摄像头画面')
    return recognize_camera_frames_via_vocabulary([image_bgr])


def recognize_images_via_vocabulary(
    images: List[np.ndarray],
) -> Tuple[Optional[str], List[dict], Optional[str]]:
    """
    批量词库识图。
    返回 (汇总结果文本, 每张图详情列表, 错误信息)。
    """
    details: List[dict] = []
    words: List[str] = []

    for idx, image in enumerate(images):
        ranked = rank_vocabulary_matches(image)
        uncertain = False
        if not ranked:
            ranked = rank_vocabulary_matches(image, top_k=3, relaxed=True)
            uncertain = bool(ranked)
        if ranked:
            label, stem, confidence = ranked[0]
            display = format_vocab_display(label, stem)
            words.append(display)
            details.append({
                'index': idx + 1,
                'word': display,
                'stem': stem,
                'confidence': f'{confidence:.2%}',
                'matched': True,
                'uncertain': uncertain,
                'top3': [
                    {
                        'word': format_vocab_display(l, s),
                        'confidence': f'{c:.2%}',
                    }
                    for l, s, c in ranked
                ],
            })
        else:
            details.append({
                'index': idx + 1,
                'word': None,
                'stem': None,
                'confidence': '0%',
                'matched': False,
                'uncertain': False,
                'top3': [],
            })

    if not words:
        return None, details, (
            '未在词库中匹配到相近手势。建议：白底黑线、尽量只画上半身与手臂（可参考词库'
            ' words-zhcn 中 you.png、there.png 的构图），或直接使用词库示意图上传。'
        )

    summary = '、'.join(words)
    return summary, details, None
