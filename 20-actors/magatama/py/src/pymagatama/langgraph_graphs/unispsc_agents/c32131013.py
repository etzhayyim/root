from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MaskState(TypedDict):
    spec_id: str
    flatness_value: float
    defect_count: int
    is_compliant: bool

def validate_mask_specs(state: MaskState):
    # Business logic for photolithography mask validation
    compliant = state['flatness_value'] < 1.0 and state['defect_count'] == 0
    return {'is_compliant': compliant}

def route_by_compliance(state: MaskState):
    return 'compliant' if state['is_compliant'] else 'rejected'

graph = StateGraph(MaskState)
graph.add_node('validate', validate_mask_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()