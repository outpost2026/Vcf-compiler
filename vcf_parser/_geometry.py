import math
from typing import Optional


def compute_bbox(points: list) -> Optional[list]:
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return [min(xs), min(ys), max(xs), max(ys)]


def bbox_contains(outer: list, inner: list) -> bool:
    return (outer[0] <= inner[0] and outer[1] <= inner[1] and
            outer[2] >= inner[2] and outer[3] >= inner[3])


def path_length(vertices: list) -> float:
    if not vertices or len(vertices) < 2:
        return 0.0
    return sum(
        math.hypot(vertices[i][0] - vertices[i - 1][0],
                   vertices[i][1] - vertices[i - 1][1])
        for i in range(1, len(vertices))
    )


def compute_global_bbox(elements: list) -> Optional[list]:
    bbox = None
    for el in elements:
        eb = el.get("bbox")
        if not eb:
            continue
        if bbox is None:
            bbox = list(eb)
        else:
            bbox[0] = min(bbox[0], eb[0])
            bbox[1] = min(bbox[1], eb[1])
            bbox[2] = max(bbox[2], eb[2])
            bbox[3] = max(bbox[3], eb[3])
    return bbox


def detect_version(binary_data: bytes) -> str:
    if b"RDVCUTFILEVER1.0.012" in binary_data or b"VER1.0.012" in binary_data:
        return "1.0.012"
    return "1.0.013"


def block_size_for_version(version: str) -> int:
    return 210 if version == "1.0.012" else 610
