from typing import TypedDict
from langgraph.graph import StateGraph, END

class ScrubProcurementState(TypedDict):
    material: str
    compliance_cert: bool
    approved: bool

def validate_materials(state: ScrubProcurementState):
    state['approved'] = 'polyester' in state['material'].lower() and state['compliance_cert']
    return state

graph = StateGraph(ScrubProcurementState)
graph.add_node('validate', validate_materials)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
