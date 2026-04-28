"""VisualProducerAgent - 封面/插图生成

主力: 腾讯混元生图 (赛道适配性)
辅助: SDXL + ControlNet (品牌 LoRA)
策略: 5 个候选封面(高对比/温和/极简/人脸/无脸)
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger


@dataclass
class CoverDescription:
    """封面设计描述"""
    style: str  # 高对比/温和/极简/人脸/无脸
    main_text: str  # 主文字 ≤ 5 词
    color_palette: str
    description: str
    prompt: str = ""  # 给生图模型的 prompt


@dataclass
class GeneratedImage:
    """已生成的图像"""
    url: str
    prompt: str
    style: str
    size: str = "1024x1024"
    is_mock: bool = False


class VisualProducerAgent:
    """封面与插图生成"""

    def __init__(self, hunyuan_secret_id: str = "", hunyuan_secret_key: str = ""):
        self.hunyuan_secret_id = hunyuan_secret_id
        self.hunyuan_secret_key = hunyuan_secret_key

    async def generate_covers(
        self,
        descriptions: List[CoverDescription],
        topic: str,
    ) -> List[GeneratedImage]:
        """并行生成多个候选封面"""
        if not descriptions:
            return []

        # 并行调用
        results = await asyncio.gather(
            *[self._generate_single(d, topic) for d in descriptions],
            return_exceptions=True,
        )

        images = []
        for r in results:
            if isinstance(r, GeneratedImage):
                images.append(r)
            elif isinstance(r, Exception):
                logger.warning(f"生图失败: {r}")

        return images

    async def _generate_single(
        self,
        desc: CoverDescription,
        topic: str,
    ) -> GeneratedImage:
        """单张图生成"""
        # 构造 prompt
        prompt = self._build_prompt(desc, topic)

        # 优先调混元(生产)
        if self.hunyuan_secret_id and self.hunyuan_secret_key:
            try:
                url = await self._call_hunyuan(prompt)
                return GeneratedImage(
                    url=url,
                    prompt=prompt,
                    style=desc.style,
                )
            except Exception as e:
                logger.warning(f"混元生图失败: {e}, 使用 mock")

        # Fallback: 返回 placeholder
        return GeneratedImage(
            url=f"https://via.placeholder.com/1024x1024?text={desc.main_text or topic[:5]}",
            prompt=prompt,
            style=desc.style,
            is_mock=True,
        )

    def _build_prompt(self, desc: CoverDescription, topic: str) -> str:
        """构造生图 prompt"""
        style_map = {
            "高对比": "high contrast, vibrant colors, bold composition",
            "温和": "soft pastel colors, warm, inviting",
            "极简": "minimalist, white space, clean typography",
            "人脸": "expressive human face, emotion-driven, close-up",
            "无脸": "product photography, no faces, lifestyle setting",
        }

        style_en = style_map.get(desc.style, "professional, magazine quality")

        prompt_parts = [
            f"Cover image for content about '{topic}',",
            f"style: {style_en},",
            f"color palette: {desc.color_palette},",
            f"composition: {desc.description},",
            "9:16 vertical aspect ratio for mobile,",
            "high resolution, professional, social media ready,",
            "no text overlay (text will be added separately)",
        ]
        return " ".join(prompt_parts)

    async def _call_hunyuan(self, prompt: str) -> str:
        """调用腾讯混元生图 API
        
        注意:实际 API 需要腾讯云 SDK 签名,这里简化为 OpenAI 兼容接口示例
        """
        # 此处为简化示例,生产需使用 tencentcloud-sdk-python
        # 或 SubmitHunyuanImageJob API + 轮询
        raise NotImplementedError("Hunyuan SDK integration needed")

    async def generate_layout_with_text(
        self,
        background_url: str,
        main_text: str,
        sub_text: str = "",
    ) -> Dict[str, Any]:
        """图文叠加(背景 AI 生成 + 文字程序化绘制)
        
        策略:不让 AI 直接生成中文(易乱码),
        而是 AI 生成背景 + 后端程序化叠加文字
        """
        return {
            "background_url": background_url,
            "main_text": main_text,
            "sub_text": sub_text,
            "font_recommendations": ["思源黑体 Bold", "阿里巴巴普惠体 Bold"],
            "stroke_color": "#000000",
            "main_text_color": "#FFFFFF",
            "safe_area": "中央 80%",
            "render_url": f"/api/render-cover?bg={background_url}&text={main_text}",
        }
