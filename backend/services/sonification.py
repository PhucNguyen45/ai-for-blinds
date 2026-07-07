"""Sonification service - convert data to audio descriptions."""

import logging

logger = logging.getLogger(__name__)


def sonify_data(data_points: list[dict], chart_type: str = "bar") -> dict | None:
    """
    Convert data points to an audio description and sonification parameters.

    Args:
        data_points: List of {"label": str, "value": float}
        chart_type: "bar", "line", "pie"

    Returns: {
        "description": str,  # Vietnamese description of the data
        "tones": [...],      # Pitch mapping for each data point
        "summary": str,      # Key insights
    }
    """
    try:
        if not data_points:
            return None

        # Validate data
        for dp in data_points:
            if "label" not in dp or "value" not in dp:
                return None

        labels = [dp["label"] for dp in data_points]
        values = [dp["value"] for dp in data_points]
        n = len(data_points)

        # Generate description
        max_val = max(values)
        min_val = min(values)
        max_idx = values.index(max_val)
        min_idx = values.index(min_val)
        total = sum(values)
        avg = total / n

        # Vietnamese description
        desc_parts = [f"Dữ liệu gồm {n} mục:"]
        for dp in data_points:
            desc_parts.append(f"{dp['label']}: {dp['value']}")

        summary = (
            f"Cao nhất là {labels[max_idx]} với {max_val}. "
            f"Thấp nhất là {labels[min_idx]} với {min_val}. "
            f"Trung bình là {avg:.1f}."
        )

        # Generate tone mapping (frequency range 200-800 Hz)
        if max_val > min_val:
            tones = [
                {
                    "label": labels[i],
                    "value": values[i],
                    "frequency": 200 + (values[i] - min_val) / (max_val - min_val) * 600,
                    "duration": 0.5,
                }
                for i in range(n)
            ]
        else:
            tones = [
                {"label": labels[i], "value": values[i], "frequency": 500, "duration": 0.5}
                for i in range(n)
            ]

        return {
            "description": ". ".join(desc_parts) + ".",
            "tones": tones,
            "summary": summary,
            "chart_type": chart_type,
            "total": total,
            "average": round(avg, 1),
            "max": {"label": labels[max_idx], "value": max_val},
            "min": {"label": labels[min_idx], "value": min_val},
        }

    except Exception as e:
        logger.error(f"Sonification error: {e}")
        return None
