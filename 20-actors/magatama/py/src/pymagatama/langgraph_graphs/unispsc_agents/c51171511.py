from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    safety_clearance: bool
    vendor_certified: bool

def validate_purity(state: ProcurementState):
    state['safety_clearance'] = state['purity'] >= 99.5
    return 'check_vendor'

def check_vendor(state: ProcurementState):
    state['vendor_certified'] = True
    return END

graph = StateGraph(ProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_vendor', check_vendor)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_vendor')
graph.compile()
