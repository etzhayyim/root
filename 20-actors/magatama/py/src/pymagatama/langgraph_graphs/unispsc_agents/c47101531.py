from typing import TypedDict
from langgraph.graph import StateGraph, END

class SepticState(TypedDict):
    tank_capacity: float
    material: str
    compliance_code: str
    is_approved: bool

def validate_specs(state: SepticState):
    state['is_approved'] = state['tank_capacity'] > 0 and state['compliance_code'] != ''
    return state

graph = StateGraph(SepticState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()