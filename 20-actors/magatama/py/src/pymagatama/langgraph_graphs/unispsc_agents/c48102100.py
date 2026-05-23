from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END

class EquipmentState(TypedDict):
    equipment_id: str
    specs: dict
    validation_checks: list[str]
    is_approved: bool

def validate_specs(state: EquipmentState):
    checks = []
    if state['specs'].get('load_capacity_kg', 0) > 0:
        checks.append('Capacity verified')
    return {'validation_checks': checks}

def approve_equipment(state: EquipmentState):
    return {'is_approved': len(state['validation_checks']) > 0}

graph = StateGraph(EquipmentState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approve_equipment)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
