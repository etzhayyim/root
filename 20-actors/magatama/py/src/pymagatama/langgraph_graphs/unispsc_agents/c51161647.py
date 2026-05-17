from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    has_gmp: bool
    is_compliant: bool

def validate_quality(state: ProcurementState):
    state['is_compliant'] = state['purity'] >= 99.0 and state['has_gmp']
    return 'check_safety'

def check_safety(state: ProcurementState):
    return 'end' if state['is_compliant'] else 'reject'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_quality)
graph.add_node('check_safety', check_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_safety')
graph.add_edge('check_safety', END)
graph = graph.compile()