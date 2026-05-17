from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PinProcurementState(TypedDict):
    material: str
    length: float
    inspection_passed: bool
    vendor_compliant: bool

def validate_materials(state: PinProcurementState):
    state['inspection_passed'] = state['material'] == 'stainless_steel'
    return state

def check_compliance(state: PinProcurementState):
    state['vendor_compliant'] = True
    return state

graph = StateGraph(PinProcurementState)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()