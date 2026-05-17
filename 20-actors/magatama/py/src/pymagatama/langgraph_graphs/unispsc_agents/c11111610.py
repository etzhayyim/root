from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    batch_id: str
    purity_level: float
    compliance_checked: bool
    approved: bool

def validate_compliance(state: MineralState):
    # Simulate regulatory check
    state['compliance_checked'] = state['purity_level'] > 95.0
    return state

def approve_batch(state: MineralState):
    state['approved'] = state['compliance_checked']
    return state

graph = StateGraph(MineralState)
graph.add_node('validate', validate_compliance)
graph.add_node('approve', approve_batch)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()