from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class EquipmentState(TypedDict):
    equipment_id: str
    specs: dict
    is_compliant: bool

def validate_specs(state: EquipmentState) -> EquipmentState:
    # Logic to verify load capacity and safety standards
    state['is_compliant'] = state['specs'].get('load_capacity', 0) > 0
    return state

def approve_procurement(state: EquipmentState) -> EquipmentState:
    # Final check for high-value items
    return state

graph = StateGraph(EquipmentState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approve_procurement)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()