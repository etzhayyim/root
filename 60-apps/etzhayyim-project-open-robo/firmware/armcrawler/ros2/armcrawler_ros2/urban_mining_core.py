import math
from typing import Any


DEFAULT_RULES = {
    'smartphone': {'destination_bin': 'li_ion_isolation', 'target_materials': ['au', 'ag', 'cu', 'li', 'co']},
    'pc': {'destination_bin': 'mixed_pcb', 'target_materials': ['au', 'ag', 'cu']},
    'server': {'destination_bin': 'mixed_pcb', 'target_materials': ['au', 'ag', 'cu', 'pd']},
    'battery-li-ion': {'destination_bin': 'li_ion_isolation', 'target_materials': ['li', 'co', 'ni', 'cu']},
    'mixed-pcb': {'destination_bin': 'mixed_pcb', 'target_materials': ['au', 'ag', 'cu', 'pd']},
    'rare-earth-magnet': {'destination_bin': 'rare_earth_magnet', 'target_materials': ['nd', 'dy']},
}


DEFAULT_BIN_TARGETS = {
    'manual_review': [3.95, 0.52, 0.42, 0.0, 0.0, math.pi / 2.0],
    'li_ion_isolation': [3.95, 0.92, 0.42, 0.0, 0.0, math.pi / 2.0],
    'mixed_pcb': [3.95, 1.34, 0.42, 0.0, 0.0, math.pi / 2.0],
    'copper_aluminum': [3.95, 1.76, 0.42, 0.0, 0.0, math.pi / 2.0],
    'ferrous': [3.95, 2.18, 0.42, 0.0, 0.0, math.pi / 2.0],
    'rare_earth_magnet': [3.95, 2.60, 0.42, 0.0, 0.0, math.pi / 2.0],
    'reject': [3.95, 2.88, 0.42, 0.0, 0.0, math.pi / 2.0],
}


def classify_inspection(
    inspection: dict[str, Any],
    rules: dict[str, Any] | None = None,
    battery_labels: set[str] | None = None,
    low_confidence_threshold: float = 0.68,
) -> dict[str, Any]:
    rules = rules or DEFAULT_RULES
    battery_labels = battery_labels or {'battery-visible', 'swollen-battery', 'li-ion'}
    labels = [str(label) for label in inspection.get('labels', [])]
    xrf = inspection.get('xrf', {}) or {}
    stream_type = pick_stream_type(labels, xrf, rules)
    confidence = score_confidence(stream_type, labels, xrf)
    hazards = sorted(set(labels).intersection(battery_labels))

    if confidence < low_confidence_threshold:
        destination_bin = 'manual_review'
        policy = 'manual_review_low_confidence'
    elif hazards:
        destination_bin = 'li_ion_isolation'
        policy = 'isolate_battery_first'
    else:
        destination_bin = rules.get(stream_type, {}).get('destination_bin', 'manual_review')
        policy = 'sort_by_material_rule'

    return {
        'item_id': inspection.get('item_id'),
        'stream_type': stream_type,
        'target_materials': rules.get(stream_type, {}).get('target_materials', []),
        'destination_bin': destination_bin,
        'confidence': round(confidence, 3),
        'hazards': hazards,
        'policy': policy,
        'mass_g': inspection.get('mass_g'),
        'toshi_kozan_lexicon': 'com.etzhayyim.apps.toshiKozan.registerEwasteStream',
    }


def pick_stream_type(labels: list[str], xrf: dict[str, Any], rules: dict[str, Any]) -> str:
    for label in labels:
        if label in rules:
            return label
    if float(xrf.get('nd', 0.0) or 0.0) > 0.01 or float(xrf.get('dy', 0.0) or 0.0) > 0.002:
        return 'rare-earth-magnet'
    if float(xrf.get('cu', 0.0) or 0.0) > 0.08 or float(xrf.get('au_ppm', 0.0) or 0.0) > 50.0:
        return 'mixed-pcb'
    return 'unknown'


def score_confidence(stream_type: str, labels: list[str], xrf: dict[str, Any]) -> float:
    if stream_type == 'unknown':
        return 0.25
    score = 0.72
    if stream_type in labels:
        score += 0.17
    if xrf:
        score += 0.08
    return min(score, 0.99)


def build_sort_command(
    classification: dict[str, Any],
    bin_targets: dict[str, Any] | None = None,
    arm_status: str = 'ready',
    arm_ready_status: str = 'ready',
) -> dict[str, Any]:
    bin_targets = bin_targets or DEFAULT_BIN_TARGETS
    destination = str(classification.get('destination_bin') or 'manual_review')
    if destination not in bin_targets:
        destination = 'manual_review'

    if arm_status != arm_ready_status:
        return {
            'event_type': 'sort_blocked',
            'item_id': classification.get('item_id'),
            'reason': 'arm_not_ready',
            'arm_status': arm_status,
            'destination_bin': destination,
            'policy': 'hold_until_robot_ready',
        }

    return {
        'event_type': 'sort_commanded',
        'item_id': classification.get('item_id'),
        'stream_type': classification.get('stream_type'),
        'destination_bin': destination,
        'target_pose': list(bin_targets[destination]),
        'confidence': classification.get('confidence'),
        'hazards': classification.get('hazards', []),
        'policy': classification.get('policy'),
    }


def quaternion_from_euler(roll: float, pitch: float, yaw: float) -> tuple[float, float, float, float]:
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)
    return (
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
        cr * cp * cy + sr * sp * sy,
    )


def build_audit_event(classification: dict[str, Any], command: dict[str, Any]) -> dict[str, Any]:
    return {
        'event_type': command.get('event_type'),
        'item_id': command.get('item_id') or classification.get('item_id'),
        'stream_type': command.get('stream_type') or classification.get('stream_type'),
        'destination_bin': command.get('destination_bin'),
        'target_materials': classification.get('target_materials', []),
        'confidence': command.get('confidence') or classification.get('confidence'),
        'hazards': command.get('hazards') or classification.get('hazards', []),
        'policy': command.get('policy') or classification.get('policy'),
        'toshi_kozan_lexicon': 'com.etzhayyim.apps.toshiKozan.registerEwasteStream',
    }
