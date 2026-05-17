from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class LoadingEquipmentState(TypedDict):
    equipment_id: str
    spec_check: bool
    safety_clearance: bool

def validate_load_capacity(state: LoadingEquipmentState):
    print(f'Validating load capacity for {state['equipment_id']}')
    return {'spec_check': True}

def perform_safety_audit(state: LoadingEquipmentState):
    print(f'Auditing safety for {state['equipment_id']}')
    return {'safety_clearance': True}

graph = StateGraph(LoadingEquipmentState)
graph.add_node('validation', validate_load_capacity)
graph.add_node('safety', perform_safety_audit)
graph.set_entry_point('validation')
graph.add_edge('validation', 'safety')
graph.add_edge('safety', END)
app = graph.compile()