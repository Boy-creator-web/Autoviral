"""Template builder for common video generation patterns."""

from __future__ import annotations

from services.video.templates.cinematic_styles import CINEMATIC_STYLES


def build_video_template(template_type: str, *, script: str) -> dict[str, str]:
    """Build a reusable template payload for downstream renderers.

    Args:
        template_type: Video archetype, for example ``fashion`` or ``product``.
        script: Primary script or storyline to render.

    Returns:
        Dictionary containing style directives and script content.
    """
    style = CINEMATIC_STYLES.get(template_type, CINEMATIC_STYLES["lifestyle"])
    return {
        "template_type": template_type,
        "script": script,
        "lighting": style["lighting"],
        "camera": style["camera"],
        "color_grade": style["color_grade"],
    }
