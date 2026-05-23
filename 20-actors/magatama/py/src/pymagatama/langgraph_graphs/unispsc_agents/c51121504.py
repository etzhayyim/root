from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    drug_name: str
    purity_level: float
    regulatory_approved: bool
    is_validated: bool

def check_quality_standards(state: ProcurementState):
    valid = state['purity_level'] >= 99.0 and state['regulatory_approved']
    return {'is_validated': valid}

def route_by_validation(state: ProcurementState):
    return 'valid' if state['is_validated'] else END

graph = StateGraph(ProcurementState)
graph.add_node('check', check_quality_standards)
graph.set_entry_point('check')
graph.add_conditional_edges('check', route_by_validation, {'valid': END})
graph.add_edge('check', END)

graph = graph.compile()
