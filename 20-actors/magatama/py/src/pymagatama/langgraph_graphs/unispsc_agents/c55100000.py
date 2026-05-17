from langgraph.graph import StateGraph, END
from typing import TypedDict

class PrintMediaState(TypedDict):
    quantity: int
    spec_approved: bool
    vendor_assigned: str

def validate_specs(state: PrintMediaState):
    state['spec_approved'] = state['quantity'] > 0
    return state

def assign_vendor(state: PrintMediaState):
    state['vendor_assigned'] = 'Standard_Print_House_01' if state['spec_approved'] else 'None'
    return state

graph = StateGraph(PrintMediaState)
graph.add_node('validate', validate_specs)
graph.add_node('assign', assign_vendor)
graph.set_entry_point('validate')
graph.add_edge('validate', 'assign')
graph.add_edge('assign', END)
graph = graph.compile()