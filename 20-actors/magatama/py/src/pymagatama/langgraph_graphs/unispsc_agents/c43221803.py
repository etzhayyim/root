from typing import TypedDict
from langgraph.graph import StateGraph, END

class OpticalAdapterState(TypedDict):
    part_number: str
    insertion_loss: float
    compliance_check: bool

def validate_specs(state: OpticalAdapterState):
    # Ensure optical specs meet industry standards
    state['compliance_check'] = state['insertion_loss'] < 0.5
    return state

def approve_procurement(state: OpticalAdapterState):
    return {'status': 'processed' if state['compliance_check'] else 'rejected'}

graph = StateGraph(OpticalAdapterState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approve_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
