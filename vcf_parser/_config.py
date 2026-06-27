import json
import logging
from pathlib import Path
from functools import lru_cache

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_machine_profile() -> dict:
    path = Path("machine_profile.json")
    if not path.exists():
        logger.warning("machine_profile.json not found — using defaults")
        return _default_machine_profile()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_kinematic_params() -> dict:
    profile = load_machine_profile()
    return {
        "max_speed_mms": profile.get("kinematic_speed_ceiling", {}).get("max_speed_mms", 800.0),
        "t_corner": profile.get("corner_brake", {}).get("measured_time_per_corner_seconds", 0.66),
        "t_corner_organic": profile.get("corner_brake", {}).get("t_corner_organic_seconds", 0.30),
        "t_lift": profile.get("kinematic_overheads", {}).get("t_lift_seconds", 2.2),
        "t_rot_vslot": profile.get("kinematic_overheads", {}).get("t_rot_vslot_seconds", 1.5),
        "setup_overhead": profile.get("kinematic_overheads", {}).get("setup_overhead_seconds", 50.0),
        "traverse_speed_mms": profile.get("kinematic_overheads", {}).get("traverse_speed_mms", 500.0),
        "traverse_distance_mm": profile.get("kinematic_overheads", {}).get("traverse_distance_between_elements_mm", 150.0),
        "return_home_time": profile.get("kinematic_overheads", {}).get("return_home_time_seconds", 15.0),
        "vibrate_curve_threshold_mm": profile.get("density_penalties", {}).get("vibrate_curve_threshold_mm", 0.2),
        "vibrate_curve_point_penalty": profile.get("density_penalties", {}).get("vibrate_curve_point_penalty_seconds", 1.2),
        "material_damping": profile.get("material_damping", {}).get("materials", {}),
    }


def _default_machine_profile() -> dict:
    return {
        "kinematic_speed_ceiling": {"max_speed_mms": 800.0},
        "corner_brake": {"measured_time_per_corner_seconds": 0.66, "t_corner_organic_seconds": 0.30},
        "kinematic_overheads": {
            "t_lift_seconds": 2.2, "t_rot_vslot_seconds": 1.5, "setup_overhead_seconds": 50.0,
            "traverse_speed_mms": 500.0, "traverse_distance_between_elements_mm": 150.0,
            "return_home_time_seconds": 15.0,
        },
        "density_penalties": {"vibrate_curve_threshold_mm": 0.2, "vibrate_curve_point_penalty_seconds": 1.2},
        "material_damping": {"materials": {}},
    }
