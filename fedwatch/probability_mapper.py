from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class OutcomeDistribution:
    rate_before: float
    implied_rate_after: float
    probs: dict[int, float]

    @property
    def dominant(self) -> tuple[int, float]:
        return max(self.probs.items(), key=lambda x: x[1])

    def __str__(self) -> str:
        parts = []
        labels = {-50: "cut 50bp", -25: "cut 25bp", 0: "hold", 25: "hike 25bp", 50: "hike 50bp"}
        for bp, p in sorted(self.probs.items()):
            if p >= 0.005:
                parts.append(f"{labels.get(bp, f'{bp:+d}bp')}: {p*100:.0f}%")
        return "  |  ".join(parts)


def map_outcomes(
    rate_before: float,
    implied_rate_after: float,
    step_size: float = 0.25,
    outcomes_bp: tuple[int, ...] = (-50, -25, 0, 25, 50),
) -> OutcomeDistribution:
    delta = rate_before - implied_rate_after
    dominant_steps = delta / step_size

    probs: dict[int, float] = {}

    if abs(dominant_steps) < 0.005:
        probs[0] = 1.0
    elif 0 < dominant_steps <= 1.0:
        probs[-25] = dominant_steps
        probs[0] = 1.0 - dominant_steps
    elif dominant_steps > 1.0:
        dominant_steps = min(dominant_steps, 2.0)
        probs[-50] = max(0.0, dominant_steps - 1.0)
        probs[-25] = max(0.0, min(1.0, dominant_steps) - max(0.0, dominant_steps - 1.0))
        probs[0] = max(0.0, 1.0 - dominant_steps)
    elif -1.0 <= dominant_steps < 0.0:
        probs[25] = abs(dominant_steps)
        probs[0] = 1.0 - abs(dominant_steps)
    else:
        dominant_steps = max(dominant_steps, -2.0)
        probs[50] = max(0.0, abs(dominant_steps) - 1.0)
        probs[25] = max(0.0, min(1.0, abs(dominant_steps)) - max(0.0, abs(dominant_steps) - 1.0))
        probs[0] = max(0.0, 1.0 - abs(dominant_steps))

    total = sum(probs.values())
    if total > 0:
        probs = {k: v / total for k, v in probs.items()}

    for bp in outcomes_bp:
        probs.setdefault(bp, 0.0)

    return OutcomeDistribution(
        rate_before=rate_before,
        implied_rate_after=implied_rate_after,
        probs=probs,
    )
