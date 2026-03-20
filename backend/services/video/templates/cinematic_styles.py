"""Preset cinematic styles for generated Autoviral videos."""

from __future__ import annotations

CINEMATIC_STYLES: dict[str, dict[str, str]] = {
    "fashion": {
        "lighting": "soft-box key light, warm rim light",
        "camera": "slow dolly-in, shallow depth of field",
        "color_grade": "high-contrast editorial look",
    },
    "product": {
        "lighting": "clean high-key product lighting",
        "camera": "macro close-up, controlled tabletop motion",
        "color_grade": "neutral commercial grade",
    },
    "lifestyle": {
        "lighting": "natural window light",
        "camera": "handheld gentle movement",
        "color_grade": "warm cinematic tone",
    },
    "tech": {
        "lighting": "cool neon edge lighting",
        "camera": "precision slider movement",
        "color_grade": "teal and blue futuristic grade",
    },
}
