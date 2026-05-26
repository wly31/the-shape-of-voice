"""
手语动画生成业务 — 分词 + 资源解析（视频合成在完整项目中由 views + ffmpeg 完成）
"""
import os
from typing import Any, Dict, List, Optional

from sign_inference.config import paths
from sign_inference.lexicon import analyze_sentence, paths_for_token


class AnimationService:
    @staticmethod
    def plan_animation(text: str, lang: str = "zh") -> Dict[str, Any]:
        """
        解析句子，返回待合成片段（初步版不生成 mp4）。
        完整版见 sign/sign_app/views.py → create_sign_language_video_zh
        """
        if lang != "zh":
            return {
                "success": False,
                "error": "初步提交版仅实现中文词表路径",
            }

        compose_tokens, segments = analyze_sentence(text, paths().words_dir)
        image_paths: List[str] = []
        missing: List[str] = []
        for tok in compose_tokens:
            ps = paths_for_token(tok, paths().words_dir)
            if ps:
                image_paths.extend(ps)
            elif tok.strip() and tok not in "，。！？,.!?;":
                missing.append(tok)

        return {
            "success": True,
            "text": text,
            "lang": lang,
            "compose_tokens": compose_tokens,
            "segments": segments,
            "image_paths": image_paths,
            "missing": missing,
            "video_url": None,
            "message": (
                f"已解析 {len(compose_tokens)} 个词，找到 {len(image_paths)} 张示意图。"
                if image_paths
                else "词库中未找到对应图片，请检查 words-zhcn 目录。"
            ),
            "hint": "调用 create_video_from_images() 接 ffmpeg 即可输出 mp4（见完整项目）。",
        }

    @staticmethod
    def create_video_from_images(
        image_paths: List[str],
        output_path: Optional[str] = None,
        fps: int = 2,
    ) -> Optional[str]:
        """
        TODO: 使用 OpenCV / imageio + ffmpeg 将图片序列合成为 mp4。
        完整实现见 sign/sign_app/views.py
        """
        if not image_paths:
            return None
        output_path = output_path or os.path.join(
            paths().sign_output_dir, "preview_output.mp4"
        )
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        # 占位：仅返回计划路径，不实际编码
        return output_path if os.path.isfile(image_paths[0]) else None
