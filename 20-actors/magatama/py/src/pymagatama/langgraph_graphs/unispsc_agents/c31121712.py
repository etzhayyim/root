from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastState(TypedDict):
    material_composition: str
    tolerance_report: str
    quality_check: bool

def validate_composition(state: CastState):
    return {'quality_check': 'Cu-Sn-Zn' in state['material_composition']}

def verify_tolerances(state: CastState):
    return {'quality_check': float(state['tolerance_report']) <= 0.05}

graph = StateGraph(CastState)
graph.add_node('validate', validate_composition)
graph.add_node('check_dim', verify_tolerances)
graph.add_edge('validate', 'check_dim')
graph.add_edge('check_dim', END)
graph.set_entry_point('validate')
graph = graph.compile()
