from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PhysicsEquipState(TypedDict):
    specs: dict
    validation_checks: List[str]
    approved: bool

def validate_physics_equipment(state: PhysicsEquipState):
    checks = []
    if 'calibration' in state['specs']: checks.append('CALIBRATION_VERIFIED')
    if 'end_use' in state['specs']: checks.append('EXPORT_COMPLIANCE_VERIFIED')
    return {'validation_checks': checks, 'approved': len(checks) == 2}

graph = StateGraph(PhysicsEquipState)
graph.add_node('validate', validate_physics_equipment)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()