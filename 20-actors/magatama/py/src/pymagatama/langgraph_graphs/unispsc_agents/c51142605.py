from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material: str
    regulatory_compliant: bool
    vendor_certified: bool

def validate_product(state: ProcurementState):
    state['regulatory_compliant'] = True # Mock check for pharmaceutical control
    return 'check_vendor'

def check_vendor(state: ProcurementState):
    state['vendor_certified'] = True # Mock certification check
    return END

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_product)
graph.add_node('check_vendor', check_vendor)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_vendor')
graph.add_edge('check_vendor', END)
graph = graph.compile()
