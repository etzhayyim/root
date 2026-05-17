from typing import TypedDict
from langgraph.graph import StateGraph, END

class OilGunState(TypedDict):
    pressure: float
    material_approved: bool
    is_valid: bool

def validate_pressure(state: OilGunState):
    state['is_valid'] = state['pressure'] > 0 and state['pressure'] <= 70
    return state

def check_compliance(state: OilGunState):
    state['material_approved'] = True
    return state

graph = StateGraph(OilGunState)
graph.add_node('validate', validate_pressure)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()