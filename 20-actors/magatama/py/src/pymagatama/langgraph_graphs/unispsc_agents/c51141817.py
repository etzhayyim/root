from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    batch_id: str
    compliance_cleared: bool
    purity_level: float

def validate_batch(state: PharmState):
    state['compliance_cleared'] = state['purity_level'] >= 99.9
    return state

def approve_procurement(state: PharmState):
    print(f'Batch {state['batch_id']} cleared for clinical distribution')
    return state

graph_builder = StateGraph(PharmState)
graph_builder.add_node('validate', validate_batch)
graph_builder.add_node('approve', approve_procurement)
graph_builder.set_entry_point('validate')
graph_builder.add_edge('validate', 'approve')
graph_builder.add_edge('approve', END)
graph = graph_builder.compile()