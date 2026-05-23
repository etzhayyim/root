from langgraph.graph import StateGraph, END
from typing import TypedDict

class ProcurementState(TypedDict):
    card_type: str
    material: str
    is_compliant: bool

def validate_material(state: ProcurementState):
    state['is_compliant'] = state['material'] == 'durable-cardstock'
    return state

def check_procurement(state: ProcurementState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_material)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
