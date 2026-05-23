from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GasketState(TypedDict):
    spec_sheet: str
    compliance_check: bool
    approved: bool

def validate_specs(state: GasketState) -> GasketState:
    # Logic to verify material and pressure rating against standards
    state['compliance_check'] = 'ASME' in state['spec_sheet']
    return state

def approve_procurement(state: GasketState) -> GasketState:
    state['approved'] = state['compliance_check']
    return state

graph = StateGraph(GasketState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approve_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
