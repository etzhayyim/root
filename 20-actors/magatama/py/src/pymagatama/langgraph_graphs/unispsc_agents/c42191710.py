from typing import TypedDict
from langgraph.graph import StateGraph, END

class GasCylinderMountState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_safety_standards(state: GasCylinderMountState):
    # Business logic for cylinder cart certification
    state['is_compliant'] = state['spec_data'].get('anti_tip_certification', False)
    return state

def route_by_compliance(state: GasCylinderMountState):
    return 'compliant' if state['is_compliant'] else 'manual_review'

graph = StateGraph(GasCylinderMountState)
graph.add_node('safety_check', validate_safety_standards)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', END)
app = graph.compile()
