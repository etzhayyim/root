from typing import TypedDict
from langgraph.graph import StateGraph, END

class SteelProcurementState(TypedDict):
    grade: str
    thickness: float
    has_mill_cert: bool
    is_approved: bool

def validate_specs(state: SteelProcurementState):
    # Validation logic for stainless steel strip standards
    if state['grade'] in ['304', '316'] and state['has_mill_cert']:
        return {'is_approved': True}
    return {'is_approved': False}

graph = StateGraph(SteelProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
