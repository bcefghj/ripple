"""MaterialCuratorAgent - 素材收集 + 版权检测

调用合规图库(Unsplash/Pexels/Pixabay),
反向图搜检测版权风险。
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger


@dataclass
class MaterialItem:
    """单个素材"""
    type: str  # image / video / music / font
    source: str  # unsplash / pexels / ...
    url: str
    license: str
    license_notes: str
    download_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    title: str = ""
    author: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CopyrightCheckResult:
    """版权检测结果"""
    is_safe: bool
    risk_level: str  # low / medium / high
    found_matches: List[Dict[str, Any]] = field(default_factory=list)
    notes: str = ""


class MaterialCuratorAgent:
    """素材收集与版权检测"""

    def __init__(
        self,
        unsplash_access_key: str = "",
        pexels_api_key: str = "",
    ):
        self.unsplash_access_key = unsplash_access_key
        self.pexels_api_key = pexels_api_key

    async def search_images(
        self,
        query: str,
        count: int = 10,
    ) -> List[MaterialItem]:
        """并行搜索多个图库"""
        results = await asyncio.gather(
            self._search_unsplash(query, count // 2),
            self._search_pexels(query, count // 2),
            self._search_pixabay(query, count // 2),
            return_exceptions=True,
        )

        items: List[MaterialItem] = []
        for r in results:
            if isinstance(r, list):
                items.extend(r)

        return items[:count]

    async def _search_unsplash(self, query: str, count: int) -> List[MaterialItem]:
        if not self.unsplash_access_key:
            return self._mock_unsplash(query, count)

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.unsplash.com/search/photos",
                    params={"query": query, "per_page": count},
                    headers={"Authorization": f"Client-ID {self.unsplash_access_key}"},
                )
                if resp.status_code != 200:
                    return []
                data = resp.json()
                items = []
                for r in data.get("results", []):
                    items.append(MaterialItem(
                        type="image",
                        source="unsplash",
                        url=r["links"]["html"],
                        download_url=r["urls"]["regular"],
                        thumbnail_url=r["urls"]["thumb"],
                        title=r.get("description") or r.get("alt_description", ""),
                        author=r["user"]["name"],
                        license="Unsplash License",
                        license_notes="免费商用,无需署名(建议署名)",
                    ))
                return items
        except Exception as e:
            logger.warning(f"Unsplash 搜索失败: {e}")
            return []

    async def _search_pexels(self, query: str, count: int) -> List[MaterialItem]:
        if not self.pexels_api_key:
            return self._mock_pexels(query, count)

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.pexels.com/v1/search",
                    params={"query": query, "per_page": count},
                    headers={"Authorization": self.pexels_api_key},
                )
                if resp.status_code != 200:
                    return []
                data = resp.json()
                items = []
                for r in data.get("photos", []):
                    items.append(MaterialItem(
                        type="image",
                        source="pexels",
                        url=r["url"],
                        download_url=r["src"]["large"],
                        thumbnail_url=r["src"]["small"],
                        author=r["photographer"],
                        license="Pexels License",
                        license_notes="免费商用,无需署名",
                    ))
                return items
        except Exception as e:
            logger.warning(f"Pexels 搜索失败: {e}")
            return []

    async def _search_pixabay(self, query: str, count: int) -> List[MaterialItem]:
        # Pixabay 公开 API(需 KEY,但 demo 端点可用)
        return self._mock_pixabay(query, count)

    def _mock_unsplash(self, query: str, count: int) -> List[MaterialItem]:
        return [
            MaterialItem(
                type="image",
                source="unsplash",
                url=f"https://unsplash.com/s/photos/{query}",
                download_url=f"https://images.unsplash.com/photo-mock-{i}?w=1024",
                thumbnail_url=f"https://images.unsplash.com/photo-mock-{i}?w=200",
                title=f"{query} demo {i}",
                author="Mock Author",
                license="Unsplash License",
                license_notes="演示数据,生产需配置 UNSPLASH_ACCESS_KEY",
            )
            for i in range(count)
        ]

    def _mock_pexels(self, query: str, count: int) -> List[MaterialItem]:
        return [
            MaterialItem(
                type="image",
                source="pexels",
                url=f"https://www.pexels.com/search/{query}",
                download_url=f"https://images.pexels.com/photos/mock-{i}.jpg",
                license="Pexels License",
                license_notes="演示数据",
            )
            for i in range(count)
        ]

    def _mock_pixabay(self, query: str, count: int) -> List[MaterialItem]:
        return [
            MaterialItem(
                type="image",
                source="pixabay",
                url=f"https://pixabay.com/zh/search/{query}/",
                download_url=f"https://cdn.pixabay.com/photo/mock-{i}.jpg",
                license="Pixabay License",
                license_notes="演示数据",
            )
            for i in range(count)
        ]

    async def search_music(self, mood: str, duration_sec: int = 30) -> List[MaterialItem]:
        """搜索版权友好的音乐
        
        生产需对接:
        - YouTube Audio Library (需登录)
        - Free Music Archive
        - Pixabay Music
        """
        return [
            MaterialItem(
                type="music",
                source="youtube_audio_library",
                url="https://www.youtube.com/audiolibrary",
                title=f"Mock {mood} track",
                license="YouTube Audio Library License",
                license_notes="仅在 YouTube 内使用安全;其他平台需独立授权",
            ),
            MaterialItem(
                type="music",
                source="freemusicarchive",
                url="https://freemusicarchive.org",
                title=f"Mock CC {mood} track",
                license="CC BY 4.0",
                license_notes="需署名作者",
            ),
        ]

    async def reverse_image_search(self, image_url: str) -> CopyrightCheckResult:
        """反向图搜检测版权
        
        生产需对接:
        - TinEye API
        - Google Vision API
        - Yandex Reverse Image
        """
        # 演示
        return CopyrightCheckResult(
            is_safe=True,
            risk_level="low",
            found_matches=[],
            notes="演示数据:实际反向图搜需 TinEye/Google Vision API",
        )

    def get_recommended_fonts(self) -> List[Dict[str, str]]:
        """免费商用字体清单"""
        return [
            {"name": "思源黑体", "license": "SIL Open Font License", "url": "https://github.com/adobe-fonts/source-han-sans"},
            {"name": "思源宋体", "license": "SIL Open Font License", "url": "https://github.com/adobe-fonts/source-han-serif"},
            {"name": "阿里巴巴普惠体", "license": "免费商用(需登记)", "url": "https://www.alibabafonts.com"},
            {"name": "站酷高端黑", "license": "免费商用", "url": "https://www.zcool.com.cn/special/zcoolfonts"},
            {"name": "庞门正道标题体", "license": "免费商用", "url": "http://pmzd.com"},
        ]
