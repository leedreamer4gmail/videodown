"""平台适配器抽象。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from videodown.core.models import ParseResult


@dataclass(frozen=True)
class ProbeSpec:
    """平台探测配置。"""

    name: str
    url: str
    order: int
    requires_cookie: bool = False


class PlatformAdapter(ABC):
    """各站点解析/下载实现需继承此类。"""

    @property
    @abstractmethod
    def slug(self) -> str:
        """内部标识，如 kuaishou / ytdlp。"""

    @abstractmethod
    def matches(self, url: str) -> bool:
        """是否由本适配器处理该链接。"""

    @abstractmethod
    def parse(self, url: str) -> ParseResult:
        """解析视频元数据与清晰度。"""

    def probe_spec(self) -> ProbeSpec | None:
        return None

    def owns_format_id(self, format_id: str | None) -> bool:
        return False

    def download_temp(self, url: str, format_id: str | None, dest: Path) -> Path:
        raise NotImplementedError(f"{self.slug} 未实现 download_temp")
