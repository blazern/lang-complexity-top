from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class YTVideo:
    url: str
    title: str
    title_pattern: str

    def to_dict(self):
        return asdict(self)

@dataclass(frozen=True)
class YTChannel:
    title: str
    url: str
    videos: set[YTVideo]

    def to_dict(self):
        return {
            "title": self.title,
            "url": self.url,
            "videos": [video.to_dict() for video in self.videos],
        }