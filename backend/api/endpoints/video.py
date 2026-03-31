"""Video factory endpoint aliases."""

from api.endpoints.videos import create_video, list_videos, router

__all__ = ["router", "list_videos", "create_video"]
