from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity_level: float
    safety_clearance: bool
    is_compliant: bool

def validate_chemistry(state: ProcurementState):
    state['is_compliant'] = state['purity_level'] >= 99.0 and state['safety_clearance']
    return state

def route_procurement(state: ProcurementState):
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_chemistry)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
