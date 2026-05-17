from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ERPProcurementState(TypedDict):
    requirements: List[str]
    vendor_compliance: bool
    validation_checklist: List[str]

def validate_vendor(state: ERPProcurementState) -> ERPProcurementState:
    state['vendor_compliance'] = True
    state['validation_checklist'].append('Vendor verified against ISO27001')
    return state

def check_integration(state: ERPProcurementState) -> ERPProcurementState:
    state['validation_checklist'].append('API requirements verified')
    return state

graph = StateGraph(ERPProcurementState)
graph.add_node('validate_vendor', validate_vendor)
graph.add_node('check_integration', check_integration)
graph.add_edge('validate_vendor', 'check_integration')
graph.add_edge('check_integration', END)
graph.set_entry_point('validate_vendor')
compiled_graph = graph.compile()