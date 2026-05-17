from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DomeSpecState(TypedDict):
    material_specs: dict
    optical_validation: bool
    compliance_check: bool

def validate_optics(state: DomeSpecState):
    transmission = state['material_specs'].get('transmission', 0)
    return {'optical_validation': transmission > 90}

def check_compliance(state: DomeSpecState):
    return {'compliance_check': True}

graph = StateGraph(DomeSpecState)
graph.add_node('optics', validate_optics)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('optics')
graph.add_edge('optics', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()