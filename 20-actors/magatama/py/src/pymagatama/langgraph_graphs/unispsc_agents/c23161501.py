from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LiftingEquipmentState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_load_capacity(state: LiftingEquipmentState):
    capacity = state['specs'].get('load_capacity_tons', 0)
    if capacity <= 0:
        state['validation_errors'].append('Load capacity must be positive.')
    return state

def check_certification(state: LiftingEquipmentState):
    cert = state['specs'].get('safety_cert')
    if not cert:
        state['validation_errors'].append('Missing safety certification.')
    return state

graph = StateGraph(LiftingEquipmentState)
graph.add_node('validate_capacity', validate_load_capacity)
graph.add_node('check_cert', check_certification)
graph.set_entry_point('validate_capacity')
graph.add_edge('validate_capacity', 'check_cert')
graph.add_edge('check_cert', END)
graph = graph.compile()