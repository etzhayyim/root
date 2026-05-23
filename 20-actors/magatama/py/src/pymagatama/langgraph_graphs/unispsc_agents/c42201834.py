from typing import TypedDict
from langgraph.graph import StateGraph, END

class XRayComponentState(TypedDict):
    part_number: str
    voltage_rating: float
    compliance_checked: bool
    approved: bool

def validate_tech_specs(state: XRayComponentState):
    state['compliance_checked'] = state['voltage_rating'] >= 50.0
    return state

def check_regulatory_status(state: XRayComponentState):
    state['approved'] = state['compliance_checked']
    return state

graph = StateGraph(XRayComponentState)
graph.add_node('validate', validate_tech_specs)
graph.add_node('regulatory', check_regulatory_status)
graph.set_entry_point('validate')
graph.add_edge('validate', 'regulatory')
graph.add_edge('regulatory', END)
graph = graph.compile()
