"""Video service package.

Keep package initialization lightweight to avoid circular imports when Celery
loads task modules (for example runpod.tasks importing video.queue).
"""

__all__: list[str] = []
